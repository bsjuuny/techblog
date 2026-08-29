---
title: "여러 AI 코딩 에이전트를 한 터미널에서 돌리기: Herdr 소개"
date: 2026-08-29 15:00:00 +0900
categories:
  - tools
  - ai-coding
category_label: "Tools · AI Coding"
tags:
  - Rust
  - Terminal
  - AI Agent
  - Claude Code
  - Codex
  - Developer Tools
excerpt: "Claude Code, Codex 같은 AI 코딩 에이전트를 여러 개 동시에 돌릴 때 터미널 창이 늘어나는 문제를, 에이전트 상태(작업 중·대기·막힘)를 인식하는 러스트 기반 터미널 멀티플렉서 Herdr가 어떻게 해결하는지 정리합니다."
toc: true
toc_sticky: true
---

> **AI 활용 안내**  
> 이 글은 Herdr 공식 저장소와 문서를 근거로 AI와 함께 초안을 작성하고 문장을 다듬었습니다. 직접 설치해 장기간 사용한 후기가 아니라, 공개된 README·문서·GitHub 정보를 바탕으로 한 소개 글입니다. 최종 내용과 공개 여부는 작성자가 직접 확인했습니다.
{: .notice--info}

> **기준일 안내**  
> 이 글의 스타 수·버전 정보는 2026년 8월 29일 GitHub 공개 API로 직접 확인한 값입니다. 이후 달라질 수 있습니다.
{: .notice--warning}

Claude Code 하나만 띄워 두고 작업하던 시절은 짧았다. 요즘은 기능 브랜치 하나에 Claude Code, 리뷰용으로 Codex, 실험적인 리팩터링에 다른 에이전트까지 동시에 돌리는 경우가 흔해졌다. 문제는 터미널 창이 그만큼 늘어난다는 것이다. 어느 창이 지금 작업 중인지, 어느 창이 승인 대기로 멈춰 있는지 눈으로 일일이 확인해야 한다.

