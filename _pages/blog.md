---
permalink: /blog/
title: "Tech Notes"
description: "Frontend 개발과 AI 도구 활용 과정에서 마주친 문제를 맥락, 선택, 구현, 검증의 흐름으로 정리하는 기술 블로그"
search: true
author_profile: false
classes: wide portfolio-page blog-index-page
---

{% assign public_posts = site.posts | where_exp: "post", "post.published != false" %}
{% assign featured_post = nil %}
{% for post in public_posts %}
  {% unless post.categories contains "generated" or post.tags contains "Auto Generated" %}
    {% assign featured_post = post %}
    {% break %}
  {% endunless %}
{% endfor %}
{% assign featured_post = featured_post | default: public_posts.first %}
{% assign latest_post = nil %}
{% for post in public_posts %}
  {% unless post.url == featured_post.url %}
    {% assign latest_post = post %}
    {% break %}
  {% endunless %}
{% endfor %}

<section class="blog-index-hero" aria-labelledby="technical-writing-title">
  <p class="portfolio-eyebrow">TECHNICAL WRITING</p>
  <h2 id="technical-writing-title">개발 과정의 판단을<br>다시 쓰는 기술 기록으로</h2>
  <p class="blog-index-hero__lead">Frontend 개발 과정에서 마주친 문제를<br> 맥락 → 선택 → 구현 → 검증의 흐름으로 정리합니다.</p>
  <p class="blog-index-hero__description">특정 프로젝트의 내부 정보를 노출하기보다, 다른 환경에서도 활용할 수 있는 기술적 기준과 시행착오에 집중합니다.</p>
  <nav class="topic-pill-list" aria-label="주요 기술 주제">
    <a class="topic-pill" href="{{ '/categories/#frontend' | relative_url }}">Frontend</a>
    <a class="topic-pill" href="{{ '/categories/#ai-coding' | relative_url }}">AI Coding</a>
    <a class="topic-pill" href="{{ '/tags/#web-performance' | relative_url }}">Performance</a>
    <a class="topic-pill" href="{{ '/categories/#ui-engineering' | relative_url }}">UI Engineering</a>
  </nav>
</section>

{% if public_posts.size > 0 %}
<section class="blog-bento" aria-label="추천 글과 주요 주제">
  <article class="bento-card bento-card--featured">
    <p class="bento-card__label">FEATURED POST</p>
    <h2><a href="{{ featured_post.url | relative_url }}">{{ featured_post.title }}</a></h2>
    <p class="bento-card__excerpt">{{ featured_post.excerpt | strip_html | truncate: 210 }}</p>
    <p class="bento-card__meta">{{ featured_post.date | date: "%Y.%m.%d" }}{% if featured_post.category_label %} · {{ featured_post.category_label }}{% elsif featured_post.categories.size > 0 %} · {{ featured_post.categories | join: " · " }}{% endif %}</p>
    {% include post-tag-pills.html tags=featured_post.tags %}
  </article>

  <article class="bento-card bento-card--topics">
    <p class="bento-card__label">TOPICS</p>
    <h2>관심 영역</h2>
    <ul class="bento-topic-list">
      <li><a href="{{ '/categories/#frontend' | relative_url }}">Frontend Architecture</a></li>
      <li><a href="{{ '/categories/#ui-engineering' | relative_url }}">UI Engineering</a></li>
      <li><a href="{{ '/categories/#ai-coding' | relative_url }}">AI Coding</a></li>
      <li><a href="{{ '/tags/#web-performance' | relative_url }}">Web Performance</a></li>
    </ul>
  </article>

  {% if latest_post %}
  <article class="bento-card bento-card--latest">
    <p class="bento-card__label">LATEST</p>
    <h2><a href="{{ latest_post.url | relative_url }}">{{ latest_post.title }}</a></h2>
    <p>{{ latest_post.excerpt | strip_html | truncate: 110 }}</p>
  </article>
  {% endif %}

  <article class="bento-card bento-card--checklist">
    <p class="bento-card__label">WRITING METHOD</p>
    <h2>실무에 남는 기록</h2>
    <ol class="method-list">
      <li>Context</li>
      <li>Decision</li>
      <li>Implementation</li>
      <li>Verification</li>
    </ol>
  </article>
</section>
{% endif %}

<aside class="notice--info ai-writing-notice" aria-label="AI 활용 안내">
  <strong>AI 활용 안내</strong>
  <p>일부 글은 작성자의 주제 선택과 검토를 바탕으로 AI와 함께 초안을 작성하고 문장을 다듬습니다. 최종 내용과 공개 여부는 작성자가 직접 확인합니다.</p>
</aside>

<div class="section-heading section-heading--split article-index-heading">
  <div>
    <p class="portfolio-eyebrow">ALL NOTES</p>
    <h2>최근 기술 글</h2>
  </div>
  <nav class="inline-links" aria-label="글 탐색">
    <a class="text-link" href="{{ '/categories/' | relative_url }}">카테고리</a>
    <a class="text-link" href="{{ '/tags/' | relative_url }}">태그</a>
    <a class="text-link" href="{{ site.atom_feed.path }}">RSS</a>
  </nav>
</div>

{% if public_posts.size > 0 %}
<div class="article-list article-list--page">
{% for post in public_posts %}
  <article class="article-item">
    <p class="project-meta">{{ post.date | date: "%Y.%m.%d" }}{% if post.category_label %} · {{ post.category_label }}{% elsif post.categories.size > 0 %} · {{ post.categories | join: " · " }}{% endif %}</p>
    <h2><a href="{{ post.url | relative_url }}">{{ post.title }}</a></h2>
    <p class="article-excerpt">{{ post.excerpt | strip_html | truncate: 200 }}</p>
    {% include post-tag-pills.html tags=post.tags %}
  </article>
{% endfor %}
</div>
{% else %}
<div class="empty-state">
  <h2>첫 번째 기술 글을 준비하고 있습니다.</h2>
  <p>공개 범위와 기술적 근거를 확인한 글만 게시합니다. 글이 등록되면 이 페이지에 최신순으로 표시합니다.</p>
</div>
{% endif %}

<section class="topic-section" aria-labelledby="topic-title">
  <div class="section-heading">
    <p class="portfolio-eyebrow">TOPIC MAP</p>
    <h2 id="topic-title">다룰 주제</h2>
  </div>
  <div class="topic-grid topic-grid--compact">
    <article class="topic-card"><h3>Frontend Architecture</h3><p>React, TypeScript, Vue, Angular의 구조와 선택 기준</p></article>
    <article class="topic-card"><h3>UI Engineering</h3><p>Web Standards, 접근성, 반응형 UI와 브라우저 대응</p></article>
    <article class="topic-card"><h3>Enterprise Frontend</h3><p>업무 UI의 상태 설계, API 연동과 운영 경험</p></article>
    <article class="topic-card"><h3>Legacy &amp; Modernization</h3><p>기존 서비스와 Modern Frontend를 함께 운영하는 방법</p></article>
  </div>
</section>
