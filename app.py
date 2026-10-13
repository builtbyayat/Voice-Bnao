#!/usr/bin/env python3
"""
VoiceBnao - Professional Text-to-Speech Engine
- Working Speed Control (Live in Player + permanently applied to downloaded MP3)
- Restored Pure Natural Voices (Madhur Neural & ElevenLabs Adam/Charlie)
- Zero distorted pitch hacks: Pure, clean natural human speech
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

# ----------------- VOICES LIST -----------------
VOICES_CONFIG = {
    "eleven": [
        {"id": "pNInz6obpgDQGcFmaJgB", "name": "Adam", "desc": "Original Deep Narrator", "gender": "Male", "badge": "👨 MALE"},
        {"id": "IKne3meq5aSn9XLyUdCD", "name": "Charlie", "desc": "Deep Mystery & Story", "gender": "Male", "badge": "👨 MALE"},
        {"id": "nPczCjzI2devNBz1zQrb", "name": "Brian", "desc": "Documentary Specialist", "gender": "Male", "badge": "👨 MALE"},
        {"id": "JBFqnCBsd6RMkjVDRZzb", "name": "George", "desc": "Resonant Voiceover", "gender": "Male", "badge": "👨 MALE"},
        {"id": "EXAVITQu4vr4xnSDxMaL", "name": "Sarah", "desc": "Natural Professional", "gender": "Female", "badge": "👩 FEMALE"}
    ],
    "neural": [
        {"id": "hi-IN-MadhurNeural", "name": "Madhur (मधुर)", "desc": "Pure Hindi Natural Male", "gender": "Male", "badge": "👨 MALE", "flag": "🇮🇳"},
        {"id": "hi-IN-SwaraNeural", "name": "Swara (स्वरा)", "desc": "Pure Hindi Natural Female", "gender": "Female", "badge": "👩 FEMALE", "flag": "🇮🇳"},
        {"id": "en-IN-PrabhatNeural", "name": "Prabhat", "desc": "Indian English Male", "gender": "Male", "badge": "👨 MALE", "flag": "🇮🇳"},
        {"id": "en-IN-NeerjaNeural", "name": "Neerja", "desc": "Indian English Female", "gender": "Female", "badge": "👩 FEMALE", "flag": "🇮🇳"}
    ]
}

HTML_CONTENT = """<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>VoiceBnao - Professional Text to Speech</title>
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
      --primary-glow: rgba(99, 102, 241, 0.25);
      --accent: #8b5cf6;
      --success: #10b981;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --radius: 14px;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', 'Noto Sans Devanagari', sans-serif; }
    body { background-color: var(--bg); color: var(--text); min-height: 100vh; padding: 24px 16px; display: flex; flex-direction: column; align-items: center; }
    .wrapper { width: 100%; max-width: 900px; }
    
    header {
      display: flex; align-items: center; justify-content: space-between;
      padding: 16px 24px; background: var(--surface); border: 1px solid var(--surface-border);
      border-radius: var(--radius); margin-bottom: 20px;
    }
    .logo-container { display: flex; align-items: center; gap: 12px; }
    .logo-mark {
      width: 40px; height: 40px; border-radius: 10px;
      background: linear-gradient(135deg, var(--primary), var(--accent));
      display: flex; align-items: center; justify-content: center; font-size: 20px; color: #fff;
    }
    .logo-text h1 { font-size: 1.15rem; font-weight: 700; }
    .logo-text span { color: var(--primary); }

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
    }
    .engine-btn.active.primary { color: #a5b4fc; border-color: rgba(99, 102, 241, 0.4); }

    .studio-panel {
      background: var(--surface); border: 1px solid var(--surface-border);
      border-radius: 20px; padding: 26px; display: flex; flex-direction: column; gap: 18px;
      box-shadow: 0 16px 40px rgba(0,0,0,0.4);
    }

    .api-card {
      background: rgba(99, 102, 241, 0.08); border: 1px dashed rgba(99, 102, 241, 0.35);
      border-radius: 12px; padding: 14px 18px; display: flex; flex-direction: column; gap: 8px;
    }
    .api-header { display: flex; justify-content: space-between; align-items: center; font-size: 0.85rem; font-weight: 600; color: #c7d2fe; }
    .api-header a { color: #818cf8; text-decoration: none; font-size: 0.8rem; }
    .api-input {
      background: #090c14; border: 1px solid var(--surface-border); color: #fff;
      padding: 10px 14px; border-radius: 8px; font-size: 0.9rem; outline: none; width: 100%;
    }

    .controls-grid { display: grid; grid-template-columns: 1.2fr 0.8fr; gap: 14px; }
    @media (max-width: 640px) { .controls-grid { grid-template-columns: 1fr; } }
    .field-group { display: flex; flex-direction: column; gap: 8px; }
    .field-label { font-size: 0.82rem; font-weight: 600; color: var(--text-muted); display: flex; justify-content: space-between; }
    
    select, textarea {
      width: 100%; background: #090c14; border: 1px solid var(--surface-border);
      color: #fff; padding: 12px 14px; border-radius: 10px; font-size: 0.95rem; outline: none;
    }
    textarea { height: 180px; resize: vertical; line-height: 1.6; }

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
      background: rgba(99, 102, 241, 0.08); border: 1px solid rgba(99, 102, 241, 0.3);
      border-radius: 16px; padding: 20px; display: none; flex-direction: column; gap: 14px;
    }
    .player-card.active { display: flex; }
    
    audio { width: 100%; }

    .btn-download-mp3 {
      background: linear-gradient(135deg, #10b981, #059669);
      color: white; border: none; padding: 14px; border-radius: 10px;
      font-size: 0.95rem; font-weight: 700; cursor: pointer; text-align: center;
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
          <h1>VoiceBnao <span>AI</span></h1>
        </div>
      </div>
      <div style="font-size:0.75rem; color:#10b981; font-weight:700;">● SYSTEM READY</div>
    </header>

    <div class="engine-switcher">
      <button class="engine-btn active primary" id="btnEleven" onclick="switchEngine('eleven')">
        ✨ 1. ElevenLabs (Adam / Charlie)
      </button>
      <button class="engine-btn" id="btnNeural" onclick="switchEngine('neural')">
        ⚡ 2. Free Neural Engine (Madhur)
      </button>
    </div>

    <main class="studio-panel">
      <div class="api-card" id="apiCard">
        <div class="api-header">
          <span>ElevenLabs API Key:</span>
          <a href="https://elevenlabs.io" target="_blank">Get Free Key (10k Chars) ↗</a>
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
            <span>Speed Control: <strong id="speedVal" style="color:var(--primary);">1.0x</strong></span>
          </label>
          <div class="slider-container">
            <input type="range" id="speedSlider" min="0.5" max="1.5" step="0.05" value="1.0" oninput="onSpeedChange(this.value)">
          </div>
        </div>
      </div>

      <div class="field-group">
        <label class="field-label">
          <span>Script Text:</span>
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
      document.getElementById('apiKeyInput').value = localStorage.getItem('sv_eleven_key') || '';
      document.getElementById('scriptText').value = ``;
      updateCounters()

      document.getElementById('scriptText').addEventListener('input', updateCounters);
      switchEngine('eleven');

      const audio = document.getElementById('audioElement');
      audio.addEventListener('play', () => {
        audio.playbackRate = parseFloat(document.getElementById('speedSlider').value);
      });
    }

    function saveKey(k) {
      localStorage.setItem('sv_eleven_key', k.trim());
    }

    function onSpeedChange(v) {
      document.getElementById('speedVal').textContent = parseFloat(v).toFixed(2) + 'x';
      const audio = document.getElementById('audioElement');
      if (audio) {
        audio.playbackRate = parseFloat(v);
      }
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
        alert('Please enter your ElevenLabs API Key or switch to Free Neural Engine tab.');
        document.getElementById('apiKeyInput').focus();
        return;
      }

      const btn = document.getElementById('generateBtn');
      btn.disabled = true;
      btn.innerHTML = '<span>⏳ Generating Voice at ' + speed.toFixed(2) + 'x...</span>';

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
          throw new Error(data.error || 'Failed to generate audio');
        }

        const audioRes = await fetch(data.audio_url);
        currentBlob = await audioRes.blob();
        const blobUrl = URL.createObjectURL(currentBlob);

        const player = document.getElementById('audioElement');
        player.src = blobUrl;
        
        player.playbackRate = speed;
        player.play();

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
      a.download = `voice_${Date.now()}.mp3`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    }

    window.onload = init;
  </script>
</body>
</html>
"""

def apply_speed_ffmpeg(file_path, speed):
    if abs(speed - 1.0) < 0.03:
        return
    temp_speed = str(file_path) + ".spd.mp3"
    speed_clamped = max(0.5, min(2.0, speed))
    try:
        cmd = [
            "ffmpeg", "-y", "-i", str(file_path),
            "-filter:a", f"atempo={speed_clamped:.2f}",
            "-vn", temp_speed
        ]
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if res.returncode == 0 and os.path.exists(temp_speed) and os.path.getsize(temp_speed) > 500:
            os.replace(temp_speed, file_path)
    except Exception:
        if os.path.exists(temp_speed):
            os.remove(temp_speed)

def generate_elevenlabs(text, voice_id, speed, api_key, out_path):
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

    apply_speed_ffmpeg(out_path, speed)

def generate_edge(text, voice_id, speed, out_path):
    pct = int(round((speed - 1.0) * 100))
    rate_str = f"+{pct}%" if pct >= 0 else f"{pct}%"
    async def _run():
        comm = edge_tts.Communicate(text, voice_id, rate=rate_str)
        await comm.save(out_path)
    asyncio.run(_run())

def generate_google_clean(text, lang_code, speed, out_path):
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
                    u = f"https://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&tl={lang_code}&q={urllib.parse.quote(sub)}"
                    req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(req, timeout=10) as r: audio_bytes.extend(r.read())
                sub = w
        if sub:
            u = f"https://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&tl={lang_code}&q={urllib.parse.quote(sub)}"
            req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as r: audio_bytes.extend(r.read())

    with open(out_path, "wb") as f:
        f.write(audio_bytes)

    apply_speed_ffmpeg(out_path, speed)

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
            speed = float(body.get("speed", 1.0))
            key = body.get("api_key", "").strip()

            is_safe, reason = check_content_safety(text)
            if not is_safe:
                self.send_response(400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"error": reason}).encode('utf-8'))
                return

            h = hashlib.md5(f"{eng}_{text}_{voice}_{speed}".encode()).hexdigest()
            out_file = AUDIO_DIR / f"{h}.mp3"

            try:
                if not out_file.exists():
                    if eng == "eleven":
                        generate_elevenlabs(text, voice, speed, key, str(out_file))
                    else:
                        try:
                            generate_edge(text, voice, speed, str(out_file))
                        except Exception:
                            lang = "hi" if "hi-" in voice else "en"
                            generate_google_clean(text, lang, speed, str(out_file))

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

print(f"🚀 VoiceBnao running on port {PORT}")
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    httpd.serve_forever()
