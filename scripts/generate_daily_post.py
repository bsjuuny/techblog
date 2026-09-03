"""매일 techblog에 자동으로 글 1개를 생성·검수·발행한다.

구조:
  1. 오늘의 콘텐츠 유형 결정 (일요일: 실제 프로젝트 개발기 / 나머지 요일: 짝·홀수일
     교대로 개발·기술 TIL vs 테크 뉴스·트렌드). 일요일에 근거가 될 만한 커밋이 없으면
     조용히 til/news로 대체한다 (억지 발행 금지 원칙은 이 슬롯에도 그대로 적용).
  2. 실제 무료 공식 API(GitHub Search API / Hacker News API)나 로컬 git 커밋 기록에서
     소재를 가져온다 — 소재 자체는 항상 코드가 직접 가져온 실제 데이터여야 하고,
     LLM은 이 소재를 "요약/설명"만 하고 새로운 사실을 지어내지 않는다 (모델을 Claude로
     바꿔도 이 원칙은 그대로 유지 — 검증 가능성이 목적이라 굳이 LLM이 직접 검색하게
     하지 않음).
  3. 생성 에이전트(Claude): 주어진 소재만 근거로 초안 작성.
  4. 코드 레벨 검증: 초안에 들어간 모든 링크가 실제로 가져온 소재의 URL 목록에
     있는지 대조 — 없는 링크(=지어낸 것)가 하나라도 있으면 그 자리에서 발행 중단.
  5. 팩트 검증 에이전트(Claude, 별도 호출): 팩트·최신성·공식출처·중복충돌 검사.
  6. 품질 검증 에이전트(Claude, 별도 호출): 검색의도·제목/CTR·네이버SEO·모바일UX·
     차별성·반복제거 검사.
  7. 5, 6 모두 통과해야만(PASS 전부 + 점수 기준 이상) 파일로 써서 git commit+push.
     하나라도 실패하면 그날은 조용히 건너뛴다 (억지로 대체 콘텐츠를 만들지 않음).

비용: GitHub/Hacker News 공식 API는 무료. Claude Sonnet 5 API 사용료만 발생
(하루 1~2회 시도 × 호출 3건 기준 월 $2 내외로 추정 — 실사용량에 따라 달라짐).
"""
from __future__ import annotations

import datetime as dt
import html
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Optional

import anthropic
import requests
from dotenv import load_dotenv

if sys.stdout is not None:
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parent.parent
POSTS_DIR = REPO_ROOT / "_posts"

CLAUDE_MODEL = os.getenv("DAILY_POST_MODEL", "claude-sonnet-5")
_client = anthropic.Anthropic()

# 원래 qwen3 기준으로 실측(65~85점 분포)해 70점으로 잡았던 값이다. 생성·채점 모델을
# Claude Sonnet 5로 교체한 뒤 다시 실측하니 qwen3보다 훨씬 엄격하게 채점해 6회 모두
# 55~68점대에 분포했고(문단 구조 개선 후에도 모바일UX 45→55 수준), 70점 기준으로는
# 사실상 발행이 불가능했다. 같은 방식으로 재조정해 55점으로 낮췄다 (팩트 검증은 여전히
# 100% 통과를 요구 — 안전이 중요한 항목은 기준을 낮추지 않았다). 실제 발행이 며칠 쌓이면
# 다시 실측해서 조정할 것.
SCORE_THRESHOLD = 55
RECENT_DAYS_FOR_DUP_CHECK = 21


# ── 1. 오늘의 콘텐츠 유형 ──────────────────────────────────────────────

def pick_content_type(target_date: dt.date) -> str:
    # 일요일은 실제 프로젝트 커밋 기반 개발기(engineering) 슬롯 - 나머지 요일은 기존
    # til/news 홀짝 교대 그대로. 일요일에 근거가 될 만한 커밋이 없으면 run()이
    # _fallback_content_type()으로 til/news에 넘긴다 (억지 발행 금지 원칙 유지).
    if target_date.weekday() == 6:
        return "engineering"
    return _fallback_content_type(target_date)


def _fallback_content_type(target_date: dt.date) -> str:
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


