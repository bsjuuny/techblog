---
permalink: /projects/
title: "Projects"
description: "React, AEM, Vue, Angular와 Web/Mobile UI 경험을 보여주는 백승준의 대표 프로젝트"
search: true
last_modified_at: 2026-08-15T00:00:00+09:00
toc: true
toc_sticky: true
author_profile: false
classes: wide portfolio-page
---

<p class="page-kicker">SELECTED WORK</p>

프로젝트명, 고객사, 근무회사, 기간, 역할과 기술을 원본 경력 자료에서 확인 가능한 범위로 구분했습니다. 확인되지 않은 성과 수치나 리딩 범위는 포함하지 않았습니다.

{% for project in site.data.projects %}
## {{ project.name }}

<dl class="project-facts">
  <div><dt>Period</dt><dd>{{ project.period }}</dd></div>
  <div><dt>Client</dt><dd>{{ project.client }}</dd></div>
  <div><dt>Company</dt><dd>{{ project.company }}</dd></div>
  <div><dt>Industry</dt><dd>{{ project.industry }}</dd></div>
  <div><dt>Role</dt><dd>{{ project.role }}</dd></div>
  <div><dt>Tech Stack</dt><dd>{{ project.stack | join: ", " }}</dd></div>
</dl>

### Overview

{{ project.summary }}

### Key Work

{% for item in project.work %}
- {{ item }}
{% endfor %}

{% unless forloop.last %}<hr class="section-divider">{% endunless %}
{% endfor %}

