import os
from typing import TypedDict
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, START, END

# 1단계: 환경 변수 로드 및 LLM 엔진 초기화 (gpt-5-nano)
load_dotenv()
llm = ChatOpenAI(model="gpt-5-nano", temperature=0.2)

# 2단계: State 스키마 정의 (노드 간 전달될 데이터 규격)
class ReportState(TypedDict):
    topic: str
    research_result: str
    final_report: str

# 3단계: Node 정의 (Research 노드 & Summary 노드)
def research_node(state: ReportState) -> dict:
    """주제 조사 Node: 입력받은 topic에 대한 핵심 기술 트렌드를 심층 조사"""
    prompt = PromptTemplate.from_template(
        "당신은 IT 수석 연구원입니다. 아래 주제에 대한 최신 기술 동향을 심층 조사하세요:\n\n주제: {topic}"
    )
    chain = prompt | llm | StrOutputParser()
    result = chain.invoke({"topic": state["topic"]})
    return {"research_result": result}

def summary_node(state: ReportState) -> dict:
    """핵심 요약 Node: research_result를 기반으로 임원 보고용 비즈니스 요약 작성"""
    prompt = PromptTemplate.from_template(
        "당신은 비즈니스 전략가입니다. 아래 조사 결과를 바탕으로 임원 보고용 [핵심 요약 3줄 + 실행 전략] 보고서를 작성하세요:\n\n{research_result}"
    )
    chain = prompt | llm | StrOutputParser()
    result = chain.invoke({"research_result": state["research_result"]})
    return {"final_report": result}

# 4단계: Workflow 그래프 구성 및 Edge 연결 (START -> research -> summary -> END)
workflow = StateGraph(ReportState)

workflow.add_node("research", research_node)
workflow.add_node("summary", summary_node)

workflow.add_edge(START, "research")
workflow.add_edge("research", "summary")
workflow.add_edge("summary", END)

# GraphRunner 컴파일
app = workflow.compile()

# 5단계: Graph 실행 (GraphRunner.run)
if __name__ == "__main__":
    initial_input = {"topic": "2026년 생성형 AI 및 멀티에이전트 오케스트레이션 트렌드"}
    final_output = app.invoke(initial_input)

    print("=" * 60)
    print("📄 [LangGraph 기반 자동 생성 보고서]")
    print(final_output["final_report"])
    print("=" * 60)