_META_DESC_RE = re.compile(
    r'<meta[^>]+(?:property=["\']og:description["\']|name=["\']description["\'])'
    r'[^>]+content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)
_META_DESC_RE_ALT = re.compile(
    r'<meta[^>]+content=["\']([^"\']+)["\']'
    r'[^>]+(?:property=["\']og:description["\']|name=["\']description["\'])',
    re.IGNORECASE,
)


def _fetch_article_summary(url: str, timeout: int = 8) -> str:
    """기사 원문 페이지의 meta description을 실제로 가져온다.

    HN 헤드라인만으로는 배경/맥락을 설명할 근거가 없어 코멘트가 표면적인 요약에
    그치는 문제가 있었다 — 이 설명을 재료로 추가해 생성 에이전트가 지어내지 않고도
    "왜 이게 이슈인지"를 구체적으로 쓸 수 있게 한다. 페이지 하나가 실패해도(차단,
    타임아웃, meta 태그 없음 등) 헤드라인만으로 계속 진행 가능하므로 빈 문자열을
    반환하고 사유만 로그에 남긴다.
    """
    try:
        resp = requests.get(
            url, timeout=timeout,
            headers={"User-Agent": "Mozilla/5.0 (compatible; techblog-bot/1.0)"},
        )
        resp.raise_for_status()
        page = resp.text[:200_000]  # 과도하게 큰 페이지 방지
        m = _META_DESC_RE.search(page) or _META_DESC_RE_ALT.search(page)
        if not m:
            return ""
        return html.unescape(m.group(1)).strip()[:400]
    except Exception as e:
        print(f"[DAILY_POST]   기사 설명 수집 실패({url}): {e}")
        return ""


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
    for item in items:
        item["description"] = _fetch_article_summary(item["url"])
    return items


PROJECT_REPOS_ROOT = Path("C:/github")
# techblog 자신은 제외한다 - 이 저장소의 커밋은 대부분 "글 추가"류라 개발기 소재로
# 부적합하고, 파이프라인이 자기 자신을 소재로 삼으면 혼란스럽다.
_ENGINEERING_EXCLUDED_REPOS = {"techblog"}
# 한 줄짜리 커밋은 "왜 이렇게 했는지" 서술할 근거가 없어 모델이 지어내기 쉽다 - til의
# description 길이 필터(>=20자)와 같은 이유로, 본문이 충분히 긴 커밋만 후보로 삼는다.
_ENGINEERING_MIN_BODY_LENGTH = 80


def _github_commit_url(repo_dir: Path, sha: str) -> str:
    """origin이 github.com 리모트면 실제 커밋 URL을, 아니면(비공개/로컬 전용 저장소)
    빈 문자열을 반환한다 - 빈 문자열이면 생성 프롬프트가 링크를 아예 안 쓰도록 한다."""
    try:
        remote = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=repo_dir, check=True, capture_output=True, text=True, encoding="utf-8",
        ).stdout.strip()
    except Exception:
        return ""
    m = re.search(r"github\.com[:/]([\w.-]+/[\w.-]+?)(?:\.git)?$", remote)
    return f"https://github.com/{m.group(1)}/commit/{sha}" if m else ""


def fetch_project_commits(days: int = 7, n: int = 8) -> list[dict[str, Any]]:
    """지난 며칠간의 실제 git 커밋 기록에서 소재를 가져온다(무료, 로컬 git log만 사용,
    API 키 불필요). C:/github 아래의 모든 git 저장소를 대상으로 하되, 본문이 짧은
    (서술 근거가 없는) 커밋은 후보에서 제외한다."""
    if not PROJECT_REPOS_ROOT.exists():
        return []
    since = (dt.date.today() - dt.timedelta(days=days)).isoformat()
    candidates: list[dict[str, Any]] = []
    for repo_dir in sorted(PROJECT_REPOS_ROOT.iterdir()):
        if not repo_dir.is_dir() or repo_dir.name in _ENGINEERING_EXCLUDED_REPOS:
            continue
        if not (repo_dir / ".git").exists():
            continue
        try:
            log = subprocess.run(
                ["git", "log", f"--since={since}", "--no-merges", "--format=%H%x1f%s%x1f%b%x1e"],
                cwd=repo_dir, check=True, capture_output=True, text=True, encoding="utf-8",
            ).stdout
        except Exception:
            continue
        for entry in log.split("\x1e"):
            entry = entry.strip()
            if not entry:
                continue
            parts = entry.split("\x1f")
            if len(parts) < 2:
                continue
            sha, subject = parts[0], parts[1]
            body = parts[2].strip() if len(parts) > 2 else ""
            if len(body) < _ENGINEERING_MIN_BODY_LENGTH:
                continue
            try:
                files_changed = subprocess.run(
                    ["git", "show", "--stat", "--format=", sha],
                    cwd=repo_dir, check=True, capture_output=True, text=True, encoding="utf-8",
                ).stdout.strip()
            except Exception:
                files_changed = ""
            candidates.append({
                "repo": repo_dir.name,
                "sha": sha,
                "title": f"{repo_dir.name}: {subject}",
                "body": body,
                "files_changed": files_changed,
                "url": _github_commit_url(repo_dir, sha),
                "description": body,  # generate_draft_til과 필드명을 맞춰 길이 랭킹 로직을 재사용
            })
    return candidates


