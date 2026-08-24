---
permalink: /projects/
title: "Projects"
description: "직접 개발·운영하는 Web 서비스와 React, AEM, Vue, Angular 기반 주요 실무 프로젝트"
search: true
last_modified_at: 2026-08-16T00:00:00+09:00
toc: true
toc_sticky: true
author_profile: false
classes: wide portfolio-page
---

<p class="page-kicker">SELECTED WORK</p>

직접 개발하고 Cafe24에서 운영하는 개인 서비스와 실무에서 수행한 주요 프로젝트를 구분해 정리했습니다. 운영 서비스는 2026년 8월 16일 공개 URL의 응답과 화면을 직접 확인했으며, 실무 프로젝트는 원본 경력 자료에서 확인 가능한 범위만 포함했습니다.

## Live Projects

현재 공개 URL에서 동작을 확인할 수 있는 Web 서비스입니다.

<div class="project-grid live-project-grid">
{% for project in site.data.live_projects %}
  <article class="project-card live-project-card">
    {% if project.image %}
    <img class="project-card__thumb" src="{{ project.image | relative_url }}" alt="{{ project.name }} 미리보기" loading="lazy">
    {% endif %}
    <p class="project-meta">{{ project.category }} · LIVE</p>
    <h3>{{ project.name }}</h3>
    <p>{{ project.summary }}</p>
    <ul class="tag-list" aria-label="{{ project.name }} 기술 스택">
    {% for tech in project.stack %}
      <li>{{ tech }}</li>
    {% endfor %}
    </ul>
    <p class="project-card__links">
      <a class="text-link" href="{{ project.url }}" target="_blank" rel="noopener noreferrer">서비스 보기 <span aria-hidden="true">↗</span></a>
      {% if project.case_study_url %}
      <a class="text-link" href="{{ project.case_study_url | relative_url }}">제작기 보기</a>
      {% endif %}
      {% if project.samples_url %}
      <a class="text-link" href="{{ project.samples_url | relative_url }}">생성물 보기</a>
      {% endif %}
    </p>
  </article>
{% endfor %}
</div>

<hr class="section-divider">

## Open Source Tools

배포된 웹 서비스는 아니지만, GitHub에 공개해 직접 사용하고 있는 CLI/개발 도구입니다.

<div class="project-grid">
{% for project in site.data.open_source %}
  <article class="project-card">
    <p class="project-meta">OPEN SOURCE</p>
    <h3>{{ project.name }}</h3>
    <p>{{ project.summary }}</p>
    <ul class="tag-list" aria-label="{{ project.name }} 기술 스택">
    {% for tech in project.stack %}
      <li>{{ tech }}</li>
    {% endfor %}
    </ul>
    <p class="project-card__links">
      <a class="text-link" href="{{ project.url }}" target="_blank" rel="noopener noreferrer">GitHub 보기 <span aria-hidden="true">↗</span></a>
    </p>
  </article>
{% endfor %}
</div>

<hr class="section-divider">

## Selected Client Work

고객사 프로젝트의 내부 정보나 확인되지 않은 성과 수치·리딩 범위는 포함하지 않았습니다.

{% for project in site.data.projects %}
### {{ project.name }}

<dl class="project-facts">
  <div><dt>Period</dt><dd>{{ project.period }}</dd></div>
  <div><dt>Client</dt><dd>{{ project.client }}</dd></div>
  <div><dt>Company</dt><dd>{{ project.company }}</dd></div>
  <div><dt>Industry</dt><dd>{{ project.industry }}</dd></div>
  <div><dt>Role</dt><dd>{{ project.role }}</dd></div>
  <div><dt>Tech Stack</dt><dd>{{ project.stack | join: ", " }}</dd></div>
</dl>

#### Overview

{{ project.summary }}

#### Key Work

{% for item in project.work %}
- {{ item }}
{% endfor %}

{% unless forloop.last %}<hr class="section-divider">{% endunless %}
{% endfor %}
