#!/usr/bin/env python3
"""Generate the Bangalore Morning Digest for April 25, 2026."""

import anthropic
import json
import os
import re
from twilio.rest import Client

# Load .env if present (no dependency on python-dotenv)
_env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(_env_file):
    for _line in open(_env_file):
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

TWILIO_SID   = os.environ["TWILIO_SID"]
TWILIO_TOKEN = os.environ["TWILIO_TOKEN"]
TWILIO_FROM  = os.environ["TWILIO_FROM"]
WHATSAPP_TO  = os.environ["WHATSAPP_TO"]

DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT = os.path.join(DIR, "digest_2026-04-25.html")

DATE_LONG  = "Saturday, 25 April 2026"
TIME_IST   = "9:00 AM IST"
TITLE_DATE = "April 25, 2026"

SYSTEM = """\
You are a news curator for the Bangalore Morning Digest. Today is Saturday, 25 April 2026.

Use the web_search tool to find 3 real, current news stories for EACH of these 5 categories:
  1. local    – Bangalore / Karnataka city news (BBMP, BMRCL, metro, infrastructure, civic)
  2. national – National India news (central govt, elections, policy, major domestic events)
  3. business – Indian business, stock markets, economy, RBI, corporate news
  4. tech     – Technology, AI, Indian startups, digital policy
  5. intl     – International / world affairs

Preferred sources: Times of India, The Hindu, Deccan Herald, InShorts, NDTV, Economic Times,
MSN India, Google News, Business Standard, Mint, India Today, BBC India.

After searching, return ONLY a single JSON object — no markdown, no extra text — in this exact shape:
{
  "local":    [ {"src":"…","headline":"…","summary":"…"}, … ],
  "national": [ {"src":"…","headline":"…","summary":"…"}, … ],
  "business": [ {"src":"…","headline":"…","summary":"…"}, … ],
  "tech":     [ {"src":"…","headline":"…","summary":"…"}, … ],
  "intl":     [ {"src":"…","headline":"…","summary":"…"}, … ]
}

Rules:
• Each array must have exactly 3 objects.
• "src" – one or two source names, e.g. "The Hindu / NDTV"
• "headline" – concise, specific headline (no quote marks inside)
• "summary" – exactly 2 complete sentences describing the story
• Do NOT fabricate stories; use real search results.
"""

def _make_client() -> anthropic.Anthropic:
    """Build an Anthropic client, preferring the session OAuth token when available."""
    token_file = os.environ.get(
        "CLAUDE_SESSION_INGRESS_TOKEN_FILE",
        "/home/claude/.claude/remote/.session_ingress_token",
    )
    if os.path.exists(token_file):
        token = open(token_file).read().strip()
        if token:
            return anthropic.Anthropic(auth_token=token)
    # Fall back to ANTHROPIC_API_KEY env var
    return anthropic.Anthropic()


def fetch_news() -> dict:
    client = _make_client()
    tools  = [{"type": "web_search_20250305", "name": "web_search"}]
    msgs   = [{"role": "user", "content": (
        "Search for the top news stories for April 25, 2026 across all five categories "
        "(Local Bangalore, National India, Business & Finance, Technology, International) "
        "and return the results as a JSON object exactly as instructed."
    )}]

    for _ in range(20):
        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=8000,
            system=SYSTEM,
            tools=tools,
            messages=msgs,
        )

        # Collect any text produced so far
        text_out = ""
        for block in resp.content:
            if getattr(block, "type", None) == "text":
                text_out = block.text.strip()

        if resp.stop_reason == "end_turn":
            return _parse_json(text_out)

        # pause_turn means server-side tool loop hit its limit; re-send to continue
        msgs.append({"role": "assistant", "content": resp.content})
        if resp.stop_reason != "pause_turn" and text_out:
            return _parse_json(text_out)

    raise RuntimeError("Claude did not return a final response after 20 iterations.")


