---
permalink: /about/
title: "풀스택 개발자 백승준 &#124; David Baek"
# 공유·검색 카드 이미지는 사이트 기본 이미지 대신 프로필 그림을 쓴다(테마 seo.html 이 header.og_image 를 og:image 로 사용, 화면 머리 이미지는 생기지 않음).
header:
  og_image: /assets/images/david.png
  og_image_alt: "풀스택 개발자 백승준 프로필 그림"
description: "풀스택 개발자 백승준(Baek Seungjun, David Baek)은 React·TypeScript 중심의 Senior Frontend Engineer로, Java·Spring Boot 백엔드 기능 개발에 참여한 경험을 갖추고 있습니다. 2009년부터 금융·제조·엔터프라이즈 웹 애플리케이션을 개발·운영했습니다."
search: true
last_modified_at: 2026-11-17T00:00:00+09:00
toc: true
toc_sticky: true
author_profile: false
classes: wide portfolio-page
---

<p class="page-kicker">ABOUT</p>

<p class="about-identity"><strong>백승준 | Baek Seungjun (David Baek)</strong><br>
Senior Frontend Engineer · 풀스택 개발자 (Full-Stack Web Developer)<br>
React · TypeScript · Java · Spring Boot · Enterprise Web Applications<br>
<a href="#english-profile" hreflang="en" lang="en">English profile</a> · <a href="https://github.com/bsjuuny" rel="me">GitHub: bsjuuny</a></p>

풀스택 개발자 백승준은 2009년부터 웹 애플리케이션 개발에 참여해 왔으며, React·TypeScript 중심의 Frontend Engineering과 Java·Spring Boot 기반 백엔드 기능 개발 참여 경험을 갖고 있습니다. 금융, 제조, 엔터프라이즈 환경에서 웹 애플리케이션을 개발하고 운영했으며, 웹 접근성, 반응형 UI, 재사용 가능한 컴포넌트 설계, API 연동과 운영 품질 개선에 중점을 둡니다.

16년 이상 Web/UI 개발을 수행하며 Web Standards와 퍼블리싱에서 JavaScript UI, SPA, Vue, Angular, React 기반 Enterprise Frontend로 업무 영역을 확장해 왔습니다.

최근에는 자동차, 금융, 보험, 전자 분야에서 React 기반 신규 개발과 운영·개선을 수행했습니다. 핵심 전문성은 **React·TypeScript 기반 Frontend**이며, 현대자동차 개인정보 정비 데이터 반출 플랫폼(고객사 현대오토에버)에서는 React UI와 함께 Spring Boot·PostgreSQL 기반 백엔드 기능 개발에 참여했습니다. 백엔드는 기능 개발 참여 범위로, 전체 백엔드 아키텍처 설계·총괄을 맡은 것은 아닙니다.

## Professional Summary

- React, TypeScript, Vue, Angular 기반 Frontend 개발 경험
- AEM 환경의 React 개발과 글로벌 사이트 상시개선 경험
- 금융·자동차·보험·전자·공공·커머스 등 다양한 도메인 경험
- Responsive Web/Mobile UI, Web Standards, Cross-browser 대응 경험
- 신규 화면 개발과 장기간 운영·유지보수를 함께 수행한 경력

## Core Expertise

<div class="expertise-grid expertise-grid--compact">
  <article>
    <h3>Enterprise Frontend</h3>
    <p>금융권과 대기업 환경의 Web/Mobile Frontend 개발·운영</p>
  </article>
  <article>
    <h3>Modern Frontend</h3>
    <p>React, TypeScript, Vue, Angular를 활용한 UI 개발</p>
  </article>
  <article>
    <h3>UI Engineering</h3>
    <p>Web Standards, Responsive UI, Cross-browser 품질 대응</p>
  </article>
  <article>
    <h3>Integration Experience</h3>
    <p>REST API, Ajax/Axios와 Frontend 중심 Backend 연동</p>
  </article>
</div>

## Tech Stack

<div class="skill-groups">
{% for group in site.data.skills.groups %}
  <section class="skill-group" aria-labelledby="skill-{{ forloop.index }}">
    <h3 id="skill-{{ forloop.index }}">{{ group.name }}</h3>
    <ul class="tag-list">
    {% for item in group.items %}<li>{{ item }}</li>{% endfor %}
    </ul>
  </section>
{% endfor %}
</div>

기술 숙련도를 임의의 퍼센트로 표현하지 않고, 실제 프로젝트에서 확인되는 경험 범위로 분류했습니다.

## Selected Projects

{% for project in site.data.projects %}
### {{ project.name }}

<dl class="project-facts">
  <div><dt>Period</dt><dd>{{ project.period }}</dd></div>
  <div><dt>Client / Company</dt><dd>{{ project.client }} / {{ project.company }}</dd></div>
  <div><dt>Role</dt><dd>{{ project.role }}</dd></div>
  <div><dt>Tech</dt><dd>{{ project.stack | join: ", " }}</dd></div>
</dl>

{{ project.summary }}
{% endfor %}

[프로젝트별 담당 업무 자세히 보기]({{ '/projects/' | relative_url }}){: .btn .btn--primary}

## Engineering Experience

### Vue·TypeScript 기반 거래소 SPA

**Context**

회원가입·인증·로그인과 운영 기능을 포함한 거래소 Frontend 개발이 필요한 환경이었습니다.

**Implementation**

