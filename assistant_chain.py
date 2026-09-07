# assistant_chain.py
# LangChain 핵심 요소(Chain, Tool, Memory, Retriever)를 활용한 업무 어시스턴트
# 파이프라인: 텍스트 입력 → 요약 → 문서 검색 → 메일 전송

import os
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

# 1. 환경 변수 로드 (.env의 OPENAI_API_KEY 사용)
load_dotenv()

# 2. LLM 엔진 초기화
llm = ChatOpenAI(model="gpt-5-nano", temperature=0.2)

# ==============================================================================
# [요소 1: Chain] 텍스트 요약 체인 (Text -> Summary)
# ==============================================================================
summary_prompt = PromptTemplate.from_template(
    """당신은 전문 비서입니다. 아래 제공된 원문 텍스트를 검토하고 핵심 내용 3줄로 명확하게 요약하세요.

[원문]:
{input_text}

[요약 결과]:"""
)
summary_chain = summary_prompt | llm | StrOutputParser()

# ==============================================================================
# [요소 2: Retriever & Memory] 문서 검색(Retriever) 및 기억(Memory)
# ==============================================================================
# 사내 정책/지식 문서 임베딩 및 벡터 저장소 구축
documents = [
    Document(page_content="사내 AI 도입 정책 가이드라인: 외부 API 사용 시 BYOK 원칙 준수 및 개인정보 마스킹 필수.", metadata={"source": "보안규정"}),
    Document(page_content="주간 보고 작성 지침: 매주 금요일 오후 4시까지 Notion 및 슬랙 채널을 통해 공유.", metadata={"source": "업무매뉴얼"}),
    Document(page_content="담당자 연락망: AI 자동화 프로젝트 PM 김철수(cs.kim@example.com), 보안담당 이영희(yh.lee@example.com).", metadata={"source": "연락망"})
]

embeddings = OpenAIEmbeddings()
vector_store = FAISS.from_documents(documents, embeddings)
retriever = vector_store.as_retriever(search_kwargs={"k": 1})

# 대화 맥락 기억용 Memory
memory = ChatMessageHistory()

# ==============================================================================
# [요소 3: Tool] 외부 발송 도구 (이메일 발송 Mock 함수)
# ==============================================================================
def send_email_tool(recipient: str, subject: str, body: str) -> str:
    """모의 이메일 발송 Tool (실제 환경에서는 SMTP/Gmail API 연동)"""
    print("\n" + "=" * 50)
    print("[메일 자동 발송 완료 알림]")
    print(f"  수신자: {recipient}")
    print(f"  제목: {subject}")
    print(f"  내용:\n{body}")
    print("=" * 50 + "\n")
    return "SUCCESS: 메일이 성공적으로 발송되었습니다."

# ==============================================================================
# [파이프라인] 텍스트입력 -> 요약 -> 문서검색 -> 메일 전송 통합 실행
# ==============================================================================
def run_assistant_pipeline(user_input_text: str, query_for_search: str, recipient_email: str):
    print("\n[1단계: 텍스트 요약 Chain 실행 중...]")
    summary_result = summary_chain.invoke({"input_text": user_input_text})
    print(f"요약 완료:\n{summary_result}")

    print("\n[2단계: 관련 사내 문서 Retriever 검색 중...]")
    retrieved_docs = retriever.invoke(query_for_search)
    referenced_doc = retrieved_docs[0].page_content if retrieved_docs else "참조 문서 없음"
    print(f"검색된 참조 지식: {referenced_doc}")

    print("\n[3단계: 최종 보고 메일 본문 구성 및 Tool 전송 중...]")
    mail_body = f"""안녕하십니까, 프로젝트 자동 보고입니다.

[요청 텍스트 핵심 요약]
{summary_result}

[관련 참조 규정/정보]
- {referenced_doc}

감사합니다.
AI 어시스턴트 드림
"""
    mail_subject = "[자동 보고] 프로젝트 현황 요약 및 사내 규정 참조 건"

    # 이메일 발송 Tool 호출
    status = send_email_tool(recipient_email, mail_subject, mail_body)

    # 대화 이력 메모리에 저장
    memory.add_user_message(user_input_text)
    memory.add_ai_message(mail_body)

    return status

if __name__ == "__main__":
    # 실습 테스트용 샘플 원문 텍스트
    sample_text = """
    2026년 3분기 AI 어시스턴트 도입 프로젝트 진행 경과를 보고합니다.
    현재 LangChain 기반의 업무 자동화 파이프라인 설계를 마쳤으며, 서버 환경 구축 및 OpenAI API 연동 테스트가 성공적으로 완료되었습니다.
    다음 단계로는 사내 회의록 요약 시스템과 Google Drive 및 메일 API를 연결하는 실증 프로젝트에 착수할 예정입니다.
    """

    # 통합 파이프라인 구동
    run_assistant_pipeline(
        user_input_text=sample_text,
        query_for_search="AI 보안 규정",
        recipient_email="manager@company.com"
    )
