import os
import html
from datetime import datetime
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

# 5단계: 결과를 HTML 파일로 저장하는 함수
def save_report_html(topic, research, report, output_path="report.html"):
    """실행 결과를 보기 좋은 HTML 파일로 저장"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    safe_topic = html.escape(topic)
    safe_research = html.escape(research).replace("\n", "<br>")
    safe_report = html.escape(report).replace("\n", "<br>")

    html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LangGraph AI 보고서</title>
<style>
  body {{ font-family: 'Segoe UI', 'Malgun Gothic', sans-serif; background: #f1f5f9; color: #1e293b; margin: 0; padding: 40px 20px; }}
  .container {{ max-width: 820px; margin: 0 auto; }}
  .header {{ background: #0f172a; color: #f8fafc; padding: 24px 28px; border-radius: 10px; margin-bottom: 20px; }}
  .header h1 {{ font-size: 18pt; margin: 0 0 6px 0; }}
  .header .meta {{ font-size: 9pt; color: #94a3b8; }}
  .badge {{ display: inline-block; background: #2563eb; color: #fff; font-size: 8pt; font-weight: bold; padding: 3px 10px; border-radius: 4px; margin-bottom: 8px; }}
  .section {{ background: #fff; border-radius: 10px; padding: 20px 24px; margin-bottom: 16px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }}
  .section h2 {{ font-size: 12pt; color: #0f172a; border-left: 4px solid #2563eb; padding-left: 10px; margin-top: 0; }}
  .content {{ font-size: 10pt; line-height: 1.7; color: #334155; }}
  .footer {{ text-align: center; font-size: 8pt; color: #94a3b8; margin-top: 24px; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <div class="badge">LangGraph AI Report</div>
    <h1>{safe_topic}</h1>
    <div class="meta">생성 시각: {now} | 모델: gpt-5-nano | 엔진: LangGraph StateGraph</div>
  </div>
  <div class="section">
    <h2>1. 리서치 결과 (Research Node)</h2>
    <div class="content">{safe_research}</div>
  </div>
  <div class="section">
    <h2>2. 최종 보고서 (Summary Node)</h2>
    <div class="content">{safe_report}</div>
  </div>
</div>
<div class="footer">LangGraph 기반 자동 생성 — AX Essential 실습 2.2</div>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    return output_path


# 6단계: Graph 실행 (GraphRunner.run)
if __name__ == "__main__":
    initial_input = {"topic": "2026년 생성형 AI 및 멀티에이전트 오케스트레이션 트렌드"}
    final_output = app.invoke(initial_input)

    # 터미널 출력
    print("=" * 60)
    print("[LangGraph 기반 자동 생성 보고서]")
    print(final_output["final_report"])
    print("=" * 60)

    # HTML 파일 저장
    output_path = save_report_html(
        topic=initial_input["topic"],
        research=final_output["research_result"],
        report=final_output["final_report"],
    )
    print(f"\nHTML 보고서 저장 완료: {output_path}")
