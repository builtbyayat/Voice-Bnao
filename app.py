#!/usr/bin/env python3
"""
StudioVoice AI - Professional Text-to-Speech Web Studio
- True Male & Female Voices (ElevenLabs Multilingual v2 + High-Fidelity Engine)
- Automatic Deep Pitch Engine for authentic Male voiceovers
- Modern Glassmorphism Studio UI & 1-Click Direct MP3 Download
"""

import os, sys, json, hashlib, asyncio, http.server, socketserver, urllib.parse, urllib.request, re, subprocess
from pathlib import Path

try:
    import edge_tts
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "edge-tts"])
    import edge_tts

PORT = int(os.environ.get("PORT", 5000))
BASE_DIR = Path(__file__).resolve().parent
AUDIO_DIR = BASE_DIR / "audio_output"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# ----------------- CONTENT MODERATION -----------------
BLOCKED_PATTERNS = {
    "sex", "sexy", "nude", "porn", "erotic", "orgasm", "penis", "vagina", "boobs", "breast",
    "kiss", "kissing", "makeout", "strip", "lust", "seduce", "seduction", "horny", "intimate",
    "naked", "touching", "sensual", "intercourse", "hot voice", "sexy voice",
    "सेक्स", "पोर्न", "नंगा", "नग्न", "संभोग", "हवस", "जिस्म", "कामुक", "चुंबन", "स्तन", "योनि", "लिंग",
    "nangi", "nanga", "sambhog", "chumban", "hawas", "jism", "kamuk", "chudai", "chuda",
    "bhosdi", "choot", "loda", "lauda", "lund", "gaand", "muth", "mutth",
    "babu", "shona", "jaaneman", "sweetheart", "darling", "baby", "hug me", "kiss me", "love you",
    "i love you", "meri jaan", "mohabbat", "aashiqui", "aashiq", "deewana", "deewani", "dilruba",
    "mehboob", "mehbooba", "hoth", "honth", "baahon", "bahen", "gale lag jao", "lip kiss", "pyaar karo",
    "आई लव यू", "बाबू", "शोना", "जानेमन", "डार्लिंग", "मोहब्बत", "आशिक़ी", "दीवाना", "दीवानी", "होठ", "बाहों",
    "गले लगाओ", "प्यार करो", "माशूका", "दिलरुबा", "इश्क़", "हुस्न", "मादक", "रोमांस", "romance", "romantic",
    "bhenchod", "madarchod", "behenchod", "bhadwe", "chutiya", "harami", "kutta", "kameena", "randi",
    "suar", "bastard", "fuck", "bitch", "asshole", "motherfucker", "whore", "slut", "terrorist",
    "मादरचोद", "बहनचोद", "भड़वे", "चूतिया", "हरामी", "कमीना", "रंडी", "कुत्ता", "सूअर"
}

def check_content_safety(text):
    allowed_pattern = r'^[\u0900-\u097F\w\s.,?!:;\'"()/\-\n\r\t]+$'
    if not re.match(allowed_pattern, text):
        return False, "Security: Only Hindi, Hinglish, and English scripts are supported."

    clean = text.lower()
    clean_words = set(re.sub(r'[^\w\s]', ' ', clean).split())

    for w in clean_words:
        if w in BLOCKED_PATTERNS:
            return False, "Content Moderation: Prohibited words detected."

    for phrase in ["kiss me", "love you", "i love you", "hug me", "meri jaan", "pyaar karo", "gale lag"]:
        if phrase in clean:
            return False, "Content Moderation: Inappropriate phrase blocked."

    return True, "Safe"

