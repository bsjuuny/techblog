---
title: "MoE 모델을 로컬에서 돌리는 colibri 엔진 살펴보기"
date: 2026-11-24 01:34:17 +0900
categories:
  - devlog
  - generated
category_label: "Dev Log · Auto"
tags:
  - Auto Generated
  - C
excerpt: "거대 MoE 모델을 GPU 없이도 계층형 캐시로 구동하는 colibri의 구조와 실측 속도, 도입 전 점검할 지점을 정리합니다."
toc: false
---

> **자동 생성 안내**  
> 이 글은 매일 정해진 시각에 실제 공개 API(GitHub/Hacker News)에서 가져온 데이터를 근거로 AI(Claude)가 자동으로 작성하고, 자동 검수(팩트·SEO·UX 기준)를 통과한 뒤 사람의 사전 검토 없이 자동 발행됩니다. 오류가 있을 수 있습니다.
{: .notice--warning}

<!-- generator-runtime: {"sha": "50de599a1185556ec5900dbbcbc4a5ce80dc5210", "branch": "master", "files": {"daily_runtime.py": "21d242511f35f976c917f20f0d4e9cde664f0fc98fb03691b4505f02cce35e26", "generate_daily_post.py": "b020e438267fe7f9b01ae5c592a375d994c117dab8f30dd7f02a2271cdb360d0", "make_og_image.py": "ff6b7c40f77aefc1ba2a9f339a3dfa9116cf0e1425f3635266a43e9742d03d96", "normalize_post_meta.py": "92346af1d91744be1ae50ba52eeb789b00ad952b978e433fae26dbc02fa9c924", "post_meta.py": "aa09670c44ac913f507f7107b3953855481a67ce63241a3efefdf8d9a056f8d3", "source_evidence.py": "6614582abad7cf456d1da846a3937cafa20ae574621d5522bba1c00342ba3933", "test_daily_runtime.py": "250e050832f6604be6d5c4b8897643170f29f618013ed813260144dde9443c80", "test_generate_daily_post.py": "8b1dcec19cbf2caea1215a03152dfea9ab8dae536114c0d8e896e146dd7f7413", "test_source_evidence.py": "87a0c341818a708fa61f72d354f59640e76442aa92597fd2b143a384635327eb", "verify_site.py": "5b5eb6394ddd0261b308918b4b7bd481ac1aea1b29d9e653ac33f9dbfe30146a"}} -->
## colibri가 해결하려는 문제는 무엇인가

colibri는 거대한 MoE(Mixture-of-Experts) 모델을 GPU 없이, 혹은 적은 메모리로 돌리기 위한 추론 엔진입니다. 프로젝트 README에 따르면 GLM-5.2는 744B 파라미터를 가지지만 토큰당 활성화되는 건 약 40B뿐이고, 그중에서도 토큰마다 실제로 바뀌는 라우팅 전문가 부분은 11GB 정도라고 설명합니다(https://github.com/JustVugg/colibri/blob/e479104ae01bdc40ce81e675299b1d230891b321/README.md).

이 구조를 이용해 자주 쓰는 전문가(hot)는 GPU에, 가끔 쓰는 건 RAM에, 거의 안 쓰는 건 NVMe에서 스트리밍해 읽는 계층 구조를 만든 것이 핵심입니다. C로 작성되었고 모델 패밀리별로 파일 하나씩 두는 구조라고 README는 밝히고 있습니다. GitHub 저장소 정보 기준으로 언어는 C, 라이선스는 Apache-2.0이고 2026-07-01에 공개되었습니다.

## 실제로 어떤 모델이, 어느 정도 속도로 돌아가나

README에 실린 벤치마크 표를 보면 모델 크기와 하드웨어에 따라 속도 편차가 큽니다. 이 표는 전부 실측값이라고 밝히고 있고, 측정 머신 사양도 README에 함께 적혀 있습니다(https://github.com/JustVugg/colibri/blob/e479104ae01bdc40ce81e675299b1d230891b321/README.md).

- Qwen3.6-35B-A3B: CUDA 환경에서 30.0 tok/s, CPU에서는 6.0 tok/s
- GLM-5.2(744B): 25GB 랩톱에서 콜드 상태로 0.05~0.1 tok/s, RTX 5090 6장에서 9.0~9.2 tok/s
- Kimi K3(2.8T): 전문가를 6.3GB/s로 읽으면서 토큰당 약 9.4초 소요

이 수치들을 보면 작은 모델은 일반 PC에서도 실사용 가능한 속도가 나오지만, 수백B~TB급 모델은 "돌아간다"는 의미이지 "쓸 만하다"는 의미는 아닙니다. 토큰당 초 단위가 걸리는 구간은 데모나 오프라인 배치 작업 용도에 가깝습니다.

## 내 프로젝트에 붙인다면 무엇을 먼저 봐야 하나

실무에 가져다 쓴다는 전제로 보면 몇 가지 확인할 지점이 있습니다. README는 OpenAI/Anthropic 호환 base URL을 로컬에 띄워준다고 설명하므로(https://github.com/JustVugg/colibri/blob/e479104ae01bdc40ce81e675299b1d230891b321/README.md), 기존 클라이언트 코드를 거의 바꾸지 않고 붙일 수 있다는 점은 장점입니다.

- 디스크가 병목이 되는 대형 모델 구간에서는 NVMe 속도가 응답 속도를 직접 좌우하므로, 배포 전에 디스크 타입부터 확인해야 합니다
- 프런트엔드 입장에서는 로컬 추론 서버의 지연 시간이 수 초~수십 초 단위로 튈 수 있다는 걸 전제로 UI(스트리밍 표시, 타임아웃 처리)를 설계해야 합니다
- 모델별 라이선스가 제각각입니다(Apache-2.0, 비상업용, Meta 라이선스 등)이므로 어떤 모델을 쓸지에 따라 배포 가능 여부가 달라집니다

생성된 지 얼마 안 된 저장소인데도 포크 수가 6441에 달한다는 점은 커뮤니티 관심이 빠르게 붙었다는 신호입니다. 다만 이 정도 규모의 신생 프로젝트가 실제 프로덕션에서 안정적으로 운영된 사례가 있는지는 README만으로는 확인되지 않습니다.

다음으로 확인할 것은 docs/quickstart.md에 있는 설치 단계와, 본인이 가진 하드웨어가 위 표의 "measured" 항목 중 어디에 가까운지 직접 `--list` 옵션으로 돌려보는 작업입니다.

---

**참고한 원본 소스**

- [JustVugg/colibri — official_readme](https://github.com/JustVugg/colibri/blob/e479104ae01bdc40ce81e675299b1d230891b321/README.md)
