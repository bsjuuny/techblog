---
title: "스타와 다운로드는 다르다: 2026년 UI/UX 스택 현황"
date: 2026-10-06 14:40:00 +0900
last_modified_at: 2026-10-06 14:40:00 +0900
categories:
  - frontend
  - trend
category_label: "Frontend · Trend"
tags:
  - UI Library
  - Design Tools
  - Tailwind CSS
  - shadcn/ui
  - npm
  - GitHub
excerpt: "GitHub 스타, npm 주간 다운로드, 2026년 디자이너 설문으로 UI 라이브러리와 디자인 도구 현황을 비교하고 지표별 한계를 정리했습니다."
toc: true
toc_sticky: true
---

> **AI 활용 안내**  
> 이 글은 작성자의 주제 선택과 관점에 따라 AI와 함께 초안을 작성하고, 공개 자료를 대조해 문장을 다듬었습니다. 최종 내용과 공개 여부는 작성자가 직접 확인했습니다.
{: .notice--info}

> **데이터 기준 안내**  
> GitHub 스타는 2026년 10월 6일, npm 다운로드는 2026년 9월 28일~10월 4일, 설문은 2026년 3월 14일~4월 6일 기준입니다. GitHub·npm 수치는 공식 API로 직접 조회했고, 설문과 접근성 수치는 원문에서 확인했습니다. 1차 출처를 확인하지 못한 수치는 "참고용"으로 따로 표시했습니다.
{: .notice--warning}

## 스타가 많은 라이브러리가 가장 많이 쓰이는 라이브러리일까

결론부터 말하면 같지 않습니다. 이번에 비교한 UI 라이브러리 중 GitHub 스타 1위는 Bootstrap이지만, 같은 시기 npm 주간 다운로드는 MUI가 약 1.7배 많았습니다. 스타가 가장 적었던 Radix는 다이얼로그 패키지 하나만으로 다운로드 2위였습니다.

이 글은 GitHub 스타, npm 주간 다운로드, 디자이너·빌더 설문으로 2026년 UI/UX 스택 현황을 정리합니다. 특정 라이브러리를 권하는 글이 아니라, 각 지표가 무엇을 말해 주고 무엇을 말해 주지 않는지 보는 글입니다.

## 디자이너와 빌더는 매주 어떤 도구를 쓰나

UX Tools의 "State of Prototyping: Spring 2026" 설문에서 주간 사용 도구 상위 10개는 다음과 같습니다.

| 순위 | 도구 | 주간 사용률 | 구분 |
|---|---|---|---|
| 1 | Figma | 82.6% | 디자인 |
| 2 | Claude | 50.8% | AI |
| 3 | ChatGPT | 48.2% | AI |
| 4 | Claude Code | 38.4% | AI |
| 5 | Figma Make | 34.8% | AI |
| 6 | FigJam | 34.0% | 협업(화이트보드) |
| 7 | Slack | 32.7% | 협업 |
| 8 | Gemini | 32.3% | AI |
| 9 | Google Meet | 24.8% | 협업 |
| 10 | Notion | 24.5% | 협업 |

*설문 기간: 2026-03-14 ~ 2026-04-06 · 응답자 1,478명 · 복수 응답 문항이라 합계가 100%를 넘습니다 · 출처: UX Tools, State of Prototyping: Spring 2026 (CC BY 4.0)*

설문 응답 기준으로, 이 설문 응답자 중 82.6%가 매주 Figma를 쓴다고 답했습니다. 2위는 Claude(50.8%)이고, 상위 10개 중 5개가 AI 도구입니다.

상위 10위 안에 Sketch와 Adobe 계열 도구는 없습니다. 이 설문 응답자 사이에서 10위 밖이라는 뜻이지, 쓰이지 않는다는 뜻은 아닙니다. 응답자는 18개 지역의 디자이너와 빌더로, 스타트업 29.3%, 프리랜서 17.9%, 대기업 17.7%, 중견 기업 15.4%, 에이전시 13.5%, 학생 6.2%이고 61.4%가 북미 외 지역입니다.

Figma의 디자인 소프트웨어 점유율이 약 40.65%(2025년 3월 기준)라는 수치도 알려져 있습니다. 1차 출처를 확인하지 못한 참고용 수치이고, 설문 사용률과는 재는 대상이 달라 비교하지 않았습니다.

## GitHub 스타와 npm 다운로드는 왜 순위가 다른가

| 순위 | 저장소 | 스타 |
|---|---|---|
| 1 | twbs/bootstrap | 174,985 |
| 2 | shadcn-ui/ui | 125,176 |
| 3 | ant-design/ant-design | 99,690 |
| 4 | mui/material-ui | 99,131 |
| 5 | tailwindlabs/tailwindcss | 97,773 |
| 6 | penpot/penpot | 60,727 |
| 7 | saadeghi/daisyui | 42,545 |
| 8 | chakra-ui/chakra-ui | 40,676 |
| 9 | mantinedev/mantine | 31,798 |
| 10 | heroui-inc/heroui | 30,871 |
| 11 | radix-ui/primitives | 19,361 |

