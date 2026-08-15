---
permalink: /blog/
title: "Tech Notes"
description: "Frontend 개발과 Enterprise UI 운영 과정에서 얻은 문제 해결 경험을 정리하는 기술 글"
search: true
author_profile: false
classes: wide portfolio-page
---

<p class="page-kicker">TECHNICAL WRITING</p>

Frontend 개발 과정에서 마주친 문제를 **맥락 → 선택 → 구현 → 검증**의 흐름으로 정리합니다. 특정 프로젝트의 내부 정보를 노출하지 않고, 다른 환경에서도 활용할 수 있는 기술적 기준에 집중합니다.

> 일부 글은 작성자의 주제 선택과 검토를 바탕으로 AI와 함께 초안을 작성하고 문장을 다듬습니다. 최종 내용과 공개 여부는 작성자가 직접 확인합니다.
{: .notice--info}

<nav class="inline-links" aria-label="글 탐색">
  <a class="text-link" href="{{ '/categories/' | relative_url }}">카테고리별 보기</a>
  <a class="text-link" href="{{ '/tags/' | relative_url }}">태그별 보기</a>
  <a class="text-link" href="{{ '/feed.xml' | relative_url }}">RSS</a>
</nav>

{% assign public_posts = site.posts | where_exp: "post", "post.published != false" %}
{% if public_posts.size > 0 %}
<div class="article-list article-list--page">
{% for post in public_posts %}
  <article class="article-item">
    <p class="project-meta">{{ post.date | date: "%Y.%m.%d" }}{% if post.category_label %} · {{ post.category_label }}{% elsif post.categories.size > 0 %} · {{ post.categories | join: " · " }}{% endif %}</p>
    <h2><a href="{{ post.url | relative_url }}">{{ post.title }}</a></h2>
    <p>{{ post.excerpt | strip_html | truncate: 200 }}</p>
    {% if post.tags.size > 0 %}<p class="article-tags">{{ post.tags | join: " · " }}</p>{% endif %}
  </article>
{% endfor %}
</div>
{% else %}
<div class="empty-state">
  <h2>첫 번째 기술 글을 준비하고 있습니다.</h2>
  <p>공개 범위와 기술적 근거를 확인한 글만 게시합니다. 글이 등록되면 이 페이지에 최신순으로 표시됩니다.</p>
</div>
{% endif %}

## 다룰 주제

<div class="topic-grid topic-grid--compact">
  <article class="topic-card"><h3>Frontend Architecture</h3><p>React, TypeScript, Vue, Angular의 구조와 선택 기준</p></article>
  <article class="topic-card"><h3>UI Engineering</h3><p>Web Standards, 접근성, 반응형 UI와 브라우저 대응</p></article>
  <article class="topic-card"><h3>Enterprise Frontend</h3><p>업무 UI의 상태 설계, API 연동과 운영 경험</p></article>
  <article class="topic-card"><h3>Legacy &amp; Modernization</h3><p>기존 서비스와 Modern Frontend를 함께 운영하는 방법</p></article>
</div>
