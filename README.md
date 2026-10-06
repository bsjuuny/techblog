# Frontend Engineering Notes

Frontend 개발 과정에서 마주친 문제, 기술 선택의 기준, 운영 경험을 정리하는 GitHub Pages 기술 블로그입니다. 경력과 프로젝트는 기술 글의 배경 정보로 분리해 제공합니다.

## 페이지

- Home: 최신 글, 주요 주제, 작성 원칙
- Blog: 실제 경험을 검증한 기술 글
- GitHub Radar: 최근 새로 떠오르는 오픈소스 프로젝트를 주 1회 큐레이션
- Categories: 주제별 글 탐색
- Projects: 기술 글의 배경이 되는 대표 프로젝트
- About: 작성자의 전문 영역과 경력 흐름

## 기술 구성

- Jekyll
- Minimal Mistakes remote theme
- GitHub Pages
- Sass

## 자동 발행

`scripts/generate_daily_post.py`는 토요일에 GitHub Radar, 일요일에 실제 프로젝트 개발기,
그 밖의 날에는 개발 노트와 기술 뉴스를 번갈아 생성합니다. GitHub Radar는 최근 30일 내
생성된 저장소를 성장 속도·최근 활동·언어 및 소유자 다양성으로 선정하며, 기존 글과 같은
링크 허용 목록·팩트 검증·품질 점수 기준을 모두 통과한 경우에만 발행합니다.

## 검색·AI 인용 (GEO)

생성형 검색 엔진이 글을 인용할 수 있도록 다음을 유지합니다.

- `_includes/head/custom.html` — 글 페이지는 `BlogPosting` JSON-LD(제목·요약·작성일·
  작성자·대표 이미지), 홈은 `Blog` JSON-LD를 내보냅니다.
- `llms.txt` — 사이트 개요, 자동 생성 글에 대한 고지, 카테고리별 전체 글 목록
  (`/llms.txt`로 발행, Liquid가 글 목록을 자동으로 채웁니다).
- `og_image` (`assets/images/og-default.png`, 생성: `scripts/make_og_image.py`) —
  공유·AI 카드용 기본 이미지.
- `excerpt`는 제목 복사본이 아니라 글의 한 줄 요약입니다. 자동 생성 글은 모델이 본문과
  별도로 내놓은 `SUMMARY`를 쓰고, 없으면 본문 첫 문단에서 뽑습니다
  (`scripts/post_meta.py`). 과거 글 소급 보정은 `scripts/normalize_post_meta.py`.
- 본문에는 H1(`# `)을 쓰지 않습니다. 레이아웃이 글 제목을 H1으로 출력하므로 본문
  소제목은 `##`부터 시작합니다.

## 로컬 실행

Ruby와 Bundler 설치 후:

```bash
bundle install
bundle exec jekyll serve --baseurl /techblog
```

`http://localhost:4000/techblog/`에서 확인할 수 있습니다.

## 검토 문서

- `PORTFOLIO_REVIEW.md`
- `CAREER_DATA_REVIEW.md`
- `SECURITY_CONTENT_REVIEW.md`
- `CONTENT_PLAN.md`

## 본문 정보 박스

글의 핵심 요약, 체크리스트, 참고자료는 Markdown에서 다음처럼 사용할 수 있습니다.

```html
<div class="summary-box">
  <strong>핵심 요약</strong>
  <p>이 글에서 기억할 가장 중요한 내용을 적습니다.</p>
</div>

<div class="checklist-box">
  <strong>실무 체크리스트</strong>
  <ul><li>배포 전에 확인할 항목</li></ul>
</div>
```

사용 가능한 클래스는 `note-box`, `summary-box`, `checklist-box`, `reference-box`, `warning-box`, `ai-note`입니다. 기존 Minimal Mistakes 알림 문법(`{: .notice--info }` 등)도 같은 디자인 체계로 표시됩니다.
