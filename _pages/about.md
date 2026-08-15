---
permalink: /about/
title: "About"
description: "Senior Frontend Engineer 백승준의 전문 영역, 기술 스택, 경력 흐름과 프로젝트 경험"
search: true
last_modified_at: 2026-08-15T00:00:00+09:00
toc: true
toc_sticky: true
author_profile: false
classes: wide portfolio-page
---

<p class="page-kicker">ABOUT</p>

16년 이상 Web/UI 개발을 수행하며 Web Standards와 퍼블리싱에서 JavaScript UI, SPA, Vue, Angular, React 기반 Enterprise Frontend로 업무 영역을 확장해 왔습니다.

최근에는 자동차, 금융, 보험, 전자 분야에서 React 기반 신규 개발과 운영·개선을 수행했습니다. Full-stack 경험은 주력 포지션이 아닌 **Frontend 중심의 통합 개발 경험**으로 다룹니다.

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
- 컴퓨터프로그래머 2급(C언어) — 원본 기술이력서에는 없어 최종 확인 필요

## Contact

경력 및 공개 가능한 작업은 [GitHub 프로필](https://github.com/bsjuuny)에서 확인할 수 있습니다.