*GitHub API 직접 조회 · 조회 기준일: 2026-10-06 · 11개 저장소 모두 보관(archived) 상태가 아니며 최근 2주 안에 push가 있었습니다*

다음은 npm 주간 다운로드입니다. 위 표의 스타 순위를 함께 적었습니다.

| 다운로드 순위 | 패키지 | 주간 다운로드 | 스타 순위 |
|---|---|---|---|
| 1 | tailwindcss | 163,032,225 | 5 |
| 2 | @radix-ui/react-dialog | 91,859,169 | 11 |
| 3 | @mui/material | 12,503,562 | 4 |
| 4 | @headlessui/react | 8,776,461 | 조회 안 함 |
| 5 | bootstrap | 7,193,994 | 1 |
| 6 | antd | 4,517,087 | 3 |
| 7 | @mantine/core | 3,305,015 | 9 |
| 8 | @chakra-ui/react | 2,006,693 | 8 |
| 9 | daisyui | 1,242,047 | 7 |
| 10 | @heroui/react | 770,905 | 10 |

*npm API 직접 조회 · 집계 기간: 2026-09-28 ~ 2026-10-04 (7일) · Radix의 스타는 저장소 전체, 다운로드는 react-dialog 한 패키지 기준입니다*

스타는 저장소가 생긴 뒤 쌓인 누적 관심이고, 다운로드는 최근 일주일의 설치 횟수입니다. 재는 대상이 다르니 순위가 엇갈립니다.

- Bootstrap은 스타 1위, 다운로드 5위입니다. 다운로드는 MUI가 Bootstrap의 약 1.7배입니다.
- Ant Design과 MUI는 스타가 거의 같지만(99,690 대 99,131), 다운로드는 MUI가 약 2.8배입니다.
- Tailwind CSS는 스타 5위, 다운로드 1위입니다.
- Radix는 스타가 가장 적지만 react-dialog 하나가 약 9,186만 회로 2위입니다. shadcn/ui 같은 라이브러리의 내부 의존성으로 쓰여 스타에 비해 실사용이 훨씬 많습니다.

Penpot은 오픈소스 디자인 도구라 다운로드 비교에서 뺐고, shadcn/ui가 없는 이유는 다음 절에서 다룹니다.

## shadcn/ui의 사용량은 어디에서 보이나

shadcn/ui는 컴포넌트 코드를 프로젝트에 복사해 넣는 방식이라 패키지 다운로드 수로 사용량을 잴 수 없습니다. 컴포넌트를 추가해 주는 CLI 패키지는 있지만, 컴포넌트 사용량과는 다른 지표입니다.

그래서 함께 설치되는 패키지를 봅니다. shadcn/ui는 동작과 접근성을 Radix 같은 헤드리스 프리미티브에, 스타일을 Tailwind CSS에 맡기고, 변형(variant) 관리에 class-variance-authority, 아이콘에 lucide-react를 씁니다. 보조 패키지 수치는 다음과 같습니다.

- lucide-react: 134,583,738
- tailwind-merge: 107,067,280
- class-variance-authority: 83,559,474
- framer-motion: 58,492,608 / motion: 28,260,335

*npm API 직접 조회 · 집계 기간: 2026-09-28 ~ 2026-10-04*

tailwind-merge는 MUI의 약 8.6배, class-variance-authority는 약 6.7배입니다. 그래도 이를 shadcn/ui 사용량으로 읽을 수는 없습니다. 모두 shadcn/ui 없이 단독으로도 쓰이고 다른 패키지의 의존성으로도 설치됩니다. motion과 framer-motion은 같은 저장소에서 나오는 애니메이션 패키지이고, motion을 설치하면 framer-motion이 의존성으로 함께 설치됩니다. 두 수치를 더하면 중복 집계입니다.

shadcn/ui 문서에 따르면 조회 직전인 2026년 9월부터 새 프로젝트는 clsx와 tailwind-merge 대신 의존성이 없는 cn 패키지를 설치합니다. 또 현재 문서는 Radix 기반과 Base UI 기반 컴포넌트를 함께 제공합니다. 앞으로 tailwind-merge나 Radix 다운로드로 shadcn/ui 사용을 추정하기는 더 어려워질 수 있습니다.

데이터로 확인되는 것은 이 구성 요소들이 최상위권 다운로드를 기록했다는 데까지이고, 그중 shadcn/ui의 비중은 확인하지 못했습니다.

