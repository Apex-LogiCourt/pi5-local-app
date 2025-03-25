### Git 커밋 메시지 컨벤션
| 타입 (`type`) | 의미                                               | 예시                            |
| ----------- | ------------------------------------------------ | ----------------------------- |
| `feat`      | 새로운 기능 추가 (feature)                              |                               |
| `fix`       | 버그 수정                                            |                               |
| `docs`      | 문서 변경 (README, 주석 등)                             |                               |
| `style`     | 코드 스타일 변경 (포매팅, 세미콜론 추가 등)                       |                               |
| `refactor`  | 코드 리팩토링 (기능 변경 없이 개선)                            |                               |
| `perf`      | 성능 개선                                            |                               |
| `test`      | 테스트 코드 추가/수정                                     |                               |
| `chore`     | 빌드, CI 설정 변경 (코드 변경 X)                           |                               |
| `revert`    | 이전 커밋 되돌리기                                       |                               |
| `build`     | 빌드 시스템 및 패키지 관련 설정 변경                            | `build: Docker Compose 설정 추가` |
| `deps`      | 의존성 관리 변경 (`package.json`, `requirements.txt` 등) | `deps: 도커 관련 패키지 추가`          |

📌 **예시**

```plaintext
feat: 사용자 검색 기능 추가
fix: 회원가입 시 이메일 중복 체크 오류 수정
docs: API 문서 업데이트
style: ESLint 적용 및 코드 정리
refactor: 데이터베이스 쿼리 최적화
perf: 이미지 로딩 속도 개선
test: 유닛 테스트 추가
chore: GitHub Actions CI/CD 설정 추가
```

- 커밋 메시지 뒤에 관련된 이슈 번호를 붙일 수 있음
- 예시 : ```feat: 사용자 검색 기능 추가 #12```