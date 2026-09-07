# ai-course

AI 교육과정 실습 프로젝트입니다.
LangChain + OpenAI를 활용하여 AI 기능을 학습합니다.

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

## 자주 발생하는 오류와 해결 방법

| 오류 | 원인 | 해결 방법 |
|------|------|-----------|
| `OPENAI_API_KEY가 설정되지 않았습니다` | .env 파일 없음 또는 키 미입력 | `.env` 파일 생성 후 API 키 입력 |
| `PermissionDeniedError: model not found` | 모델 접근 권한 없음 | OpenAI 콘솔에서 모델 권한 확인 또는 다른 모델로 변경 |
| `ModuleNotFoundError` | 패키지 미설치 | `pip install -r requirements.txt` 실행 |
| `ConnectionError` | 인터넷 연결 문제 | 네트워크 상태 확인 |
| `RateLimitError` | API 사용량 초과 | OpenAI 결제 설정 확인 |