Vue, Vue Router, TypeScript로 SPA를 구성하고 Axios/REST API 통신, Cookie 기반 인증 흐름, 다국어 UI를 구현했습니다. 업무 PL 역할과 개발을 함께 수행했습니다.

**Outcome**

회원 관련 Frontend와 운영 기능을 하나의 SPA 흐름으로 구성하고 서비스 운영을 병행했습니다.

### Legacy Web에서 Modern Frontend까지

Web Standards·퍼블리싱 경험을 바탕으로 jQuery, Vue, Angular, React 순으로 기술 범위를 확장했습니다. 신규 프레임워크 경험만 강조하지 않고, 기존 서비스의 운영 안정성과 점진적 개선을 함께 고려해 왔습니다.

## Career Timeline

### Recent / Key Experience

<div class="career-list">
{% for career in site.data.career %}
  {% if career.tier == "recent" %}
  <article class="career-item">
    <div class="career-heading">
      <h4>{{ career.company }}</h4>
      <span>{{ career.period }}</span>
    </div>
    <p><strong>{{ career.position }}</strong> · {{ career.summary }}</p>
  </article>
  {% endif %}
{% endfor %}
</div>

### Earlier Experience

<div class="career-list career-list--compact">
{% for career in site.data.career %}
  {% if career.tier == "earlier" %}
  <article class="career-item">
    <div class="career-heading">
      <h4>{{ career.company }}</h4>
      <span>{{ career.period }}</span>
    </div>
    <p><strong>{{ career.position }}</strong> · {{ career.summary }}</p>
  </article>
  {% endif %}
{% endfor %}
</div>

초기 경력을 삭제하지 않고 간결하게 유지해 전체 경력 흐름이 끊기지 않도록 구성했습니다.

## Education

- 유한대학 컴퓨터정보과 졸업
- 용산고등학교 졸업

## Certifications

- 정보처리산업기사 (2008.07)
- 컴퓨터프로그래머 2급(C언어)

## English Profile
{: #english-profile}

<div lang="en" markdown="1">

**Baek Seungjun (백승준), also known as David Baek** — Senior Frontend Engineer & Full-Stack Web Developer based in South Korea.

### Professional Background

I have been building web applications since 2009. Over more than 16 years my work has grown from web standards and UI publishing, through JavaScript UI and single-page applications with Vue and Angular, to React-based enterprise frontend development. Most of my recent work has been for automotive, banking, insurance, and electronics companies, where I have both built new features and kept long-running services stable in production.

### Core Technical Expertise

- **Frontend:** React, TypeScript, JavaScript, Vue.js, Angular / AngularJS, HTML5, CSS3, jQuery
- **Platform:** Adobe Experience Manager (AEM) with React for global sites
- **Integration and backend:** REST API, GraphQL, Ajax / Axios, Java / Spring Boot, PostgreSQL, AWS Elastic Beanstalk
- **Quality:** web standards, web accessibility, responsive web and mobile UI, cross-browser support

### Frontend Engineering

Frontend is the core of my work. I have built React interfaces on AEM for LG Electronics' global sites and dealer shop, the React UI for Hanwha Life's OCR-based remote identity verification, and a Vue and TypeScript exchange SPA covering sign-up, authentication, multilingual UI, and operations tools, where I also acted as the work-stream lead. I care about predictable UI states, reusable components, and incremental improvement of legacy screens rather than rewrites for their own sake.

### Full-Stack Development Experience

On the Hyundai Motor privacy maintenance-data export platform (client: Hyundai AutoEver; 2026.04–2026.07, via Lockplace), I developed the React frontend and took part in Spring Boot and PostgreSQL feature development, connecting the two through REST APIs. My backend experience is hands-on feature work; I did not design or lead the overall backend architecture.

### Enterprise Projects

| Project | Period | Role |
|---|---|---|
| Hyundai Motor privacy maintenance-data export platform (client: Hyundai AutoEver) | 2026.04–2026.07 | Frontend-focused full-stack development |
| KB Star Banking operations (KB Kookmin Bank) | 2025.05–2026.02 | Web/mobile channel operations and development |
| LG Electronics Dealer Shop | 2025.02–2025.04 | Frontend development (React, AEM) |
| Hanwha Life remote identity verification enhancement | 2024.09–2025.01 | Frontend development (React, OCR) |
| LG Electronics global site operations | 2023.10–2024.07 | Frontend development and operations (React, AEM) |
| Kia Connect Store | 2022.06–2023.07 | Frontend development (HTML, CSS, JavaScript, jQuery) |

Details for each project are in [Selected Projects](#selected-projects) above and on the [Projects]({{ '/projects/' | relative_url }}) page (Korean).

### Technical Writing

I write [David Baek Dev Notes]({{ '/' | relative_url }}), a Korean-language blog on frontend architecture, UI engineering, and production troubleshooting. Some posts are generated automatically from public data and are labeled as such at the top of each post; those are not presented as personal work history.

### GitHub Projects

My personal projects are on GitHub at [github.com/bsjuuny](https://github.com/bsjuuny), including an HR policy search assistant ([hr-chatbot](https://github.com/bsjuuny/hr-chatbot)), a shared rulebook for coordinating AI coding agents ([harness-history](https://github.com/bsjuuny/harness-history)), and a CLI that routes coding tasks between AI tools ([portable-ai-dispatcher](https://github.com/bsjuuny/portable-ai-dispatcher)). These are personal projects, not commercial products.

</div>

## Contact

경력 및 공개 가능한 작업은 [GitHub 프로필](https://github.com/bsjuuny)에서 확인할 수 있습니다.
