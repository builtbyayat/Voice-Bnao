#!/usr/bin/env python3
import os, sys, json, hashlib, asyncio, webbrowser, http.server, socketserver, urllib.parse, urllib.request
from pathlib import Path

# Auto-install edge-tts if missing
try:
    import edge_tts
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "edge-tts"])
    import edge_tts

PORT = 5000
BASE_DIR = Path(__file__).resolve().parent
AUDIO_DIR = BASE_DIR / "audio_output"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

ELEVENLABS_VOICES = [
    {"id": "pNInz6obpgDQGcFmaJgB", "name": "Adam (एडम) - सबसे लोकप्रिय डीप आवाज़ (GK/Facts/Shorts)", "gender": "Male"},
    {"id": "IKne3meq5aSn9XLyUdCD", "name": "Charlie (चार्ली) - रहस्य और कहानियों के लिए", "gender": "Male"},
    {"id": "nPczCjzI2devNBz1zQrb", "name": "Brian (ब्रायन) - गंभीर और प्रोफेशनल आवाज़", "gender": "Male"},
    {"id": "JBFqnCBsd6RMkjVDRZzb", "name": "George (जॉर्ज) - गहरा और दमदार नरेटर", "gender": "Male"},
    {"id": "EXAVITQu4vr4xnSDxMaL", "name": "Sarah (सारा) - नेचुरल फीमेल आवाज़", "gender": "Female"},
    {"id": "pFZP5JQG7iQjIQuC4Bku", "name": "Lily (लिली) - शांत और मधुर फीमेल आवाज़", "gender": "Female"}
]

FREE_VOICES = [
    {"id": "hi-IN-MadhurNeural", "name": "हिन्दी - मधुर (Madhur)", "gender": "Male", "flag": "🇮🇳"},
    {"id": "hi-IN-SwaraNeural", "name": "हिन्दी - स्वरा (Swara)", "gender": "Female", "flag": "🇮🇳"},
    {"id": "en-IN-PrabhatNeural", "name": "English (India) - Prabhat", "gender": "Male", "flag": "🇮🇳"},
    {"id": "en-IN-NeerjaNeural", "name": "English (India) - Neerja", "gender": "Female", "flag": "🇮🇳"}
]

