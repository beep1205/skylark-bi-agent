import threading, subprocess, time
from flask import Flask, request, jsonify, render_template_string
import anthropic, requests

# ===== PASTE YOUR DETAILS HERE =====
MONDAY_API_KEY = "eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjYzMTAwNDE4MCwiYWFpIjoxMSwidWlkIjoxMDA4MTI1MDQsImlhZCI6IjIwMjYtMDMtMTBUMDU6MzQ6MTYuMTE3WiIsInBlciI6Im1lOndyaXRlIiwiYWN0aWQiOjM0MTUzMjE5LCJyZ24iOiJhcHNlMiJ9.qxvJrxMrxx4BJX3mXDOOt1DAtIFrbgnifoMYk9RsX0M"
ANTHROPIC_API_KEY = "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"
WORK_ORDERS_BOARD_ID = "5027108643"
DEALS_BOARD_ID = "5027108688"
# ====================================

app = Flask(__name_
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

def fetch_monday_board(board_id):
    url = "https://api.monday.com/v2"
    headers = {"Authorization": MONDAY_API_KEY, "Content-Type": "application/json"}
    query = f"""
    {{
      boards(ids: [{board_id}]) {{
        name
        items_page(limit: 200) {{
          items {{
            name
            column_values {{ text column {{ title }} }}
          }}
        }}
      }}
    }}
    """
    try:
        r = requests.post(url, json={"query": query}, headers=headers)
        return r.json().get("data", {}).get("boards", [{}])[0]
    except Exception as e:
        return {"error": str(e)}

def board_to_text(board_data):
    if not board_data or "error" in board_data:
        return "Board data unavailable"
    lines = [f"Board: {board_data.get('name', 'Unknown')}"]
    items = board_data.get("items_page", {}).get("items", [])
    lines.append(f"Total records: {len(items)}")
    for item in items[:100]:
        cols = [f"{cv['column']['title']}={cv['text']}"
                for cv in item.get("column_values", []) if cv.get("text")]
        lines.append(f"• {item['name']}: " + " | ".join(cols))
    return "\n".join(lines)

HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Skylark BI Agent</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body { font-family: 'Segoe UI', sans-serif; background:#0f1117; color:#e0e0e0; height:100vh; display:flex; flex-direction:column; }
  header { background:#1a1d27; padding:16px 24px; border-bottom:1px solid #2a2d3a; }
  header h1 { color:#f59e0b; font-size:20px; }
  header p { color:#6b7280; font-size:13px; }
  #chat { flex:1; overflow-y:auto; padding:24px; display:flex; flex-direction:column; gap:16px; }
  .msg { max-width:80%; padding:12px 16px; border-radius:12px; font-size:14px; line-height:1.6; white-space:pre-wrap; }
  .user { background:#1d4ed8; align-self:flex-end; }
  .assistant { background:#1a1d27; border:1px solid #2a2d3a; align-self:flex-start; }
  .chips { display:flex; flex-wrap:wrap; gap:8px; padding:0 24px 12px; }
  .chip { background:#1a1d27; border:1px solid #374151; color:#9ca3af; padding:6px 12px; border-radius:20px; font-size:12px; cursor:pointer; }
  .chip:hover { border-color:#f59e0b; color:#f59e0b; }
  #bar { padding:16px 24px; background:#1a1d27; border-top:1px solid #2a2d3a; display:flex; gap:12px; }
  textarea { flex:1; background:#0f1117; border:1px solid #374151; color:#e0e0e0; padding:12px; border-radius:8px; font-size:14px; resize:none; }
  button { background:#f59e0b; color:#0f1117; border:none; padding:12px 24px; border-radius:8px; font-weight:700; cursor:pointer; }
  button:hover { background:#d97706; }
</style>
</head>
<body>
<header>
  <h1>Skylark Drones — BI Agent</h1>
  <p>Ask any business question about your pipeline, deals, or work orders</p>
</header>
<div id="chat">
  <div class="msg assistant">Hi! I am your Skylark Drones BI Agent. I have live access to your Work Orders and Deals boards. Ask me anything!</div>
</div>
<div class="chips">
  <div class="chip" onclick="ask(this)">How is our pipeline this quarter?</div>
  <div class="chip" onclick="ask(this)">Top deals by value?</div>
  <div class="chip" onclick="ask(this)">Work order status summary?</div>
  <div class="chip" onclick="ask(this)">Prepare a leadership update</div>
</div>
<div id="bar">
  <textarea id="inp" rows="2" placeholder="Ask a business question..."></textarea>
  <button onclick="send()">Send</button>
</div>
<script>
  let history = [];
  function ask(el) { document.getElementById('inp').value = el.textContent; send(); }
  async function send() {
    const inp = document.getElementById('inp');
    const msg = inp.value.trim();
    if (!msg) return;
    inp.value = '';
    add(msg, 'user');
    history.push({role:'user', content:msg});
    const t = add('Thinking...', 'assistant');
    const res = await fetch('/chat', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({history})});
    const data = await res.json();
    t.remove();
    add(data.reply || 'Error', 'assistant');
    history.push({role:'assistant', content:data.reply});
  }
  function add(text, cls) {
    const d = document.createElement('div');
    d.className = 'msg ' + cls;
    d.textContent = text;
    document.getElementById('chat').appendChild(d);
    document.getElementById('chat').scrollTop = 99999;
    return d;
  }
  document.getElementById('inp').addEventListener('keydown', e => {
    if(e.key==='Enter' && !e.shiftKey){ e.preventDefault(); send(); }
  });
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/chat", methods=["POST"])
def chat():
    history = request.json.get("history", [])
    wo = board_to_text(fetch_monday_board(WORK_ORDERS_BOARD_ID))
    deals = board_to_text(fetch_monday_board(DEALS_BOARD_ID))
    system = f"""You are a Business Intelligence agent for Skylark Drones, a drone surveying company.
You have real-time access to two monday.com boards:

=== WORK ORDERS ===
{wo}

=== DEALS ===
{deals}

Answer founder-level business questions clearly. Provide insights not just raw data.
Handle missing or messy data gracefully. For leadership update requests, give a structured
summary covering pipeline health, top deals, work order status, and key risks."""

    resp = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system=system,
        messages=history
    )
    return jsonify({"reply": resp.content[0].text})

# Start server
def run():
    app.run(port=5001)

threading.Thread(target=run, daemon=True).start()
time.sleep(2)

# Get public URL
result = subprocess.Popen(
    ["ssh", "-o", "StrictHostKeyChecking=no", "-R", "80:localhost:5001", "localhost.run"],
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT
)
print("Waiting for public URL...")
for line in result.stdout:
    decoded = line.decode()
    print(decoded, end="")
    if "https" in decoded and "localhost.run" in decoded:
        break
