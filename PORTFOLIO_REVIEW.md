# Portfolio Review

검토일: 2026-08-15  
대상: GitHub Pages `techblog` 저장소와 공개 Home/About

## 기존 사이트 문제

- Home이 `Welcome to Jekyll!` 기본 게시글과 사이드 프로필 중심이라 채용용 포트폴리오 역할을 하지 못했다.
- 사이트 제목이 `Tech Blog`, 작성자가 `David Baek`으로 표시돼 이력서의 백승준과 즉시 연결되지 않았다.
- About에 경력 근거보다 강한 Architecture, 공통 컴포넌트, Code Review, AI 활용 주장이 포함돼 있었다.
- 최근 프로젝트의 고객사·근무회사·역할·기술이 한 문단에 섞여 SI 경력의 관계가 불명확했다.
- 16년 경력이 동일한 깊이로 길게 나열돼 최근 Enterprise Frontend 경험이 묻혔다.
- 공개 화면 캡처에 내부 시스템, 계정·직원 정보, 업무 제목이 포함돼 있었다.
- 공개 이력서 PDF에 채용에 불필요한 개인정보와 보상 정보가 포함돼 있었다.
- Email 주소가 이력서와 다르며 공개 연락처로 사용해도 되는지 확인되지 않았다.
- SEO 제목과 설명이 일반적인 `Tech Blog` 수준이었고 기본 소셜 미리보기 정보가 부족했다.
- 기본 테스트 게시글·카테고리·이미지 파일이 남아 있었다.

## 변경 내용

- Home을 Senior Frontend Engineer 채용용 Landing Page로 교체했다.
- Primary Position을 `Senior Frontend Engineer`, 보조 표현을 `16+ Years in Web Development`로 통일했다.
- Home, About, Projects, Blog, GitHub 역할을 분리하고 전체 내비게이션을 재구성했다.
- `_data/projects.yml`, `_data/career.yml`, `_data/skills.yml`로 반복 데이터를 단일화했다.
- 프로젝트를 기간, 고객사, 근무회사, 산업, 역할, 기술, 수행업무로 분리했다.
- About의 근거가 약한 문장을 삭제하거나 실제 이력서 수준으로 완화했다.
- 최근/주요 경력과 이전 경력을 분리하되 전체 경력 흐름은 유지했다.
- 기본 Jekyll 게시글과 테스트 파일을 제거했다.
- 공개 이미지와 이력서 PDF의 민감 정보 노출 경로를 제거 대상으로 분류했다.

## 디자인 개선

- Minimal Mistakes/Jekyll 구조는 유지하고 밝은 기본 스킨과 절제된 Navy 계열을 적용했다.
- Hero, Summary, Expertise, Featured Projects, Career Journey 순으로 30~60초 스캔 흐름을 설계했다.
- 카드 수를 제한하고 Typography, whitespace, border 중심으로 계층을 구성했다.
- 375px부터 Desktop까지 대응하는 Grid와 CTA 레이아웃을 추가했다.
- 과도한 애니메이션·Gradient·기술 로고·이모지를 사용하지 않았다.

## Career 개선

- Web Standards/Publishing → JavaScript UI → Responsive/Mobile → SPA → Vue → Angular/TypeScript → React → AEM/React 흐름을 시각적으로 정리했다.
- 린시코리아, 해쉬스톤, 게임소마 누락을 보완했다.
- 앤서스랩·웹젠 기간을 원본 기술이력서 기준으로 조정했다.
- 한빛소프트 파트장, 현진아이씨티 업무 PL 등 원본에서 확인되는 역할만 표시했다.
- 근거가 없는 Tech Lead, Architecture Lead, Engineering Manager 표현은 사용하지 않았다.

## 기술 포지셔닝 개선

- Primary: React, JavaScript, HTML/CSS, Responsive Web
- Experienced: TypeScript, Vue/Vuex, Angular, AEM, jQuery
- Integration/Backend Experience: REST API, Ajax/Axios, Spring Boot, PostgreSQL
- Full-stack은 주력 타이틀이 아니라 최근 프로젝트의 Frontend 중심 보조 경험으로만 표현했다.
- 프로젝트별 Java/GraphQL은 근거가 불충분해 공개 문구에서 제거했다.
- 기술 숙련도 퍼센트와 확인되지 않은 성과 수치를 사용하지 않았다.

## SEO 개선

- 사이트 제목을 `백승준 | Senior Frontend Engineer`로 변경했다.
- 채용·기술 검색을 고려한 한국어 meta description을 추가했다.
- GitHub 프로필과 연결되는 Person 구조화 데이터를 추가했다.
- favicon, theme-color, OpenGraph 기본 이미지를 설정했다.
- `robots.txt`, sitemap/feed 플러그인, canonical 기반 설정을 정리했다.
- 모든 내부 링크에 `relative_url`을 적용해 `/techblog/` base path를 고려했다.

## Accessibility 개선

- 기존 Theme의 Skip Navigation과 semantic main/navigation 구조를 유지했다.
- 주요 섹션에 명시적 heading과 `aria-labelledby`를 적용했다.
- Project/Expertise를 `article`, CTA 묶음을 `nav`로 구성했다.
- keyboard focus가 명확하게 보이도록 `:focus-visible` 스타일을 추가했다.
- prefers-reduced-motion 환경에서 동작을 최소화했다.
- 작은 화면에서도 기술명과 프로젝트 정보가 잘리거나 가로 스크롤을 만들지 않도록 처리했다.

## Performance 개선

- React/Next.js 등 추가 SPA Framework로 마이그레이션하지 않았다.
- 별도 JavaScript와 외부 UI dependency를 추가하지 않았다.
- Google Analytics와 댓글 provider를 비활성화해 불필요한 외부 script를 줄였다.
- Home에서 프로젝트 이미지를 사용하지 않아 초기 이미지 비용을 줄였다.
- CSS는 Jekyll Sass 압축 설정을 유지했다.

## 추가 권장사항

1. 사용자 확인 후 AI-assisted Development의 실제 활용 범위를 2~3개 항목으로 명확히 한다.
2. Java/GraphQL의 프로젝트별 직접 사용 범위를 확인한 뒤 필요한 경우만 복원한다.
3. 공개 가능한 화면은 실제 고객사 화면 대신 비식별 mockup으로 새로 제작한다.
4. 민감 파일이 포함된 Git history 정리 여부를 별도 승인 후 결정한다.
5. 실제 경험 기반 기술 글을 한 편씩 작성해 Blog의 신뢰도를 높인다.