## AI 대화형 UI, 다크 모드, 접근성은 데이터로 어디까지 보이나

세 주제 모두 직접 확인한 데이터의 범위가 좁습니다.

- **AI 대화형 UI**: 확인한 것은 설문 응답자의 AI 도구 주간 사용률뿐입니다. 작업에 쓰는 도구에 관한 수치이고, 제품에 AI 대화형 UI가 얼마나 들어가는지는 확인하지 못했습니다. Gartner는 2025년 3월 보도자료에서 2028년까지 업무용 앱의 20% 이상이 AI 개인화 알고리즘으로 사용자에 맞춰 바뀌는 경험을 제공할 것으로 예측했습니다. 측정치가 아닌 예측입니다.
- **다크 모드**: 직접 확인한 데이터가 없습니다. 스마트폰 사용자 대다수가 다크 모드를 쓴다는 수치가 자주 인용되지만, 1차 출처를 확인하지 못해 근거로 쓰지 않았습니다.
- **접근성**: WebAIM이 2026년 2월 상위 100만 개 홈페이지를 자동 검사한 결과, 95.9%에서 WCAG 2 오류가 검출됐습니다(2025년 94.8%). 다운로드 2위와 4위는 키보드·포커스 같은 상호작용을 담당하는 헤드리스 컴포넌트지만, 많이 설치된다고 사이트 접근성이 좋아졌다고 볼 수는 없습니다.

## 이 숫자들을 읽을 때 무엇을 조심해야 하나

**다운로드 수**

- CI 설치, 미러, 의존성 전이 설치가 포함됩니다. 사용자 수나 프로젝트 수가 아닙니다.
- tailwindcss는 v4 이후 다른 패키지의 의존성으로도 설치되어 수치가 부풀 수 있습니다.
- Radix는 react-dialog 한 패키지만 조회했습니다. 다른 Radix 패키지가 더 높을 수 있습니다.

**비교 범위**

- 비교 대상은 필자가 임의로 골랐고 Vue·Svelte·웹 컴포넌트 계열은 뺐습니다. React 중심의 단면입니다.

**설문**

- 뉴스레터·소셜 채널·스폰서 네트워크로 모집한 자발적 응답이라 선택 편향이 있습니다. 프로토타이핑 주제라 AI·신규 도구 사용자가 더 많이 응답했을 수 있습니다.
- Slack, Notion, Google Meet 같은 협업 도구도 함께 물었으므로 순위를 디자인 도구 점유율로 읽으면 안 됩니다.
- AI 도구 사용률은 "주간 사용"이지 "UI/UX 작업에 사용"이 아닙니다.
- 결과는 응답자 1,478명에 한정되며 디자이너 전체로 일반화할 수 없습니다.

**참고용 수치**

- 1차 출처를 확인하지 못한 Figma 점유율은 "알려져 있다"로 표시하고 근거로 쓰지 않았습니다. Gartner 수치는 예측입니다.

## 정리: 지표마다 답하는 질문이 다르다

스타는 쌓인 관심, 다운로드는 지금의 설치 규모(부풀림 포함), 설문은 특정 응답자 집단의 습관을 보여 줍니다. 세 지표의 순서가 다른 것은 데이터가 틀려서가 아니라 답하는 질문이 다르기 때문입니다.

라이브러리 검토에 쓴다면 한 주 수치 대신 몇 달 치 추이를 보고, 내 프로젝트에서 직접 의존성인지 전이 의존성인지(`npm ls <패키지>`)부터 확인하는 것이 다음 단계입니다.

---

**참고 자료**

- GitHub REST API, Get a repository: <https://docs.github.com/en/rest/repos/repos#get-a-repository>
- npm 다운로드 수 API 문서: <https://github.com/npm/registry/blob/main/docs/download-counts.md>
- UX Tools, State of Prototyping: Spring 2026 (데이터셋 CC BY 4.0): <https://survey.uxtools.co/spring-2026>
- shadcn/ui 문서: <https://ui.shadcn.com/docs>
- shadcn/ui 변경 기록, September 2026 - cn: <https://ui.shadcn.com/docs/changelog/2026-09-cn>
- WebAIM, The WebAIM Million (2026): <https://webaim.org/projects/million/>
- Gartner, "Gartner Predicts Over 20% of Workplace Apps Will Use AI-Driven Personalization Algorithms for Adaptive Worker Experiences by 2028" (2025-03-12): <https://www.gartner.com/en/newsroom/press-releases/2025-03-12-gartner-predicts-over-20-percent-of-workplace-apps-will-use-ai-driven-personalization-algorithms-for-adaptive-worker-experiences-by-2028>
- 참고용 수치(Figma 점유율): 블로그·시장조사 사이트 재인용이며 1차 출처를 확인하지 못했습니다.
