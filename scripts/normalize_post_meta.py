"""이미 발행된 글의 요약문(excerpt)과 본문 H1을 소급 보정한다.

생성 파이프라인(`generate_daily_post.py`)은 2026-10-06부터 요약문을 따로 받고 본문 H1을
정규화하지만, 그 전에 쌓인 글은 그대로다. 이 스크립트는 그 글들만 한 번 훑어 고친다.

- `excerpt`가 비었거나 제목을 그대로 복사한 값이면, 본문 첫 문단에서 요약문을 만든다.
- 본문의 H1(`# `)은 제목과 같은 내용이면 지우고, 아니면 H2로 내린다
  (레이아웃이 이미 글 제목을 H1으로 출력하므로 한 페이지에 H1이 둘이 되지 않게).

요약문은 LLM을 다시 부르지 않고 본문에서 직접 뽑는다 — 과거 글의 요약을 모델이 새로
지어낼 위험을 피하기 위함이다(`post_meta.derive_excerpt`).

실행:
    python scripts/normalize_post_meta.py --dry-run   # 바뀔 파일만 보여 준다
    python scripts/normalize_post_meta.py             # 실제로 고친다
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    from scripts.post_meta import derive_excerpt, normalize_headings
except ModuleNotFoundError:  # 스크립트로 직접 실행될 때
    from post_meta import derive_excerpt, normalize_headings

POSTS_DIR = Path(__file__).resolve().parent.parent / "_posts"

_FRONT_MATTER_RE = re.compile(r"\A---\n(?P<front>.*?\n)---\n(?P<body>.*)\Z", re.DOTALL)
_TITLE_RE = re.compile(r"^title:\s*(.+?)\s*$", re.MULTILINE)
_EXCERPT_RE = re.compile(r"^excerpt:\s*(.*?)\s*$", re.MULTILINE)


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def _same_text(a: str, b: str) -> bool:
    return re.sub(r"\s+", "", a) == re.sub(r"\s+", "", b)


def normalize_file(path: Path) -> list[str]:
    """파일을 보정하고, 무엇을 바꿨는지 사람이 읽을 수 있는 목록으로 돌려준다."""
    raw = path.read_text(encoding="utf-8")
    m = _FRONT_MATTER_RE.match(raw)
    if not m:
        return []

    front, body = m.group("front"), m.group("body")
    title_m = _TITLE_RE.search(front)
    if not title_m:
        return []
    title = _unquote(title_m.group(1))

    changes: list[str] = []

    # front matter와 본문 사이의 빈 줄은 그대로 둔다 — H1·요약문 말고는 아무것도
    # 바꾸지 않아야 diff에서 실제 변경만 보인다.
    leading = body[: len(body) - len(body.lstrip("\n"))]
    new_body = normalize_headings(body, title)
    if new_body != body.strip("\n"):
        changes.append("본문 H1 정리")
    new_body = leading + new_body + "\n"

    excerpt_m = _EXCERPT_RE.search(front)
    current = _unquote(excerpt_m.group(1)) if excerpt_m else ""
    if not current or _same_text(current, title):
        derived = derive_excerpt(new_body, fallback=current or title)
        if derived and not _same_text(derived, title):
            line = f'excerpt: "{derived}"'
            if excerpt_m:
                front = front[: excerpt_m.start()] + line + front[excerpt_m.end():]
            else:
                front = front + line + "\n"
            changes.append(f"요약문: {derived[:60]}…")

    if changes:
        path.write_text(f"---\n{front}---\n{new_body}", encoding="utf-8")
    return changes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="바뀔 내용만 출력하고 쓰지 않는다")
    args = parser.parse_args()

    changed = 0
    for path in sorted(POSTS_DIR.glob("*.md")):
        original = path.read_text(encoding="utf-8")
        changes = normalize_file(path)
        if args.dry_run and changes:
            path.write_text(original, encoding="utf-8")
        if changes:
            changed += 1
            print(f"- {path.name}: {', '.join(changes)}")

    print(f"\n{'(dry-run) ' if args.dry_run else ''}{changed}개 파일 보정")
    return 0


if __name__ == "__main__":
    sys.exit(main())
