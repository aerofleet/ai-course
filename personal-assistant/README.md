# 하루비서

React + Vite + TypeScript 개인 비서입니다. Flask 서버가 OpenAI Responses API(`gpt-5-nano`, `ASSISTANT_OPENAI_MODEL`로 변경 가능)로 질문을 구조화하고 실제 Google Calendar/Gmail 조회 결과로 답변을 생성합니다. Calendar/Gmail 조회는 브라우저에서 수행하고, 질문·일정 정보·메일 제목/미리보기를 서버와 OpenAI에 전달합니다. 일정 생성은 사용자 확인 후 실행하며 메일 발송 기능은 없습니다.

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
2. `오늘 일정 알려줘`, `앞으로 3개월 내 중요한 일정 확인해줘`, `이번 주 일정 보여줘`, `최근 중요한 메일 요약해줘`, `프로젝트 관련 메일 검색해줘` 등을 입력합니다. 상대 기간은 브라우저 시간대와 서버 시각으로 계산합니다. 기본 캘린더만 조회하며 최대 1년·500건까지 페이지를 따라 조회합니다. 500건을 넘으면 답변에 조회 한계를 알립니다. 중요도는 일정 제목/장소를 근거로 한 추정으로 설명합니다.
3. `내일 오후 2시에 회의 추가해줘`를 입력하면 일정 정보가 표시됩니다. `확인하고 추가`를 누른 후 생성 권한에 동의해야 실제 일정이 만들어집니다.
4. `답장 초안 만들어줘`는 최근 메일 제목과 미리보기를 근거로 OpenAI가 검토용 초안을 작성합니다. 발송 기능은 없습니다.

토큰은 JavaScript 메모리에만 보관하며 새로고침하면 사라집니다. `연결 해제`는 메모리의 토큰을 지우고 Google에 취소를 요청합니다. 메일·일정 결과도 새로고침하거나 연결을 해제하면 화면에서 사라집니다.

## 검증 기준

- 목표 KPI: 명령 5종이 입력에 따라 각각 분류되고, 3개월 요청에서 실제 조회 기간 3개월을 유지하며 일정 생성은 확인 전 쓰기 요청 0건.
- OKR 연결: 일정과 메일을 한 화면에서 처리하는 개인 비서 MVP의 핵심 흐름 완성.
- 평가셋: `python -m unittest discover -s tests -v`의 14개 회귀 사례(기간·월말·빈 결과·다음 달 일정·생성 확인·인증·API 오류), `npm test`의 Calendar 5개 사례(3개월 Google 쿼리·페이지·500건 상한·권한/중간 페이지 실패·잘못된 기간), 실제 OpenAI 질문/가상 면접 smoke, Google 테스트 계정의 실제 캘린더/메일 5개 명령 및 확인/취소.
- Before/After: 변경 전 원문 질문은 `period=today`로 분류됨. 변경 후 실제 OpenAI 호출은 `calendar_read`, `importantOnly=true`, `앞으로 3개월`로 분류되며 가상 다음 달 면접을 답변에 포함함. 로컬 회귀 Python 14/14·Calendar 5/5와 프런트 빌드 통과. 실제 사용자 Google 데이터 E2E는 로그인한 브라우저에서 별도 확인 필요.
- 합격 기준: 회귀 14/14, `npm run build` 성공, 실제 OpenAI smoke 성공, 인증 없는 운영 API 401, 5개 명령 결과 표시와 생성 취소 시 Calendar 변경 0건. API smoke는 `PYTHONPATH=. python tests/smoke_assistant_live.py`로 실행하며 소량의 OpenAI 비용이 발생합니다.