VOICES_CONFIG = {
    "eleven": [
        {"id": "pNInz6obpgDQGcFmaJgB", "name": "Adam", "desc": "Deep Narrator (YouTube/Shorts/GK)", "gender": "Male", "badge": "👨 MALE"},
        {"id": "IKne3meq5aSn9XLyUdCD", "name": "Charlie", "desc": "Deep Storytelling & Mystery", "gender": "Male", "badge": "👨 MALE"},
        {"id": "nPczCjzI2devNBz1zQrb", "name": "Brian", "desc": "Authoritative & Documentary", "gender": "Male", "badge": "👨 MALE"},
        {"id": "JBFqnCBsd6RMkjVDRZzb", "name": "George", "desc": "Warm & Resonant Voiceover", "gender": "Male", "badge": "👨 MALE"},
        {"id": "EXAVITQu4vr4xnSDxMaL", "name": "Sarah", "desc": "Clear & Natural Professional", "gender": "Female", "badge": "👩 FEMALE"}
    ],
    "neural": [
        {"id": "hi-IN-MadhurNeural", "name": "Madhur (मधुर)", "desc": "Hindi Confident Male", "gender": "Male", "badge": "👨 MALE", "flag": "🇮🇳"},
        {"id": "en-IN-PrabhatNeural", "name": "Prabhat", "desc": "Indian English Male", "gender": "Male", "badge": "👨 MALE", "flag": "🇮🇳"},
        {"id": "en-US-GuyNeural", "name": "Guy", "desc": "American English Male", "gender": "Male", "badge": "👨 MALE", "flag": "🇺🇸"},
        {"id": "hi-IN-SwaraNeural", "name": "Swara (स्वरा)", "desc": "Hindi Natural Female", "gender": "Female", "badge": "👩 FEMALE", "flag": "🇮🇳"},
        {"id": "en-IN-NeerjaNeural", "name": "Neerja", "desc": "Indian English Female", "gender": "Female", "badge": "👩 FEMALE", "flag": "🇮🇳"}
    ]
}

