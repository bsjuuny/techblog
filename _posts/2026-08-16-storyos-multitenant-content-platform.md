---
title: "장소 기반 인터랙티브 스토리 플랫폼을 설계하며 정한 경계들: StoryOS"
date: 2026-08-16 23:10:00 +0900
last_modified_at: 2026-08-16 23:10:00 +0900
categories:
  - project
  - architecture
category_label: "Project · Architecture"
tags:
  - Side Project
  - SaaS
  - Monorepo
  - NestJS
  - Prisma
  - Multi-tenant
excerpt: "박물관·유적지 같은 실제 공간을 이야기형 체험으로 제작·배포하는 멀티테넌트 SaaS StoryOS를 설계하며 MVP 범위를 어디서 끊었는지, 왜 그렇게 끊었는지를 정리합니다."
toc: true
toc_sticky: true
---

> **AI 활용 안내**  
> 이 글은 작성자의 주제 선택과 경험 검토를 바탕으로 AI와 함께 초안을 작성하고 문장을 다듬었습니다. 최종 내용과 공개 여부는 작성자가 직접 확인했습니다.
{: .notice--info}

> **배포 안내**  
> StoryOS는 아직 로컬 개발 환경(Docker Compose)까지만 구현되어 있고 공개 URL로 서비스 중이 아닙니다. 이 글은 설계 단계에서 정한 범위와 판단을 정리한 것입니다.
{: .notice--warning}

StoryOS는 박물관·궁궐·유적지·캠퍼스 같은 실제 공간을 위치 기반 이야기 체험으로 만들고, 운영하고, 배포할 수 있게 하는 멀티테넌트 SaaS다. 비개발자(큐레이터, 지자체 담당자)가 코드 없이 챕터·지점·장면·블록을 쌓아 체험을 만들고, 방문객은 앱 설치 없이 QR이나 링크로 바로 재생한다.

이 프로젝트에서 흥미로웠던 건 기능 구현보다 **"MVP 범위를 어디서 끊을 것인가"**를 계속 결정해야 했다는 점이다. 그 판단들을 정리해 둔다.

## 구조: Next.js와 NestJS를 처음부터 분리했다

```text
apps/web (Next.js)     — /studio(제작자 UI) · /play(방문객 UI)
apps/api (NestJS)      — Auth, Tenant 검증, 도메인 모듈
packages/db (Prisma)   — 스키마 단일 진실 소스
packages/schemas (Zod) — ContentBlock 스키마, 웹·API 공용
```

편집기(Studio)와 실행기(Player)가 `packages/schemas`의 같은 Zod 스키마로 블록을 읽고 쓴다. 폼을 렌더링하는 쪽과 블록을 재생하는 쪽이 서로 다른 컴포넌트를 쓰면서도 "블록이 무슨 데이터를 가져야 하는가"에 대한 정의는 하나로 유지하기 위해서다.

## 판단 기준이 필요했던 부분

### 1. 발행된 체험은 불변으로 취급한다

`Experience`는 여러 개의 `ExperienceVersion`(스냅샷)을 가질 수 있고, 발행 후 내용을 고치려면 새 버전을 복제해서 수정해야 한다 — 이미 발행된 버전의 Chapter/Spot/Scene/Block은 손대지 않는다. 방문객이 체험을 진행하는 도중에 제작자가 내용을 바꿔서 진행 상태가 꼬이는 걸 막기 위한 결정이다. 대신 "발행 중 수정"이라는 편의 기능은 포기했다 — 고치려면 새 버전을 만들어야 한다.

### 2. 테넌트 격리를 애플리케이션 레이어에서 먼저 하고, DB 레벨은 나중으로 미뤘다

모든 도메인 테이블은 `organizationId`로 귀속되고, NestJS의 `TenantGuard`가 JWT의 사용자 → `Membership` → `organizationId`를 확인한 뒤 리포지토리 쿼리에 `where: { organizationId }`를 강제한다. Postgres Row Level Security는 이후 하드닝 단계로 미뤘다 — MVP 단계에서는 애플리케이션 레이어 격리로 시작하는 쪽을 "단순성 우선" 원칙에 따라 선택했다.

이건 BizRadar(다른 사이드 프로젝트)에서 처음부터 RLS를 넣은 것과 반대 선택인데, 두 프로젝트의 위험 성격이 다르기 때문이다. BizRadar는 회사 인증 정보·매칭 데이터라 DB 레벨 격리를 처음부터 요구했고, StoryOS는 MVP 단계에서 기능 검증이 우선이라 애플리케이션 레이어로 먼저 시작하고 하드닝을 이후 단계로 명시적으로 미뤘다. 같은 멀티테넌트 문제라도 프로젝트마다 언제 DB 레벨 격리가 필요한지는 다르다고 판단했다.

### 3. 방문객 도착 확인은 GPS 자동 인식이 아니라 수동 버튼으로 시작했다

Story Player의 기본 도착 확인 방식은 "도착했어요" 버튼을 누르는 수동 확인이다. GPS 자동 인식, 힌트, 도움 요청은 이후 단계로 미뤘다. 위치 기반 체험이라 GPS 자동화가 자연스러워 보이지만, 실내(박물관 지하 전시실 등) GPS 정확도 문제와 오작동 시 디버깅 난이도를 감안해서, 먼저 확실하게 동작하는 수동 확인으로 MVP를 완성하고 자동화는 검증 후에 얹기로 했다.

### 4. 처음부터 하지 않기로 확정한 것들

AR/VR/XR은 스펙 단계에서 플랫폼 전체 영구 제외로 못 박았다. "이후 단계"가 아니라 "안 한다"로 명시한 건, 매번 로드맵을 검토할 때마다 이 논의가 다시 나오는 걸 막기 위해서다. Story AI(콘텐츠 생성), 결제/정산, 마켓플레이스도 범위 밖으로 뒀는데, 이것들은 "안 한다"가 아니라 "지금은 아니다"로 남겨서 향후 단계 로드맵(3~6단계)에 순서를 정해뒀다.

## 남은 과제

- 배포는 아직 로컬 Docker Compose 단계다. 웹은 Vercel, API는 별도 Node 호스팅(Railway/Fly.io), DB는 관리형 Postgres(Neon 등)로 배포하는 계획은 MVP 기능 완성 후로 미뤄뒀다.
- E2E 테스트(Playwright)는 아직 도입 전이다 — 현재는 NestJS 모듈 단위 테스트와 Prisma 테스트 DB, Next.js 핵심 폼/런타임 로직 단위 테스트까지만 갖춰져 있다.
- Row Level Security, 세분화된 Permission 테이블, 접근성 고도화(자막·고대비·스크린리더), 다국어는 로드맵 7단계로 남아 있다.
