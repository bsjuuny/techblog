from __future__ import annotations

from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
TEXT_EXTENSIONS = {".html", ".md", ".markdown", ".yml", ".yaml", ".scss", ".css", ".txt"}
REPORTS = {
    "PORTFOLIO_REVIEW.md",
    "CAREER_DATA_REVIEW.md",
    "SECURITY_CONTENT_REVIEW.md",
    "CONTENT_PLAN.md",
}
REQUIRED = [
    "_config.yml",
    "index.html",
    "_layouts/portfolio.html",
    "_pages/about.md",
    "_pages/projects.md",
    "_pages/blog.md",
    "_posts/2026-08-15-responsive-web-production-checklist.md",
    "_posts/2026-08-15-ai-generated-frontend-code-review-checklist.md",
    "_data/navigation.yml",
    "_data/projects.yml",
    "_data/career.yml",
    "_data/skills.yml",
    "assets/css/main.scss",
    "_sass/_portfolio.scss",
    "robots.txt",
]
FORBIDDEN_PUBLIC_PATHS = [
    ROOT / "assets" / "etc" / "이력서_백승준_20260123.pdf",
    ROOT / "assets" / "images" / "kaonsoft",
    ROOT / "assets" / "images" / "nsuslab",
]
PII_PATTERN = re.compile(
    r"010[- .]?\d{3,4}[- .]?\d{4}|"
    r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}",
    re.IGNORECASE,
)
LIQUID_OPEN = re.compile(r"{%\s*(for|if|unless)\b")
LIQUID_CLOSE = re.compile(r"{%\s*end(for|if|unless)\s*%}")


errors: list[str] = []

for relative in REQUIRED:
    if not (ROOT / relative).is_file():
        errors.append(f"required file missing: {relative}")

for path in FORBIDDEN_PUBLIC_PATHS:
    if path.exists():
        errors.append(f"sensitive public path still exists: {path.relative_to(ROOT)}")

config = (ROOT / "_config.yml").read_text(encoding="utf-8")
for required_setting in [
    'title: "Frontend Engineering Notes"',
    'baseurl: "/techblog"',
    'url: "https://bsjuuny.github.io"',
    "jekyll-sitemap",
]:
    if required_setting not in config:
        errors.append(f"config setting missing: {required_setting}")

for path in ROOT.rglob("*"):
    if not path.is_file() or ".git" in path.parts or path.suffix.lower() not in TEXT_EXTENSIONS:
        continue
    relative = path.relative_to(ROOT)
    text = path.read_text(encoding="utf-8")

    if "\t" in text and path.suffix.lower() in {".yml", ".yaml"}:
        errors.append(f"tab indentation in YAML: {relative}")

    if path.name not in REPORTS and PII_PATTERN.search(text):
        errors.append(f"PII-like value in public source: {relative}")

    if path.name not in REPORTS and any(
        token in text for token in ("assets/images/nsuslab", "assets/images/kaonsoft", "이력서_백승준_20260123")
    ):
        errors.append(f"removed sensitive asset is still referenced: {relative}")

    if path.suffix.lower() in {".html", ".md", ".markdown"}:
        if text.startswith("---\n") and "\n---\n" not in text[4:]:
            errors.append(f"unclosed front matter: {relative}")

        stack: list[str] = []
        tokens = sorted(
            [(match.start(), "open", match.group(1)) for match in LIQUID_OPEN.finditer(text)]
            + [(match.start(), "close", match.group(1)) for match in LIQUID_CLOSE.finditer(text)]
        )
        for _, kind, name in tokens:
            if kind == "open":
                stack.append(name)
            elif not stack or stack.pop() != name:
                errors.append(f"unbalanced Liquid tag in {relative}: end{name}")
                break
        if stack:
            errors.append(f"unclosed Liquid tag in {relative}: {stack[-1]}")

if errors:
    print("SITE SOURCE CHECK: FAILED")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

print("SITE SOURCE CHECK: PASSED")
print(f"required files: {len(REQUIRED)}")
print("baseurl: /techblog")
print("sensitive public paths: removed")
print("PII-like values in public source: none")
print("Liquid block balance: passed")
