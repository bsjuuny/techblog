---
title: "Linger로 보는 로컬 PC AI 에이전트의 실제 조건"
date: 2026-11-22 01:34:15 +0900
categories:
  - devlog
  - generated
category_label: "Dev Log · Auto"
tags:
  - Auto Generated
  - TypeScript
excerpt: "Linger가 주장하는 12GB GPU 로컬 구동과 메모리 기능이 실무 도입 시 어떤 전제와 제약을 거는지 README 근거로 짚습니다."
toc: false
---

> **자동 생성 안내**  
> 이 글은 매일 정해진 시각에 실제 공개 API(GitHub/Hacker News)에서 가져온 데이터를 근거로 AI(Claude)가 자동으로 작성하고, 자동 검수(팩트·SEO·UX 기준)를 통과한 뒤 사람의 사전 검토 없이 자동 발행됩니다. 오류가 있을 수 있습니다.
{: .notice--warning}

<!-- generator-runtime: {"sha": "09e5d013cd9fb2f9675d3f42af18a1213d35762c", "branch": "master", "files": {"daily_runtime.py": "21d242511f35f976c917f20f0d4e9cde664f0fc98fb03691b4505f02cce35e26", "generate_daily_post.py": "0d3114c7e4e5a0e7bae4f67be2ee59086a1bcb6fe09cf045bd6ae760ededb02b", "make_og_image.py": "ff6b7c40f77aefc1ba2a9f339a3dfa9116cf0e1425f3635266a43e9742d03d96", "normalize_post_meta.py": "92346af1d91744be1ae50ba52eeb789b00ad952b978e433fae26dbc02fa9c924", "post_meta.py": "aa09670c44ac913f507f7107b3953855481a67ce63241a3efefdf8d9a056f8d3", "source_evidence.py": "6614582abad7cf456d1da846a3937cafa20ae574621d5522bba1c00342ba3933", "test_daily_runtime.py": "250e050832f6604be6d5c4b8897643170f29f618013ed813260144dde9443c80", "test_generate_daily_post.py": "135f5e19d16c2cc95e4a47f116618ef483dc286b352e63175d87e456c179aff6", "test_source_evidence.py": "87a0c341818a708fa61f72d354f59640e76442aa92597fd2b143a384635327eb", "verify_site.py": "5b5eb6394ddd0261b308918b4b7bd481ac1aea1b29d9e653ac33f9dbfe30146a"}} -->
## Linger, PC 한 대로 로컬 AI 에이전트를 돌린다는 주장은 어디까지 사실인가

Linger는 2026-11-10에 공개된 오픈소스 개인 에이전트입니다. GitHub 저장소 정보 기준으로 stars는 3255, 언어는 TypeScript, forks는 308입니다. README에 따르면 추론 엔진은 PolyStrata라는 MoE 추론 엔진입니다.

프로젝트 README에 따르면 125B 파라미터급 Qwen3.8-Flash-Next 모델을 12GB GPU + 64GB RAM 조합에서 구동할 수 있다고 설명합니다(https://github.com/simplexai-labs/linger/blob/2f03b64f56f1e7a116d5b19f20a1f3a5fe07b63c/README.md). 방식은 자주 쓰이는 expert는 GPU에, 가끔 쓰이는 건 RAM에, 드물게 쓰이는 건 SSD에 두는 계층형 라우팅입니다. RTX 3060(12GB) 기준 45.5 tok/s라는 수치도 README에 제시돼 있습니다.

## 모델 선택과 메모리는 자동으로 결정되는가

README는 "Model Autopilot" 기능으로 하드웨어를 감지해 적합한 모델을 자동 설치한다고 설명합니다. 49개 모델, 2개 추론 엔진, 1비트~8비트 양자화, 64K~256K 컨텍스트를 조합해 사전 테스트한 결과를 카탈로그로 쓴다는 설명입니다.

실무자 입장에서 확인할 점은 이렇습니다.

- Mac 16GB~32GB, Linux NVIDIA 8GB~24GB 등 티어별 권장 모델과 속도 수치가 README 표에 있지만, 대부분 "시뮬레이션된 티어"에서 측정했다고 명시돼 있어 실제 기기 성능은 더 낮을 수 있습니다.
- SimplexAI 점수는 제3자 AIHOT 스케일을 썼다고 돼 있는데, 이 스케일 자체의 신뢰도는 README만으로는 검증할 수 없습니다.
- Intel Mac용 패키지가 없고 Docker Compose로 대체해야 한다는 점도 설치 전에 챙겨야 할 제약입니다.

이 자동 선택 로직이 실제 프로덕션 환경, 특히 멀티유저 서버에서 어떻게 동작하는지는 README 범위를 넘는 부분이라 여기까지는 확인되지 않습니다.

## 메모리·프로액티브 기능, 내 프로젝트에 넣을 때 뭘 따져야 하나

README는 LoCoMo 벤치마크에서 Linger가 95%를 기록해 Zep(94.7%), Mem0(92.5%) 등 경쟁 제품보다 높다고 주장합니다(https://github.com/simplexai-labs/linger/blob/2f03b64f56f1e7a116d5b19f20a1f3a5fe07b63c/README.md). 매일 밤 메일, 채팅, 회의 내용을 위키 페이지로 정리해 모든 에이전트가 검색할 수 있게 하는 구조입니다.

"Another Me"라는 프로액티브 기능도 눈에 띕니다. 사용자의 반응을 보고 규칙을 매일 밤 재작성한다는 설명인데, 재학습이 아니라 짧은 규칙 목록만 갱신한다고 돼 있습니다.

프런트엔드 개발자가 이 프로젝트를 도입 전 검토할 포인트는 다음과 같습니다.

- 라이선스가 NOASSERTION으로 표기돼 있어 상업적 사용 전 라이선스 조건을 직접 확인해야 합니다.
- 기본 계정이 `owner@linger.local` / `test1234`로 생성된다고 Docker Compose 가이드에 명시돼 있어, 배포 전 반드시 교체해야 합니다.
- macOS 패키지가 아직 서명되지 않아 `xattr` 명령으로 격리 속성을 풀어야 실행된다는 점도 사용자 온보딩 문서에 반영해야 할 부분입니다.

다음에 확인할 것은 실제로 Docker Compose로 띄워보고 PolyStrata 라우팅이 본인 GPU 사양에서 README 수치와 얼마나 차이 나는지 직접 재는 작업입니다.

---

**참고한 원본 소스**

- [simplexai-labs/linger — official_readme](https://github.com/simplexai-labs/linger/blob/2f03b64f56f1e7a116d5b19f20a1f3a5fe07b63c/README.md)
