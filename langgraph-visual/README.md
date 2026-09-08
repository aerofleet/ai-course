# LangGraph 작동 방식 시각화 예제

## 프로젝트 목적

LangGraph가 어떻게 작동하는지 **눈으로 직접 확인**할 수 있는 간단한 예제입니다.
OpenAI API Key 없이 실행되며, 순수 Python 함수만 사용합니다.

---

## LangGraph란?

LangGraph는 **여러 작업을 순서대로 연결해서 실행**하는 도구입니다.

작업 흐름을 "그래프"로 만들어서, 어떤 순서로 실행되는지 한눈에 볼 수 있습니다.

---

## 핵심 개념 4가지

### 1. Node (노드)

- **하나의 작업**을 담당하는 함수입니다.
- 예: "입력 확인", "학습 안내 생성", "결과 정리"

### 2. Edge (엣지)

- 노드에서 **다음 노드로 이동하는 경로**입니다.
- 예: `check_input` → `decide_level` (check_input이 끝나면 decide_level로 이동)

### 3. State (상태)

- 그래프 전체에서 **공유되는 데이터**입니다.
- 노드를 지날 때마다 State가 **조금씩 업데이트**됩니다.
- 이 예제의 State:
  - `user_name`: 사용자 이름
  - `study_level`: 학습 수준
  - `message`: 안내 메시지
  - `step_log`: 지나온 노드 기록

### 4. 조건 분기 (Conditional Edge)

- 조건에 따라 **다른 노드로 이동**하는 것입니다.
- 이 예제에서는 `study_level` 값에 따라:
  - `"beginner"` → `beginner_guide` 노드로 이동
  - `"advanced"` → `advanced_guide` 노드로 이동

---

## 그래프 흐름

```
START
  → check_input (입력 정보 확인)
  → decide_level (학습 수준 확인)
  → [조건 분기]
      ├── beginner_guide (입문자 안내)
      └── advanced_guide (경험자 안내)
  → finish (결과 정리)
  → END
```

---

## 설치 방법

```bash
pip install -r requirements.txt
```

---

## 실행 방법

```bash
python visualize_langgraph.py
```

---

## HTML 시각화 파일 열기

실행이 끝나면 `langgraph_flow.html` 파일이 생성됩니다.

- **Windows**: 파일을 더블클릭하거나, 아래 명령어 실행
  ```bash
  start langgraph_flow.html
  ```
- **Mac**: `open langgraph_flow.html`
- **Linux**: `xdg-open langgraph_flow.html`

브라우저에서 그래프 구조가 시각적으로 보입니다.

---

## 성공했을 때 확인할 것

### 터미널 출력 확인

아래와 비슷한 결과가 나오면 성공입니다:

```
최종 메시지:
입력 정보를 확인했습니다.
입문자에게는 LangGraph의 노드와 엣지부터 설명합니다.
LangGraph 작동 흐름 확인 완료!

실행된 노드 순서:
  1. check_input 실행
  2. decide_level 실행
  3. beginner_guide 실행
  4. finish 실행
```

### HTML 파일 확인

- `langgraph_flow.html`을 브라우저에서 열었을 때 그래프 다이어그램이 보이면 성공

---

## 오류가 발생했을 때 확인할 것

### `ModuleNotFoundError: No module named 'langgraph'`

langgraph 패키지가 설치되지 않은 것입니다.

```bash
pip install -r requirements.txt
```

### HTML 파일에서 그래프가 안 보일 때

- 인터넷 연결을 확인하세요 (Mermaid CDN을 사용합니다)
- 브라우저를 새로고침 해보세요
- Chrome, Edge 등 최신 브라우저를 사용하세요

### Python 버전 오류

Python 3.10 이상을 권장합니다.

```bash
python --version
```