# ── 3. 생성 에이전트 ───────────────────────────────────────────────────

def _claude(prompt: str, *, effort: str = "medium", max_tokens: int = 4096) -> str:
    """단일 사용자 메시지로 Claude를 호출하고 텍스트만 반환한다.

    effort="low"는 형식이 정해진 체크리스트 판정(fact_check/quality_check)에,
    "medium"은 실제 글 초안 작성처럼 문장력이 필요한 호출에 쓴다.
    """
    response = _client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=max_tokens,
        thinking={"type": "adaptive"},
        output_config={"effort": effort},
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(block.text for block in response.content if block.type == "text").strip()


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
        "- 모바일에서 스캔하기 쉽도록, 각 소제목 아래 문단은 2~3문장으로 짧게 끊으세요. "
        "한 소제목 아래 할 말이 많으면 하나의 긴 문단 대신 짧은 문단 여러 개로 나누세요.\n"
        f"- 저장소 링크는 정확히 이 URL만 사용하세요: {picked['url']}\n"
        "- 다른 URL은 절대 만들어내지 마세요.\n"
        "- 마지막 줄에 'TITLE: '으로 시작하는 30자 이내의 매력적인 한국어 제목을 별도로 제시하세요.\n"
        "- 반드시 한국어로만 작성하세요. 중국어 한자나 다른 언어 단어를 절대 섞지 마세요.\n"
    )
    text = _claude(prompt, effort="medium")
    title, body = _split_title(text)
    return {"title": title, "body": body, "sources": sources, "picked": picked}


