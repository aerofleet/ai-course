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
