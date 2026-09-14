import os
import json
import requests
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

llm = ChatOpenAI(model="gpt-4.1-nano", temperature=0.2)

summary_prompt = PromptTemplate.from_template(
    """당신은 사내 지식 관리 수석 비서입니다. 아래 문서를 임원 및 팀 공유용으로 요약하세요.
요구사항:
1. 핵심 안건 및 의사결정 사항 (3줄 요약)
2. 후속 실행 과제 (Action Item 2건)

[문서 원문]:
{document_text}

[요약 결과]:"""
)
summary_chain = summary_prompt | llm | StrOutputParser()


def fetch_document_from_drive(file_id: str) -> dict:
    """Google Drive API 문서 수집기 (Mock / Ingestion Adapter)
    실서비스: drive_service.files().get_media(fileId=file_id).execute()
    """
    return {
        "title": "2026 Q3 AI 업무자동화 도입 추진 회의록.docx",
        "content": (
            "일시: 2026-09-14 14:00\n"
            "안건: 전사 LangChain 및 API 기반 보고서 자동화 구축 건\n"
            "결정사항: Google Drive 문서 수집 후 Notion 자동 아카이빙 파이프라인 도입 확정.\n"
            "차주까지 인프라 보안 검토 및 Notion API 권한 격리 조치 완료 요망."
        ),
    }


def save_summary_to_notion(title: str, summary_content: str) -> dict:
    """Notion API 호출 함수 (페이지 생성 및 팀 보고 저장)"""
    if not NOTION_TOKEN or not NOTION_DATABASE_ID:
        return {
            "object": "page",
            "id": "mock-9b12e3",
            "status": "mock",
            "message": "NOTION_TOKEN/DATABASE_ID 미설정 - Mock 응답",
        }

    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }
    payload = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": {
            "문서명": {"title": [{"text": {"content": title}}]},
            "구분": {"select": {"name": "AI 자동 보고"}},
        },
        "children": [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {"type": "text", "text": {"content": summary_content}}
                    ]
                },
            }
        ],
    }
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    return response.json()


def run_pipeline(file_id: str = "sample-file-id-001") -> dict:
    """파이프라인 통합 실행 - 웹앱에서도 호출 가능"""
    steps = []

    # 1단계: Google Drive 문서 수집
    doc = fetch_document_from_drive(file_id)
    steps.append({
        "step": 1,
        "label": "Google Drive 문서 수집",
        "status": "success",
        "detail": f"파일명: {doc['title']}",
        "content": doc["content"],
    })

    # 2단계: GPT 요약 Chain 실행
    summary = summary_chain.invoke({"document_text": doc["content"]})
    steps.append({
        "step": 2,
        "label": "GPT 요약 Chain 실행",
        "status": "success",
        "detail": "gpt-4.1-nano 모델 사용",
        "content": summary,
    })

    # 3단계: Notion API 저장
    result = save_summary_to_notion(doc["title"], summary)
    notion_status = "mock" if result.get("status") == "mock" else "success"
    steps.append({
        "step": 3,
        "label": "Notion API 페이지 생성",
        "status": notion_status,
        "detail": f"Page ID: {result.get('id', 'N/A')}",
        "content": json.dumps(result, ensure_ascii=False, indent=2),
    })

    return {"steps": steps, "document": doc, "summary": summary, "notion": result}


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 [1단계] Google Drive에서 대상 문서 수집 완료")
    doc = fetch_document_from_drive("sample-file-id-001")
    print(f"- 파일명: {doc['title']}")

    print("\n🧠 [2단계] GPT 요약 Chain 실행 중...")
    summary = summary_chain.invoke({"document_text": doc["content"]})
    print(f"요약 완료:\n{summary}")

    print("\n📦 [3단계] Notion API 호출 및 페이지 생성 중...")
    result = save_summary_to_notion(doc["title"], summary)
    print(f"응답: {json.dumps(result, ensure_ascii=False, indent=2)}")
    print("✅ [완료] 파이프라인 실행 완료!")
    print("=" * 60)
