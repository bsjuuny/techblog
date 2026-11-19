---
title: "Nginx 10년 묵은 RCE 버그 외, 오늘 챙길 인프라 뉴스 5가지"
date: 2026-11-19 09:31:37 +0900
categories:
  - news
  - generated
category_label: "Tech News · Auto"
tags:
  - Auto Generated
excerpt: "Nginx HTTP/2 치명적 RCE와 Quad9의 프랑스 철수를 중심으로, AI 감사·신규 모델 발표 등 오늘의 개발자용 뉴스를 정리합니다."
toc: false
---

> **자동 생성 안내**  
> 이 글은 매일 정해진 시각에 실제 공개 API(GitHub/Hacker News)에서 가져온 데이터를 근거로 AI(Claude)가 자동으로 작성하고, 자동 검수(팩트·SEO·UX 기준)를 통과한 뒤 사람의 사전 검토 없이 자동 발행됩니다. 오류가 있을 수 있습니다.
{: .notice--warning}

<!-- generator-runtime: {"sha": "300d6dde8cff60e6a9a3d85e9328afa26c978cc0", "branch": "master", "files": {"daily_runtime.py": "21d242511f35f976c917f20f0d4e9cde664f0fc98fb03691b4505f02cce35e26", "generate_daily_post.py": "0d3114c7e4e5a0e7bae4f67be2ee59086a1bcb6fe09cf045bd6ae760ededb02b", "make_og_image.py": "ff6b7c40f77aefc1ba2a9f339a3dfa9116cf0e1425f3635266a43e9742d03d96", "normalize_post_meta.py": "92346af1d91744be1ae50ba52eeb789b00ad952b978e433fae26dbc02fa9c924", "post_meta.py": "aa09670c44ac913f507f7107b3953855481a67ce63241a3efefdf8d9a056f8d3", "source_evidence.py": "6614582abad7cf456d1da846a3937cafa20ae574621d5522bba1c00342ba3933", "test_daily_runtime.py": "250e050832f6604be6d5c4b8897643170f29f618013ed813260144dde9443c80", "test_generate_daily_post.py": "135f5e19d16c2cc95e4a47f116618ef483dc286b352e63175d87e456c179aff6", "test_source_evidence.py": "87a0c341818a708fa61f72d354f59640e76442aa92597fd2b143a384635327eb", "verify_site.py": "5b5eb6394ddd0261b308918b4b7bd481ac1aea1b29d9e653ac33f9dbfe30146a"}} -->
## Nginx HTTP/2 RCE부터 Quad9의 프랑스 철수까지, 오늘 챙겨볼 인프라·보안 소식

오늘 브리핑은 인프라와 보안 쪽 무게가 특히 큽니다. Nginx의 치명적인 원격 코드 실행 취약점, DNS 차단을 둘러싼 Quad9의 결단, 그리고 AI가 감사와 코딩 영역에서 밀어붙이는 변화까지 묶었습니다. 하나하나가 독립된 사건이지만, 읽다 보면 '복잡성이 더 이상 방어막이 되지 못한다'는 공통된 신호가 보입니다.

## Nginx HTTP/2 취약점, 내 서버는 안전한가

