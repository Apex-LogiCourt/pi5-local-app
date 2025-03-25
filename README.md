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

---


### 전체 디렉토리 구조 

```
/logiCourt
├── core
│   ├── case_generation/      
│   │   ├── prompt_templates/ # 사건 생성 프롬프트 템플릿 저장
│   │   ├── evaluators/       # 생성된 사건 평가 (논리적 오류 체크)
│   │   └── case_builder.py   # 사건 빌더 (케이스 데이터 구성)
│   ├── interrogation/        
│   │   ├── prompt_templates/ # 심문용 프롬프트
│   │   └── interrogator.py   # 심문 체인 (증인 답변 생성)
│   ├── evidence.py           # 증거품 관리 및 반박 기능
│   ├── realtime_judgment.py  # 런타임 중 판사 AI 
│   ├── verdict.py            # 최종 판결 로직
│   ├── controller.py         # ✅ 체인 결합 & 게임 실행 총괄
│   ├── chain_config.yaml     # 체인 설정값 (프롬프트 선택, 평가 기준 등)
│   ├── requirements.txt      # 필요한 패키지 목록
│   └── Dockerfile            # 컨테이너 설정 파일

├── rag
│   ├── vector_db/             # 벡터DB (ChromaDB) 관련 모듈
│   ├── legal_document_retriever.py # 법률 문서 검색 엔진
│   ├── embeddings.py          # 문서 벡터화 (Hugging Face 모델 사용)
│   ├── requirements.txt       # RAG 관련 패키지 목록
│   └── Dockerfile             # 컨테이너 설정

├── data
│   ├── case_files/            # 생성된 사건 데이터 저장
│   ├── legal_document/        # 법률 문서 원본 (RAG 참고용)
│   ├── game_logs/             # 게임 실행 로그
│   ├── evidence_resource/     # 증거품 이미지 저장
│   └── config.json            # 환경 변수 모음

├── hardware
│   ├── gpio_handler.py        # GPIO 핀 관리 (이의 있음 버튼 등)
│   ├── devices/
│   │   ├── rfid_reader.py     # RFID 리더기 핸들러
│   │   ├── eink_display.py    # E-Ink 제어 모듈
│   │   ├── button_listener.py # GPIO 버저 버튼
│   │   └── TTS_module.py      # 음성 입출력
│   ├── stubs/                 # 🔥 하드웨어 스텁 코드 모음
│   │   ├── stub_gpio.py       # GPIO 핀 동작 에뮬레이션
│   │   ├── stub_rfid.py       # RFID 리더기 가짜 응답
│   │   ├── stub_eink.py       # 가짜 E-Ink 디스플레이 동작
│   │   ├── stub_button.py     # 버튼 이벤트 에뮬레이션
│   │   └── stub_tts.py        # 음성 입출력
│   ├── gpio_config.yaml       # GPIO 핀 매핑 설정
│   ├── requirements.txt       # GPIO 관련 패키지 목록
│   └── Dockerfile             # 하드웨어 컨테이너 설정

├── ui
│   ├── chat_panel.py     # 채팅 기반 인터페이스
│   └── gui.py            # PyQt GUI (시각적 인터페이스)

├── tests/               # 테스트 코드 모음

├── docs/                      # 기타 프로젝트 관련 문서 

├── main.py                    # 게임 메인 루프
├── config.py                  # API 키 등 설정
├── .gitignore
├── README.md
├── dockerfile.base        
├── requirements.txt        
└── docker-compose.yml      # 컨테이너 orchestration
```



#### 1. `core/` (게임 로직 & AI 체인)
- **게임 진행을 담당하는 핵심 모듈**  
 - **LangChain 체인을 활용하여 사건 생성, 심문, 판결을 수행**  
-  **체인 결합 및 게임 로직 실행 (`controller.py`)**

```
/logiCourt/core
│   ├── case_generation/      # 사건 생성 (LLM 활용)
│   │   ├── prompt_templates/ # 사건 생성 프롬프트 템플릿 저장
│   │   ├── evaluators/       # 생성된 사건 평가 (논리적 오류 체크)
│   │   └── case_builder.py   # 사건 빌더 (케이스 데이터 구성)
│   ├── interrogation/        # 증인 심문 (LLM 기반)
│   │   ├── prompt_templates/ # 심문용 프롬프트
│   │   └── interrogator.py   # 심문 체인 (증인 답변 생성)
│   ├── evidence.py           # 증거품 관리 및 반박 기능
│   ├── realtime_judgment.py  # 판사 AI (실시간 심판)
│   ├── verdict.py            # 최종 판결 로직 (게임 종료 조건)
│   ├── controller.py         # ✅ 체인 결합 & 게임 실행 총괄
│   ├── chain_config.yaml     # 체인 설정값 (프롬프트 선택, 평가 기준 등)
│   └── requirements.txt      # 필요한 패키지 목록
│   └── Dockerfile            # 컨테이너 설정 파일
```

##### **주요 파일 설명**