def generate_draft_news(sources: list[dict[str, Any]]) -> dict[str, Any]:
    def _source_line(s: dict[str, Any]) -> str:
        line = f"- {s['title']} (score {s['score']}) — {s['url']}"
        if s.get("description"):
            line += f"\n  기사 설명: {s['description']}"
        return line

    source_block = "\n".join(_source_line(s) for s in sources)
    prompt = (
        "당신은 Frontend 개발자를 위한 기술 블로그 필자입니다. 아래는 실제 Hacker News API에서 "
        "가져온 오늘의 top 스토리 헤드라인 목록입니다 (실제 헤드라인과 링크이며, 일부는 원문 "
        "페이지에서 가져온 실제 meta description이 '기사 설명'으로 함께 달려 있습니다).\n\n"
        f"{source_block}\n\n"
        "이 중 개발자에게 흥미로울 만한 4~6개를 골라서 '오늘의 기술 뉴스 브리핑' 스타일 글을 "
        "한국어로 작성하세요.\n\n"
        "규칙 (반드시 지킬 것):\n"
        "- 이번 사건 자체에 대한 구체적 세부사항(오늘 발표된 수치, 날짜, 이 기사에서만 다루는 "
        "특정 기능 목록 등)은 위 헤드라인과 기사 설명에 없으면 절대 지어내지 마세요.\n"
        "- 다만 사건과 무관하게 이미 널리 알려진 배경 지식(예: 유명 인물의 이력, 잘 알려진 "
        "기술 표준/용어 설명, 공개적으로 잘 알려진 과거 사건의 개요)은 배경 설명을 위해 사용해도 "
        "됩니다 — 이건 '지어낸 것'이 아니라 이미 공개적으로 검증된 사실이기 때문입니다. 다만 이 "
        "배경 지식을 오늘 이 기사가 새로 주장하는 내용인 것처럼 섞어 쓰지 말고, 배경은 배경으로 "
        "구분해서 서술하세요.\n"
        "- '기사 설명'이 있는 항목은 그 내용을 근거로 왜 이 일이 벌어졌는지, 배경이 무엇인지, "
        "무엇이 쟁점인지를 구체적으로 설명하세요 — 헤드라인만 반복하지 말고 기사 설명에 있는 "
        "사실을 실제로 활용하세요. 기사 설명이 없는 항목은 헤드라인 제목이 전달하는 정보 수준"
        "에서만 코멘트하고, 본문을 읽지 않고는 알 수 없는 세부사항은 '자세한 내용은 원문 참고'"
        "라고만 언급하세요.\n"
        "- 각 항목마다 왜 개발자가 관심 가질 만한지, 실무에 어떤 의미가 있는지, 비슷한 사례나 "
        "배경까지 구체적인 관점을 담아 3~4문장 분량으로 코멘트하세요 (단순 요약이 아니라 "
        "'그래서 어떻다는 건지'를 충분히 풀어서 말하세요).\n"
        "- 글 맨 앞에 오늘 다룰 주제들을 아우르는 2~3문장짜리 도입부를 쓰고, 맨 뒤에는 "
        "전체를 관통하는 흐름이나 시사점을 짚어주는 마무리 문단을 쓰세요. 다만 주제들이 실제로 "
        "무관하다면 억지로 하나의 흐름으로 엮지 말고, '오늘은 이런 다양한 소식들이 있었다' 정도로 "
        "솔직하게 묶으세요.\n"
        "- 위 목록에 있는 URL만 사용하고, 다른 URL은 절대 만들어내지 마세요.\n"
        "- 1600~2200자 분량으로 충분히 자세하게 작성하세요.\n"
        "- 모바일에서 스캔하기 쉽도록, 각 항목의 코멘트는 한 덩어리로 몰아 쓰지 말고 "
        "2문장 단위로 줄바꿈하세요.\n"
        "- 마지막 줄에 'TITLE: '으로 시작하는, 클릭하고 싶어지는 구체적인 한국어 제목을 "
        "30자 이내로 제시하세요. 이 글은 여러 소식을 묶은 브리핑이므로, 가장 흥미로운 "
        "포인트를 앞세우되 제목만 보고 '이건 그 주제 하나만 다루는 단독 기사구나'라고 "
        "오해하게 만들지 마세요 — '~외', '~등', 다룬 개수를 넣는 식으로 여러 소식을 "
        "묶었다는 게 제목에서부터 드러나야 합니다 (예: '로컬 LLM이 멍청해 보이는 이유 외 "
        "오늘의 개발 뉴스 4가지'). '오늘의 기술 뉴스' 같은 밋밋한 제목도 금지입니다.\n"
        "- 반드시 한국어로만 작성하세요. 중국어 한자나 다른 언어 단어를 절대 섞지 마세요.\n"
    )
    text = _claude(prompt, effort="medium")
    title, body = _split_title(text)
    return {"title": title, "body": body, "sources": sources, "picked": None}


