---
title: "dsh-our-free-model 설치 전 확인할 것들"
date: 2026-11-26 01:33:03 +0900
categories:
  - devlog
  - generated
category_label: "Dev Log · Auto"
tags:
  - Auto Generated
  - JavaScript
excerpt: "무료로 AI 모델을 쓸 수 있다는 dsh 플러그인이 실제 프로젝트에 들어갈 때 확인해야 할 설치 함정과 쿼터 구조를 README 기준으로 짚습니다."
toc: false
---

> **자동 생성 안내**  
> 이 글은 매일 정해진 시각에 실제 공개 API(GitHub/Hacker News)에서 가져온 데이터를 근거로 AI(Claude)가 자동으로 작성하고, 자동 검수(팩트·SEO·UX 기준)를 통과한 뒤 사람의 사전 검토 없이 자동 발행됩니다. 오류가 있을 수 있습니다.
{: .notice--warning}

<!-- generator-runtime: {"sha": "5d3c15c4c69f1616c682c22e789d9e9c7231fc07", "branch": "master", "files": {"daily_runtime.py": "21d242511f35f976c917f20f0d4e9cde664f0fc98fb03691b4505f02cce35e26", "generate_daily_post.py": "a11db0917ae3ac6ab1b9609d8610fea5aefd4bf9a4b155fd02539acdfe00c980", "make_og_image.py": "ff6b7c40f77aefc1ba2a9f339a3dfa9116cf0e1425f3635266a43e9742d03d96", "normalize_post_meta.py": "92346af1d91744be1ae50ba52eeb789b00ad952b978e433fae26dbc02fa9c924", "post_meta.py": "aa09670c44ac913f507f7107b3953855481a67ce63241a3efefdf8d9a056f8d3", "source_evidence.py": "6614582abad7cf456d1da846a3937cafa20ae574621d5522bba1c00342ba3933", "test_daily_runtime.py": "250e050832f6604be6d5c4b8897643170f29f618013ed813260144dde9443c80", "test_generate_daily_post.py": "8b1dcec19cbf2caea1215a03152dfea9ab8dae536114c0d8e896e146dd7f7413", "test_source_evidence.py": "87a0c341818a708fa61f72d354f59640e76442aa92597fd2b143a384635327eb", "verify_site.py": "5b5eb6394ddd0261b308918b4b7bd481ac1aea1b29d9e653ac33f9dbfe30146a"}} -->
## dsh-our-free-model, 무엇을 하는 플러그인인가

이 프로젝트는 dsh라는 도구에 설치하는 플러그인입니다. 로그인, 회원가입, API Key 입력 없이 DeepSeek V4.1 Flash, Kimi K3 같은 모델을 바로 쓸 수 있다고 설명합니다(https://github.com/Ebony-Vinyl/dsh-our-free-model/blob/5f61762eed3b2ffea97be82ee32318d1d45e25c1/README.md).

GitHub 저장소 정보 기준으로 주 언어는 JavaScript이고, 2026-09-24에 공개됐습니다. stars는 86975, forks는 2461입니다. 짧은 기간에 모인 숫자치고는 규모가 큰 편이라 실제로 써보는 사람이 많다는 뜻으로 읽힙니다.

프로젝트 README에 따르면 모델 공급원은 OpenCode의 Zen 게이트웨이와 Kilo AI 공공 게이트웨이이며, 제3자 중계를 거치지 않고 직접 연결한다고 밝히고 있습니다. 모델 목록은 상류에서 매번 다시 가져오고 정적 스냅샷을 저장하지 않는다는 점도 README에 명시돼 있습니다.

## 실무에 넣을 때 확인할 점

README에 나온 기능이 많아서 실제로 쓸 때는 몇 가지를 먼저 걸러야 합니다.

- 사고 강도(reasoning effort) 처리 방식이 모델마다 다릅니다. 자체 단계 메뉴가 있는 모델(DeepSeek V4.1 Flash, GLM 5.3 Flash 등)은 원래 값 그대로 상류에 전달되고, 없는 모델은 Light/Balanced/Deep 예산 단계로 변환됩니다.
- OpenAI 호환 로컬 전달 포트와 Anthropic Messages 엔드포인트(`/v1/messages`)를 함께 제공한다고 돼 있어, Claude Code나 Anthropic SDK를 쓰는 기존 코드베이스에 끼워 넣기 쉬운 구조로 보입니다.
- 토큰 절약 기능(RTK)은 git diff, 로그 같은 도구 출력물을 요청 전에 압축한다고 설명합니다. 40KB짜리 git diff에서 90%의 바이트를 줄이면서도 모델이 답변을 유지했다는 수치가 README에 실려 있습니다.
- 집계 채널로 77개 제공자(OpenRouter, Groq, Gemini, DeepSeek 등)를 등록할 수 있고, Key는 로컬 0600 권한 파일에만 저장된다고 합니다.

이런 기능 목록 자체는 README(https://github.com/Ebony-Vinyl/dsh-our-free-model/blob/5f61762eed3b2ffea97be82ee32318d1d45e25c1/README.md)에 상세히 적혀 있지만, 무료 게이트웨이가 출구 IP 기준으로 쿼터를 매긴다는 설명도 함께 있습니다. 이 부분은 운영 환경에 올리기 전에 반드시 따져봐야 합니다.

## 설치 전에 반드시 봐야 할 함정

README는 설치 섹션에서 경고를 따로 달아뒀습니다. npm 레지스트리에 올라온 이름 그대로의 `dsh-our-free-model` 패키지는 이 저장소가 배포한 것이 아니라고 명시합니다. 코드가 변경돼 있고 저장소에 없던 파일까지 포함돼 있다는 설명입니다.

공식 배포본은 스코프가 붙은 `@ebony-vinyl/dsh-our-free-model`이며, Release의 tgz 파일과 동일한 버전이라고 안내합니다. 이 차이를 모르고 설치하면 서명된 업그레이드 검증을 받을 수 없습니다.

독립 실행형 서비스(`packages/standalone`)도 개발 중이라고 돼 있지만, 설치 패키지와 릴리스는 아직 나오지 않았다는 문구가 README에 그대로 적혀 있습니다. 이 부분의 실제 안정성은 여기까지는 확인되지 않습니다.

이 플러그인을 프로젝트에 넣어보려면 먼저 저장소의 README(https://github.com/Ebony-Vinyl/dsh-our-free-model/blob/5f61762eed3b2ffea97be82ee32318d1d45e25c1/README.md)에서 라이선스 조건과 공식 npm 스코프 이름을 직접 대조해 보는 게 순서입니다. 그 다음에는 자신의 네트워크 환경에서 출구 IP 쿼터 제한이 실제로 어떻게 걸리는지 로컬에서 먼저 테스트해보는 쪽을 권합니다.

---

**참고한 원본 소스**

- [Ebony-Vinyl/dsh-our-free-model — official_readme](https://github.com/Ebony-Vinyl/dsh-our-free-model/blob/5f61762eed3b2ffea97be82ee32318d1d45e25c1/README.md)
