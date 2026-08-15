---
permalink: /blog/
title: "Tech Blog"
description: "Frontend 개발과 Enterprise UI 경험을 정리하는 백승준의 기술 블로그"
search: true
author_profile: false
classes: wide portfolio-page
---

<p class="page-kicker">TECHNICAL WRITING</p>

## 실제 경험을 검증한 글만 공개합니다

현재 공개된 기술 아티클은 없습니다. 프로젝트와 운영 경험에서 일반화할 수 있고 회사 내부정보를 포함하지 않는 주제부터 순차적으로 정리할 예정입니다.

{% assign public_posts = site.posts | where_exp: "post", "post.published != false" %}
{% if public_posts.size > 0 %}
<div class="article-list">
{% for post in public_posts %}
  <article>
    <p class="project-meta">{{ post.date | date: "%Y.%m.%d" }}</p>
    <h2><a href="{{ post.url | relative_url }}">{{ post.title }}</a></h2>
    <p>{{ post.excerpt | strip_html | truncate: 180 }}</p>
  </article>
{% endfor %}
</div>
{% else %}
<div class="empty-state">
  <h2>Articles in preparation</h2>
  <p>존재하지 않는 글을 발행된 것처럼 표시하지 않습니다. 작성 후보는 저장소의 콘텐츠 계획에서 별도로 관리합니다.</p>
</div>
{% endif %}

