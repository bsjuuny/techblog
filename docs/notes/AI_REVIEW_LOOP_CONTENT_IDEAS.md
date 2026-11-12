# AI 코드 리뷰 루프 글감 (여행 챗봇 SSE 재개 기능 작업에서)

여행 챗봇 사이드 프로젝트에 실시간 스트리밍(SSE)·재개(resume) 기능을 넣고, Codex CLI로
"문제가 없을 때까지" 반복 검수를 돌린 작업에서 나온 글감. 전부 실제로 겪은 일이라
CONTENT_PLAN.md의 공개 원칙(실제 수행 경험만)을 그대로 만족한다.

## 후보

1. **AI 코드 리뷰 루프: Codex에게 20번 넘게 검수받은 이야기** (작성 1순위, 발행됨)
   좁은 범위(diff) 검수는 계속 클린하게 나오는데, 전체 프로젝트를 홀리스틱하게 보면
   그때마다 새 문제가 나오는 패턴이 반복 확인됨. 비용 관리를 위해 라운드마다 범위를
   좁히고 reasoning effort를 낮춘 운영 방식도 함께 다룸.

2. **`return res.json()` vs `return await res.json()` — try/catch를 조용히 우회하는 버그**
   외부 카탈로그 fetch에 timeout을 걸었는데, 헤더는 timeout 안에 왔지만 본문 읽기
   도중 timeout이 나는 경우 그 reject가 try 블록 밖에서 일어나 catch를 못 잡던 실화.
   재현 코드 곁들이면 좋은 JS 비동기 함정 글.

3. **DoS를 막으려다 새 DoS를 만든 이야기 — 캐시 상한 설계의 함정**
   동시 스트림 개수 상한(MAX_CONCURRENT_STREAMS)을 고쳤더니 "거부된 요청이 쌓여
   전체 상한을 채우는" 새 DoS가 생기고, 그걸 고쳤더니 "완료된 id를 재사용하면
   상한을 우회하는" 문제가 또 나온 3~4단계 연쇄 실화. 경계 조건 하나가 어떻게
   파급되는지 보여주는 구체적 사례.

4. **SSE 재개(resume) 기능을 처음부터 설계한다면**
   EventEmitter 기반 pub/sub, entry 생명주기, "완료 후 3분" vs "진행 중인데 10분
   무응답"이라는 서로 다른 목적의 두 TTL, AbortController로 좀비 fetch 막기까지
   정리한 레퍼런스 아키텍처 글.

5. **멈춘 fetch 하나가 서버 전체를 마비시킬 때 — 싱글플라이트 캐시의 함정**
   동시 요청 중복 방지용 싱글플라이트(single-flight) promise 캐시 패턴은 흔하지만,
   그 안의 fetch에 timeout이 없으면 요청 하나가 멈추는 순간 그 캐시를 공유하는
   모든 이후 요청이 프로세스 재시작 전까지 같이 멈춘다는, 잘 안 알려진 함정.

## 우선순위

1. AI 코드 리뷰 루프 (발행됨: `_posts/2026-09-07-ai-code-review-loop-with-codex.md`)
2. return await res.json() 버그
3. DoS를 막으려다 DoS를 만든 이야기
4. SSE 재개 기능 아키텍처
5. 싱글플라이트 캐시의 함정