|파일명|역할|
|---|---|
|`case_builder.py`|사건 데이터를 LLM을 이용해 생성하고 평가|
|`interrogator.py`|증인 심문을 담당하는 체인|
|`evidence.py`|증거품 관리, 태깅, 반박 기능|
|`realtime_judgment.py`|판사가 실시간으로 판단 (LLM 기반)|
|`verdict.py`|최종 판결을 담당 (게임 종료 판단)|
|`controller.py`|**체인 결합 및 게임 진행** (사건 생성 → 심문 → 판결)|
|`chain_config.yaml`|사건 생성 & 심문 체인 설정값 관리|
|`requirements.txt`|게임 로직 실행을 위한 패키지 목록|
|`Dockerfile`|`core/` 컨테이너 설정|

---

#### 2. `rag/` (검색 증강 생성, RAG)

- **벡터DB(ChromaDB)와 법률 문서를 검색하여 증거를 제공**  
- **LLM이 사건을 만들 때 참고할 수 있는 법률 문서 검색**  
- **심문 과정에서 법 조항을 기반으로 반박 논리를 지원**

```
/logiCourt/rag
│   ├── vector_db/             # 벡터DB (ChromaDB) 관련 모듈
│   ├── legal_document_retriever.py # 법률 문서 검색 엔진
│   ├── embeddings.py          # 문서 벡터화 (Hugging Face 모델 사용)
│   ├── requirements.txt       # RAG 관련 패키지 목록
│   └── Dockerfile             # 컨테이너 설정
```

##### **주요 파일 설명**

| 파일명                           | 역할                             |
| ----------------------------- | ------------------------------ |
| `vector_db/`                  | 벡터DB 관련 코드 (ChromaDB 활용)       |
| `legal_document_retriever.py` | **법률 문서 검색 (법 조항 조회 및 근거 제공)** |
| `embeddings.py`               | 텍스트 데이터를 벡터화 (RAG의 핵심)         |
| `requirements.txt`            | RAG 관련 패키지 목록                  |
| `Dockerfile`                  | `rag/` 컨테이너 설정                 |

---

#### 3.`hardware/` (라즈베리파이 & 물리 장치)

 - **게임을 실물 디바이스와 연동**  
 - **버튼, RFID, E-Ink 디스플레이 활용 가능**

```
/logiCourt/hardware
│   ├── gpio_handler.py        # GPIO 핀 관리 (이의 있음 버튼 등)
│   ├── devices/
│   │   ├── rfid_reader.py     # RFID 리더기 핸들러
│   │   ├── eink_display.py    # E-Ink 제어 모듈
│   │   ├── button_listener.py # 버튼 이벤트 에뮬레이션
│   │   └── TTS_module.py      # 음성 입출력
│   ├── stubs/                 # 🔥 하드웨어 스텁 코드 모음
│   │   ├── stub_gpio.py       # GPIO 핀 동작 에뮬레이션
│   │   ├── stub_rfid.py       # RFID 리더기 가짜 응답
│   │   ├── stub_eink.py       # 가짜 E-Ink 디스플레이 동작
│   │   ├── stub_button.py     # 버튼 이벤트 에뮬레이션
│   │   └── stub_tts.py        # 음성 입출력 
│   ├── gpio_config.yaml       # GPIO 핀 매핑 설정
│   ├── requirements.txt       # GPIO 관련 패키지 목록
│   └── Dockerfile             # 하드웨어 컨테이너 설정
```

##### **주요 파일 설명**
| 파일명                  | 역할                        |
| -------------------- | ------------------------- |
| `gpio_handler.py`    | GPIO 핸들링                  |
| `rfid_reader.py`     | RFID 태그 인식 (예: 증거 태깅)     |
| `eink_display.py`    | **E-Ink 디스플레이에 판결 내용 출력** |
| `button_listener.py` | **버저 버튼 인터럽트**            |
| `TTS_module.py`      | **음성 모듈(TTS) **           |
| `gpio_config.yaml`   | GPIO 핀 매핑 설정 파일           |

---
#### 4. `data/` (데이터 저장소)
- **게임 진행 중 생성되는 데이터 및 리소스 저장**  
 - **사건 파일, 법률 문서, 증거 데이터 보관**

```
/logiCourt/data
│   ├── case_files/            # 생성된 사건 데이터 저장
│   ├── legal_document/        # 법률 문서 원본 (RAG 참고용)
│   ├── game_logs/             # 게임 실행 로그
│   ├── evidence_resource/     # 증거품 이미지, 녹음 파일 등
│   └── config.json            # 환경 변수 모음
```

##### **주요 파일 설명**
| 파일명                  | 역할                               |
| -------------------- | -------------------------------- |
| `case_files/`        | LLM이 생성한 사건 케이스 저장               |
| `legal_document/`    | 실제 법률 문서 데이터                     |
| `game_logs/`         | **플레이어 게임 진행 로그 (심문, 증거 제출 기록)** |
| `evidence_resource/` | **증거 파일 저장소 (이미지, 오디오 등)**       |
| `config.json`        | 환경 변수 (DB 연결 정보 등)               |


---

#### 5.`ui/` (사용자 인터페이스)
- **게임 인터페이스 (GUI & 채팅 패널)**
```
/logiCourt/ui
│   ├── chat_panel.py     # 채팅 기반 인터페이스
│   └── gui.py            # PyQt GUI (시각적 인터페이스)
```

##### **주요 파일 설명**
| 파일명             | 역할                       |
| --------------- | ------------------------ |
| `chat_panel.py` | Chainlit 기반 **채팅 인터페이스** |
| `gui.py`        | PyQt 기반 **시각적 인터페이스**    |


