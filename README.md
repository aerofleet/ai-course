# ai-course

AI 교육과정 실습 프로젝트입니다.
LangChain + OpenAI를 활용하여 AI 기능을 학습합니다.

## 개인 비서 웹앱

`personal-assistant/`에 React + Vite + TypeScript 개인 비서 MVP가 있습니다. Google Calendar/Gmail을 브라우저에서 직접 연결하며 설정과 사용법은 [`personal-assistant/README.md`](personal-assistant/README.md)를 참고하세요. CI는 웹앱 빌드를 확인한 뒤 서버에서 빌드하고 `/assistant/` 경로로 제공합니다. GitHub Actions 저장소 변수 `VITE_GOOGLE_CLIENT_ID`에는 웹 애플리케이션 유형 Google OAuth Client ID가 필요합니다.

## 프로젝트 구조

```
ai-course/
├── .github/workflows/
│   └── deploy.yml        # CI/CD 자동 배포 워크플로우
├── .env.example          # API 키 설정 예시
├── .env                  # 실제 API 키 (GitHub에 올라가지 않음)
├── .gitignore
├── requirements.txt      # 필요한 패키지 목록
├── check_langchain.py    # LangChain 정상 작동 확인 스크립트
├── assistant_chain.py    # 업무 어시스턴트 파이프라인 (Chain, Retriever, Tool, Memory)
├── SUBMISSION.md         # 과제 제출용 구조 분석 요약
└── README.md
```

## 환경

- Python 3.12
- 실행 서버: Ubuntu (OCI)
- 가상환경: `~/ai-venv`

## 설치 방법

### 1. 레포 클론

```bash
git clone https://github.com/aerofleet/ai-course.git
cd ai-course
```

### 2. 패키지 설치

```bash
pip install -r requirements.txt
```

### 3. API 키 설정

`.env.example`을 복사해서 `.env` 파일을 만듭니다.

```bash
cp .env.example .env
```

`.env` 파일을 열어서 본인의 OpenAI API 키를 입력합니다.

```
OPENAI_API_KEY=sk-proj-여기에본인키입력
```

API 키는 https://platform.openai.com/api-keys 에서 발급받을 수 있습니다.

## 실행 방법

```bash
source ~/ai-venv/bin/activate
cd ~/ai-course
python check_langchain.py
```

### 성공 시 출력 예시

```
==================================================
LangChain 정상 작동 확인 완료!

질문: LangChain이 무엇인지 초등학생도 이해할 수 있게 한 문장으로 설명해줘.

AI 응답:
LangChain은 컴퓨터가 사람처럼 글로 묻는 질문에 더 똑똑하게 대답하도록 도와주는 도구 모음이야.
==================================================
```

## 워크플로우

```
로컬 (IntelliJ) → GitHub → AI 서버 (SSH)
  코드 작성/편집     push/pull    pull & 실행
```

1. 로컬에서 코드 작성 후 `git push`
2. GitHub Actions가 자동으로 서버에 배포
3. 서버에서 `python 파일명.py` 실행

## CI/CD (GitHub Actions)

`main` 브랜치에 push하면 GitHub Actions가 자동으로 AI 서버에 배포합니다.

### 자동 배포 흐름

```
git push → GitHub Actions 실행 → SSH로 서버 접속 → git pull + pip install
```

### GitHub Secrets 설정

레포 → Settings → Secrets and variables → Actions에 아래 값을 등록해야 합니다.

| Secret | 설명 |
|--------|------|
| `SERVER_HOST` | AI 서버 IP |
| `SERVER_USER` | SSH 접속 사용자명 |
| `SSH_PRIVATE_KEY` | SSH 개인키 전체 내용 |
| `OPENAI_API_KEY` | OpenAI API 키 |

### 배포 확인

GitHub 레포 → Actions 탭에서 배포 성공/실패 여부를 확인할 수 있습니다.

## 업무 어시스턴트 파이프라인 (assistant_chain.py)

LangChain 핵심 요소 4가지를 활용한 업무 자동화 파이프라인입니다.

### 파이프라인 흐름

```
텍스트 입력 → [Chain] 요약 → [Retriever] 문서 검색 → [Tool] 메일 전송
                                                       [Memory] 대화 이력 저장
```

### LangChain 핵심 요소

| 요소 | 역할 | 구현 |
|------|------|------|
| **Chain** | 프롬프트 + LLM을 연결하여 텍스트 3줄 요약 | `PromptTemplate \| ChatOpenAI \| StrOutputParser` |
| **Retriever** | 사내 정책 문서에서 관련 문서 검색 | LLM 기반 문서 매칭 |
| **Tool** | 요약 + 검색 결과를 메일로 자동 발송 | `send_email_tool()` (Mock) |
| **Memory** | 대화 이력을 저장하여 맥락 유지 | `ChatMessageHistory` |

### 실행

```bash
source ~/ai-venv/bin/activate
cd ~/ai-course
python assistant_chain.py
```

### 실행 결과 예시

