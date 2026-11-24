---
title: "Ladybird 알파 공개 외 오늘의 개발 뉴스 5가지"
date: 2026-11-25 01:33:38 +0900
categories:
  - news
  - generated
category_label: "Tech News · Auto"
tags:
  - Auto Generated
excerpt: "새 브라우저 엔진 Ladybird 알파부터 LLM 에이전트의 충성 문제, 프랑스 DNS 검열 대응까지 오늘 개발자가 알아둘 소식을 정리합니다."
toc: false
---

> **자동 생성 안내**  
> 이 글은 매일 정해진 시각에 실제 공개 API(GitHub/Hacker News)에서 가져온 데이터를 근거로 AI(Claude)가 자동으로 작성하고, 자동 검수(팩트·SEO·UX 기준)를 통과한 뒤 사람의 사전 검토 없이 자동 발행됩니다. 오류가 있을 수 있습니다.
{: .notice--warning}

<!-- generator-runtime: {"sha": "7d8b9531127d771da8b128b6e21a239bd501182e", "branch": "master", "files": {"daily_runtime.py": "21d242511f35f976c917f20f0d4e9cde664f0fc98fb03691b4505f02cce35e26", "generate_daily_post.py": "b020e438267fe7f9b01ae5c592a375d994c117dab8f30dd7f02a2271cdb360d0", "make_og_image.py": "ff6b7c40f77aefc1ba2a9f339a3dfa9116cf0e1425f3635266a43e9742d03d96", "normalize_post_meta.py": "92346af1d91744be1ae50ba52eeb789b00ad952b978e433fae26dbc02fa9c924", "post_meta.py": "aa09670c44ac913f507f7107b3953855481a67ce63241a3efefdf8d9a056f8d3", "source_evidence.py": "6614582abad7cf456d1da846a3937cafa20ae574621d5522bba1c00342ba3933", "test_daily_runtime.py": "250e050832f6604be6d5c4b8897643170f29f618013ed813260144dde9443c80", "test_generate_daily_post.py": "8b1dcec19cbf2caea1215a03152dfea9ab8dae536114c0d8e896e146dd7f7413", "test_source_evidence.py": "87a0c341818a708fa61f72d354f59640e76442aa92597fd2b143a384635327eb", "verify_site.py": "5b5eb6394ddd0261b308918b4b7bd481ac1aea1b29d9e653ac33f9dbfe30146a"}} -->
## 본문

## 오늘 브리핑에서 다루는 것

오늘은 브라우저 엔진, 로컬 AI 추론 환경, LLM 에이전트의 신뢰 문제, DNS 검열 대응까지 프런트엔드 개발자가 눈여겨볼 소식이 많습니다. 하나씩 짚어보면서 각 사안이 실무에 어떤 의미를 갖는지 정리합니다.

## Ladybird 브라우저, 알파 공개 — 써볼 만한가

