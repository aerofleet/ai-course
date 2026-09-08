"""
LangGraph 작동 방식 시각화 예제

이 파일은 LangGraph의 기본 개념을 이해하기 위한 예제입니다.
OpenAI API Key 없이 순수 Python 함수만 사용합니다.

핵심 개념:
- 노드(Node): 하나의 작업을 담당하는 함수
- 엣지(Edge): 노드에서 다음 노드로 이동하는 경로
- State: 노드를 지나면서 업데이트되는 데이터
- 조건 분기: 조건에 따라 다른 노드로 이동하는 것
"""

# ============================================================
# 1단계: 필요한 라이브러리 가져오기
# ============================================================

from typing import Literal, TypedDict  # State의 구조를 정의할 때 사용
from langgraph.graph import StateGraph, START, END  # LangGraph 핵심 도구


# ============================================================
# 2단계: State 구조 정의하기
# ============================================================
# State는 그래프 전체에서 공유되는 데이터입니다.
# 각 노드가 실행될 때마다 State가 조금씩 업데이트됩니다.

class StudyState(TypedDict):
    user_name: str        # 사용자 이름
    study_level: str      # 학습 수준 ("beginner" 또는 "advanced")
    message: str          # 현재까지 만들어진 안내 메시지
    step_log: list[str]   # 어떤 노드를 지나왔는지 기록하는 리스트


# ============================================================
# 3단계: 각 노드 함수 만들기
# ============================================================
# 노드는 하나의 작업을 담당하는 함수입니다.
# 각 함수는 현재 State를 받아서 업데이트된 값을 반환합니다.

def check_input(state: StudyState) -> dict:
    """
    [check_input 노드]
    사용자의 이름과 학습 수준을 확인합니다.
    가장 처음 실행되는 노드입니다.
    """
    return {
        "message": state["message"] + "입력 정보를 확인했습니다.\n",
        "step_log": state["step_log"] + ["check_input 실행"],
    }


def decide_level(state: StudyState) -> dict:
    """
    [decide_level 노드]
    study_level 값을 확인합니다.
    이 노드 다음에 조건 분기가 일어납니다.
    """
    return {
        "step_log": state["step_log"] + ["decide_level 실행"],
    }


def beginner_guide(state: StudyState) -> dict:
    """
    [beginner_guide 노드]
    study_level이 "beginner"일 때 실행됩니다.
    입문자를 위한 안내 메시지를 추가합니다.
    """
    return {
        "message": state["message"] + "입문자에게는 LangGraph의 노드와 엣지부터 설명합니다.\n",
        "step_log": state["step_log"] + ["beginner_guide 실행"],
    }


def advanced_guide(state: StudyState) -> dict:
    """
    [advanced_guide 노드]
    study_level이 "advanced"일 때 실행됩니다.
    경험자를 위한 안내 메시지를 추가합니다.
    """
    return {
        "message": state["message"] + "경험자에게는 조건 분기와 상태 관리 중심으로 설명합니다.\n",
        "step_log": state["step_log"] + ["advanced_guide 실행"],
    }


def finish(state: StudyState) -> dict:
    """
    [finish 노드]
    마지막 안내 메시지를 정리합니다.
    모든 흐름의 끝에서 실행됩니다.
    """
    return {
        "message": state["message"] + "LangGraph 작동 흐름 확인 완료!\n",
        "step_log": state["step_log"] + ["finish 실행"],
    }


# ============================================================
# 4단계: 조건 분기 함수 만들기
# ============================================================
# study_level 값에 따라 다음에 실행할 노드를 결정합니다.
# "beginner"이면 beginner_guide, "advanced"이면 advanced_guide로 이동합니다.

def route_by_level(state: StudyState) -> Literal["beginner_guide", "advanced_guide"]:
    """
    [조건 분기 함수]
    study_level 값을 보고 다음 노드 이름을 문자열로 반환합니다.
    LangGraph는 이 반환값을 보고 해당 노드로 이동합니다.
    """
    if state["study_level"] == "advanced":
        return "advanced_guide"
    else:
        # "beginner"이거나 그 외 값이면 기본적으로 beginner_guide로 이동
        return "beginner_guide"