```
[1단계: 텍스트 요약 Chain 실행 중...]
요약 완료:
- 2026년 3분기 AI 어시스턴트 도입 프로젝트의 진행 경과를 보고합니다.
- LangChain 기반 업무 자동화 파이프라인 설계 완료, 서버 환경 구축 및 OpenAI API 연동 테스트 성공.
- 다음 단계로 사내 회의록 요약 시스템과 Google Drive 및 메일 API 연동 실증 프로젝트 착수 예정.

[2단계: 관련 사내 문서 Retriever 검색 중...]
검색된 참조 지식: 사내 AI 도입 정책 가이드라인: 외부 API 사용 시 BYOK 원칙 준수 및 개인정보 마스킹 필수.

[3단계: 최종 보고 메일 본문 구성 및 Tool 전송 중...]
==================================================
[메일 자동 발송 완료 알림]
  수신자: manager@company.com
  제목: [자동 보고] 프로젝트 현황 요약 및 사내 규정 참조 건
  ...
==================================================
```

### 사용 모델

- LLM: `gpt-5-nano` (고정)

## 자주 발생하는 오류와 해결 방법

| 오류 | 원인 | 해결 방법 |
|------|------|-----------|
| `OPENAI_API_KEY가 설정되지 않았습니다` | .env 파일 없음 또는 키 미입력 | `.env` 파일 생성 후 API 키 입력 |
| `PermissionDeniedError: model not found` | 모델 접근 권한 없음 | OpenAI 콘솔에서 모델 권한 확인 또는 다른 모델로 변경 |
| `ModuleNotFoundError` | 패키지 미설치 | `pip install -r requirements.txt` 실행 |
| `ConnectionError` | 인터넷 연결 문제 | 네트워크 상태 확인 |
| `RateLimitError` | API 사용량 초과 | OpenAI 결제 설정 확인 |
# 후속 조회와 한국 음력 날짜 표시 변환 (2026-09-26)

## 비서용 LangGraph 및 팀 공유 (2026-09-27)

- 실제 비서 API의 명령 해석과 응답 생성을 `assistant_graph.py`의 LangGraph로 연결한다. 실행 경로는 `승인·입력 검증 → 일정 생성 및 초대 → 결과 보고`다. 실행 API는 Calendar 웹 클라이언트로 발급된 `calendar.events` 토큰을 검증한다.
- 팀 이메일 입력란에 쉼표로 구분해 최대 50명을 입력하거나 명령에 이메일을 명시한다. `내일 오전 10시부터 11시까지 회의 만들고 팀에 공유해줘`를 입력하면 제목·시간·초대 대상을 표시한다. `확인하고 생성·공유` 승인 후 생성한다. 공유 방식은 Calendar 참석자 초대(`attendees`, `sendUpdates=all`)이며 별도 Gmail 안내 메일 발송은 아니다.
- 오전/오후만 입력하면 시작 시간을 질문한다. 팀 이메일이 없으면 이메일을 질문한다. 추가 답변은 미완료 요청과 합쳐 해석한다. 정보가 확보되면 중복 질문 대신 승인 화면으로 진행한다.
- 사용자별 작업 ID에서 Google 이벤트 ID를 생성한다. 응답 시간 초과 후 같은 확인 버튼으로 재시도하면 기존 이벤트를 조회해 복구한다. 동시 생성의 409도 기존 이벤트를 확인한다. 새로고침으로 작업 ID가 사라지거나 새 명령을 입력하면 같은 작업 재시도가 아니므로 다시 생성할 수 있다.
- 결과는 이벤트 ID와 Google 응답에 근거한다. 초대 알림 요청 성공은 상대방의 수신·열람·참석 수락을 보장하지 않는다. 팀 목록과 미완료 요청은 화면 메모리에만 유지한다. Graph 체크포인트로 토큰을 저장하지 않는다.
- OKR: 자연어 회의 생성과 팀 초대를 하나의 승인으로 완료한다. KPI/합격 기준: 승인 전 Google 쓰기 0건, 동일 작업 재시도 중복 생성 0건, 수신자 불일치 0건. 평가셋은 정상 생성·초대, 읽기 토큰 거부, 승인 누락, 오류·시간 초과, 재시도·동시 충돌, 이메일 오류와 실제 OpenAI 시간·수신자 추가 답변이다.
- Before: 비서 실행 LangGraph 연결과 팀 초대 미구현. After: Graph 경로 및 Calendar 초대 구현. 검증 명령: `python -m unittest discover -s tests`, `npm test --prefix personal-assistant`, `npm run build --prefix personal-assistant`, `PYTHONPATH=. python tests/smoke_calendar_conversation_live.py`. 실제 사용자 Google 계정의 일정 생성·초대 수신 E2E는 미검증이며 별도 확인이 필요하다. 일정 충돌 확인 및 기존 이벤트의 참석자 수정은 이번 기능에 포함하지 않는다.
- 결과: Python 68/68, 프론트엔드 15/15, 실제 OpenAI 합성 대화 18/18, TypeScript/Vite 빌드 성공. Google 생성·초대 및 실패 복구는 모의 API 응답으로 검증했다.