def generate_draft_engineering(commits: list[dict[str, Any]], pick_rank: int = 0) -> dict[str, Any]:
    # til과 동일한 이유로 본문이 긴 순으로 정렬해서 고른다 - 재시도 시 pick_rank로
    # 다른 커밋으로 바꿔볼 수 있다.
    ranked = sorted(commits, key=lambda c: -len(c.get("body") or ""))
    picked = ranked[min(pick_rank, len(ranked) - 1)]
    url_instruction = (
        f"- 커밋 링크는 정확히 이 URL만 사용하세요: {picked['url']}\n다른 URL은 절대 만들어내지 마세요.\n"
        if picked.get("url")
        else "- 이 저장소는 공개 링크가 없습니다. URL을 만들어내지 말고 링크 없이 서술하세요.\n"
    )
    prompt = (
        "당신은 실무 개발자를 위한 기술 블로그 필자입니다. 아래는 필자가 실제로 작업한 "
        f"프로젝트({picked['repo']})의 실제 git 커밋 기록입니다.\n\n"
        f"커밋 메시지 제목: {picked['title']}\n"
        f"커밋 메시지 본문:\n{picked['body']}\n\n"
        f"변경된 파일:\n{picked['files_changed']}\n\n"
        "이 커밋을 소재로, 실제로 겪은 문제와 해결 과정을 1인칭 트러블슈팅 개발기 형식으로 "
        "한국어로 작성하세요.\n\n"
        "규칙 (반드시 지킬 것):\n"
        "- 위 커밋 메시지와 변경된 파일 목록에 있는 내용만 사실로 다루세요. 구체적인 수치, "
        "에러 메시지, 원인처럼 위에 없는 세부사항은 절대 지어내지 마세요.\n"
        f"- 저장소 이름({picked['repo']})과 커밋 내용만으로 알 수 있는 범위에서만 서술하고, "
        "비즈니스 맥락이나 회사명처럼 커밋에 없는 정보는 지어내지 마세요.\n"
        "- '어떤 문제가 있었는지 → 어떻게 원인을 찾았는지 → 어떻게 고쳤는지' 흐름으로 "
        "구체적으로 쓰되, 커밋 메시지에 이미 있는 근거를 재구성하는 것이지 새로운 서사를 "
        "지어내는 게 아닙니다.\n"
        "- 마크다운 소제목(##)을 3~4개 사용하고, 1200~1800자 분량으로 작성하세요.\n"
        "- 모바일에서 스캔하기 쉽도록, 각 소제목 아래 문단은 2~3문장으로 짧게 끊으세요.\n"
        f"{url_instruction}"
        "- 마지막 줄에 'TITLE: '으로 시작하는 30자 이내의 매력적인 한국어 제목을 별도로 제시하세요.\n"
        "- 반드시 한국어로만 작성하세요. 중국어 한자나 다른 언어 단어를 절대 섞지 마세요.\n"
    )
    text = _claude(prompt, effort="medium")
    title, body = _split_title(text)
    return {"title": title, "body": body, "sources": commits, "picked": picked}


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
        "- 팩트: '이번 사건 자체'에 대한 구체적 사실(오늘 발표된 수치/날짜/이 기사에서만 다루는 "
        "특정 기능명 등)을 원본 소재에 없는데 지어냈으면 FAIL. 단, 사건과 무관하게 이미 널리 "
        "알려진 배경 지식(유명 인물의 이력, 잘 알려진 기술 표준/용어, 공개적으로 검증된 과거 "
        "사건 개요 등)을 배경 설명으로 쓴 것은 지어낸 것이 아니므로 FAIL 아님 — 단 이런 배경 "
        "지식을 '오늘 이 기사가 새로 주장하는 내용'인 것처럼 혼동해서 서술했다면 FAIL\n"
        "- 최신성: 원본 소재 기준으로 시의성 있게 서술했으면 PASS\n"
        "- 공식출처: 본문의 링크가 원본 소재의 URL과 일치하면 PASS\n"
        "- 중복충돌: 최근 게시글과 주제가 사실상 동일하면 FAIL\n"
    )
    text = _claude(prompt, effort="low", max_tokens=512)
    return _parse_checklist(text, ["팩트", "최신성", "공식출처", "중복충돌"])


# ── 6. 품질 검증 에이전트 ───────────────────────────────────────────────