HTML_CONTENT = """<!DOCTYPE html>
<html lang="hi" data-theme="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Ultimate AI Voice Studio - ElevenLabs Quality</title>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800&display=swap" rel="stylesheet">
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; }
    body { background: #090d16; color: #f0f4f9; min-height: 100vh; padding: 20px 14px; }
    .container { max-width: 900px; margin: 0 auto; }
    header { display: flex; align-items: center; justify-content: space-between; padding: 16px 22px; background: #111728; border: 1px solid rgba(255,255,255,0.08); border-radius: 16px; margin-bottom: 20px; }
    .brand h1 { font-size: 1.2rem; font-weight: 700; }
    .brand span { color: #fbbc04; }
    .tabs { display: flex; background: #111728; border: 1px solid rgba(255,255,255,0.08); padding: 4px; border-radius: 14px; gap: 6px; margin-bottom: 20px; }
    .tab { flex: 1; padding: 12px; border-radius: 10px; border: none; background: transparent; color: #9aa0a6; font-size: 0.92rem; font-weight: 700; cursor: pointer; text-align: center; }
    .tab.active.eleven { background: linear-gradient(135deg, #7c3aed, #6366f1); color: #fff; box-shadow: 0 4px 16px rgba(124, 58, 237, 0.4); }
    .tab.active.free { background: linear-gradient(135deg, #4285f4, #1a73e8); color: #fff; box-shadow: 0 4px 16px rgba(66, 133, 244, 0.4); }
    .card { background: #111728; border: 1px solid rgba(255,255,255,0.08); border-radius: 20px; padding: 24px; display: flex; flex-direction: column; gap: 18px; box-shadow: 0 12px 36px rgba(0,0,0,0.4); }
    .api-box { background: rgba(124, 58, 237, 0.1); border: 1px dashed rgba(124, 58, 237, 0.35); border-radius: 12px; padding: 14px; display: flex; flex-direction: column; gap: 8px; }
    .api-box input { background: #0f1524; border: 1px solid rgba(255,255,255,0.12); color: #fff; padding: 10px 14px; border-radius: 8px; font-size: 0.9rem; outline: none; }
    .row { display: grid; grid-template-columns: 1.2fr 0.8fr; gap: 14px; }
    @media(max-width:650px){ .row { grid-template-columns: 1fr; } }
    label { font-size: 0.85rem; font-weight: 600; color: #9aa0a6; display: flex; justify-content: space-between; margin-bottom: 6px; }
    select, textarea { width: 100%; background: #192238; border: 1px solid rgba(255,255,255,0.08); color: #fff; padding: 12px 14px; border-radius: 12px; font-size: 0.95rem; outline: none; }
    textarea { height: 180px; resize: vertical; line-height: 1.6; }
    .btn-gen { background: linear-gradient(135deg, #7c3aed, #4285f4); color: white; border: none; padding: 16px; border-radius: 12px; font-size: 1.05rem; font-weight: 700; cursor: pointer; }
    .btn-gen:hover { transform: translateY(-2px); }
    .btn-gen:disabled { opacity: 0.6; cursor: not-allowed; }
    .player-box { background: rgba(66, 133, 244, 0.08); border: 1px solid rgba(66, 133, 244, 0.3); border-radius: 14px; padding: 20px; display: none; flex-direction: column; gap: 14px; }
    .player-box.active { display: flex; }
    audio { width: 100%; }
    .btn-down { background: linear-gradient(135deg, #34a853, #227b3b); color: white; border: none; padding: 14px; border-radius: 12px; font-size: 1rem; font-weight: 700; cursor: pointer; text-align: center; }
    .btn-down:hover { transform: translateY(-2px); }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="brand">
        <h1>Ultimate <span>AI Voice Studio</span></h1>
      </div>
      <span style="color:#a78bfa; font-weight:600; font-size:0.85rem">👑 ElevenLabs Quality</span>
    </header>

    <div class="tabs">
      <button class="tab active eleven" id="tabEleven" onclick="switchTab('eleven')">👑 1. ElevenLabs Engine (Adam / Charlie)</button>
      <button class="tab free" id="tabFree" onclick="switchTab('free')">⚡ 2. Free Unlimited Engine (Madhur / Swara)</button>
    </div>

    <div class="card">
      <div class="api-box" id="elevenBox">
        <label style="color:#c4b5fd">
          🔑 ElevenLabs Free API Key (हर महीने 10,000 अक्षर फ्री):
          <a href="https://elevenlabs.io" target="_blank" style="color:#a78bfa">यहाँ से 30 सेकंड में फ्री लें ↗</a>
        </label>
        <input type="password" id="elevenKey" placeholder="अपनी ElevenLabs API Key डालें (उदा. sk_...)" oninput="localStorage.setItem('eleven_key', this.value.trim())">
      </div>

      <div class="row">
        <div>
          <label>आवाज़ चुनें (Voice):</label>
          <select id="voiceSelect"></select>
        </div>
        <div>
          <label>स्पीड (Speed): <span id="spVal" style="color:#4285f4">1.0x</span></label>
          <div style="background:#192238; padding:10px 14px; border-radius:12px; display:flex; align-items:center;">
            <input type="range" id="spRange" min="0.7" max="1.4" step="0.05" value="1.0" style="flex:1; accent-color:#4285f4" oninput="document.getElementById('spVal').textContent=this.value+'x'">
          </div>
        </div>
      </div>

      <div>
        <label>अपनी पूरी स्क्रिप्ट यहाँ लिखें:</label>
        <textarea id="scriptInput" placeholder="यहाँ अपनी GK Quiz या कहानी लिखें..."></textarea>
      </div>

      <button class="btn-gen" id="genBtn" onclick="generate()">✨ असली आवाज़ बनाएं (Generate Audio)</button>

      <div class="player-box" id="playerBox">
        <label style="color:#fff">🎧 जनरेट किया गया ऑडियो सुनें:</label>
        <audio id="audioEl" controls preload="auto"></audio>
        <button class="btn-down" onclick="downloadMp3()">⬇️ MP3 ऑडियो सीधे अपने लैपटॉप में डाउनलोड करें (100% Working)</button>
      </div>
    </div>
  </div>

  <script>
    const ELEVEN = ELEVEN_PLACEHOLDER;
    const FREE = FREE_PLACEHOLDER;
    let mode = 'eleven';
    let loadedBlob = null;

    function init() {
      document.getElementById('elevenKey').value = localStorage.getItem('eleven_key') || '';
      document.getElementById('scriptInput').value = `सही जवाब है तीन।\\n\\nसवाल नंबर चार। कौन-सा पक्षी पीछे की तरफ भी उड़ सकता है?\\nसही जवाब है हमिंगबर्ड।\\n\\nसवाल नंबर पाँच। दुनिया का सबसे बड़ा रेगिस्तान कौन-सा है?\\nसही जवाब है अंटार्कटिका।`;
      switchTab('eleven');
    }

    function switchTab(m) {
      mode = m;
      document.getElementById('tabEleven').classList.toggle('active', m === 'eleven');
      document.getElementById('tabFree').classList.toggle('active', m === 'free');
      document.getElementById('elevenBox').style.display = (m === 'eleven') ? 'flex' : 'none';

      const sel = document.getElementById('voiceSelect');
      sel.innerHTML = '';
      const list = (m === 'eleven') ? ELEVEN : FREE;
      list.forEach(v => {
        const opt = document.createElement('option');
        opt.value = v.id;
        opt.textContent = `${v.name} • [${v.gender}]`;
        sel.appendChild(opt);
      });
    }

    async function generate() {
      const text = document.getElementById('scriptInput').value.trim();
      if(!text) { alert('कृपया स्क्रिप्ट लिखें!'); return; }
      const voice = document.getElementById('voiceSelect').value;
      const speed = parseFloat(document.getElementById('spRange').value);
      const key = document.getElementById('elevenKey').value.trim();

      if(mode === 'eleven' && !key) {
        alert('ElevenLabs के लिए कृपया ऊपर अपनी फ्री API Key डालें! (या ऊपर Free Unlimited Engine टैब चुनें)');
        document.getElementById('elevenKey').focus();
        return;
      }

      const btn = document.getElementById('genBtn');
      btn.disabled = true; btn.textContent = '⏳ आवाज़ बन रही है... कृपया प्रतीक्षा करें';

      try {
        const res = await fetch('/api/tts', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ engine: mode, text, voice, speed, api_key: key })
        });
        const data = await res.json();
        if(!res.ok || data.error) throw new Error(data.error || 'त्रुटि हुई');

        const audioRes = await fetch(data.audio_url);
        loadedBlob = await audioRes.blob();
        const blobUrl = URL.createObjectURL(loadedBlob);

        const player = document.getElementById('audioEl');
        player.src = blobUrl;
        player.play();
        document.getElementById('playerBox').classList.add('active');
      } catch(e) {
        alert('त्रुटि: ' + e.message);
      } finally {
        btn.disabled = false; btn.textContent = '✨ असली आवाज़ बनाएं (Generate Audio)';
      }
    }

    function downloadMp3() {
      if(!loadedBlob) return;
      const blobUrl = URL.createObjectURL(loadedBlob);
      const a = document.createElement('a');
      a.href = blobUrl;
      a.download = `voice_${Date.now()}.mp3`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      setTimeout(() => URL.revokeObjectURL(blobUrl), 2000);
    }

    window.onload = init;
  </script>
</body>
</html>
"""

