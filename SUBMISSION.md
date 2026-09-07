# 과제 제출용 구조 분석 요약

## 프로젝트명

LangChain 기반 업무 어시스턴트 파이프라인 (`assistant_chain.py`)

## 파이프라인 흐름

`텍스트 입력 → 요약(Chain) → 문서 검색(Retriever) → 메일 전송(Tool) + 대화 이력 저장(Memory)`

## LangChain 핵심 요소

| 핵심 요소 | 역할 | 구현 방식 |
|---|---|---|
| **Chain** | 프롬프트 템플릿과 LLM(gpt-5-nano)을 파이프(`\|`)로 연결하여 긴 보고 텍스트를 핵심 3줄로 압축 | `PromptTemplate \| ChatOpenAI \| StrOutputParser` |
| **Retriever** | 사내 정책·업무매뉴얼·연락망 등 지식 문서에서 질문과 가장 관련 있는 문서를 LLM으로 검색하여 환각(hallucination) 방지 | LLM 기반 문서 매칭 (KNOWLEDGE_BASE → retriever_chain) |
| **Tool** | 최종 생성된 요약문과 참조 문서를 규격에 맞게 조합하여 이메일 발송 함수로 자동 전달 | `send_email_tool()` Mock 함수 (실제 환경에서는 SMTP/Gmail API 연동) |
| **Memory** | 사용자 입력과 AI 응답을 대화 이력으로 저장하여 후속 대화에서 맥락 유지 | `ChatMessageHistory` (add_user_message / add_ai_message) |

## 작업 환경 구성

- 로컬(IntelliJ)에서 코드 작성 → GitHub push → GitHub Actions CI/CD로 AI 서버 자동 배포
- 실행 서버: Ubuntu (OCI), Python 3.12, 가상환경 `ai-venv`
- 모델: `gpt-5-nano` 고정