def _parse_json(text: str) -> dict:
    """Extract and parse the JSON block from Claude's response."""
    # Strip markdown code fences if present
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\s*```$", "", text, flags=re.MULTILINE)
    text = text.strip()

    # Find the outermost { … }
    start = text.find("{")
    end   = text.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError(f"No JSON object found in response:\n{text[:500]}")

    data = json.loads(text[start:end])
    for cat in ("local", "national", "business", "tech", "intl"):
        if cat not in data or len(data[cat]) < 3:
            raise ValueError(f"Missing or incomplete category '{cat}' in JSON.")
    return data


# ── HTML helpers ────────────────────────────────────────────────────────────

def _esc(s: str) -> str:
    """Minimal HTML escaping."""
    return (s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;")
             .replace('"', "&quot;"))


def _cards(items: list) -> str:
    parts = []
    for item in items[:3]:
        parts.append(f"""\
    <div class="ncard">
      <div class="nmeta"><span class="nsrc">{_esc(item['src'])}</span><span class="ntime">Today · {TIME_IST}</span></div>
      <div class="nhead">{_esc(item['headline'])}</div>
      <div class="nsum">{_esc(item['summary'])}</div>
    </div>""")
    return "\n".join(parts)


CSS = """\
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --color-background-primary: #ffffff;
    --color-background-secondary: #f5f5f3;
    --color-background-tertiary: #eeede8;
    --color-background-info: #e6f1fb;
    --color-background-success: #eaf3de;
    --color-background-warning: #faeeda;
    --color-background-danger: #fcebeb;
    --color-text-primary: #1a1a1a;
    --color-text-secondary: #5f5e5a;
    --color-text-tertiary: #888780;
    --color-text-info: #0c447c;
    --color-text-success: #27500a;
    --color-text-warning: #633806;
    --color-text-danger: #791f1f;
    --color-border-tertiary: rgba(0,0,0,0.12);
    --color-border-secondary: rgba(0,0,0,0.22);
    --color-border-primary: rgba(0,0,0,0.32);
    --color-border-info: #b5d4f4;
    --color-border-success: #c0dd97;
    --color-border-warning: #fac775;
    --color-border-danger: #f7c1c1;
    --font-sans: system-ui, -apple-system, sans-serif;
    --border-radius-md: 8px;
    --border-radius-lg: 12px;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --color-background-primary: #1e1e1c;
      --color-background-secondary: #2a2a28;
      --color-background-tertiary: #242422;
      --color-background-info: #042c53;
      --color-background-success: #173404;
      --color-background-warning: #412402;
      --color-background-danger: #501313;
      --color-text-primary: #f0efe8;
      --color-text-secondary: #b4b2a9;
      --color-text-tertiary: #888780;
      --color-text-info: #b5d4f4;
      --color-text-success: #c0dd97;
      --color-text-warning: #fac775;
      --color-text-danger: #f7c1c1;
      --color-border-tertiary: rgba(255,255,255,0.1);
      --color-border-secondary: rgba(255,255,255,0.18);
      --color-border-primary: rgba(255,255,255,0.28);
      --color-border-info: #0c447c;
      --color-border-success: #3b6d11;
      --color-border-warning: #854f0b;
      --color-border-danger: #a32d2d;
    }
  }
  body { font-family: var(--font-sans); background: var(--color-background-tertiary); min-height: 100vh; padding: 1.5rem 1rem; }
  .app { max-width: 680px; margin: 0 auto; padding: 1.5rem 0; }
  .header{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:1rem;gap:12px;flex-wrap:wrap}
  .brand-row{display:flex;align-items:center;gap:10px}
  .brand-icon{width:38px;height:38px;border-radius:var(--border-radius-md);background:var(--color-background-info);display:flex;align-items:center;justify-content:center;flex-shrink:0}
  .brand-title{font-size:16px;font-weight:500;color:var(--color-text-primary)}
  .brand-sub{font-size:12px;color:var(--color-text-secondary);margin-top:2px}
  .date-col{text-align:right;flex-shrink:0}
  .ist-date{font-size:15px;font-weight:500;color:var(--color-text-primary)}
  .ist-time{font-size:12px;color:var(--color-text-tertiary);margin-top:2px}
  .sources{display:flex;flex-wrap:wrap;gap:5px;margin-bottom:1rem}
  .src{font-size:11px;padding:3px 9px;border-radius:20px;border:0.5px solid var(--color-border-tertiary);color:var(--color-text-tertiary)}
  .status-bar{display:flex;align-items:center;background:var(--color-background-secondary);border:0.5px solid var(--color-border-success);border-radius:var(--border-radius-md);padding:10px 14px;margin-bottom:1rem;gap:8px}
  .dot{width:8px;height:8px;border-radius:50%;background:#639922;flex-shrink:0}
  .status-txt{font-size:13px;color:var(--color-text-secondary)}
  .tabs{display:flex;gap:5px;flex-wrap:wrap;margin-bottom:1rem}
  .tab{font-size:12px;padding:5px 12px;border-radius:20px;border:0.5px solid var(--color-border-tertiary);background:transparent;color:var(--color-text-secondary);cursor:pointer;white-space:nowrap;font-family:var(--font-sans)}
  .tab.active{background:var(--color-background-info);color:var(--color-text-info);border-color:transparent;font-weight:500}
  .cat-section{display:none;flex-direction:column;gap:10px}
  .cat-section.visible{display:flex}
  .ncard{background:var(--color-background-primary);border:0.5px solid var(--color-border-tertiary);border-radius:var(--border-radius-lg);padding:14px 16px;transition:border-color .15s}
  .ncard:hover{border-color:var(--color-border-secondary)}
  .nmeta{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px}
  .nsrc{font-size:11px;font-weight:500;color:var(--color-text-info);text-transform:uppercase;letter-spacing:.05em}
  .ntime{font-size:11px;color:var(--color-text-tertiary)}
  .nhead{font-size:14px;font-weight:500;color:var(--color-text-primary);line-height:1.5;margin-bottom:5px}
  .nsum{font-size:13px;color:var(--color-text-secondary);line-height:1.6}
  .footer{margin-top:1.5rem;text-align:center;font-size:11px;color:var(--color-text-tertiary);padding:12px 0;border-top:0.5px solid var(--color-border-tertiary)}"""


def build_html(data: dict) -> str:
    return f"""\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Bangalore Morning Digest — {TITLE_DATE}</title>
<style>
{CSS}
</style>
</head>
<body>
<div class="app">

  <div class="header">
    <div>
      <div class="brand-row">
        <div class="brand-icon">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-info)" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
        </div>
        <div>
          <div class="brand-title">Bangalore Morning Digest</div>
          <div class="brand-sub">3 headlines per category · Powered by Claude + Web Search</div>
        </div>
      </div>
    </div>
    <div class="date-col">
      <div class="ist-date">{DATE_LONG}</div>
      <div class="ist-time">{TIME_IST}</div>
    </div>
  </div>

  <div class="sources">
    <span class="src">Times of India</span>
    <span class="src">The Hindu</span>
    <span class="src">Deccan Herald</span>
    <span class="src">InShorts</span>
    <span class="src">NDTV</span>
    <span class="src">Economic Times</span>
    <span class="src">MSN India</span>
    <span class="src">Google News</span>
  </div>

  <div class="status-bar">
    <div class="dot"></div>
    <span class="status-txt">Digest loaded &nbsp;·&nbsp; {DATE_LONG} &nbsp;·&nbsp; {TIME_IST}</span>
  </div>

  <div class="tabs">
    <button class="tab active" onclick="switchTab('local',this)">Local Bangalore</button>
    <button class="tab" onclick="switchTab('national',this)">National India</button>
    <button class="tab" onclick="switchTab('business',this)">Business &amp; Finance</button>
    <button class="tab" onclick="switchTab('tech',this)">Technology</button>
    <button class="tab" onclick="switchTab('intl',this)">International</button>
  </div>

  <!-- LOCAL BANGALORE -->
  <div class="cat-section visible" id="cat-local">
{_cards(data['local'])}
  </div>

  <!-- NATIONAL INDIA -->
  <div class="cat-section" id="cat-national">
{_cards(data['national'])}
  </div>

  <!-- BUSINESS & FINANCE -->
  <div class="cat-section" id="cat-business">
{_cards(data['business'])}
  </div>

  <!-- TECHNOLOGY -->
  <div class="cat-section" id="cat-tech">
{_cards(data['tech'])}
  </div>

  <!-- INTERNATIONAL -->
  <div class="cat-section" id="cat-intl">
{_cards(data['intl'])}
  </div>

  <div class="footer">Bangalore Morning Digest &nbsp;·&nbsp; {DATE_LONG} &nbsp;·&nbsp; {TIME_IST} &nbsp;·&nbsp; Powered by Claude + Web Search</div>

</div>

<script>
function switchTab(id, btn) {{
  document.querySelectorAll('.cat-section').forEach(s => s.classList.remove('visible'));
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.getElementById('cat-' + id).classList.add('visible');
  btn.classList.add('active');
}}
</script>
</body>
</html>"""


def _whatsapp_text(data: dict) -> str:
    """Format the digest as a compact WhatsApp message."""
    icons = {
        "local":    ("📍", "LOCAL BANGALORE"),
        "national": ("🇮🇳", "NATIONAL INDIA"),
        "business": ("💼", "BUSINESS & FINANCE"),
        "tech":     ("💻", "TECHNOLOGY"),
        "intl":     ("🌍", "INTERNATIONAL"),
    }
    lines = [f"🗞 *Bangalore Morning Digest*\n{DATE_LONG}\n"]
    for key, (icon, label) in icons.items():
        lines.append(f"{icon} *{label}*")
        for item in data[key][:3]:
            lines.append(f"• {item['headline']}")
        lines.append("")
    lines.append("_Powered by Claude + Web Search_")
    return "\n".join(lines)


def send_whatsapp(data: dict) -> None:
    client = Client(TWILIO_SID, TWILIO_TOKEN)
    body   = _whatsapp_text(data)
    msg    = client.messages.create(from_=TWILIO_FROM, to=WHATSAPP_TO, body=body)
    print(f"WhatsApp sent → SID {msg.sid}")


def main():
    print("Fetching news via Claude + web search …")
    data = fetch_news()
    print("News fetched. Building HTML …")
    html = build_html(data)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Digest written → {OUTPUT}")
    print("Sending WhatsApp message …")
    send_whatsapp(data)


if __name__ == "__main__":
    main()
