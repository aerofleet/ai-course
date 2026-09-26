# 하루비서

React + Vite + TypeScript 개인 비서입니다. Flask 서버가 OpenAI Responses API(`gpt-5-nano`, `ASSISTANT_OPENAI_MODEL`로 변경 가능)로 질문과 후속 의도를 구조화합니다. Calendar/Gmail 조회는 브라우저에서 수행합니다. 일정 목록은 서버가 Calendar 원본과 명시적 분류 기준으로 구성하며 날짜·시간·후보를 모델이 다시 작성하지 않습니다. 질문·이전 조회 범위·중요도 기준은 OpenAI에 전달되고, 메일 요약/답장에는 제목·미리보기도 전달됩니다. 일정 생성은 사용자 확인 후 실행하며 메일 발송 기능은 없습니다.

## 실행

Node.js 20.19 이상 또는 22.12 이상을 사용합니다.

```bash
npm install
cp .env.example .env
# .env의 VITE_GOOGLE_CLIENT_ID를 실제 Web OAuth Client ID로 변경
npm run dev
```

터미널에 표시되는 로컬 주소의 `/assistant/` 경로를 브라우저에서 엽니다. `npm run build`로 TypeScript 검사와 배포용 빌드를 검증할 수 있습니다. `.env`는 Git에 포함되지 않습니다. Vite의 `VITE_` 값은 브라우저 번들에 공개되므로 Client ID만 넣고 Client Secret이나 API 키를 넣지 마세요.

저장소 루트의 서버용 `.env`에는 `OPENAI_API_KEY`와 `ASSISTANT_GOOGLE_CLIENT_ID`(프런트와 동일한 웹 OAuth Client ID)를 설정하고 `python webapp.py`를 별도 실행합니다. 개발 서버는 `/pipeline/api/assistant/`를 Flask 8080 포트로 프록시합니다. 운영은 기존 `/pipeline/` 프록시를 사용합니다. 배포 워크플로가 웹 Client ID를 서버 환경에도 전달하며 OpenAI 키는 서버의 기존 `.env`에서 읽습니다.

비서 API는 Google 액세스 토큰의 Client ID·읽기 권한·만료를 검사합니다. 인증되지 않은 요청은 401이며 검증된 사용자당 분당 30회로 제한합니다. OpenAI/Google 오류 시 규칙 기반 응답으로 대체하지 않고 오류를 안내합니다. OpenAI 요청에는 `store: false`를 사용하며 서버에 질문/메일/일정/Google 토큰을 저장하지 않습니다.

## Google Cloud 설정

1. Google Cloud Console에서 프로젝트를 만들고 Google Calendar API와 Gmail API를 활성화합니다.
2. Google Auth Platform의 동의 화면을 설정합니다. 테스트 상태라면 사용할 Google 계정을 테스트 사용자에 추가합니다.
3. OAuth Client ID를 **웹 애플리케이션** 유형으로 생성합니다. 승인된 JavaScript 원본에 실제 브라우저 주소를 등록합니다. 로컬 실행은 보통 `http://localhost:5173`입니다. 배포 사이트는 해당 HTTPS 원본을 추가합니다. 원본에는 `/assistant/` 경로를 포함하지 않습니다.
4. Client ID를 `.env`의 `VITE_GOOGLE_CLIENT_ID`에 입력한 뒤 개발 서버를 다시 시작합니다.

GitHub Actions 배포에서는 저장소 변수(또는 Secret) `VITE_GOOGLE_CLIENT_ID`에 같은 **웹** Client ID를 등록합니다. 배포 서버에서는 워크플로가 이 값으로 `/assistant/` 빌드를 생성합니다. 값을 바꾼 뒤에는 Actions의 `Deploy to AI Server` 워크플로를 수동 실행할 수 있습니다. 데스크톱용 OAuth Client ID는 브라우저 로그인에 사용할 수 없습니다.

Google 로그인에서 `401 invalid_client`가 표시되면, 등록값이 JSON 경로·`VITE_GOOGLE_CLIENT_ID=` 접두사·따옴표 없이 Client ID 자체인지 확인합니다. 웹 애플리케이션 유형 Client ID의 승인된 JavaScript 원본에 실제 HTTPS 원본을 등록하고, 값 변경 후에는 반드시 워크플로를 다시 실행해야 합니다. 이전 빌드에는 새 환경변수가 자동 반영되지 않습니다.

배포 서버의 Nginx에는 기존 HTTPS `server` 블록 안에 아래 경로를 한 번 설정해야 합니다. 설정 파일을 백업하고 `nginx -t` 통과 후 reload합니다. CI는 빌드 후 이 경로가 HTTP 200을 반환하는지 검사합니다.

```nginx
location = /assistant/ {
    rewrite ^ /assistant/index.html last;
}
location ^~ /assistant/ {
    alias /home/ubuntu/ai-course/personal-assistant/dist/;
    index index.html;
    try_files $uri $uri/ /assistant/index.html;
}
```

Calendar 조회는 `calendar.readonly`, 일정 생성 확인 시 `calendar.events`, Gmail 조회는 `gmail.readonly` 범위를 각각 요청합니다. Gmail 검색 쿼리를 사용하므로 `gmail.metadata`만으로는 구현할 수 없습니다. Gmail 읽기 권한은 민감한 범위이므로 외부 사용자에게 배포할 때 Google의 검증 요구사항을 확인해야 합니다.

