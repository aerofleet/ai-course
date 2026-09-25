# 하루비서

React + Vite + TypeScript로 만든 브라우저 기반 개인 비서 MVP입니다. 한국어 명령을 규칙으로 분류해 Google Calendar 일정과 Gmail 메일을 보여줍니다. Gmail 요약은 최근 메일의 제목과 미리보기 텍스트를 묶어 표시하며, 답장 초안은 템플릿입니다. LLM 호출이나 메일 발송은 없습니다.

## 실행

Node.js 20.19 이상 또는 22.12 이상을 사용합니다.

```bash
npm install
cp .env.example .env
# .env의 VITE_GOOGLE_CLIENT_ID를 실제 Web OAuth Client ID로 변경
npm run dev
```

터미널에 표시되는 로컬 주소의 `/assistant/` 경로를 브라우저에서 엽니다. `npm run build`로 TypeScript 검사와 배포용 빌드를 검증할 수 있습니다. `.env`는 Git에 포함되지 않습니다. Vite의 `VITE_` 값은 브라우저 번들에 공개되므로 Client ID만 넣고 Client Secret이나 API 키를 넣지 마세요.

## Google Cloud 설정

1. Google Cloud Console에서 프로젝트를 만들고 Google Calendar API와 Gmail API를 활성화합니다.
2. Google Auth Platform의 동의 화면을 설정합니다. 테스트 상태라면 사용할 Google 계정을 테스트 사용자에 추가합니다.
3. OAuth Client ID를 **웹 애플리케이션** 유형으로 생성합니다. 승인된 JavaScript 원본에 실제 브라우저 주소를 등록합니다. 로컬 실행은 보통 `http://localhost:5173`입니다. 배포 사이트는 해당 HTTPS 원본을 추가합니다. 원본에는 `/assistant/` 경로를 포함하지 않습니다.
4. Client ID를 `.env`의 `VITE_GOOGLE_CLIENT_ID`에 입력한 뒤 개발 서버를 다시 시작합니다.

GitHub Actions 배포에서는 저장소 변수(또는 Secret) `VITE_GOOGLE_CLIENT_ID`에 같은 **웹** Client ID를 등록합니다. 배포 서버에서는 워크플로가 이 값으로 `/assistant/` 빌드를 생성합니다. 값을 바꾼 뒤에는 Actions의 `Deploy to AI Server` 워크플로를 수동 실행할 수 있습니다. 데스크톱용 OAuth Client ID는 브라우저 로그인에 사용할 수 없습니다.

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
2. `오늘 일정 알려줘`, `이번 주 일정 보여줘`, `최근 중요한 메일 요약해줘`, `프로젝트 관련 메일 검색해줘` 등을 입력합니다.
3. `내일 오후 2시에 회의 추가해줘`를 입력하면 일정 정보가 표시됩니다. `확인하고 추가`를 누른 후 생성 권한에 동의해야 실제 일정이 만들어집니다.
4. `답장 초안 만들어줘`는 최근 메일을 바탕으로 확인용 템플릿만 보여줍니다. 발송 기능은 없습니다.

토큰은 JavaScript 메모리에만 보관하며 새로고침하면 사라집니다. `연결 해제`는 메모리의 토큰을 지우고 Google에 취소를 요청합니다. 메일·일정 결과도 새로고침하거나 연결을 해제하면 화면에서 사라집니다.

## 검증 기준

- 목표 KPI: 명령 5종(일정 조회/생성, 메일 검색/요약, 답장 초안)이 입력에 따라 각각 분류되고, 일정 생성은 확인 전 API 요청 0건.
- OKR 연결: 일정과 메일을 한 화면에서 처리하는 개인 비서 MVP의 핵심 흐름 완성.
- 평가셋: Google 테스트 계정 1개, 오늘/이번 주 일정 각 1건, 최근·중요 메일 각 1건, 정상 권한과 거부/만료/빈 결과 조건. 브라우저에서 5개 명령과 확인/취소 흐름을 실행.
- Before/After: 신규 프로젝트라 도입 전 측정값은 없습니다. 실행 결과는 테스트 계정과 OAuth Client ID를 설정한 뒤 기록합니다.
- 합격 기준: `npm run build` 성공, 5개 명령 결과 표시, 생성 취소 시 Google Calendar 변경 0건, 에러 상황 한국어 안내 표시.
