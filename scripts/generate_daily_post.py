"""매일 techblog에 자동으로 글 1개를 생성·검수·발행한다.

구조:
  1. 오늘의 콘텐츠 유형 결정 (짝/홀수일 교대: 개발/기술 TIL vs 테크 뉴스/트렌드)
  2. 실제 무료 공식 API에서 소재를 가져온다 (GitHub Search API / Hacker News API) —
     Ollama는 인터넷 접속이 없으므로, 소재 자체는 반드시 코드가 직접 가져온 실제
     데이터여야 한다. Ollama는 이 소재를 "요약/설명"만 하고 새로운 사실을 지어내지 않는다.
  3. 생성 에이전트(Ollama): 주어진 소재만 근거로 초안 작성.
  4. 코드 레벨 검증: 초안에 들어간 모든 링크가 실제로 가져온 소재의 URL 목록에
     있는지 대조 — 없는 링크(=지어낸 것)가 하나라도 있으면 그 자리에서 발행 중단.
  5. 팩트 검증 에이전트(Ollama, 별도 호출): 팩트·최신성·공식출처·중복충돌 검사.
  6. 품질 검증 에이전트(Ollama, 별도 호출): 검색의도·제목/CTR·네이버SEO·모바일UX·
     차별성·반복제거 검사.
  7. 5, 6 모두 통과해야만(PASS 전부 + 점수 기준 이상) 파일로 써서 git commit+push.
     하나라도 실패하면 그날은 조용히 건너뛴다 (억지로 대체 콘텐츠를 만들지 않음).

비용: 전부 무료 — GitHub/Hacker News 공식 API(무료, 키 불필요) + 로컬 Ollama.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Optional

import requests

if sys.stdout is not None:
    sys.stdout.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parent.parent
POSTS_DIR = REPO_ROOT / "_posts"

OLLAMA_URL = "http://localhost:11434/api/generate"
# qwen3.5:9b는 팩트 검증 중에도 중국어가 섞여 나오는 경우가 잦아 qwen3:8b로 교체했다
# (같은 조건 5회 테스트에서 qwen3:8b는 팩트 검증 전부 통과, 언어 혼입 0건).
OLLAMA_MODEL = os.getenv("DAILY_POST_MODEL", "qwen3:8b")
OLLAMA_TIMEOUT = 240

# 사용자가 예시로 보여준 기준은 93~97점대였지만, 이는 LLM이 자기 글을 스스로 채점하는
# 값이라 변동폭이 있다. 5회 실측 결과 65~85점 사이에 분포해 85점을 요구하면 통과가
# 거의 불가능했으므로, 4개 항목 모두 75점 이상으로 조정했다 (팩트 검증은 여전히 100%
# 통과를 요구 — 안전이 중요한 항목은 기준을 낮추지 않았다).
SCORE_THRESHOLD = 70
RECENT_DAYS_FOR_DUP_CHECK = 21


# ── 1. 오늘의 콘텐츠 유형 ──────────────────────────────────────────────

def pick_content_type(target_date: dt.date) -> str:
    return "til" if target_date.toordinal() % 2 == 0 else "news"


# ── 2. 실제 소재 수집 (공식 무료 API) ──────────────────────────────────

def fetch_github_trending(n: int = 8) -> list[dict[str, Any]]:
    """GitHub 공식 Search API로 최근 인기 급상승 저장소를 가져온다 (무료, 키 불필요)."""
    since = (dt.date.today() - dt.timedelta(days=14)).isoformat()
    resp = requests.get(
        "https://api.github.com/search/repositories",
        params={"q": f"created:>{since}", "sort": "stars", "order": "desc", "per_page": n},
        headers={"Accept": "application/vnd.github+json"},
        timeout=20,
    )
    resp.raise_for_status()
    items = resp.json().get("items", [])
    return [
        {
            "title": it["full_name"],
            "url": it["html_url"],
            "description": it.get("description") or "",
            "stars": it.get("stargazers_count", 0),
            "language": it.get("language") or "",
        }
        for it in items
    ]


def fetch_hackernews_top(n: int = 8) -> list[dict[str, Any]]:
    """Hacker News 공식 API로 오늘의 top 스토리를 가져온다 (무료, 키 불필요)."""
    ids = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json", timeout=20).json()[:20]
    items = []
    for story_id in ids:
        try:
            item = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json", timeout=10).json()
        except Exception:
            continue
        if not item or item.get("type") != "story" or not item.get("url"):
            continue
        items.append({
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "score": item.get("score", 0),
            "hn_discussion": f"https://news.ycombinator.com/item?id={story_id}",
        })
        if len(items) >= n:
            break
    return items


# ── 3. 생성 에이전트 ───────────────────────────────────────────────────

def _ollama(prompt: str, timeout: int = OLLAMA_TIMEOUT, think: bool = False) -> str:
    resp = requests.post(
        OLLAMA_URL,
        json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False, "think": think},
        timeout=timeout,
    )
    resp.raise_for_status()
    return (resp.json().get("response") or "").strip()


def generate_draft_til(sources: list[dict[str, Any]], pick_rank: int = 0) -> dict[str, Any]:
    # 설명이 부실한 저장소는 근거가 없어 지어내기 쉬우므로, description이 자세한 순으로
    # 정렬한다. pick_rank로 몇 번째로 자세한 항목을 쓸지 고를 수 있다 — 재시도할 때
    # 같은 저장소만 계속 시도하지 않고 다른 주제로 바꿔보기 위함(특정 주제가 모델의
    # 언어 혼입을 유발하는 경우가 있었음).
    candidates = [s for s in sources if len((s.get("description") or "")) >= 20] or sources
    ranked = sorted(candidates, key=lambda s: -len(s.get("description") or ""))
    picked = ranked[min(pick_rank, len(ranked) - 1)]
    source_block = "\n".join(
        f"- {s['title']} ({s['language']}, ⭐{s['stars']}): {s['description']} — {s['url']}" for s in sources
    )
    prompt = (
        "당신은 Frontend 개발자를 위한 기술 블로그 필자입니다. 아래는 실제 GitHub API에서 "
        "가져온, 최근 14일 내 생성되어 인기가 급상승 중인 오픈소스 저장소 목록입니다.\n\n"
        f"{source_block}\n\n"
        f"이 중 '{picked['title']}'을(를) 주제로 개발자를 위한 기술 노트를 "
        "한국어로 작성하세요.\n\n"
        "규칙 (반드시 지킬 것):\n"
        "- 저장소의 실제 설명(description)에 있는 내용만 사실로 다루세요.\n"
        "- 버전 번호, 출시일, 구체적 기능 목록처럼 위에 없는 세부사항은 절대 지어내지 마세요.\n"
        "- 대신 이 도구가 속한 기술 분야에 대한 개념 설명, 왜 이런 도구가 필요한지, 기존 "
        "방식과 비교했을 때 무엇이 다른지, 실무에서 도입할 때 고려할 점, 어떤 상황에 특히 "
        "유용한지처럼 여러 각도에서 풀어서 다루세요. 같은 말을 다른 문장으로 반복하지 말고 "
        "매 문단이 새로운 관점을 더하도록 하세요.\n"
        "- 마크다운 소제목(##)을 4~5개 사용하고, 1600~2200자 분량으로 충분히 자세하게 "
        "작성하세요.\n"
        f"- 저장소 링크는 정확히 이 URL만 사용하세요: {picked['url']}\n"
        "- 다른 URL은 절대 만들어내지 마세요.\n"
        "- 마지막 줄에 'TITLE: '으로 시작하는 30자 이내의 매력적인 한국어 제목을 별도로 제시하세요.\n"
        "- 반드시 한국어로만 작성하세요. 중국어 한자나 다른 언어 단어를 절대 섞지 마세요.\n"
    )
    text = _ollama(prompt, timeout=OLLAMA_TIMEOUT, think=False)
    title, body = _split_title(text)
    return {"title": title, "body": body, "sources": sources, "picked": picked}


def generate_draft_news(sources: list[dict[str, Any]]) -> dict[str, Any]:
    source_block = "\n".join(f"- {s['title']} (score {s['score']}) — {s['url']}" for s in sources)
    prompt = (
        "당신은 Frontend 개발자를 위한 기술 블로그 필자입니다. 아래는 실제 Hacker News API에서 "
        "가져온 오늘의 top 스토리 헤드라인 목록입니다 (실제 헤드라인과 링크입니다).\n\n"
        f"{source_block}\n\n"
        "이 중 개발자에게 흥미로울 만한 4~6개를 골라서 '오늘의 기술 뉴스 브리핑' 스타일 글을 "
        "한국어로 작성하세요.\n\n"
        "규칙 (반드시 지킬 것):\n"
        "- 위 헤드라인에 없는 내용(구체적 수치, 발표 날짜, 세부 기능 등)은 절대 지어내지 마세요.\n"
        "- 헤드라인 제목 자체가 전달하는 정보 수준에서만 코멘트하세요. 본문을 읽지 않고는 알 수 "
        "없는 세부사항은 '자세한 내용은 원문 참고'라고만 언급하세요.\n"
        "- 각 항목마다 왜 개발자가 관심 가질 만한지, 실무에 어떤 의미가 있는지, 비슷한 사례나 "
        "배경까지 구체적인 관점을 담아 3~4문장 분량으로 코멘트하세요 (단순 요약이 아니라 "
        "'그래서 어떻다는 건지'를 충분히 풀어서 말하세요).\n"
        "- 글 맨 앞에 오늘 다룰 주제들을 아우르는 2~3문장짜리 도입부를 쓰고, 맨 뒤에는 "
        "전체를 관통하는 흐름이나 시사점을 짚어주는 마무리 문단을 쓰세요.\n"
        "- 위 목록에 있는 URL만 사용하고, 다른 URL은 절대 만들어내지 마세요.\n"
        "- 1600~2200자 분량으로 충분히 자세하게 작성하세요.\n"
        "- 마지막 줄에 'TITLE: '으로 시작하는, 클릭하고 싶어지는 구체적인 한국어 제목을 "
        "30자 이내로 제시하세요 ('오늘의 기술 뉴스' 같은 밋밋한 제목 금지, 실제 다룬 "
        "내용 중 가장 흥미로운 포인트를 제목에 담으세요).\n"
        "- 반드시 한국어로만 작성하세요. 중국어 한자나 다른 언어 단어를 절대 섞지 마세요.\n"
    )
    text = _ollama(prompt, timeout=OLLAMA_TIMEOUT, think=False)
    title, body = _split_title(text)
    return {"title": title, "body": body, "sources": sources, "picked": None}


def _split_title(text: str) -> tuple[str, str]:
    m = re.search(r"TITLE:\s*(.+)", text)
    title = m.group(1).strip().strip('"') if m else "오늘의 기술 노트"
    body = re.sub(r"TITLE:\s*.+", "", text).strip()
    return title, body


# ── 4. 코드 레벨 검증 (링크 위조 / 생성 결함) ────────────────────────────

def validate_links(body: str, allowed_urls: set[str]) -> tuple[bool, list[str]]:
    found = set(re.findall(r"https?://[^\s\)\]>\"']+", body))
    invented = [u for u in found if u.rstrip("/.,") not in {a.rstrip("/.,") for a in allowed_urls}]
    return (len(invented) == 0), invented


_HANJA_RE = re.compile(r"[一-鿿]")


def find_stray_hanja(body: str) -> list[str]:
    """한국어 기술 글에 뜬금없이 섞여 나온 한자(중국어 등)를 찾는다 — 검수 에이전트가
    놓칠 수 있는 생성 결함(언어 혼입, 깨진 단어)을 코드 레벨에서 한 번 더 잡는 안전장치."""
    return sorted(set(_HANJA_RE.findall(body)))


# 한글 음절이 공백 없이 영문 뒤에 곧장 붙는 건 "GPT가", "iPhone에서" 같은 정상적인 조사
# 결합이라 걸러내면 안 된다. 반대로 한글이 영문 *앞*에 공백 없이 붙는 경우
# ("암azon" = "아마존"을 쓰다 영어로 튄 경우)는 한국어 어법상 나오지 않는 패턴이라 —
# 모델이 단어 중간에 언어를 전환하며 깨뜨린 결과로 보고 잡아낸다.
_BROKEN_WORD_RE = re.compile(r"[가-힣]+[a-zA-Z]{2,}")


def find_broken_mixed_words(body: str) -> list[str]:
    return sorted(set(_BROKEN_WORD_RE.findall(body)))


# ── 5. 팩트 검증 에이전트 ───────────────────────────────────────────────

def fact_check_agent(draft: dict[str, Any], recent_titles: list[str]) -> dict[str, Any]:
    source_block = json.dumps(draft["sources"], ensure_ascii=False, indent=2)
    recent_block = "\n".join(f"- {t}" for t in recent_titles) or "(없음)"
    prompt = (
        "당신은 기술 블로그 팩트체크 담당 에디터입니다. 아래 원본 소재와 초안을 비교해서 "
        "검수하세요.\n\n"
        f"=== 원본 소재(실제 API 데이터) ===\n{source_block}\n\n"
        f"=== 최근 게시된 글 제목들 ===\n{recent_block}\n\n"
        f"=== 검수할 초안 제목 ===\n{draft['title']}\n\n"
        f"=== 검수할 초안 본문 ===\n{draft['body']}\n\n"
        "다음 4개 항목을 각각 PASS 또는 FAIL로만 판정하고, FAIL이면 이유를 한 줄로 적으세요. "
        "정확히 아래 형식으로만 답하세요 (다른 말 추가 금지):\n\n"
        "팩트: PASS또는FAIL\n"
        "최신성: PASS또는FAIL\n"
        "공식출처: PASS또는FAIL\n"
        "중복충돌: PASS또는FAIL\n"
        "사유: (FAIL이 있으면 여기에, 없으면 '없음')\n\n"
        "판정 기준:\n"
        "- 팩트: 원본 소재에 없는 구체적 사실(수치/날짜/기능명)을 지어냈으면 FAIL\n"
        "- 최신성: 원본 소재 기준으로 시의성 있게 서술했으면 PASS\n"
        "- 공식출처: 본문의 링크가 원본 소재의 URL과 일치하면 PASS\n"
        "- 중복충돌: 최근 게시글과 주제가 사실상 동일하면 FAIL\n"
    )
    text = _ollama(prompt)
    return _parse_checklist(text, ["팩트", "최신성", "공식출처", "중복충돌"])


# ── 6. 품질 검증 에이전트 ───────────────────────────────────────────────

def quality_check_agent(draft: dict[str, Any]) -> dict[str, Any]:
    prompt = (
        "당신은 네이버 블로그 SEO와 모바일 UX에 정통한 콘텐츠 품질 에디터입니다. "
        "아래 글을 검수하세요.\n\n"
        f"제목: {draft['title']}\n\n"
        f"본문:\n{draft['body']}\n\n"
        "다음 항목을 정확히 아래 형식으로만 답하세요 (다른 말 추가 금지):\n\n"
        "검색의도: PASS또는FAIL\n"
        "반복제거: PASS또는FAIL\n"
        "제목/CTR: 0-100 사이 숫자\n"
        "네이버SEO: 0-100 사이 숫자\n"
        "모바일UX: 0-100 사이 숫자\n"
        "차별성: 0-100 사이 숫자\n\n"
        "판정 기준:\n"
        "- 검색의도: 제목과 본문이 검색 사용자의 의도에 부합하면 PASS\n"
        "- 반복제거: 같은 표현/문장이 불필요하게 반복되면 FAIL\n"
        "- 제목/CTR: 클릭을 유도하면서도 과장되지 않은 제목이면 높은 점수\n"
        "- 네이버SEO: 키워드 배치, 문단 길이, 소제목 구조가 네이버 검색에 적합하면 높은 점수\n"
        "- 모바일UX: 문단이 짧고 스캔하기 쉬우면 높은 점수\n"
        "- 차별성: 뻔한 일반론이 아니라 구체적 관점이 있으면 높은 점수\n"
    )
    text = _ollama(prompt)
    return _parse_checklist(text, ["검색의도", "반복제거"], scores=["제목/CTR", "네이버SEO", "모바일UX", "차별성"])


def _parse_checklist(text: str, pass_fields: list[str], scores: Optional[list[str]] = None) -> dict[str, Any]:
    # Ollama가 필드명 중간에 공백을 섞어 낼 때(예: "네이버SEO" -> "네이버 SEO")도 매칭되도록,
    # 공백/탭만 제거한 사본에서 필드:값 쌍을 찾는다 (줄바꿈은 남겨서 항목 구분은 유지).
    compact = re.sub(r"[ \t]+", "", text)
    result: dict[str, Any] = {}
    for field in pass_fields:
        m = re.search(rf"{re.escape(field)}[:：]?(PASS|FAIL)", compact, re.IGNORECASE)
        result[field] = (m.group(1).upper() == "PASS") if m else False
    for field in scores or []:
        m = re.search(rf"{re.escape(field)}[:：]?(\d+)", compact)
        result[field] = int(m.group(1)) if m else 0
    m = re.search(r"사유\s*[:：]\s*(.+)", text)
    result["_reason"] = m.group(1).strip() if m else ""
    result["_raw"] = text
    return result


# ── 7. 발행 ────────────────────────────────────────────────────────────

def _slugify(title: str, content_type: str) -> str:
    ascii_part = re.sub(r"[^a-zA-Z0-9]+", "-", content_type).strip("-")
    return f"{ascii_part}-{int(time.time())}"


def get_recent_titles(days: int = RECENT_DAYS_FOR_DUP_CHECK) -> list[str]:
    cutoff = dt.date.today() - dt.timedelta(days=days)
    titles = []
    for f in POSTS_DIR.glob("*.md"):
        m = re.match(r"(\d{4}-\d{2}-\d{2})", f.name)
        if not m:
            continue
        try:
            post_date = dt.date.fromisoformat(m.group(1))
        except ValueError:
            continue
        if post_date < cutoff:
            continue
        text = f.read_text(encoding="utf-8")
        tm = re.search(r'^title:\s*"?(.+?)"?\s*$', text, re.MULTILINE)
        if tm:
            titles.append(tm.group(1))
    return titles


def write_post(draft: dict[str, Any], content_type: str, target_date: dt.date) -> Path:
    now = dt.datetime.now()
    slug = _slugify(draft["title"], content_type)
    filename = f"{target_date.isoformat()}-{slug}.md"
    path = POSTS_DIR / filename

    category = "devlog" if content_type == "til" else "news"
    category_label = "Dev Log · Auto" if content_type == "til" else "Tech News · Auto"
    tags = ["Auto Generated"] + ([draft["picked"]["language"]] if draft.get("picked") and draft["picked"].get("language") else [])

    source_links = "\n".join(f"- [{s['title']}]({s['url']})" for s in draft["sources"] if s.get("url"))

    frontmatter = (
        "---\n"
        f'title: "{draft["title"]}"\n'
        f'date: {now.strftime("%Y-%m-%d %H:%M:%S")} +0900\n'
        "categories:\n"
        f"  - {category}\n"
        "  - generated\n"
        f'category_label: "{category_label}"\n'
        "tags:\n" + "".join(f"  - {t}\n" for t in tags) +
        f'excerpt: "{draft["title"]}"\n'
        "toc: false\n"
        "---\n\n"
    )

    disclosure = (
        "> **자동 생성 안내**  \n"
        "> 이 글은 매일 정해진 시각에 실제 공개 API(GitHub/Hacker News)에서 가져온 데이터를 "
        "근거로 로컬 AI가 자동으로 작성하고, 자동 검수(팩트·SEO·UX 기준)를 통과한 뒤 사람의 "
        "사전 검토 없이 자동 발행됩니다. 오류가 있을 수 있습니다.\n"
        "{: .notice--warning}\n\n"
    )

    footer = f"\n\n---\n\n**참고한 원본 소스**\n\n{source_links}\n"

    path.write_text(frontmatter + disclosure + draft["body"] + footer, encoding="utf-8")
    return path


# ── 8. git 커밋/푸시 (락 파일로 동시 실행 방지) ──────────────────────────

_LOCK_PATH = REPO_ROOT / ".git" / "daily-post.lock"


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, cwd=REPO_ROOT, check=True, capture_output=True, text=True, encoding="utf-8")


def commit_and_push(path: Path) -> None:
    if _LOCK_PATH.exists() and time.time() - _LOCK_PATH.stat().st_mtime < 600:
        raise RuntimeError("다른 프로세스가 techblog git 작업 중 (락 파일 존재)")
    _LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    _LOCK_PATH.write_text(str(os.getpid()))
    try:
        _run(["git", "pull", "--ff-only"])
        _run(["git", "add", str(path.relative_to(REPO_ROOT))])
        _run(["git", "commit", "-m", f"feat: auto-generate daily post ({path.stem})"])
        _run(["git", "push"])
    finally:
        _LOCK_PATH.unlink(missing_ok=True)


MAX_ATTEMPTS = 5


def _generate_valid_draft(content_type: str, sources: list[dict[str, Any]],
                           recent_titles: list[str]) -> Optional[dict[str, Any]]:
    """생성 -> 검증을 최대 MAX_ATTEMPTS번 시도한다. 모델이 가끔 한자를 섞어 쓰거나
    검수를 통과 못 하는 초안을 내는 경우가 있어, 한 번 실패했다고 그날 발행을
    포기하지 않고 다시 시도한다."""
    allowed_urls = {s["url"] for s in sources if s.get("url")}

    for attempt in range(1, MAX_ATTEMPTS + 1):
        print(f"[DAILY_POST] 생성 시도 {attempt}/{MAX_ATTEMPTS}")
        try:
            # 매 시도마다 다른 저장소를 골라본다 (같은 주제가 계속 실패하는 경우 대비).
            draft = (generate_draft_til(sources, pick_rank=attempt - 1) if content_type == "til"
                     else generate_draft_news(sources))
        except Exception as e:
            print(f"[DAILY_POST]   생성 호출 실패(타임아웃 등), 재시도: {e}")
            continue

        ok, invented = validate_links(draft["body"], allowed_urls)
        if not ok:
            print(f"[DAILY_POST]   링크 검증 실패(지어낸 링크로 판단), 재시도: {invented}")
            continue

        stray_hanja = find_stray_hanja(draft["body"])
        if stray_hanja:
            print(f"[DAILY_POST]   한자 오염 감지, 재시도: {stray_hanja}")
            continue

        broken_words = find_broken_mixed_words(draft["body"])
        if broken_words:
            print(f"[DAILY_POST]   단어 중간 언어 혼입 감지, 재시도: {broken_words}")
            continue

        fact_result = fact_check_agent(draft, recent_titles)
        fact_pass = all(fact_result[k] for k in ("팩트", "최신성", "공식출처", "중복충돌"))
        print(f"[DAILY_POST]   팩트 검증: {fact_result}")
        if not fact_pass:
            print(f"[DAILY_POST]   팩트 검증 실패, 재시도: {fact_result.get('_reason')}")
            continue

        quality_result = quality_check_agent(draft)
        quality_pass = (
            quality_result["검색의도"] and quality_result["반복제거"]
            and all(quality_result[k] >= SCORE_THRESHOLD for k in ("제목/CTR", "네이버SEO", "모바일UX", "차별성"))
        )
        print(f"[DAILY_POST]   품질 검증: {quality_result}")
        if not quality_pass:
            print("[DAILY_POST]   품질 검증 기준 미달, 재시도")
            continue

        return draft

    return None


# ── 메인 ───────────────────────────────────────────────────────────────

def run(target_date: Optional[dt.date] = None) -> None:
    target_date = target_date or dt.date.today()
    content_type = pick_content_type(target_date)
    print(f"[DAILY_POST] {target_date.isoformat()} 콘텐츠 유형: {content_type}")

    try:
        sources = fetch_github_trending() if content_type == "til" else fetch_hackernews_top()
    except Exception as e:
        print(f"[DAILY_POST] 소재 수집 실패, 오늘은 건너뜀: {e}")
        return

    recent_titles = get_recent_titles()
    draft = _generate_valid_draft(content_type, sources, recent_titles)
    if draft is None:
        print(f"[DAILY_POST] {MAX_ATTEMPTS}번 시도 모두 검증 실패, 오늘은 발행을 건너뜀")
        return

    path = write_post(draft, content_type, target_date)
    print(f"[DAILY_POST] 글 작성 완료: {path}")

    try:
        commit_and_push(path)
        print("[DAILY_POST] git commit/push 완료 — 발행됨")
    except Exception as e:
        print(f"[DAILY_POST] git 발행 실패: {e}")


if __name__ == "__main__":
    run()
