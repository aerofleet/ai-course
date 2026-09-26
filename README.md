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

- OKR 연결: 가족 생일·기념일 조회를 같은 대화에서 완료할 수 있도록 한다.
- 목표 KPI/합격 기준: 기존 회귀 및 음력 변환 평가셋 실패 0건, 실제 OpenAI 대화 14/14 통과.
- 평가셋: Python 51건, 프론트엔드 12건, 실제 OpenAI 대화 14건. 복합 생일·기념일·음력 변환 요청과 등록일 기반 변환, 한국 시간 유지 및 원본 불변을 검증한다.
- Before: 음력 변환 도구 없음. After: `convertLunar`를 구조화된 명령으로 전달하며 직전 기간·필터·변환 상태를 유지한다. 지원하지 않는 삭제·수정·발송은 조회로 바꾸지 않고 지원 한계를 설명한다.
- 평가셋: 고정 한국 시각, 합성 가족 일정, 음력 2026-01-01 → 양력 2026-02-17, 시간/종일 일정, 윤달 모호성, 원본 불변, 반복 변환, 기간 외 제외, 지원하지 않는 작업 및 실제 OpenAI 후속 대화. 검증: `python -m unittest discover -s tests`, `npm test --prefix personal-assistant`, `npm run build --prefix personal-assistant`, `PYTHONPATH=. python tests/smoke_calendar_conversation_live.py`.
- 변환 근거: [한국 음양력 변환 라이브러리](https://github.com/usingsky/korean_lunar_calendar_py), `korean-lunar-calendar==0.4.0`. 지원 연도 1000~2050. 모델이 날짜를 계산하지 않는다.
- 제목에 `음력 10/10` 또는 `음력 10월 10일`처럼 월·일이 명시되면 해당 날짜를 우선 사용한다. 음력 표기만 있으면 사용자 요청에 따른 규칙으로 등록일의 월·일을 음력으로 해석하고 변환 근거를 표시한다. 예: `장모님 생신(음력)`의 2026-11-10 등록일 → 음력 2026-11-10 → 양력 2026-12-18. 명시된 기준 날짜와 양력 등록일이 이미 같으면 이동하지 않는다. Google Calendar 원본은 변경하지 않는다.
- 괄호 표기: `(음력)`, `（음력）`, `(음력 10/2)`, `(음력) 10/2`, 내부 공백을 인식한다. 특정 일정 변환은 그 일정만 처리하며 카드의 날짜를 새 조회 기간으로 사용하지 않는다. 월·일이 없으면 등록일 기준 규칙을 사용하고 `음력 10월 2일 평달이야` 같은 추가 답변이 있으면 해당 기준 날짜를 우선 적용한다.
- 한계: 조회된 원본 일정만 변환하므로 원래 조회 범위 밖에 등록된 음력 일정까지 발견한다고 보장하지 않는다. 음력 표기만 있는데 이미 양력으로 변환해 등록한 일정도 등록일 기준 규칙이 적용되므로 정확한 음력 월·일을 제목 또는 추가 답변에 제공해야 한다. 윤달 모호성은 별도 확인한다. 추가 정보는 브라우저 대화에만 유지하며 원본 일정에는 쓰지 않는다. 실제 사용자 Google 계정 E2E는 미검증이다.
