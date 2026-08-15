# Security Content Review

검토일: 2026-08-15

## 요약

현재 공개 자산에서 개인정보와 내부 업무정보가 확인됐다. 단순히 About에서 접기 UI로 숨기는 것은 보호가 아니며, 파일 자체가 GitHub Pages 경로에 있으면 직접 접근할 수 있다.

## 자산별 분류

| 자산 | 분류 | 이유 | 조치 |
| --- | --- | --- | --- |
| `assets/etc/이력서_백승준_20260123.pdf` | REMOVE_RECOMMENDED | 전화번호, 개인 Email, 주소, 생년정보, 연봉·희망연봉 등 채용에 불필요한 개인정보 포함 | 공개 소스에서 제거하고 비식별 Resume를 별도 제작하기 전까지 링크 금지 |
| `assets/images/kaonsoft/groupware1.png` | REMOVE_RECOMMENDED | 로그인 ID와 입력된 비밀번호 화면 노출 | 공개 소스에서 제거 |
| `assets/images/kaonsoft/groupware2.png` | REMOVE_RECOMMENDED | 직원 사진·이름·결재 문서·조직 정보 노출 | 공개 소스에서 제거 |
| `assets/images/kaonsoft/groupware3.png` | REMOVE_RECOMMENDED | 직원 사진·이름과 내부 결재 설정 화면 노출 | 공개 소스에서 제거 |
| `assets/images/kaonsoft/groupware4.png` | REMOVE_RECOMMENDED | 직원 사진·이름과 사내 자원예약 정보 노출 | 공개 소스에서 제거 |
| `assets/images/kaonsoft/groupware5.png` | REMOVE_RECOMMENDED | 다수 직원 이름, 사번·조직 프로필 정보 노출 | 공개 소스에서 제거 |
| `assets/images/nsuslab/backoffice.png` | REMOVE_RECOMMENDED | Back Office, Player ID·계정 관련 데이터 노출 | 공개 소스에서 제거 |
| `assets/images/nsuslab/myinfo.png` | REMOVE_RECOMMENDED | 계정·개인정보 입력 화면과 Email 정보 노출 | 공개 소스에서 제거 |
| `assets/images/nsuslab/pr1.png` | REVIEW_REQUIRED | 조직 내부 PR 제목과 업무 내용 노출 | 공개 소스에서 제거 권장 |
| `assets/images/nsuslab/deposit.png` | REVIEW_REQUIRED | 결제수단과 내부 운영 UI 노출 | 공개 소스에서 제거 권장 |
| `assets/images/nsuslab/rg.png` | REVIEW_REQUIRED | Responsible Gaming 내부 화면과 정책 UI 노출 | 공개 소스에서 제거 권장 |
| `assets/images/nsuslab/git-2020.png` | REVIEW_REQUIRED | 비공개 조직 기여 이력과 계정 식별자 노출 | 공개 소스에서 제거 권장 |
| `assets/images/nsuslab/git-2021.png` | REVIEW_REQUIRED | 비공개 조직 기여 이력과 계정 식별자 노출 | 공개 소스에서 제거 권장 |
| `assets/images/webzen/*` | SAFE | 공개 회사 사이트 화면으로 확인됨 | 현재는 미노출 유지, 저작권·사용 허용 여부는 별도 확인 |
| `_config.yml`의 Google Analytics ID | SAFE | 공개 측정 ID로 Secret이 아님 | 성능·개인정보 최소화를 위해 analytics 비활성화 |
| `_config.yml`의 Email | REVIEW_REQUIRED | 이력서와 다른 공개 연락처이며 공개 의사 불명확 | 공개 Email 제거 |

## Git history 주의

- 민감 파일은 과거 commit에 포함돼 있어 현재 파일만 제거해도 Git history에서 복구될 수 있다.
- Secret 또는 실제 비밀번호가 포함됐을 가능성이 있다면 관련 자격증명을 즉시 폐기·변경해야 한다.
- history rewrite는 협업과 원격 저장소에 큰 영향을 주므로 자동 수행하지 않았다.
- 필요하면 별도 승인 후 `git filter-repo` 등으로 민감 경로를 제거하고 force push, fork/cache 재확인을 수행해야 한다.

## 공개용 대안

- 실제 고객사 화면 대신 비식별 mockup을 제작한다.
- 회사명·URL·계정·수치·직원 정보가 없는 구조도 또는 UI pattern 예시를 사용한다.
- Resume를 공개하려면 전화번호·주소·생년정보·연봉·희망연봉을 제거한 별도 PDF를 만든다.