Wiz Research를 포함한 5개 독립 연구팀이 Nginx에서 인증 없이 원격 코드 실행이 가능한 치명적 취약점 두 개를 발견했습니다([원문](https://www.wiz.io/blog/nginx-http2-rce-vulnerabilities)). CVE-2026-123633과 CVE-2026-123007 둘 다 CVSS 9.2이고, HTTP/2가 켜져 있으면 공격 대상이 됩니다.

CVE-2026-123007은 2015년 버전 1.9.5부터 존재했던 버그라고 합니다. 10년 넘게 숨어 있던 메모리 안전성 결함이 지금에야 발견됐다는 뜻입니다.

실무적으로는 두 가지를 바로 확인해야 합니다. 첫째, 리버스 프록시든 정적 파일 서버든 HTTP/2를 켜둔 Nginx 인스턴스가 있는지 찾아야 합니다. 둘째, 패치가 바로 안 되면 `http2 off;`로 임시 비활성화하는 선택지가 있습니다.

눈여겨볼 대목은 이 취약점들을 AI 모델(Gemini 4 Carbon, ChatGPT 5.6 Sol)로 영향도를 검증했다는 부분입니다. 복잡한 메모리 상호작용을 추적하는 일이 AI 덕분에 쉬워지면서, 오래된 코드베이스에 숨어 있던 버그가 앞으로 더 빨리, 더 많이 드러날 가능성이 커 보입니다.

## Quad9은 왜 프랑스에서 DNS 서비스를 접는가

스위스 비영리 DNS 리졸버 Quad9이 2026년 11월 24일부터 프랑스 사용자에게 응답하지 않기로 했습니다([원문](https://techstackups.com/articles/quad9-leaves-france-dns-blocking/)). beIN Sports의 해적 스트리밍 차단 명령을 거부해 벌금을 받았고, 비슷한 소송이 20건 더 걸려 있어 더는 버틸 수 없다는 게 이유입니다.

이 사안이 개발자에게 중요한 이유는 DNS가 콘텐츠를 담는 시스템이 아니라 단순 포인터 전달 시스템이라는 데 있습니다. 법원이 리졸버에게 '도메인을 막아라'라고 명령해도, 실제 서버는 그대로 살아있고 사용자는 다른 리졸버나 DoH로 몇 초 만에 우회할 수 있습니다.

더 심각한 문제는 선례입니다.

- Quad9이 프랑스 법원 명령을 따르려면 전 세계 사용자에게 동일하게 차단을 적용해야 합니다. 한 국가의 법이 전 세계 리졸버 설정을 좌우하는 구조가 굳어질 수 있습니다.
- Quad9은 사용자 기록을 전혀 남기지 않기 때문에 '프랑스 사용자'만 골라 차단하는 지오블로킹도 기술적으로 신뢰할 수 없습니다.
- DINUM, EDF, SNCF, 마르세유 AP-HM 병원 등 프랑스 내 공공·인프라 기관들도 Quad9에 의존하고 있는데, 이들은 서비스 중단을 사전에 통보받지 못합니다.

인프라를 설계할 때 공개 DNS 리졸버 하나에 의존하는 구조가 생각보다 정치적 리스크에 취약하다는 걸 보여주는 사례입니다.

## KPMG 감사에 AI 에이전트를 투입했더니 벌어진 일

KPMG UK가 'Project Exponential'이라는 이름으로 FTSE 250 상장사 감사에 100개 이상의 AI 에이전트를 투입했습니다([원문](https://europeanbusinessmagazine.com/ai-agents-better-questions-kpmg/)). 감사 책임자 Cath Burnet에 따르면, 일부 AI 에이전트가 사람 감사팀보다 더 깊이 파고들어 더 나은 질문을 던진 사례가 있었다고 합니다.

다만 이건 정식 법정 감사가 아니라 실험이었다는 점을 짚어야 합니다. 감사 파트너가 사인은 했지만, 이 결과가 실제 회계 승인 근거로 쓰이지는 않았습니다. 실험 중에는 AI 에이전트가 규제 요건과 기업 문서를 잘못 매칭해서 사람이 개입해야 했던 사례도 있었다고 합니다.

개발자 입장에서 흥미로운 건 이게 '보조 도구'가 아니라 '워크플로 전체를 나눠 맡는 자율 에이전트' 모델이라는 점입니다. 에이전트들이 정보를 수집하고, 분석하고, 결론 초안을 내고, 서로 역할을 나눠 조율했다고 하니, 단일 LLM 호출이 아니라 멀티 에이전트 오케스트레이션을 실무 프로세스에 꽂아본 사례로 볼 만합니다. KPMG는 20개 대형 감사로 확대할 계획이라고 밝혔지만, 데이터 품질 문제 때문에 수천 건 규모로 바로 가긴 어렵다고 합니다.

## Microsoft Ignite 2026, 모델 7종 발표는 숫자만 보면 될까

Microsoft가 Ignite 2026에서 MAI Cyber 2 Flash, MAI Code 2, MAI Code 2 Flash, MAI Image 2.7, MAI Realtime 1, Dragon Copilot Transcribe, Decision 1.1까지 7개 모델과 2세대 AI 가속기 Maia 200을 공개했습니다([원문](https://microsoft.ai/news/microsoft-ignite-2026/)).

가격 대비 성능을 강조하는 발표라는 점이 눈에 띕니다. MAI Code 2는 GPT-6.1 Sol 대비 98% 코딩 품질을 40% 가격에, Opus 5.5 대비로는 96% 성능을 5% 가격에 낸다고 발표 자료에 나와 있습니다. Decision 1.1은 GPT-6.1 Sol 대비 50배 빠르고 79배 싸다고 합니다.

이 수치들은 모두 Microsoft 측 발표 자료에 실린 벤치마크 결과입니다. 제3자 독립 검증 결과가 아니라는 점은 구분해서 봐야 합니다. 토큰 비용이 치솟는 상황에서 에이전트를 24시간 돌리려는 수요를 정조준한 라인업이라는 건 분명하지만, 실제 워크로드에서 발표된 비율이 재현되는지는 각자 벤치마크해볼 일입니다.

## 그 외 짧게 보고 넘어갈 소식

- DaisyRose-27B: Qwen3.8 기반으로 1,200개 태스크 강화학습을 거쳐 Terminal-Bench 4.1 점수를 5.6%에서 12%로 올렸다는 모델 소개입니다. 원문을 확인하지 못해 제목과 링크만 소개합니다 — [radixark.com](https://www.radixark.com/blog/daisyrose-27b)
- Software companies are trying to kill home computing — 원문을 확인하지 못해 제목만 소개합니다 — [lateblt.livejournal.com](https://lateblt.livejournal.com/526188.html)
- Ruby의 Regexp 및 String 대소문자 변환 관련 다중 취약점 공지입니다. 원문을 확인하지 못해 제목만 소개합니다 — [ruby-lang.org](https://www.ruby-lang.org/en/news/2026/11/18/multiple-vulnerabilities-in-regexp-and-string/). Ruby를 운영 중이라면 공지 원문에서 영향받는 버전을 직접 확인하는 게 우선입니다.

오늘 소식들을 가로지르는 한 가지는, 오래 안전하다고 믿어온 기반들이 생각보다 쉽게 흔들린다는 점입니다. 10년 묵은 Nginx 버그, 법 하나로 끊기는 DNS 리졸버, 사람보다 질문을 더 잘 던지는 AI 에이전트까지, 전제를 다시 점검해볼 타이밍입니다. 다음으로는 자신의 Nginx 배포가 HTTP/2를 쓰고 있는지, 그리고 조직이 어떤 공개 DNS 리졸버에 암묵적으로 의존하고 있는지부터 확인해보면 됩니다.

---

**참고한 원본 소스**

- [Unauthenticated remote code execution in Nginx](https://www.wiz.io/blog/nginx-http2-rce-vulnerabilities)
- [DNS resolvers are the wrong place to fight piracy](https://techstackups.com/articles/quad9-leaves-france-dns-blocking/)
- [Seven new models at scalable price-performance](https://microsoft.ai/news/microsoft-ignite-2026/)
- [AI agents ask better questions than KPMG accountants in audit trial](https://europeanbusinessmagazine.com/ai-agents-better-questions-kpmg/)
- [DaisyRose-27B: 1,200-task RL took Qwen3.8 from 5.6% to 12% on Terminal-Bench 4.1](https://www.radixark.com/blog/daisyrose-27b)
- [Software companies are trying to kill home computing](https://lateblt.livejournal.com/526188.html)
- [Multiple vulnerabilities in Regexp and String case conversion](https://www.ruby-lang.org/en/news/2026/11/18/multiple-vulnerabilities-in-regexp-and-string/)