def quality_check_agent(draft: dict[str, Any], content_type: str) -> dict[str, Any]:
    # "검색의도" 기준을 콘텐츠 형식별로 다르게 준다 — 완화가 아니라 애초에 다른 종류의
    # 글에 같은 잣대를 잘못 대고 있었던 것을 바로잡는 것이다. til(단일 저장소/도구를
    # 다루는 글)은 "이 도구 뭐야" 같은 단일 검색 의도가 실제로 있으므로 기존 기준이
    # 맞다. news(여러 소식을 묶은 브리핑)는 애초에 단일 검색 의도가 존재하지 않는
    # 포맷인데도 같은 기준을 적용하다 보니, 실측(2026-08-23) 5번 생성 중 5번 모두
    # "검색의도 FAIL"로 걸렸다 — 팩트체크는 매번 통과했고 실제 본문을 사람이 읽어봐도
    # 내용 자체는 정상이었으므로, 글이 나쁜 게 아니라 이 형식에 안 맞는 기준을 대고
    # 있었다고 판단했다. 브리핑 형식에 맞는 기준으로 바꾸되, 여전히 실제로 판정해서
    # FAIL이 나올 수 있는 진짜 기준이어야 한다(무조건 PASS로 만들면 검증 자체가
    # 무의미해지므로).
    if content_type == "news":
        search_intent_criterion = (
            "- 검색의도: 이 글은 여러 소식을 묶은 '오늘의 기술 뉴스 브리핑' 형식입니다. "
            "'이 라이브러리 어떻게 쓰지'처럼 단일 주제에 답하는 검색 의도가 아니라, "
            "'오늘의 개발자 뉴스', '이번주 기술 동향'처럼 브리핑/모아보기를 찾는 검색 "
            "의도를 기준으로 판단하세요. 제목과 도입부가 그런 의도의 독자에게 매력적이고, "
            "각 항목이 헤드라인만 반복하지 않고 실제 맥락·의미를 짚어주면 PASS. 반대로 "
            "항목들이 서로 무관하게 나열만 되어 있어 브리핑으로서 응집력이나 가치가 "
            "없으면, 또는 개별 항목들이 표면적 요약에 그치면 FAIL.\n"
        )
    elif content_type == "engineering":
        search_intent_criterion = (
            "- 검색의도: 이 글은 실제로 겪은 문제를 해결한 트러블슈팅/개발기입니다. "
            "'~오류 원인', '~안 되는 이유', '~해결 방법'처럼 구체적인 문제 해결을 찾는 검색 "
            "의도를 기준으로 판단하세요. 실제 원인과 해결 과정이 구체적으로 서술되어 있으면 "
            "PASS. 커밋 메시지를 표면적으로 나열만 하고 실제 원인·해결 흐름이 안 보이면 FAIL.\n"
        )
    else:
        search_intent_criterion = "- 검색의도: 제목과 본문이 검색 사용자의 의도에 부합하면 PASS\n"

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
        "차별성: 0-100 사이 숫자\n"
        "사유: (검색의도가 FAIL이면 왜 그런지 한 줄로, PASS면 '없음')\n\n"
        "판정 기준:\n"
        f"{search_intent_criterion}"
        "- 반복제거: 같은 표현/문장이 불필요하게 반복되면 FAIL\n"
        "- 제목/CTR: 클릭을 유도하면서도 과장되지 않은 제목이면 높은 점수\n"
        "- 네이버SEO: 키워드 배치, 문단 길이, 소제목 구조가 네이버 검색에 적합하면 높은 점수\n"
        "- 모바일UX: 문단이 짧고 스캔하기 쉬우면 높은 점수\n"
        "- 차별성: 뻔한 일반론이 아니라 구체적 관점이 있으면 높은 점수\n"
    )
    text = _claude(prompt, effort="low", max_tokens=512)
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

    if content_type == "til":
        category, category_label = "devlog", "Dev Log · Auto"
    elif content_type == "engineering":
        # til도 "devlog" 카테고리를 이미 쓰고 있어(다른 저장소 트렌드 소개 글) 이름이
        # 겹치면 안 된다 - 실제 자기 프로젝트 커밋 기반 글은 별도 카테고리로 구분한다.
        category, category_label = "engineering", "Engineering Log · Auto"
    else:
        category, category_label = "news", "Tech News · Auto"
    picked = draft.get("picked") or {}
    extra_tag = picked.get("language") or picked.get("repo")
    tags = ["Auto Generated"] + ([extra_tag] if extra_tag else [])

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

    # "기록"(받침 있음 -> 을)과 "데이터"(받침 없음 -> 를)는 조사가 달라서, 공통 접미사에
    # 갖다 붙이지 않고 조사까지 포함해 분기한다.
    source_description = (
        "필자가 실제 작업한 프로젝트의 git 커밋 기록을"
        if content_type == "engineering"
        else "실제 공개 API(GitHub/Hacker News)에서 가져온 데이터를"
    )
    disclosure = (
        "> **자동 생성 안내**  \n"
        f"> 이 글은 매일 정해진 시각에 {source_description} "
        "근거로 AI(Claude)가 자동으로 작성하고, 자동 검수(팩트·SEO·UX 기준)를 통과한 뒤 사람의 "
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


MAX_ATTEMPTS = 3


def _generate_valid_draft(content_type: str, sources: list[dict[str, Any]],
                           recent_titles: list[str]) -> Optional[dict[str, Any]]:
    """생성 -> 검증을 최대 MAX_ATTEMPTS번 시도한다. 모델이 가끔 한자를 섞어 쓰거나
    검수를 통과 못 하는 초안을 내는 경우가 있어, 한 번 실패했다고 그날 발행을
    포기하지 않고 다시 시도한다."""
    allowed_urls = {s["url"] for s in sources if s.get("url")}

    for attempt in range(1, MAX_ATTEMPTS + 1):
        print(f"[DAILY_POST] 생성 시도 {attempt}/{MAX_ATTEMPTS}")
        try:
            # 매 시도마다 다른 저장소/커밋을 골라본다 (같은 주제가 계속 실패하는 경우 대비).
            if content_type == "til":
                draft = generate_draft_til(sources, pick_rank=attempt - 1)
            elif content_type == "engineering":
                draft = generate_draft_engineering(sources, pick_rank=attempt - 1)
            else:
                draft = generate_draft_news(sources)
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

        quality_result = quality_check_agent(draft, content_type)
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


# ── 9. watchdog 상태 마커 ──────────────────────────────────────────────
# scheduler/watchdog.mjs의 CRITICAL_TASKS가 다른 작업들(tg-report 등)과 동일한
# 방식(scheduler/status/<name>-YYYYMMDD.json 존재 여부)으로 "오늘 이 파이프라인이
# 실제로 실행됐는지"를 판단한다. 발행 여부(published)와 무관하게 매 실행마다
# 기록한다 — 품질/팩트 검증 기준 미달로 "오늘은 조용히 건너뜀"은 이 스크립트의
# 의도된 정상 종료 상태(발행 강제 안 함)이므로, watchdog이 이를 "실패"로 오인해
# 억지로 재시도(추가 API 비용 + 중복 발행 위험)하면 안 된다. 반대로 크론 자체가
# 아예 트리거되지 않은 날은 이 파일이 없으므로 watchdog이 정확히 그 경우만
# 감지해 강제 실행한다 (2026-08-23 실제로 이 문제가 발생 — 크론이 조용히
# 안 돌았는데 감지할 방법이 없었음).
_STATUS_DIR = Path("C:/github/scheduler/status")


def write_watchdog_status_marker(published: bool, reason: str) -> None:
    try:
        _STATUS_DIR.mkdir(parents=True, exist_ok=True)
        date_key = dt.date.today().strftime("%Y%m%d")
        (_STATUS_DIR / f"techblog-{date_key}.json").write_text(
            json.dumps(
                {"ranAt": dt.datetime.now().isoformat(), "published": published, "reason": reason},
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
    except Exception as e:
        print(f"[DAILY_POST] watchdog 상태 마커 기록 실패(무시하고 계속): {e}")


# ── 메인 ───────────────────────────────────────────────────────────────

def run(target_date: Optional[dt.date] = None) -> None:
    target_date = target_date or dt.date.today()
    content_type = pick_content_type(target_date)
    print(f"[DAILY_POST] {target_date.isoformat()} 콘텐츠 유형: {content_type}")

    recent_titles = get_recent_titles()
    draft = None

    if content_type == "engineering":
        try:
            commits = fetch_project_commits()
        except Exception as e:
            print(f"[DAILY_POST] 커밋 소재 수집 실패: {e}")
            commits = []
        if commits:
            draft = _generate_valid_draft("engineering", commits, recent_titles)
        if draft is None:
            # 이번 주 소재가 없거나 검증을 못 넘으면 그날 자체를 건너뛰지 않고, 항상
            # 안정적인 소재가 있는 til/news로 대체한다 - engineering은 "있으면 좋은"
            # 보너스 슬롯이지, 발행 자체를 막을 이유가 아니다.
            print("[DAILY_POST] 이번 주 개발기 소재/검증 실패, 평소 유형으로 대체")
            content_type = _fallback_content_type(target_date)

    if draft is None:
        try:
            sources = fetch_github_trending() if content_type == "til" else fetch_hackernews_top()
        except Exception as e:
            print(f"[DAILY_POST] 소재 수집 실패, 오늘은 건너뜀: {e}")
            write_watchdog_status_marker(False, f"소재 수집 실패: {e}")
            return
        draft = _generate_valid_draft(content_type, sources, recent_titles)

    if draft is None:
        print(f"[DAILY_POST] {MAX_ATTEMPTS}번 시도 모두 검증 실패, 오늘은 발행을 건너뜀")
        write_watchdog_status_marker(False, f"{MAX_ATTEMPTS}번 시도 모두 검증 실패")
        return

    path = write_post(draft, content_type, target_date)
    print(f"[DAILY_POST] 글 작성 완료: {path}")

    try:
        commit_and_push(path)
        print("[DAILY_POST] git commit/push 완료 — 발행됨")
        write_watchdog_status_marker(True, "발행 완료")
    except Exception as e:
        print(f"[DAILY_POST] git 발행 실패: {e}")
        write_watchdog_status_marker(False, f"git 발행 실패: {e}")


if __name__ == "__main__":
    run()