**[Herdr](https://github.com/herdrdev/herdr)**는 이 문제를 "AI 에이전트를 인식하는 터미널 멀티플렉서"로 풀어보려는 오픈소스 프로젝트다. tmux처럼 패널·탭·세션을 다루면서도, 각 패널에서 실행 중인 프로세스가 코딩 에이전트라는 것을 알고 그 상태(작업 중/대기/막힘)를 사이드바에 보여준다.

## Herdr가 푸는 문제

Herdr 저장소의 설명은 짧고 명확하다.

> the runtime your coding agents live on

즉 Herdr는 "터미널을 여러 개로 나누는 도구"가 아니라, **에이전트가 계속 실행되는 배경 서버**에 더 가깝다. 실제 터미널 세션은 Herdr라는 백그라운드 서버 안에서 돌고, 사용자는 여기에 접속(attach)했다가 떼어냈다(detach) 다시 붙는 클라이언트일 뿐이다.

이 구조 덕분에 나오는 특징이 있다.

- 노트북 뚜껑을 닫거나, 네트워크가 끊기거나, 기기를 재부팅해도 에이전트는 계속 작업을 이어간다.
- 다른 터미널에서, 또는 SSH로 원격에서 같은 세션에 다시 붙을 수 있다.
- 여러 에이전트를 패널/탭으로 나눠 놓고, 지금 어떤 게 작업 중이고 어떤 게 사람의 승인을 기다리는지 사이드바에서 한눈에 볼 수 있다.

## 설치와 기본 사용

공식 사이트 [herdr.dev](https://herdr.dev/)에서 최신 설치 방법과 문서를 확인할 수 있다. macOS·Linux에서는 설치 스크립트나 패키지 매니저로 받을 수 있다.

```bash
# 설치 스크립트
curl -fsSL https://herdr.dev/install.sh | sh

# Homebrew
brew install herdr

# mise
mise use -g herdr
```

Windows는 [별도 베타 지원 문서](https://herdr.dev/docs/windows-beta/)가 있으며, PowerShell 한 줄 명령으로 설치한다.

```powershell
# PowerShell (권장)
powershell -ExecutionPolicy Bypass -c "irm https://herdr.dev/install.ps1 | iex"

# 보안 정책 때문에 PowerShell이 막히면 명령 프롬프트에서
curl.exe -fsSLo install.cmd https://herdr.dev/install.cmd && install.cmd && del install.cmd
```

Windows Terminal, PowerShell 앱, Windows용 Alacritty, `cmd.exe` 패널을 지원하지만, 문서에는 원격 대상 호스트로는 아직 Windows를 지정할 수 없고(원격 호스트는 Linux나 macOS여야 한다) 일부 키 입력·커서 렌더링이 베타 단계의 제약을 받는다고 명시되어 있다.

설치 후에는 작업 디렉터리에서 다음 명령으로 시작한다.

```bash
herdr
```

세션에서 빠져나올 때는 tmux와 비슷하게 프리픽스 키 조합(`Ctrl+B Q`)으로 detach하고, 다시 `herdr`를 실행하면 같은 세션에 재접속(reattach)된다. 실행 중이던 에이전트는 그 사이에도 계속 작업을 진행하고 있다.

## 에이전트를 위해 설계된 부분

Herdr를 다른 터미널 멀티플렉서와 구분 짓는 지점은 "에이전트 인식(agent-aware)"이라는 설계다.

- 각 패널에서 실행 중인 프로세스를 에이전트로 식별하고, **작업 중(working) · 대기(idle) · 막힘(blocked)** 상태를 사이드바에 실시간으로 표시한다.
- 에이전트가 사람의 승인이나 입력을 기다리며 멈춰 있는 상태를 놓치지 않도록 알림(소리·시스템 알림)을 지원한다.
- CLI와 소켓 API를 통해 에이전트가 Herdr 자체를 조작할 수 있다 — 새 패널을 만들거나, 다른 에이전트에게 프롬프트를 보내거나, 다른 에이전트가 실제로 막혔는지 확인하는 식이다. 사람만 에이전트를 다루는 게 아니라, 에이전트끼리도 Herdr를 통해 서로를 조율할 수 있다는 뜻이다.
- 마우스로 패널을 나누고 포커스를 옮기는 것도 지원해서, tmux 단축키에 익숙하지 않은 사용자도 접근하기 쉽다.
- Catppuccin, Gruvbox, Nord, Dracula 같은 테마와 플러그인 마켓플레이스로 확장할 수 있다.

문서에 따르면 Claude Code, Codex, Cursor, OpenCode, Grok 같은 도구와의 연동이 언급되어 있다. 특정 에이전트 전용 도구가 아니라, 터미널에서 실행되는 코딩 에이전트 전반을 대상으로 한다.

## 가벼운 러스트 바이너리라는 선택

Herdr는 Electron 기반 GUI 앱이 아니라 단일 Rust 바이너리로 배포된다. 별도의 클라우드 계정도 필요 없이, 로컬 노트북이든 SSH로 접속하는 원격 서버든 이미 작업하던 환경에서 그대로 실행된다. 라이선스는 원래 AGPL-3.0-or-later였다가, 2026년 8월 29일 기준 GitHub API 확인 결과 **Apache License 2.0**으로 재라이선싱된 상태다. 같은 날 기준 스타 수는 33,000개를 넘겼고, 2026년 3월 말 저장소가 만들어진 뒤로 빠르게 커진 편이다.

## 왜 지금 이런 도구가 나오는가

이 흐름은 앞선 [2026년 8월 AI 인프라 동향]({{ '/technology/ai-infrastructure/ai-infrastructure-trends-august-2026/' | relative_url }}) 글에서 짚었던 방향과 맞닿아 있다. AI가 "질문에 답하는 도구"에서 "여러 도구를 연결해 장시간 작업하는 에이전트"로 넘어가면서, 정작 그 에이전트를 여러 개 동시에 돌릴 때의 운영 문제 — 세션 유지, 상태 확인, 승인 대기 알림 — 가 새로운 카테고리의 도구를 필요로 하고 있다. Herdr는 그 빈틈을 tmux에 익숙한 개발자 워크플로 위에서 채우려는 시도로 볼 수 있다.

물론 이 글은 공식 저장소·문서를 바탕으로 한 소개이지, 직접 여러 프로젝트에서 장기간 사용해 본 후기는 아니다. 실제 도입을 고려한다면 [herdr.dev/docs](https://herdr.dev/docs)의 빠른 시작 가이드와 지원 에이전트 목록을 먼저 확인하는 것을 권한다.

## 참고 자료

- [GitHub: herdrdev/herdr](https://github.com/herdrdev/herdr)
- [공식 사이트: herdr.dev](https://herdr.dev)
- [Herdr 공식 문서](https://herdr.dev/docs)
- [설치 가이드](https://herdr.dev/docs/install/)
- [Windows 지원(베타) 문서](https://herdr.dev/docs/windows-beta/)
