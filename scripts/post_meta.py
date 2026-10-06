"""글 메타데이터(요약문·제목 구조) 정규화 — 생성 파이프라인과 소급 보정 스크립트가 함께 쓴다.

생성형 엔진(ChatGPT/Perplexity/Google AI 등)은 글을 인용할 때 meta description과 문서의
제목 구조를 근거로 "이 글이 무엇에 답하는 글인지"를 판단한다. 그래서 두 가지를 보장한다.

1. `excerpt`가 제목을 그대로 복사한 값이면 안 된다 — meta description / og:description /
   JSON-LD description이 전부 제목 반복이 되어 인용할 거리가 없어진다.
2. 본문에 H1(`# `)이 또 있으면 안 된다 — 레이아웃이 이미 글 제목을 H1으로 내보내므로
   한 페이지에 H1이 둘이 된다.

여기 있는 함수는 네트워크·API를 쓰지 않는 순수 함수다 (소급 보정 때 LLM을 다시 호출하면
비용도 들고, 과거 글의 요약을 모델이 새로 지어낼 위험이 있어 본문에서 직접 뽑는다).
"""
from __future__ import annotations

import re

EXCERPT_LIMIT = 160
_MIN_SENTENCE_CUT = 60

_FENCE_RE = re.compile(r"^\s*(```|~~~)")
_H1_RE = re.compile(r"^#\s+(.*\S)\s*$")
_ATTR_RE = re.compile(r"^\{:.*\}\s*$")
_SKIP_LINE_RE = re.compile(r"^\s*(>|#{1,6}\s|[-*_]{3,}\s*$|!\[|\||\{:)")
_LIST_RE = re.compile(r"^\s*([-*+]|\d+\.)\s+")
_SENTENCE_END_RE = re.compile(r"[.!?]['\"]?\s|다\.\s|요\.\s")


def _strip_inline_markdown(text: str) -> str:
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)          # 이미지
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)      # 링크 -> 링크 텍스트
    text = re.sub(r"`([^`]*)`", r"\1", text)                  # 인라인 코드
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"\1", text)
    text = re.sub(r"<[^>]+>", "", text)                       # 남은 HTML 태그
    text = text.replace('"', "'").replace("\\", "")           # YAML 큰따옴표 안에 들어갈 값
    return re.sub(r"\s+", " ", text).strip()


def _iter_prose_lines(body: str):
    """코드 블록·인용(자동 생성 고지)·제목·표를 건너뛰고 본문 산문 줄만 내보낸다."""
    in_fence = False
    for raw in body.splitlines():
        if _FENCE_RE.match(raw):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        yield raw


def clean_excerpt(text: str, limit: int = EXCERPT_LIMIT) -> str:
    """모델이 써 준 한 줄 요약을 front matter(`excerpt: "..."`)에 넣을 수 있게 다듬는다."""
    return _truncate_at_sentence(_strip_inline_markdown(text), limit)


def derive_excerpt(body: str, fallback: str = "", limit: int = EXCERPT_LIMIT) -> str:
    """본문의 첫 산문 문단에서 요약문을 만든다. 뽑을 게 없으면 fallback을 그대로 돌려준다."""
    paragraph: list[str] = []
    list_fallback = ""
    for line in _iter_prose_lines(body):
        stripped = line.strip()
        if not stripped:
            if paragraph:
                break
            continue
        if _ATTR_RE.match(stripped) or _SKIP_LINE_RE.match(stripped):
            continue
        if _LIST_RE.match(stripped):
            # 목록만 있는 글(라다 브리핑 등)을 위한 2순위 후보. 산문 문단이 먼저다.
            if not list_fallback:
                list_fallback = _strip_inline_markdown(_LIST_RE.sub("", stripped))
            continue
        paragraph.append(stripped)

    text = _strip_inline_markdown(" ".join(paragraph)) or list_fallback
    if not text:
        return fallback
    return _truncate_at_sentence(text, limit)


def _truncate_at_sentence(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    window = text[: limit + 1]
    cuts = [m.end() for m in _SENTENCE_END_RE.finditer(window + " ")]
    cuts = [c for c in cuts if c >= _MIN_SENTENCE_CUT]
    if cuts:
        return window[: cuts[-1]].strip()
    head = window[:limit].rstrip()
    if " " in head:
        head = head[: head.rfind(" ")].rstrip()
    return head + "…"


def _normalized(text: str) -> str:
    return re.sub(r"\s+", "", _strip_inline_markdown(text)).lower()


def normalize_headings(body: str, title: str) -> str:
    """본문 H1을 없앤다. 제목과 같은 내용이면 지우고, 아니면 H2로 내린다.

    코드 블록 안의 `# 주석`은 건드리지 않는다.
    """
    target = _normalized(title)
    out: list[str] = []
    in_fence = False
    for raw in body.splitlines():
        if _FENCE_RE.match(raw):
            in_fence = not in_fence
            out.append(raw)
            continue
        m = None if in_fence else _H1_RE.match(raw)
        if m is None:
            out.append(raw)
            continue
        if _normalized(m.group(1)) == target:
            # 제목을 그대로 반복한 H1 — 줄 자체를 없애고 뒤따르는 빈 줄 중복도 정리한다.
            while out and not out[-1].strip():
                out.pop()
            continue
        out.append(f"## {m.group(1)}")

    text = "\n".join(out)
    return re.sub(r"\n{3,}", "\n\n", text).strip("\n")
