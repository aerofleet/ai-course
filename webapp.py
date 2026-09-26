import json
import traceback
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 512 * 1024
from assistant_api import assistant_api
app.register_blueprint(assistant_api)

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Drive → GPT → Notion 자동화 파이프라인</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Malgun Gothic', sans-serif; background: #0f172a; color: #e2e8f0; min-height: 100vh; }

  .container { max-width: 960px; margin: 0 auto; padding: 24px 16px; }

  .header { text-align: center; margin-bottom: 32px; }
  .header .badge { display: inline-block; background: #2563eb; color: #fff; font-size: 12px; font-weight: 700; padding: 4px 12px; border-radius: 4px; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 1px; }
  .header h1 { font-size: 24px; color: #f8fafc; margin-bottom: 6px; }
  .header p { font-size: 14px; color: #94a3b8; }

  .architecture { display: flex; align-items: center; justify-content: center; gap: 8px; margin-bottom: 32px; flex-wrap: wrap; }
  .arch-step { background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 12px 16px; text-align: center; min-width: 140px; }
  .arch-step .icon { font-size: 24px; margin-bottom: 4px; }
  .arch-step .label { font-size: 12px; color: #94a3b8; }
  .arch-step .tech { font-size: 11px; color: #64748b; margin-top: 2px; }
  .arch-arrow { font-size: 20px; color: #2563eb; }

  .run-section { text-align: center; margin-bottom: 32px; }
  .run-btn { background: #2563eb; color: #fff; border: none; padding: 14px 40px; font-size: 16px; font-weight: 700; border-radius: 8px; cursor: pointer; transition: all .2s; }
  .run-btn:hover { background: #1d4ed8; transform: translateY(-1px); }
  .run-btn:disabled { background: #475569; cursor: not-allowed; transform: none; }
  .run-btn.running { animation: pulse 1.5s infinite; }
  @keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:.7; } }

  .results { display: none; }
  .results.show { display: block; }

  .step-card { background: #1e293b; border: 1px solid #334155; border-radius: 8px; margin-bottom: 16px; overflow: hidden; }
  .step-header { display: flex; align-items: center; gap: 12px; padding: 14px 16px; border-bottom: 1px solid #334155; }
  .step-num { background: #2563eb; color: #fff; width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 700; flex-shrink: 0; }
  .step-num.success { background: #059669; }
  .step-num.mock { background: #d97706; }
  .step-label { font-size: 14px; font-weight: 600; color: #f1f5f9; }
  .step-detail { font-size: 12px; color: #94a3b8; }
  .step-body { padding: 14px 16px; }
  .step-content { background: #0f172a; border-radius: 6px; padding: 12px; font-family: 'Courier New', monospace; font-size: 13px; line-height: 1.5; color: #38bdf8; white-space: pre-wrap; word-break: break-word; }

  .error-box { background: #450a0a; border: 1px solid #dc2626; border-radius: 8px; padding: 16px; color: #fca5a5; font-size: 14px; }

  .footer { text-align: center; margin-top: 32px; padding-top: 16px; border-top: 1px solid #1e293b; font-size: 12px; color: #64748b; }
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <div class="badge">AX Essential 2.3 실습</div>
    <h1>문서 요약 &amp; 저장 자동화 파이프라인</h1>
    <p>Google Drive API → GPT 요약 Chain → Notion API 자동 저장</p>
  </div>

  <div class="architecture">
    <div class="arch-step">
      <div class="icon">📁</div>
      <div class="label">Google Drive</div>
      <div class="tech">문서 수집</div>
    </div>
    <div class="arch-arrow">→</div>
    <div class="arch-step">
      <div class="icon">🧠</div>
      <div class="label">GPT Chain</div>
      <div class="tech">gpt-5-nano</div>
    </div>
    <div class="arch-arrow">→</div>
    <div class="arch-step">
      <div class="icon">📝</div>
      <div class="label">Notion API</div>
      <div class="tech">페이지 자동 생성</div>
    </div>
  </div>

  <div class="run-section">
    <button class="run-btn" id="runBtn" onclick="runPipeline()">파이프라인 실행</button>
  </div>

  <div class="results" id="results"></div>

  <div class="footer">
    goorm AX Essential &middot; AI 어시스턴트와 자동화 &middot; L2.3 API 연동을 통한 자동화 확장
  </div>
</div>

<script>
async function runPipeline() {
  const btn = document.getElementById('runBtn');
  const results = document.getElementById('results');
  btn.disabled = true;
  btn.textContent = '실행 중...';
  btn.classList.add('running');
  results.className = 'results';
  results.innerHTML = '';

  try {
    const res = await fetch('api/run', { method: 'POST' });
    const data = await res.json();

    if (data.error) {
      results.innerHTML = '<div class="error-box">' + data.error + '</div>';
    } else {
      let html = '';
      data.steps.forEach(s => {
        html += '<div class="step-card">';
        html += '<div class="step-header">';
        html += '<div class="step-num ' + s.status + '">' + s.step + '</div>';
        html += '<div><div class="step-label">' + s.label + '</div>';
        html += '<div class="step-detail">' + s.detail + '</div></div>';
        html += '</div>';
        html += '<div class="step-body"><div class="step-content">' + escapeHtml(s.content) + '</div></div>';
        html += '</div>';
      });
      results.innerHTML = html;
    }
    results.className = 'results show';
  } catch (e) {
    results.innerHTML = '<div class="error-box">요청 실패: ' + e.message + '</div>';
    results.className = 'results show';
  }

  btn.disabled = false;
  btn.textContent = '파이프라인 실행';
  btn.classList.remove('running');
}

function escapeHtml(t) {
  const d = document.createElement('div');
  d.textContent = t;
  return d.innerHTML;
}
</script>
</body>
</html>"""


@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route("/api/run", methods=["POST"])
def api_run():
    try:
        from drive_notion_auto_pipeline import run_pipeline
        result = run_pipeline()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"{type(e).__name__}: {e}", "trace": traceback.format_exc()}), 500


@app.route("/health")
def health():
    from assistant_api import model_name
    import os
    return jsonify({"status": "ok", "assistant": {"provider": "openai", "model": model_name(),
                   "configured": bool(os.getenv('OPENAI_API_KEY') and (os.getenv('ASSISTANT_GOOGLE_CLIENT_ID') or os.getenv('VITE_GOOGLE_CLIENT_ID')))}})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