## Gmail 전용 OAuth 클라이언트 연결

- `VITE_GOOGLE_GMAIL_CLIENT_ID`를 Gmail 버튼에 사용하고 서버는 `ASSISTANT_GOOGLE_GMAIL_CLIENT_ID`로 Gmail 읽기 토큰의 발급 대상을 확인한다. 미설정이면 기존 공용 클라이언트를 사용한다. Calendar 클라이언트 설정은 별개다.
- 배포 변수는 GitHub Actions에서 프론트 빌드와 서버 시작 환경에 전달한다. Google Identity Services token model을 사용하므로 Client Secret을 저장하거나 브라우저에 전달하지 않는다.
- Google Cloud의 해당 웹 클라이언트에 승인된 JavaScript 원본 `<APP_ORIGIN>`을 등록하고 Gmail API와 `gmail.readonly` 권한을 활성화해야 한다. 앱이 Testing 상태면 로그인 계정을 Test users에 등록해야 한다. 사용자가 Gmail 연결 버튼에서 직접 동의해야 연결이 완료된다.
- OKR 연결: 메일 조회·요약을 같은 비서에서 제공한다. KPI/합격 기준: 클라이언트/권한 조합 인증 평가 5/5, 전체 Python 52/52, 프론트 13/13, 빌드 성공. Before: Gmail도 Calendar 클라이언트 사용. After: 전용 Gmail 클라이언트 및 권한을 구분한다. 실제 Google 계정 동의·메일 조회는 사용자 로그인 없이는 미검증이다.
- 검증 명령: `python -m unittest discover -s tests`, `npm test --prefix personal-assistant`, `npm run build --prefix personal-assistant`.

- OKR 연결: 가족 생일·기념일 조회를 같은 대화에서 완료할 수 있도록 한다.
- 목표 KPI/합격 기준: 기존 회귀 및 음력 변환 평가셋 실패 0건, 실제 OpenAI 대화 14/14 통과.
- 평가셋: Python 51건, 프론트엔드 12건, 실제 OpenAI 대화 14건. 복합 생일·기념일·음력 변환 요청과 등록일 기반 변환, 한국 시간 유지 및 원본 불변을 검증한다.
- Before: 음력 변환 도구 없음. After: `convertLunar`를 구조화된 명령으로 전달하며 직전 기간·필터·변환 상태를 유지한다. 지원하지 않는 삭제·수정·발송은 조회로 바꾸지 않고 지원 한계를 설명한다.
- 평가셋: 고정 한국 시각, 합성 가족 일정, 음력 2026-01-01 → 양력 2026-02-17, 시간/종일 일정, 윤달 모호성, 원본 불변, 반복 변환, 기간 외 제외, 지원하지 않는 작업 및 실제 OpenAI 후속 대화. 검증: `python -m unittest discover -s tests`, `npm test --prefix personal-assistant`, `npm run build --prefix personal-assistant`, `PYTHONPATH=. python tests/smoke_calendar_conversation_live.py`.
- 변환 근거: [한국 음양력 변환 라이브러리](https://github.com/usingsky/korean_lunar_calendar_py), `korean-lunar-calendar==0.4.0`. 지원 연도 1000~2050. 모델이 날짜를 계산하지 않는다.
- 제목에 `음력 10/10` 또는 `음력 10월 10일`처럼 월·일이 명시되면 해당 날짜를 우선 사용한다. 음력 표기만 있으면 사용자 요청에 따른 규칙으로 등록일의 월·일을 음력으로 해석하고 변환 근거를 표시한다. 예: `장모님 생신(음력)`의 2026-11-10 등록일 → 음력 2026-11-10 → 양력 2026-12-18. 명시된 기준 날짜와 양력 등록일이 이미 같으면 이동하지 않는다. Google Calendar 원본은 변경하지 않는다.
- 괄호 표기: `(음력)`, `（음력）`, `(음력 10/2)`, `(음력) 10/2`, 내부 공백을 인식한다. 특정 일정 변환은 그 일정만 처리하며 카드의 날짜를 새 조회 기간으로 사용하지 않는다. 월·일이 없으면 등록일 기준 규칙을 사용하고 `음력 10월 2일 평달이야` 같은 추가 답변이 있으면 해당 기준 날짜를 우선 적용한다.
- 한계: 조회된 원본 일정만 변환하므로 원래 조회 범위 밖에 등록된 음력 일정까지 발견한다고 보장하지 않는다. 음력 표기만 있는데 이미 양력으로 변환해 등록한 일정도 등록일 기준 규칙이 적용되므로 정확한 음력 월·일을 제목 또는 추가 답변에 제공해야 한다. 윤달 모호성은 별도 확인한다. 추가 정보는 브라우저 대화에만 유지하며 원본 일정에는 쓰지 않는다. 실제 사용자 Google 계정 E2E는 미검증이다.
