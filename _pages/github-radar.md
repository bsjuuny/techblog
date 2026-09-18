---
permalink: /github-radar/
title: "GitHub Radar"
description: "최근 새로 떠오르는 오픈소스 프로젝트를 성장 속도와 활동성 기준으로 골라 소개합니다"
search: true
author_profile: false
classes: wide portfolio-page
---

<p class="page-kicker">OPEN SOURCE RADAR</p>

최근 30일 안에 등장한 GitHub 프로젝트 가운데 빠르게 관심을 얻고 있고, 실제 개발 활동이 이어지는 저장소를 매주 골라 소개합니다. 단순한 star 총합 순위가 아니라 **생성 후 일평균 star, 최근 push, 언어와 소유자 다양성**을 함께 봅니다.

> GitHub가 공식 기간별 star 증가량이나 Trending API를 제공하는 것은 아닙니다. 이 코너의 수치는 수집 시점의 공개 데이터를 바탕으로 계산한 탐색용 지표이며, 품질 보증이나 실사용 추천을 뜻하지 않습니다. 도입 전에는 라이선스, 보안, 유지보수 상태를 직접 확인해 주세요.
{: .notice--info}

<nav class="inline-links" aria-label="GitHub Radar 탐색">
  <a class="text-link" href="{{ '/blog/' | relative_url }}">전체 기술 글</a>
  <a class="text-link" href="{{ '/categories/' | relative_url }}">카테고리별 보기</a>
  <a class="text-link" href="{{ site.atom_feed.path }}">RSS</a>
</nav>

{% assign radar_key = "github-radar" %}
{% assign radar_posts = site.categories[radar_key] %}
{% if radar_posts.size > 0 %}
<div class="article-list article-list--page">
{% for post in radar_posts %}
  {% if post.published != false %}
  <article class="article-item">
    <p class="project-meta">{{ post.date | date: "%Y.%m.%d" }} · {{ post.category_label | default: "GitHub Radar" }}</p>
    <h2><a href="{{ post.url | relative_url }}">{{ post.title }}</a></h2>
    <p>{{ post.excerpt | strip_html | truncate: 200 }}</p>
    {% if post.tags.size > 0 %}<p class="article-tags">{{ post.tags | join: " · " }}</p>{% endif %}
  </article>
  {% endif %}
{% endfor %}
</div>
{% else %}
<div class="empty-state">
  <h2>첫 번째 GitHub Radar를 준비하고 있습니다.</h2>
  <p>후보가 충분하고 자동 팩트·품질 검증을 통과한 주에만 새 브리핑을 게시합니다.</p>
</div>
{% endif %}

## 선정 기준

- 생성된 지 2~30일 사이이며 star가 50개 이상이고 라이선스가 표시된 공개 저장소
- 최근 14일 안에 push가 있고, 포크·보관·비활성 상태가 아닌 저장소
- 생성 후 일평균 star를 중심으로 정렬하되 최근 활동을 보조 신호로 반영
- 같은 소유자는 한 번, 같은 주 언어는 최대 두 번만 선정
- 최근 60일 안에 본문에서 소개한 저장소는 제외
