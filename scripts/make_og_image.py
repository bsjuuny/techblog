"""소셜/AI 카드용 기본 OG 이미지(1200x630)를 만든다.

`_config.yml`의 `og_image`가 가리키는 파일을 생성한다. 글마다 대표 이미지가 없는
블로그라서, 공유·인용될 때 쓰일 기본 카드 한 장이 필요하다. 제목·부제를 바꿀 일이
있으면 아래 상수만 고쳐서 다시 실행하면 된다.

실행: python scripts/make_og_image.py

글꼴은 Segoe UI(Windows 기본)를 쓰고, 한글 글리프가 없으므로 카드 문구는 ASCII만
쓴다 — 한글을 넣으려면 Malgun Gothic(malgun.ttf)으로 바꿔야 한다.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT_PATH = Path(__file__).resolve().parent.parent / "assets" / "images" / "og-default.png"
SIZE = (1200, 630)
BG = "#0d1117"
ACCENT = "#58a6ff"
TITLE = "Frontend Engineering Notes"
SUBTITLE = "React | TypeScript | Web Standards | Enterprise UI"
FOOTER = "bsjuuny.github.io/techblog"

FONT_BOLD = "C:/Windows/Fonts/segoeuib.ttf"
FONT_REGULAR = "C:/Windows/Fonts/segoeui.ttf"


def _font(path: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.truetype("C:/Windows/Fonts/arial.ttf", size)


def main() -> None:
    image = Image.new("RGB", SIZE, BG)
    draw = ImageDraw.Draw(image)

    draw.rectangle([(0, 0), (SIZE[0], 10)], fill=ACCENT)
    draw.rectangle([(80, 250), (86, 330)], fill=ACCENT)

    draw.text((120, 238), TITLE, font=_font(FONT_BOLD, 62), fill="#e6edf3")
    draw.text((120, 322), SUBTITLE, font=_font(FONT_REGULAR, 30), fill="#8b949e")
    draw.text((120, 520), FOOTER, font=_font(FONT_REGULAR, 26), fill="#6e7681")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    image.save(OUT_PATH, optimize=True)
    print(f"[OG] 생성: {OUT_PATH} ({OUT_PATH.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