## 사용 흐름

1. `Calendar 연결`을 눌러 권한을 동의합니다. 메일 기능은 `Gmail 연결`을 별도로 누릅니다.
2. `오늘 일정 알려줘`, `앞으로 3개월 내 중요한 일정 확인해줘`, `이번 주 일정 보여줘`, `최근 중요한 메일 요약해줘` 등을 입력합니다. 상대 기간은 브라우저 시간대와 서버 시각으로 계산합니다. 기본 캘린더와 등록된 공유/가족 캘린더를 조회하며, 숨김·미선택 캘린더도 읽기 권한이 있으면 포함합니다. 조회 상한은 1년·50개 캘린더·캘린더당 500건·전체 2,000건입니다. 조회 실패나 상한으로 결과가 일부일 때 답변에 표시합니다. 동일 UID·시작 시각의 공유 사본은 한 번 표시하며 반복 일정의 다른 날짜는 유지합니다.
3. `내일 오후 2시에 회의 추가해줘`를 입력하면 일정 정보가 표시됩니다. `확인하고 추가`를 누른 후 생성 권한에 동의해야 실제 일정이 만들어집니다.
4. `답장 초안 만들어줘`는 최근 메일 제목과 미리보기를 근거로 OpenAI가 검토용 초안을 작성합니다. 발송 기능은 없습니다.

토큰은 JavaScript 메모리에만 보관하며 새로고침하면 사라집니다. `연결 해제`는 메모리의 토큰을 지우고 Google에 취소를 요청합니다. 메일·일정 결과도 새로고침하거나 연결을 해제하면 화면에서 사라집니다.

## 후속 질문과 중요도 기준

- `앞으로 3개월 내 생일과 기념일 확인해줘` 뒤 `목록만 추려줘`는 같은 조회 범위와 원본 결과를 사용합니다. 새 날짜를 명시하면 새 범위로 조회합니다.
- `생일과 기념일이 나한테는 중요 일정이야`는 이 대화의 중요도 기준을 생일·생신과 기념일로 변경합니다. 새로고침/연결 해제 시 기준과 조회 맥락이 사라지며, Calendar 재연결이나 일정 생성 후에는 이전 조회 결과를 재사용하지 않습니다.
- 기본 중요도 기준에는 생일·생신, 기념일, 마감, 회의·면접·시험, 병원·예약, 결제, 여행이 포함됩니다. 해당 제목 키워드와 Calendar의 birthday 이벤트 유형/생일 캘린더를 근거로 모든 일치 항목을 표시합니다. 모델이 일부 후보만 선정하지 않습니다.
- `장인생신이 누락됐어` 또는 날짜가 포함된 일정 카드 붙여넣기는 생성 요청으로 바꾸지 않고 같은 기간의 캘린더를 다시 조회해 제목을 찾습니다. 조회에 없으면 일정 삭제/미등록으로 단정하지 않고 범위와 공유 권한을 확인하도록 안내합니다.
- 종일 일정은 Google의 종료일 미포함 규칙을 적용합니다. 시간 일정은 사용자 시간대로 변환하고 음력 표기는 제목 그대로 유지합니다. 음력 날짜를 임의로 양력 변환하지 않습니다.

## 검증 기준

- 목표 KPI: 대화 평가 8/8 통과, 가족 생일/생신·기념일 fixture 5/5 포함, 목록 후속 질문의 기간 축소 0건, 원본 날짜/시간 불일치 0건, 동일 입력·데이터·기준에서 일정 목록 일치율 100%, 확인 전 일정 쓰기 0건.
- OKR 연결: 일정과 메일을 한 화면에서 처리하는 개인 비서 MVP의 핵심 흐름 완성.
- 평가셋: `python -m unittest discover -s tests -v`의 36개 회귀 사례, `npm test`의 Calendar/날짜 표시 12개 사례, 실제 OpenAI 대화 8개. 대화 평가는 기준 시각 `2026-09-26 14:30 Asia/Seoul`, 가상 생일/생신·기념일 5개와 결제 1개로 수행합니다. Google fixture는 공유/숨김 캘린더, 페이지, UID 중복, 500건 상한, 실패·빈 결과를 포함합니다.
- Before/After: 변경 전 사용자 대화에서 후속 질문의 기간 유실, 생신 후보 누락, 원본과 다른 날짜/UTC 시간 표시, 조회 확인 요구가 관측됐습니다. 변경 후 로컬 Python 36/36·Calendar/날짜 12/12, 실제 OpenAI 대화 8/8와 프런트 빌드 통과. 실제 사용자 Google 데이터 E2E는 로그인한 브라우저에서 별도 확인 필요합니다.
- 합격 기준: 위 평가 전부 통과, 운영 앱/health 200, 인증 없는 운영 API 401, 로그인한 Google 계정에서 공유 캘린더 포함 조회와 확인/취소 흐름 검증. live 평가는 `PYTHONPATH=. python tests/smoke_calendar_conversation_live.py`로 실행하며 소량의 OpenAI 비용이 발생합니다.