def generate_elevenlabs(text, voice_id, api_key, out_path):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    req = urllib.request.Request(
        url,
        data=json.dumps({
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.50, "similarity_boost": 0.80, "use_speaker_boost": True}
        }).encode('utf-8'),
        headers={"xi-api-key": api_key, "Content-Type": "application/json", "Accept": "audio/mpeg"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=45) as resp:
        with open(out_path, "wb") as f:
            f.write(resp.read())

def generate_edge(text, voice_id, speed, out_path):
    pct = int(round((speed - 1.0) * 100))
    rate_str = f"+{pct}%" if pct >= 0 else f"{pct}%"
    async def _run():
        comm = edge_tts.Communicate(text, voice_id, rate=rate_str)
        await comm.save(out_path)
    asyncio.run(_run())

class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

    def do_GET(self):
        p = urllib.parse.urlparse(self.path).path
        if p == "/" or p == "/index.html":
            html = HTML_CONTENT.replace("ELEVEN_PLACEHOLDER", json.dumps(ELEVENLABS_VOICES))
            html = html.replace("FREE_PLACEHOLDER", json.dumps(FREE_VOICES))
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
            return

        if p.startswith("/audio/"):
            fn = p.split("/audio/")[1]
            fp = AUDIO_DIR / fn
            if fp.exists():
                with open(fp, "rb") as f: data = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "audio/mpeg")
                self.end_headers()
                self.wfile.write(data)
                return
        self.send_error(404)

    def do_POST(self):
        if self.path == "/api/tts":
            length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(length).decode('utf-8'))
            eng = body.get("engine", "eleven")
            text = body.get("text", "").strip()
            voice = body.get("voice", "")
            speed = float(body.get("speed", 1.0))
            key = body.get("api_key", "").strip()

            h = hashlib.md5(f"{eng}_{text}_{voice}_{speed}".encode()).hexdigest()
            out_file = AUDIO_DIR / f"{h}.mp3"

            try:
                if not out_file.exists():
                    if eng == "eleven":
                        generate_elevenlabs(text, voice, key, str(out_file))
                    else:
                        generate_edge(text, voice, speed, str(out_file))

                resp = json.dumps({"audio_url": f"/audio/{h}.mp3"}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(resp)
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return
        self.send_error(404)

socketserver.TCPServer.allow_reuse_address = True
print(f"\n🚀 AI Voice Studio running at: http://localhost:{PORT}")
try: webbrowser.open(f"http://localhost:{PORT}")
except: pass
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    httpd.serve_forever()