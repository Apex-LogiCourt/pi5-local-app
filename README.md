# pi5-local-app
### 프로젝트 실행 방법
##### 초기 실행 시 
1. 도커 엔진 실행
	- Docker desektop 실행
2. 루트 디렉토리에서 Base 이미지부터 빌드 후에 나머지 이미지 빌드
	- 프로젝트 루트 디렉토리에서 아래 명령어를 입력 
	- `docker compose up base --build -d`
	- `docker compose up core --build -d` 
3. 일단 컨테이너 종료 
	- `docker compose down`

##### 일반적인 실행 
1. 도커엔진 실행
2. `docker compose up`
3. 터미널에 뜨는 Local URL에 접속하면 됨 
```powershell
core-1  | Collecting usage statistics. To deactivate, set browser.gatherUsageStats to false.
core-1  |
core-1  | 
core-1  |   You can now view your Streamlit app in your browser.
core-1  | 
core-1  |   Local URL: http://localhost:8501 //이 부분
core-1  |   Network URL: http://172~                                                                          
core-1  |   External URL: http://118~  
```

- 볼륨 마운트 해놔서 소스코드 변경하면 일반적인 경우 빌드 없이 동작함
- 변경 사항이 씹힐 때는 `docker compose up --build` 로 빌드해주고 기다리면 됨

---

### 브랜치 관리 
- 방식이 결정되면 이후에 추가 

---

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