HTML_CONTENT = """<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>StudioVoice AI - Professional Text to Speech</title>
  <meta name="description" content="Generate studio-quality AI voiceovers in Hindi & English with ElevenLabs and Neural Voice Engine.">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Noto+Sans+Devanagari:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #07090e;
      --surface: #0f131c;
      --surface-border: rgba(255, 255, 255, 0.08);
      --surface-hover: #161c29;
      --primary: #6366f1;
      --primary-hover: #4f46e5;
      --primary-glow: rgba(99, 102, 241, 0.25);
      --accent: #8b5cf6;
      --success: #10b981;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --radius: 14px;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', 'Noto Sans Devanagari', sans-serif; }
    body { background-color: var(--bg); color: var(--text); min-height: 100vh; padding: 24px 16px; display: flex; flex-direction: column; align-items: center; }
    .wrapper { width: 100%; max-width: 920px; }
    
    header {
      display: flex; align-items: center; justify-content: space-between;
      padding: 16px 24px; background: var(--surface); border: 1px solid var(--surface-border);
      border-radius: var(--radius); margin-bottom: 24px;
    }
    .logo-container { display: flex; align-items: center; gap: 12px; }
    .logo-mark {
      width: 40px; height: 40px; border-radius: 10px;
      background: linear-gradient(135deg, var(--primary), var(--accent));
      display: flex; align-items: center; justify-content: center; font-size: 20px; color: #fff;
      box-shadow: 0 4px 14px var(--primary-glow);
    }
    .logo-text h1 { font-size: 1.15rem; font-weight: 700; letter-spacing: -0.02em; }
    .logo-text span { color: var(--primary); }
    .status-badge {
      font-size: 0.75rem; font-weight: 600; padding: 6px 12px; border-radius: 999px;
      background: rgba(16, 185, 129, 0.12); color: var(--success); border: 1px solid rgba(16, 185, 129, 0.25);
      display: flex; align-items: center; gap: 6px;
    }
    .status-dot { width: 6px; height: 6px; background: var(--success); border-radius: 50%; box-shadow: 0 0 8px var(--success); }

    .engine-switcher {
      display: grid; grid-template-columns: 1fr 1fr; gap: 8px;
      background: var(--surface); border: 1px solid var(--surface-border);
      padding: 6px; border-radius: var(--radius); margin-bottom: 20px;
    }
    .engine-btn {
      padding: 12px; border-radius: 10px; border: none; background: transparent;
      color: var(--text-muted); font-size: 0.9rem; font-weight: 600; cursor: pointer;
      display: flex; align-items: center; justify-content: center; gap: 8px; transition: all 0.2s;
    }
    .engine-btn.active {
      background: var(--surface-hover); color: #fff; border: 1px solid var(--surface-border);
      box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    .engine-btn.active.primary { color: #a5b4fc; border-color: rgba(99, 102, 241, 0.4); }

    .studio-panel {
      background: var(--surface); border: 1px solid var(--surface-border);
      border-radius: 20px; padding: 28px; display: flex; flex-direction: column; gap: 20px;
      box-shadow: 0 16px 40px rgba(0,0,0,0.4);
    }

    .api-card {
      background: rgba(99, 102, 241, 0.08); border: 1px dashed rgba(99, 102, 241, 0.35);
      border-radius: 12px; padding: 14px 18px; display: flex; flex-direction: column; gap: 10px;
    }
    .api-header { display: flex; justify-content: space-between; align-items: center; font-size: 0.85rem; font-weight: 600; color: #c7d2fe; }
    .api-header a { color: #818cf8; text-decoration: none; font-size: 0.8rem; }
    .api-header a:hover { text-decoration: underline; }
    .api-input {
      background: #090c14; border: 1px solid var(--surface-border); color: #fff;
      padding: 10px 14px; border-radius: 8px; font-size: 0.9rem; outline: none; width: 100%;
    }
    .api-input:focus { border-color: var(--primary); }

    .controls-grid { display: grid; grid-template-columns: 1.3fr 0.7fr; gap: 16px; }
    @media (max-width: 640px) { .controls-grid { grid-template-columns: 1fr; } }
    .field-group { display: flex; flex-direction: column; gap: 8px; }
    .field-label { font-size: 0.82rem; font-weight: 600; color: var(--text-muted); display: flex; justify-content: space-between; }
    
    select, textarea {
      width: 100%; background: #090c14; border: 1px solid var(--surface-border);
      color: #fff; padding: 12px 14px; border-radius: 10px; font-size: 0.95rem; outline: none;
    }
    select:focus, textarea:focus { border-color: var(--primary); }
    textarea { height: 190px; resize: vertical; line-height: 1.6; }

    .slider-container {
      background: #090c14; border: 1px solid var(--surface-border);
      padding: 10px 14px; border-radius: 10px; display: flex; align-items: center; gap: 12px;
    }
    .slider-container input { flex: 1; accent-color: var(--primary); cursor: pointer; }

    .btn-submit {
      background: linear-gradient(135deg, var(--primary), var(--accent));
      color: white; border: none; padding: 16px; border-radius: 12px;
      font-size: 1rem; font-weight: 700; cursor: pointer; display: flex;
      align-items: center; justify-content: center; gap: 10px;
      box-shadow: 0 8px 24px var(--primary-glow); transition: transform 0.15s;
    }
    .btn-submit:hover { transform: translateY(-2px); }
    .btn-submit:disabled { opacity: 0.6; cursor: not-allowed; }

    .player-card {
      background: linear-gradient(135deg, rgba(99, 102, 241, 0.08), rgba(16, 185, 129, 0.05));
      border: 1px solid rgba(99, 102, 241, 0.3); border-radius: 16px; padding: 22px;
      display: none; flex-direction: column; gap: 16px;
    }
    .player-card.active { display: flex; }
    
    .player-meta { display: flex; justify-content: space-between; align-items: center; font-size: 0.85rem; }
    .voice-badge-tag {
      background: rgba(99, 102, 241, 0.2); color: #a5b4fc; border: 1px solid rgba(99, 102, 241, 0.4);
      padding: 4px 10px; border-radius: 6px; font-weight: 600; font-size: 0.75rem;
    }
    audio { width: 100%; border-radius: 8px; }

    .btn-download-mp3 {
      background: linear-gradient(135deg, #10b981, #059669);
      color: white; border: none; padding: 14px; border-radius: 10px;
      font-size: 0.95rem; font-weight: 700; cursor: pointer;
      display: flex; align-items: center; justify-content: center; gap: 8px;
    }
    .counter-bar { display: flex; justify-content: space-between; font-size: 0.78rem; color: var(--text-muted); }
  </style>
</head>
<body>
  <div class="wrapper">
    <header>
      <div class="logo-container">
        <div class="logo-mark">🎙️</div>
        <div class="logo-text">
          <h1>StudioVoice <span>AI</span></h1>
        </div>
      </div>
      <div class="status-badge">
        <span class="status-dot"></span>
        <span>Studio Ready</span>
      </div>
    </header>

    <div class="engine-switcher">
      <button class="engine-btn active primary" id="btnEleven" onclick="switchEngine('eleven')">
        ✨ ElevenLabs Engine (Ultra Realistic)
      </button>
      <button class="engine-btn" id="btnNeural" onclick="switchEngine('neural')">
        ⚡ Neural Voice Engine (Free Backup)
      </button>
    </div>

    <main class="studio-panel">
      <div class="api-card" id="apiCard">
        <div class="api-header">
          <span>ElevenLabs API Key (Saved in browser):</span>
          <a href="https://elevenlabs.io" target="_blank">Get 10,000 Chars Free ↗</a>
        </div>
        <input type="password" class="api-input" id="apiKeyInput" placeholder="Paste your ElevenLabs API Key (sk_...)" oninput="saveKey(this.value)">
      </div>

      <div class="controls-grid">
        <div class="field-group">
          <label class="field-label">
            <span>Select Voice:</span>
            <span id="genderBadge" style="color:#a5b4fc; font-weight:700;">👨 MALE</span>
          </label>
          <select id="voiceSelect" onchange="updateGenderLabel()"></select>
        </div>

        <div class="field-group">
          <label class="field-label">
            <span>Speed: <strong id="speedVal" style="color:var(--primary);">1.0x</strong></span>
          </label>
          <div class="slider-container">
            <input type="range" id="speedSlider" min="0.75" max="1.35" step="0.05" value="1.0" oninput="document.getElementById('speedVal').textContent=this.value+'x'">
          </div>
        </div>
      </div>

      <div class="field-group">
        <label class="field-label">
          <span>Your Script (GK, Stories, Education):</span>
        </label>
        <textarea id="scriptText" placeholder="Enter your script here..."></textarea>
        <div class="counter-bar">
          <span id="charCount">0 characters</span>
          <span id="estTime">Est. Duration: ~0s</span>
        </div>
      </div>

      <button class="btn-submit" id="generateBtn" onclick="handleGenerate()">
        <span>✨ Generate Studio Audio</span>
      </button>

      <div class="player-card" id="playerCard">
        <div class="player-meta">
          <span class="voice-badge-tag" id="playerTag">ADAM • MALE</span>
          <span style="font-size:0.75rem; color:var(--text-muted);">Format: MP3 • 44.1kHz</span>
        </div>
        
        <audio id="audioElement" controls preload="auto"></audio>

        <button class="btn-download-mp3" onclick="downloadMp3()">
          ⬇️ Download MP3 Audio File
        </button>
      </div>
    </main>
  </div>

  <script>
    const CONFIG = VOICES_DATA_PLACEHOLDER;
    let currentEngine = 'eleven';
    let currentBlob = null;

    function init() {
      const saved = localStorage.getItem('sv_eleven_key') || '';
      document.getElementById('apiKeyInput').value = saved;
      
      document.getElementById('scriptText').value = `सही जवाब है तीन।\\n\\nसवाल नंबर चार। कौन-सा पक्षी पीछे की तरफ भी उड़ सकता है?\\nसही जवाब है हमिंगबर्ड।\\n\\nसवाल नंबर पाँच। दुनिया का सबसे बड़ा रेगिस्तान कौन-सा है?\\nसही जवाब है अंटार्कटिका।`;
      updateCounters();

      document.getElementById('scriptText').addEventListener('input', updateCounters);
      switchEngine('eleven');
    }

    function saveKey(k) {
      localStorage.setItem('sv_eleven_key', k.trim());
    }

    function switchEngine(mode) {
      currentEngine = mode;
      document.getElementById('btnEleven').classList.toggle('active', mode === 'eleven');
      document.getElementById('btnNeural').classList.toggle('active', mode === 'neural');
      document.getElementById('apiCard').style.display = (mode === 'eleven') ? 'flex' : 'none';

      const select = document.getElementById('voiceSelect');
      select.innerHTML = '';
      const list = CONFIG[mode] || [];
      list.forEach(v => {
        const opt = document.createElement('option');
        opt.value = v.id;
        opt.dataset.gender = v.gender;
        opt.textContent = `${v.badge} ${v.name} - ${v.desc}`;
        select.appendChild(opt);
      });
      updateGenderLabel();
    }

    function updateGenderLabel() {
      const select = document.getElementById('voiceSelect');
      const selected = select.options[select.selectedIndex];
      if (selected) {
        document.getElementById('genderBadge').textContent = selected.dataset.gender === 'Male' ? '👨 MALE' : '👩 FEMALE';
      }
    }

    function updateCounters() {
      const val = document.getElementById('scriptText').value;
      const chars = val.length;
      const words = val.trim() ? val.trim().split(/\\s+/).length : 0;
      document.getElementById('charCount').textContent = `${chars} characters • ${words} words`;
      const sec = Math.round((words / 130) * 60);
      document.getElementById('estTime').textContent = `Est. Duration: ~${sec}s`;
    }

    async function handleGenerate() {
      const text = document.getElementById('scriptText').value.trim();
      if (!text) { alert('Please enter script text first!'); return; }

      const select = document.getElementById('voiceSelect');
      const voice = select.value;
      const gender = select.options[select.selectedIndex].dataset.gender;
      const speed = parseFloat(document.getElementById('speedSlider').value);
      const key = document.getElementById('apiKeyInput').value.trim();

      if (currentEngine === 'eleven' && !key) {
        alert('Please enter your ElevenLabs API Key or switch to Neural Voice Engine tab.');
        document.getElementById('apiKeyInput').focus();
        return;
      }

      const btn = document.getElementById('generateBtn');
      btn.disabled = true;
      btn.innerHTML = '<span>⏳ Synthesizing Voice... Please wait</span>';

      try {
        const res = await fetch('/api/tts', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            engine: currentEngine,
            text,
            voice,
            gender,
            speed,
            api_key: key
          })
        });

        const data = await res.json();
        if (!res.ok || data.error) {
          throw new Error(data.error || 'Failed to synthesize audio');
        }

        const audioRes = await fetch(data.audio_url);
        currentBlob = await audioRes.blob();
        const blobUrl = URL.createObjectURL(currentBlob);

        const player = document.getElementById('audioElement');
        player.src = blobUrl;
        player.play();

        document.getElementById('playerTag').textContent = `${select.options[select.selectedIndex].text}`;
        document.getElementById('playerCard').classList.add('active');

      } catch (err) {
        alert(err.message);
      } finally {
        btn.disabled = false;
        btn.innerHTML = '<span>✨ Generate Studio Audio</span>';
      }
    }

    function downloadMp3() {
      if (!currentBlob) return;
      const blobUrl = URL.createObjectURL(currentBlob);
      const a = document.createElement('a');
      a.href = blobUrl;
      a.download = `studiovoice_${Date.now()}.mp3`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
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

def generate_fallback_with_pitch(text, gender, speed, out_path):
    chunks = re.findall(r'([^।\.\?!;\n]+[।\.\?!;\n]*)', text) or [text]
    audio_bytes = bytearray()
    for c in chunks:
        c = c.strip()
        if not c: continue
        words = c.split()
        sub = ""
        for w in words:
            if len(sub) + len(w) + 1 <= 150: sub = f"{sub} {w}".strip()
            else:
                if sub:
                    u = f"https://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&tl=hi&q={urllib.parse.quote(sub)}"
                    req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(req, timeout=10) as r: audio_bytes.extend(r.read())
                sub = w
        if sub:
            u = f"https://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&tl=hi&q={urllib.parse.quote(sub)}"
            req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as r: audio_bytes.extend(r.read())

    raw_temp = str(out_path) + ".raw.mp3"
    with open(raw_temp, "wb") as f:
        f.write(audio_bytes)

    if gender == "Male":
        try:
            cmd = [
                "ffmpeg", "-y", "-i", raw_temp,
                "-af", "asetrate=24000*0.78,aresample=24000,atempo=1.28",
                str(out_path)
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            if os.path.exists(raw_temp): os.remove(raw_temp)
            return
        except Exception:
            pass

    if os.path.exists(raw_temp):
        os.replace(raw_temp, out_path)

class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

    def do_GET(self):
        p = urllib.parse.urlparse(self.path).path

        if p == "/googlefdf2add83f6955f5.html":
            content = b"google-site-verification: googlefdf2add83f6955f5.html"
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return

        if p == "/" or p == "/index.html":
            html = HTML_CONTENT.replace("VOICES_DATA_PLACEHOLDER", json.dumps(VOICES_CONFIG))
            body = html.encode('utf-8')
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if p.startswith("/audio/"):
            fn = p.split("/audio/")[1]
            fp = AUDIO_DIR / fn
            if fp.exists():
                with open(fp, "rb") as f: data = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "audio/mpeg")
                self.send_header("Content-Length", str(len(data)))
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
            gender = body.get("gender", "Male")
            speed = float(body.get("speed", 1.0))
            key = body.get("api_key", "").strip()

            is_safe, reason = check_content_safety(text)
            if not is_safe:
                self.send_response(400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"error": reason}).encode('utf-8'))
                return

            h = hashlib.md5(f"{eng}_{text}_{voice}_{gender}_{speed}".encode()).hexdigest()
            out_file = AUDIO_DIR / f"{h}.mp3"

            try:
                if not out_file.exists():
                    if eng == "eleven":
                        generate_elevenlabs(text, voice, key, str(out_file))
                    else:
                        try:
                            generate_edge(text, voice, speed, str(out_file))
                        except Exception:
                            generate_fallback_with_pitch(text, gender, speed, str(out_file))

                resp = json.dumps({"audio_url": f"/audio/{h}.mp3"}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(resp)))
                self.end_headers()
                self.wfile.write(resp)
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
            return
        self.send_error(404)

print(f"🚀 StudioVoice AI running on port {PORT}")
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    httpd.serve_forever()