# ============================================================
# 5단계: 그래프 만들기
# ============================================================
# StateGraph에 노드를 등록하고, 엣지로 연결합니다.

# 그래프 객체 생성 (State 구조를 알려줍니다)
graph = StateGraph(StudyState)

# 노드 등록: add_node("노드 이름", 실행할 함수)
graph.add_node("check_input", check_input)
graph.add_node("decide_level", decide_level)
graph.add_node("beginner_guide", beginner_guide)
graph.add_node("advanced_guide", advanced_guide)
graph.add_node("finish", finish)

# 일반 엣지 연결: add_edge(출발 노드, 도착 노드)
# START → check_input → decide_level 순서로 이동합니다
graph.add_edge(START, "check_input")
graph.add_edge("check_input", "decide_level")

# 조건 분기 엣지: decide_level 다음에 조건에 따라 다른 노드로 이동
# route_by_level 함수의 반환값이 노드 이름이 됩니다
graph.add_conditional_edges("decide_level", route_by_level)

# beginner_guide와 advanced_guide는 모두 finish로 이동
graph.add_edge("beginner_guide", "finish")
graph.add_edge("advanced_guide", "finish")

# finish 노드 다음은 END (그래프 종료)
graph.add_edge("finish", END)

# 그래프 컴파일: 실행 가능한 상태로 만듭니다
app = graph.compile()


# ============================================================
# 6단계: 그래프 실행하기
# ============================================================

# 초기 입력 데이터 (State의 시작 값)
initial_state = {
    "user_name": "구름이",
    "study_level": "beginner",
    "message": "",
    "step_log": [],
}

print("=" * 50)
print("  LangGraph 작동 방식 시각화 예제")
print("=" * 50)
print()
print(f"사용자: {initial_state['user_name']}")
print(f"학습 수준: {initial_state['study_level']}")
print()

# 그래프 실행: invoke()에 초기 State를 넣으면 모든 노드를 거쳐 최종 State가 반환됩니다
result = app.invoke(initial_state)

# 최종 결과 출력
print("-" * 50)
print("최종 메시지:")
print(result["message"])

print("실행된 노드 순서:")
for i, step in enumerate(result["step_log"], 1):
    print(f"  {i}. {step}")
print()


# ============================================================
# 7단계: Mermaid 그래프를 HTML 파일로 저장하기
# ============================================================
# LangGraph는 그래프 구조를 Mermaid 문법으로 추출할 수 있습니다.
# Mermaid는 텍스트로 다이어그램을 그리는 도구입니다.

# 그래프 구조를 Mermaid 문법으로 변환
mermaid_code = app.get_graph().draw_mermaid()

print("-" * 50)
print("Mermaid 그래프 코드:")
print(mermaid_code)
print()

# HTML 파일 생성
html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LangGraph 작동 방식 시각화</title>
    <style>
        body {{
            font-family: 'Segoe UI', sans-serif;
            background-color: #f8f9fa;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 40px 20px;
        }}
        h1 {{
            text-align: center;
            color: #2c3e50;
            margin-bottom: 8px;
        }}
        .description {{
            text-align: center;
            color: #666;
            font-size: 15px;
            margin-bottom: 40px;
            line-height: 1.6;
        }}
        .mermaid {{
            display: flex;
            justify-content: center;
            background: white;
            border-radius: 12px;
            padding: 32px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}
    </style>
</head>
<body>
    <h1>LangGraph 작동 방식 시각화</h1>
    <p class="description">
        노드는 작업을 의미하고, 엣지는 다음 이동 경로를 의미합니다.<br>
        State는 노드를 지나면서 계속 업데이트됩니다.
    </p>
    <div class="mermaid">
{mermaid_code}
    </div>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
    <script>
        mermaid.initialize({{ startOnLoad: true, theme: 'default' }});
    </script>
</body>
</html>"""

# HTML 파일 저장
with open("langgraph_flow.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print("langgraph_flow.html 파일이 생성되었습니다!")
print("브라우저에서 langgraph_flow.html을 열면 그래프 구조를 볼 수 있습니다.")