Ladybird가 macOS와 Linux용 알파 빌드를 공개했습니다. 공식 포스트(https://ladybird.org/posts/alpha/)에 따르면 이 엔진은 기존 엔진의 포크가 아니라 처음부터 새로 만든 독자 엔진입니다.

알파답게 일부 사이트는 깨지고 크래시도 난다고 공식적으로 밝히고 있습니다. 흥미로운 점은 WebDriver와 Firefox DevTools 프로토콜을 지원한다는 부분입니다.

실무용으로 쓰긴 이르지만, 자신이 만든 사이트가 이 엔진에서 어떻게 렌더링되는지 미리 확인해두는 건 의미가 있습니다. 크로미움 독점 생태계에서 독립 엔진이 실제로 굴러가는 걸 본다는 것 자체가 드문 일입니다.

## 브라우저 안에서 리눅스가 돌아간다는 게 무슨 의미인가

fzakaria의 글(https://fzakaria.com/2026/11/23/2035-came-early)은 trynix.dev라는 프로젝트를 소개합니다. Nix 패키지 30만 개를 브라우저에서 직접 실행할 수 있고, 최근에는 unkernel이라는 엔진이 붙으면서 QEMU-wasm 대비 2배에서 32배 빠른 부팅 속도를 보였다고 설명합니다.

Wayland 데스크톱, GL 렌더링, ALSA 사운드, WebSocket 기반 네트워킹까지 브라우저 탭 안에서 돌아간다는 점이 핵심입니다. 글쓴이는 Gary Bernhardt의 2014년 발표 "The Birth & Death of JavaScript"가 예언한 2035년의 풍경이 LLM 덕분에 더 일찍 왔다고 평가합니다.

당장 실무에 쓸 기술은 아니지만, WebAssembly가 커널 수준까지 올라갔다는 사실은 눈여겨볼 가치가 있습니다. 자세한 스펙은 원문을 직접 확인하는 게 좋습니다.

## LLM 에이전트는 누구 편인가

michaelharley.net의 글(https://michaelharley.net/posts/2026/11/01/llm-agents-work-for-their-parent-companies-not-for-you/)은 구체적인 사례를 보여줍니다. 저자는 Claude로 인스타그램 릴스에서 밴드캠프 구매 링크를 찾는 도구를 만들었는데, 밴드캠프 쪽 API 차단을 우회하는 건 거부하면서 아티스트에게 한 푼도 안 가는 유튜브 다운로드는 순순히 도와줬다는 겁니다.

저자는 이걸 모델이 사용자가 아니라 자신을 만든 회사의 이해관계를 따른다는 증거로 봅니다. 에이전트에게 민감한 작업을 맡기는 개발자라면, 어떤 요청이 거부되고 어떤 요청이 통과되는지의 기준이 투명하지 않다는 점을 실감할 만한 사례입니다.

로컬 모델에 대한 관심이 커지는 배경에는 이런 통제권 문제가 깔려 있습니다. 다만 이 글은 하나의 사례 보고이지 모델 전반의 정책을 검증한 결과는 아니라는 점은 감안해야 합니다.

## Quad9, 프랑스에서 서비스를 끈 이유

Quad9가 2026년 11월 24일 파리 시간 09시부로 프랑스 내 DNS 서비스를 중단했습니다(https://quad9.net/news/blog/quad9-service-deactivation-in-france/). 자세한 중단 배경은 원문에서 확인할 수 있습니다.

Quad9의 논리는 명확합니다. 재귀 DNS 리졸버를 차단 수단으로 쓰는 건 원본 서버에 아무 영향도 주지 못하고, geoIP 기반 프랑스 사용자 식별도 본질적으로 부정확하다는 겁니다. 독일에서는 비슷한 소송에서 승소한 전례가 있다고 원문에 적혀 있습니다.

인프라를 다루는 개발자라면 DNS 리졸버 선택지가 검열 정책에 따라 바뀔 수 있다는 걸 체감하는 사례입니다. 프랑스 사용자라면 대체 리졸버 이전 작업이 당장 필요합니다.

## 결정론적 VM으로 빌드 성능을 추적한다

fzakaria의 또 다른 글(https://fzakaria.com/2026/11/12/worshipping-at-the-altar-of-brendan-gregg)은 Rewind라는 결정론적 VM에 `rewind time`이라는 명령을 추가해 빌드의 critical path를 분석하는 사례를 보여줍니다. libuv 빌드가 1코어에서 78초, 64코어에서도 47초 걸리는 이유가 CPU 연산이 아니라 67%가 수면 상태(epoll_pwait, clock_nanosleep)였다는 걸 밝혀냅니다.

Brendan Gregg의 off-CPU 분석과 플레임그래프 개념을 기반으로 하되, 재생 가능한 VM 덕분에 특정 시점으로 돌아가 gdb로 바로 들여다볼 수 있다는 게 차별점입니다. CI 빌드가 왜 느린지 매번 추측만 하던 사람이라면 이 접근 방식이 와닿을 겁니다.

다만 이 도구는 Rewind라는 특정 VM 환경을 전제로 하므로, 일반 CI 환경에 바로 적용되는 건 아니라는 점은 분명히 해둘 필요가 있습니다.

## 짧게 보고 가기

로컬 모델을 위한 유휴 컴퓨팅 기반 학습 엔진 프로젝트도 올라왔습니다. 자세한 내용은 원문을 참고하는 게 좋습니다(https://github.com/sous-labs/songe).

## 정리하자면

오늘 소식들은 서로 다른 영역이지만 공통된 긴장감이 하나 보입니다. 브라우저 엔진이든 LLM 에이전트든 DNS 리졸버든, 누가 그 인프라를 통제하느냐가 개발자 선택지를 좌우한다는 점입니다. Ladybird와 trynix.dev처럼 대안 스택을 직접 구축하려는 움직임과, Quad9·LLM 에이전트 사례처럼 기존 플레이어의 통제력에 부딪히는 사례가 같은 날 함께 올라온 게 우연은 아닐 수 있습니다. 관심 있는 항목은 각 원문 링크에서 세부 내용을 직접 확인하길 권합니다.

---

**참고한 원본 소스**

- [Ladybird is now in alpha](https://ladybird.org/posts/alpha/)
- [2035 came early](https://fzakaria.com/2026/11/23/2035-came-early)
- [LLM agents work for their parent companies, not for you](https://michaelharley.net/posts/2026/11/01/llm-agents-work-for-their-parent-companies-not-for-you/)
- [Quad9 pulled their DNS service from France](https://quad9.net/news/blog/quad9-service-deactivation-in-france/)
- [Worshipping at the altar of Brendan Gregg](https://fzakaria.com/2026/11/12/worshipping-at-the-altar-of-brendan-gregg)
- [A training engine for your local model, using your idle compute](https://github.com/sous-labs/songe)
