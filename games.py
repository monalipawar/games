"""
OrbitParkour — a cosmic endless-runner parkour game
Part of Monali's App Universe

Run with: streamlit run OrbitParkour.py
"""

import streamlit as st
import streamlit.components.v1 as components
import json
import os
from datetime import datetime

# ---------------------------------------------------------------------------
# Config & persistence
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="OrbitParkour",
    page_icon="🪐",
    layout="wide",
    initial_sidebar_state="collapsed",
)

SCORES_FILE = "orbitparkour_scores.json"


def load_scores():
    if os.path.exists(SCORES_FILE):
        try:
            with open(SCORES_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {"high_score": 0, "history": []}
    return {"high_score": 0, "history": []}


def save_scores(data):
    with open(SCORES_FILE, "w") as f:
        json.dump(data, f, indent=2)


if "scores" not in st.session_state:
    st.session_state.scores = load_scores()

# ---------------------------------------------------------------------------
# THEMES — consistent with App Universe design system
# ---------------------------------------------------------------------------
THEMES = {
    "Default": {"primary": "#7C4DFF", "secondary": "#00E5FF", "accent": "#FF4DA6", "bg1": "#0a0e27", "bg2": "#1a1445"},
    "Cyberpunk": {"primary": "#FF2E92", "secondary": "#00FFF0", "accent": "#FFE600", "bg1": "#0d0221", "bg2": "#1f0140"},
    "Sunset": {"primary": "#FF6B6B", "secondary": "#FFB347", "accent": "#FF3CAC", "bg1": "#1a0e2e", "bg2": "#3d1a4a"},
    "Ocean": {"primary": "#00C9FF", "secondary": "#4FFBDF", "accent": "#0083FE", "bg1": "#031a2e", "bg2": "#0a3d5c"},
    "Midnight": {"primary": "#5C6BC0", "secondary": "#9575CD", "accent": "#EC407A", "bg1": "#060818", "bg2": "#131a3a"},
}

if "opk_theme" not in st.session_state:
    st.session_state.opk_theme = "Default"

with st.sidebar:
    st.markdown("### 🎨 Theme")
    st.session_state.opk_theme = st.selectbox(
        "Choose a theme", list(THEMES.keys()),
        index=list(THEMES.keys()).index(st.session_state.opk_theme)
    )
    st.markdown("---")
    st.markdown(f"### 🏆 High Score\n# {st.session_state.scores['high_score']}")
    if st.session_state.scores["history"]:
        st.markdown("### 📜 Recent Runs")
        for run in reversed(st.session_state.scores["history"][-8:]):
            st.caption(f"{run['score']} pts — {run['date']}")
    if st.button("🗑️ Reset Scores"):
        st.session_state.scores = {"high_score": 0, "history": []}
        save_scores(st.session_state.scores)
        st.rerun()

t = THEMES[st.session_state.opk_theme]

# ---------------------------------------------------------------------------
# Global cosmic glassmorphism CSS
# ---------------------------------------------------------------------------
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');

html, body, [class*="css"] {{
    font-family: 'Outfit', sans-serif;
}}

.stApp {{
    background: radial-gradient(ellipse at top, {t['bg2']} 0%, {t['bg1']} 60%, #000000 100%);
}}

.opk-title {{
    text-align: center;
    font-size: 3rem;
    font-weight: 800;
    background: linear-gradient(90deg, {t['primary']}, {t['secondary']}, {t['accent']});
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0;
    letter-spacing: 2px;
}}

.opk-subtitle {{
    text-align: center;
    color: rgba(255,255,255,0.6);
    font-weight: 300;
    margin-top: 0;
    margin-bottom: 1.2rem;
}}

.opk-glass {{
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 20px;
    padding: 10px;
    backdrop-filter: blur(12px);
    box-shadow: 0 8px 32px rgba(0,0,0,0.4);
}}

section[data-testid="stSidebar"] {{
    background: rgba(10,14,39,0.85);
    backdrop-filter: blur(10px);
    border-right: 1px solid rgba(255,255,255,0.08);
}}
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="opk-title">🪐 ORBITPARKOUR</p>', unsafe_allow_html=True)
st.markdown('<p class="opk-subtitle">Dash across the asteroid belt — jump, slide, survive.</p>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Game canvas (HTML5 canvas embedded via components — required for real-time
# input & animation loop, which Streamlit's rerun model can't drive smoothly)
# ---------------------------------------------------------------------------
game_html = f"""
<!DOCTYPE html>
<html>
<head>
<style>
  html, body {{
    margin: 0; padding: 0; overflow: hidden;
    font-family: 'Outfit', sans-serif;
    background: transparent;
  }}
  #wrap {{
    position: relative;
    width: 100%;
    max-width: 900px;
    margin: 0 auto;
  }}
  canvas {{
    display: block;
    width: 100%;
    background: linear-gradient(180deg, {t['bg2']} 0%, {t['bg1']} 100%);
    border-radius: 18px;
    border: 1px solid rgba(255,255,255,0.15);
    box-shadow: 0 8px 40px rgba(0,0,0,0.5), inset 0 0 60px rgba(124,77,255,0.08);
  }}
  #hud {{
    position: absolute;
    top: 14px; left: 20px; right: 20px;
    display: flex;
    justify-content: space-between;
    color: white;
    font-weight: 600;
    font-size: 18px;
    text-shadow: 0 2px 8px rgba(0,0,0,0.8);
    pointer-events: none;
  }}
  #overlay {{
    position: absolute;
    inset: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    color: white;
    background: rgba(5,5,20,0.55);
    border-radius: 18px;
    backdrop-filter: blur(6px);
  }}
  #overlay h1 {{
    font-size: 2.2rem;
    margin: 0 0 8px 0;
    background: linear-gradient(90deg, {t['primary']}, {t['secondary']});
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }}
  #overlay p {{ opacity: 0.75; margin: 4px 0; font-weight: 300; }}
  #startBtn {{
    margin-top: 16px;
    padding: 12px 28px;
    font-size: 16px;
    font-weight: 600;
    font-family: 'Outfit', sans-serif;
    color: white;
    background: linear-gradient(90deg, {t['primary']}, {t['accent']});
    border: none;
    border-radius: 999px;
    cursor: pointer;
    box-shadow: 0 4px 20px rgba(124,77,255,0.5);
  }}
  #startBtn:hover {{ filter: brightness(1.15); }}
  .hint {{ font-size: 13px; opacity: 0.55; margin-top: 10px; }}
</style>
</head>
<body>
<div id="wrap">
  <div id="hud">
    <span id="scoreLabel">Score: 0</span>
    <span id="bestLabel">Best: {st.session_state.scores['high_score']}</span>
  </div>
  <canvas id="game" width="900" height="420"></canvas>
  <div id="overlay">
    <h1>🪐 ORBITPARKOUR</h1>
    <p>Jump asteroids. Slide under debris. Dodge flyers. Don't crash.</p>
    <button id="startBtn">▶ Start Run</button>
    <p class="hint">SPACE = Jump &nbsp;•&nbsp; Hold ↑ / Tap-top = Fly &nbsp;•&nbsp; Hold ↓ / Tap-bottom = Slide</p>
  </div>
</div>

<script>
const canvas = document.getElementById('game');
const ctx = canvas.getContext('2d');
const overlay = document.getElementById('overlay');
const startBtn = document.getElementById('startBtn');
const scoreLabel = document.getElementById('scoreLabel');
const bestLabel = document.getElementById('bestLabel');

const COLORS = {{
  primary: "{t['primary']}",
  secondary: "{t['secondary']}",
  accent: "{t['accent']}"
}};

let W = canvas.width, H = canvas.height;
const groundY = H - 70;

let stars = [];
for (let i = 0; i < 90; i++) {{
  stars.push({{
    x: Math.random() * W,
    y: Math.random() * (H - 90),
    r: Math.random() * 1.6 + 0.3,
    s: Math.random() * 0.6 + 0.15
  }});
}}

let player, obstacles, particles, gameSpeed, score, running, gameOver, spawnTimer, elapsed;
let thrusting = false;
const ceilingY = 40;

function resetGame() {{
  player = {{
    x: 120, y: groundY, w: 34, h: 44,
    vy: 0, sliding: false,
    baseH: 44, slideH: 24, tilt: 0
  }};
  obstacles = [];
  particles = [];
  gameSpeed = 3.6;
  score = 0;
  spawnTimer = 75;
  elapsed = 0;
  running = false;
  gameOver = false;
  thrusting = false;
}}
resetGame();

function flyStart() {{
  if (running && !player.sliding) thrusting = true;
}}
function flyEnd() {{ thrusting = false; }}
function jumpImpulse() {{
  if (running && !player.sliding) {{
    player.vy = -9.5;
  }}
}}
function slideStart() {{
  if (running && player.y >= groundY - 1) player.sliding = true;
}}
function slideEnd() {{ player.sliding = false; }}

document.addEventListener('keydown', (e) => {{
  if (e.code === 'Space') {{ e.preventDefault(); if (!e.repeat) jumpImpulse(); }}
  if (e.code === 'ArrowUp') {{ e.preventDefault(); flyStart(); }}
  if (e.code === 'ArrowDown') {{ e.preventDefault(); slideStart(); }}
}});
document.addEventListener('keyup', (e) => {{
  if (e.code === 'ArrowUp') flyEnd();
  if (e.code === 'ArrowDown') slideEnd();
}});

canvas.addEventListener('touchstart', (e) => {{
  const rect = canvas.getBoundingClientRect();
  const touchY = e.touches[0].clientY - rect.top;
  if (touchY < rect.height / 2) flyStart(); else slideStart();
}});
canvas.addEventListener('touchend', () => {{ flyEnd(); slideEnd(); }});
canvas.addEventListener('mousedown', (e) => {{
  const rect = canvas.getBoundingClientRect();
  const clickY = e.clientY - rect.top;
  if (clickY < rect.height / 2) flyStart(); else slideStart();
}});
canvas.addEventListener('mouseup', () => {{ flyEnd(); slideEnd(); }});

function spawnObstacle() {{
  const type = Math.random();
  if (type < 0.4) {{
    // ground asteroid (jump/fly over)
    const size = 30 + Math.random() * 26;
    obstacles.push({{ x: W + 20, y: groundY - size, w: size, h: size, type: 'rock' }});
  }} else if (type < 0.65) {{
    // floating debris (slide under, or stay low)
    const h = 26;
    obstacles.push({{ x: W + 20, y: groundY - player.baseH - 6, w: 46, h: h, type: 'debris' }});
  }} else {{
    // airborne flyer — sits at a random altitude, must dodge above/below it
    const size = 34 + Math.random() * 20;
    const minY = ceilingY + 10;
    const maxY = groundY - player.baseH - size - 10;
    const y = minY + Math.random() * Math.max(10, maxY - minY);
    obstacles.push({{ x: W + 20, y: y, w: size, h: size, type: 'flyer' }});
  }}
}}

function rectsOverlap(a, b) {{
  return a.x < b.x + b.w && a.x + a.w > b.x && a.y < b.y + b.h && a.y + a.h > b.y;
}}

function update(dt) {{
  if (!running) return;
  elapsed++;
  gameSpeed = Math.min(7.5, 3.6 + elapsed * 0.0008);
  score += Math.floor(gameSpeed / 3);

  // player physics
  const curH = player.sliding ? player.slideH : player.baseH;
  player.h = curH;
  if (!player.sliding) {{
    if (thrusting) {{
      player.vy -= 0.85 * dt;
      if (player.vy < -5.5) player.vy = -5.5;
    }} else {{
      player.vy += 0.85 * dt;
      if (player.vy > 9) player.vy = 9;
    }}
    player.y += player.vy * dt;
    const topLimit = ceilingY + curH;
    if (player.y < topLimit) {{ player.y = topLimit; player.vy = 0; }}
    if (player.y >= groundY) {{ player.y = groundY; player.vy = 0; }}

    // thrust trail particles (Geometry Dash ship style)
    if (running) {{
      particles.push({{
        x: player.x - 2,
        y: player.y - curH / 2 + (Math.random() * 10 - 5),
        vx: -gameSpeed * 0.6 - Math.random() * 1.5,
        vy: (Math.random() - 0.5) * 1.5,
        life: 22,
        maxLife: 22,
        r: 2 + Math.random() * 2.5
      }});
    }}
  }} else {{
    player.y = groundY;
    player.vy = 0;
  }}
  for (let p of particles) {{
    p.x += p.vx * dt; p.y += p.vy * dt; p.life -= dt;
  }}
  particles = particles.filter(p => p.life > 0);

  const targetTilt = Math.max(-0.5, Math.min(0.5, -player.vy * 0.06));
  player.tilt += (targetTilt - player.tilt) * Math.min(1, 0.25 * dt);

  // spawn
  spawnTimer -= dt;
  if (spawnTimer <= 0) {{
    spawnObstacle();
    spawnTimer = Math.max(60, 100 - elapsed * 0.01) + Math.random() * 35;
  }}

  // move obstacles
  for (let o of obstacles) o.x -= gameSpeed * dt;
  obstacles = obstacles.filter(o => o.x + o.w > -20);

  // collision
  const playerBox = {{
    x: player.x + 6, y: player.y - curH + 6,
    w: player.w - 12, h: curH - 10
  }};
  for (let o of obstacles) {{
    if (rectsOverlap(playerBox, o)) {{
      endGame();
      break;
    }}
  }}

  // stars parallax
  for (let s of stars) {{
    s.x -= s.s * (gameSpeed / 3) * dt;
    if (s.x < 0) {{ s.x = W; s.y = Math.random() * (H - 90); }}
  }}

  scoreLabel.textContent = 'Score: ' + score;
}}

function drawRoundedRect(x, y, w, h, r) {{
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}}

function draw() {{
  ctx.clearRect(0, 0, W, H);

  // stars
  ctx.fillStyle = 'rgba(255,255,255,0.7)';
  for (let s of stars) {{
    ctx.globalAlpha = 0.4 + s.s;
    ctx.beginPath();
    ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
    ctx.fill();
  }}
  ctx.globalAlpha = 1;

  // ground
  const grad = ctx.createLinearGradient(0, groundY, 0, H);
  grad.addColorStop(0, COLORS.primary + '55');
  grad.addColorStop(1, 'rgba(0,0,0,0)');
  ctx.fillStyle = grad;
  ctx.fillRect(0, groundY, W, H - groundY);
  ctx.strokeStyle = COLORS.secondary + 'aa';
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(0, groundY);
  ctx.lineTo(W, groundY);
  ctx.stroke();

  // obstacles
  for (let o of obstacles) {{
    if (o.type === 'rock') {{
      ctx.fillStyle = COLORS.accent;
      ctx.beginPath();
      ctx.arc(o.x + o.w/2, o.y + o.h/2, o.w/2, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = 'rgba(255,255,255,0.3)';
      ctx.stroke();
    }} else if (o.type === 'debris') {{
      ctx.fillStyle = COLORS.secondary;
      drawRoundedRect(o.x, o.y, o.w, o.h, 8);
      ctx.fill();
      ctx.strokeStyle = 'rgba(255,255,255,0.4)';
      ctx.stroke();
    }} else {{
      // flyer — spiky airborne asteroid
      ctx.save();
      ctx.translate(o.x + o.w/2, o.y + o.h/2);
      ctx.fillStyle = COLORS.primary;
      ctx.beginPath();
      const spikes = 8, rOuter = o.w/2, rInner = o.w/3.2;
      for (let i = 0; i < spikes * 2; i++) {{
        const r = i % 2 === 0 ? rOuter : rInner;
        const a = (Math.PI / spikes) * i;
        ctx.lineTo(Math.cos(a) * r, Math.sin(a) * r);
      }}
      ctx.closePath();
      ctx.fill();
      ctx.strokeStyle = 'rgba(255,255,255,0.35)';
      ctx.stroke();
      ctx.restore();
    }}
  }}

  // thrust particle trail
  for (let p of particles) {{
    const alpha = p.life / p.maxLife;
    ctx.globalAlpha = alpha * 0.8;
    ctx.fillStyle = COLORS.secondary;
    ctx.beginPath();
    ctx.arc(p.x, p.y, p.r * alpha, 0, Math.PI * 2);
    ctx.fill();
  }}
  ctx.globalAlpha = 1;

  // player (Geometry Dash-style ship: tilts with velocity, glows when thrusting)
  const curH2 = player.sliding ? player.slideH : player.baseH;
  const cx = player.x + player.w / 2;
  const cy = player.y - curH2 / 2;
  const tilt = player.tilt;

  ctx.save();
  ctx.translate(cx, cy);
  ctx.rotate(tilt);

  if (thrusting) {{
    ctx.shadowColor = COLORS.secondary;
    ctx.shadowBlur = 18;
  }}

  const pg = ctx.createLinearGradient(-player.w/2, -curH2/2, -player.w/2, curH2/2);
  pg.addColorStop(0, COLORS.primary);
  pg.addColorStop(1, COLORS.secondary);
  ctx.fillStyle = pg;
  drawRoundedRect(-player.w/2, -curH2/2, player.w, curH2, 10);
  ctx.fill();
  ctx.strokeStyle = 'rgba(255,255,255,0.6)';
  ctx.lineWidth = 1.5;
  ctx.stroke();

  ctx.shadowBlur = 0;

  // small rear thruster flame when flying
  if (thrusting) {{
    ctx.fillStyle = COLORS.accent;
    ctx.beginPath();
    ctx.moveTo(-player.w/2, -6);
    ctx.lineTo(-player.w/2 - 12 - Math.random() * 3, 0);
    ctx.lineTo(-player.w/2, 6);
    ctx.closePath();
    ctx.fill();
  }}

  // visor
  ctx.fillStyle = 'rgba(255,255,255,0.85)';
  ctx.beginPath();
  ctx.arc(2, -curH2 * 0.18, 5, 0, Math.PI * 2);
  ctx.fill();

  ctx.restore();

  if (gameOver) {{
    ctx.fillStyle = 'rgba(5,5,20,0.5)';
    ctx.fillRect(0, 0, W, H);
  }}
}}

let lastTime = null;
function loop(ts) {{
  if (lastTime === null) lastTime = ts;
  let dt = (ts - lastTime) / (1000 / 60); // normalize to 60fps units
  lastTime = ts;
  dt = Math.max(0.1, Math.min(dt, 2.5)); // clamp to avoid big jumps on tab-switch/lag
  update(dt);
  draw();
  requestAnimationFrame(loop);
}}

function endGame() {{
  running = false;
  gameOver = true;
  overlay.style.display = 'flex';
  const best = Math.max(score, parseInt(bestLabel.textContent.split(': ')[1]));
  bestLabel.textContent = 'Best: ' + best;
  document.getElementById('startBtn').textContent = '↻ Run Again';
  overlay.querySelector('h1').textContent = '💥 Crashed!';
  overlay.querySelector('p').textContent = 'Score: ' + score;
  window.parent.postMessage({{ type: 'orbitparkour_score', score: score }}, '*');
}}

startBtn.addEventListener('click', () => {{
  resetGame();
  running = true;
  gameOver = false;
  overlay.style.display = 'none';
}});

requestAnimationFrame(loop);
</script>
</body>
</html>
"""

components.html(game_html, height=460, scrolling=False)

st.markdown("""
<div style="text-align:center; margin-top: 14px; color: rgba(255,255,255,0.45); font-size: 13px;">
Controls: <b>Space</b> to jump, <b>hold ↑</b> to fly, <b>hold ↓</b> to slide — or tap/hold top/bottom half of the canvas on mobile.
</div>
""", unsafe_allow_html=True)

st.markdown("---")

col1, col2 = st.columns([2, 1])
with col1:
    st.markdown("#### 📝 Log your run")
    st.caption("Since the canvas game runs in-browser, enter your score here after a run to save it to your history.")
with col2:
    manual_score = st.number_input("Score", min_value=0, step=10, label_visibility="collapsed")
    if st.button("💾 Save Score", use_container_width=True):
        st.session_state.scores["history"].append({
            "score": int(manual_score),
            "date": datetime.now().strftime("%Y-%m-%d %H:%M")
        })
        if manual_score > st.session_state.scores["high_score"]:
            st.session_state.scores["high_score"] = int(manual_score)
            st.success("🏆 New high score!")
        save_scores(st.session_state.scores)
        st.rerun()
