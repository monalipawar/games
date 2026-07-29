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
# ---------------------------------------------------------------------------
# Game canvas (Three.js WebGL scene embedded via components — required for
# real-time 3D rendering & input, which Streamlit's rerun model can't drive)
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
  #gameCanvasHolder {{
    width: 100%;
    aspect-ratio: 900 / 420;
    border-radius: 18px;
    overflow: hidden;
    border: 1px solid rgba(255,255,255,0.15);
    box-shadow: 0 8px 40px rgba(0,0,0,0.5), inset 0 0 60px rgba(124,77,255,0.08);
    background: linear-gradient(180deg, {t['bg2']} 0%, {t['bg1']} 100%);
  }}
  #gameCanvasHolder canvas {{ display: block; width: 100% !important; height: 100% !important; }}
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
  #loadingMsg {{
    position: absolute; inset: 0; display: flex; align-items: center; justify-content: center;
    color: rgba(255,255,255,0.6); font-size: 14px;
  }}
</style>
</head>
<body>
<div id="wrap">
  <div id="gameCanvasHolder">
    <div id="loadingMsg">Loading 3D engine…</div>
  </div>
  <div id="hud">
    <span id="scoreLabel">Score: 0</span>
    <span id="bestLabel">Best: {st.session_state.scores['high_score']}</span>
  </div>
  <div id="bossBarWrap" style="
    position:absolute; top:44px; left:50%; transform:translateX(-50%);
    width:60%; max-width:420px; display:none; z-index:4;">
    <div style="text-align:center; color:#ff3355; font-size:12px; font-weight:600; text-shadow:0 2px 6px rgba(0,0,0,0.8); margin-bottom:3px;">⚠ BOSS</div>
    <div style="background:rgba(255,255,255,0.15); border-radius:8px; height:12px; overflow:hidden; border:1px solid rgba(255,255,255,0.3);">
      <div id="bossBarFill" style="background:linear-gradient(90deg,#ff3355,#ffe600); height:100%; width:100%; transition:width 0.2s;"></div>
    </div>
  </div>
  <button id="shootBtn" style="
    position:absolute; bottom:14px; right:14px; z-index:5;
    width:56px; height:56px; border-radius:50%; border:2px solid rgba(255,255,255,0.4);
    background:linear-gradient(135deg,{t['accent']},{t['primary']}); color:white; font-size:22px;
    box-shadow:0 4px 16px rgba(0,0,0,0.5); cursor:pointer;">🔫</button>
  <div id="overlay">
    <h1>🪐 ORBITPARKOUR</h1>
    <p>Jump asteroids. Slide under debris. Shoot back. Don't crash.</p>
    <button id="startBtn">▶ Start Run</button>
    <p class="hint">SPACE = Jump &nbsp;•&nbsp; Hold ↑ / Top = Fly &nbsp;•&nbsp; ↓ / Bottom = Slide &nbsp;•&nbsp; ← → / A D = Steer &nbsp;•&nbsp; F / 🔫 = Shoot</p>
  </div>
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
(function() {{

const COLORS = {{
  primary: "{t['primary']}",
  secondary: "{t['secondary']}",
  accent: "{t['accent']}",
  bg1: "{t['bg1']}",
  bg2: "{t['bg2']}"
}};

function hexToInt(h) {{ return parseInt(h.replace('#',''), 16); }}

const holder = document.getElementById('gameCanvasHolder');
const overlay = document.getElementById('overlay');
const startBtn = document.getElementById('startBtn');
const scoreLabel = document.getElementById('scoreLabel');
const bestLabel = document.getElementById('bestLabel');
const shootBtn = document.getElementById('shootBtn');
const bossBarWrap = document.getElementById('bossBarWrap');
const bossBarFill = document.getElementById('bossBarFill');

const BASE_W = 900, BASE_H = 420;

// ---------- scene setup ----------
const scene = new THREE.Scene();
scene.fog = new THREE.Fog(hexToInt(COLORS.bg1), 20, 95);

const camera = new THREE.PerspectiveCamera(75, BASE_W / BASE_H, 0.1, 200);
camera.position.set(0, 3.6, 8.5);
camera.lookAt(0, 2.6, -14);

const renderer = new THREE.WebGLRenderer({{ antialias: true, alpha: true }});
renderer.setSize(BASE_W, BASE_H);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
document.getElementById('loadingMsg').remove();
holder.appendChild(renderer.domElement);

// lights
scene.add(new THREE.AmbientLight(0xffffff, 0.55));
const dirLight = new THREE.DirectionalLight(0xffffff, 0.9);
dirLight.position.set(-6, 12, 6);
scene.add(dirLight);
const rimLight = new THREE.PointLight(hexToInt(COLORS.secondary), 1.2, 30);
rimLight.position.set(0, 4, 6);
scene.add(rimLight);

// starfield
const starGeo = new THREE.BufferGeometry();
const starCount = 500;
const starPos = new Float32Array(starCount * 3);
for (let i = 0; i < starCount; i++) {{
  starPos[i*3] = (Math.random() - 0.5) * 120;
  starPos[i*3+1] = Math.random() * 60 - 5;
  starPos[i*3+2] = -Math.random() * 150 + 10;
}}
starGeo.setAttribute('position', new THREE.BufferAttribute(starPos, 3));
const starMat = new THREE.PointsMaterial({{ color: 0xffffff, size: 0.35, transparent: true, opacity: 0.8 }});
const stars = new THREE.Points(starGeo, starMat);
scene.add(stars);

// ground: scrolling grid strip segments
const groundY = 0;
const ceilingY = 9;
const groundSegs = [];
const segLen = 20;
const segCount = 6;
const trenchHalfWidth = 11.5;
const trenchWallH = 13;
for (let i = 0; i < segCount; i++) {{
  const g = new THREE.Group();
  const planeGeo = new THREE.PlaneGeometry(34, segLen);
  const planeMat = new THREE.MeshStandardMaterial({{
    color: hexToInt(COLORS.bg2), roughness: 0.8, metalness: 0.2,
    emissive: hexToInt(COLORS.primary), emissiveIntensity: 0.06
  }});
  const plane = new THREE.Mesh(planeGeo, planeMat);
  plane.rotation.x = -Math.PI / 2;
  g.add(plane);
  const gridHelper = new THREE.GridHelper(34, 17, hexToInt(COLORS.secondary), hexToInt(COLORS.primary));
  gridHelper.material.transparent = true;
  gridHelper.material.opacity = 0.35;
  g.add(gridHelper);

  // trench side walls
  const wallMat = new THREE.MeshStandardMaterial({{
    color: hexToInt(COLORS.bg2), roughness: 0.6, metalness: 0.4,
    emissive: hexToInt(COLORS.secondary), emissiveIntensity: 0.08
  }});
  const wallGeo = new THREE.PlaneGeometry(segLen, trenchWallH);
  const wallL = new THREE.Mesh(wallGeo, wallMat);
  wallL.position.set(-trenchHalfWidth, trenchWallH / 2, 0);
  wallL.rotation.y = Math.PI / 2;
  g.add(wallL);
  const wallR = new THREE.Mesh(wallGeo, wallMat.clone());
  wallR.position.set(trenchHalfWidth, trenchWallH / 2, 0);
  wallR.rotation.y = -Math.PI / 2;
  g.add(wallR);

  // horizontal trim lines on walls (greebled trench detailing)
  for (let k = 1; k <= 3; k++) {{
    const trimGeo = new THREE.PlaneGeometry(segLen, 0.12);
    const trimMat = new THREE.MeshBasicMaterial({{ color: hexToInt(COLORS.secondary), transparent: true, opacity: 0.4 }});
    const trimL = new THREE.Mesh(trimGeo, trimMat);
    trimL.position.set(-trenchHalfWidth + 0.02, k * (trenchWallH / 4), 0);
    trimL.rotation.y = Math.PI / 2;
    g.add(trimL);
    const trimR = trimL.clone();
    trimR.position.x = trenchHalfWidth - 0.02;
    trimR.rotation.y = -Math.PI / 2;
    g.add(trimR);
  }}

  g.position.set(0, groundY, -i * segLen);
  scene.add(g);
  groundSegs.push(g);
}}

// ---------- ship ----------
const shipGroup = new THREE.Group();

const bodyMat = new THREE.MeshStandardMaterial({{
  color: hexToInt(COLORS.secondary), roughness: 0.35, metalness: 0.6,
  emissive: hexToInt(COLORS.primary), emissiveIntensity: 0.25
}});
const bodyGeo = new THREE.ConeGeometry(0.55, 2.3, 8);
const body = new THREE.Mesh(bodyGeo, bodyMat);
body.rotation.x = Math.PI / 2;
shipGroup.add(body);

const wingMat = new THREE.MeshStandardMaterial({{
  color: hexToInt(COLORS.accent), roughness: 0.4, metalness: 0.5
}});
const wingGeo = new THREE.BoxGeometry(1.9, 0.08, 0.7);
const wingL = new THREE.Mesh(wingGeo, wingMat);
wingL.position.set(-0.9, 0, 0.2);
wingL.rotation.z = 0.12;
shipGroup.add(wingL);
const wingR = wingL.clone();
wingR.position.x = 0.9;
wingR.rotation.z = -0.12;
shipGroup.add(wingR);

const canopyMat = new THREE.MeshStandardMaterial({{
  color: 0xffffff, roughness: 0.05, metalness: 0.1,
  emissive: hexToInt(COLORS.secondary), emissiveIntensity: 0.3,
  transparent: true, opacity: 0.85
}});
const canopyGeo = new THREE.SphereGeometry(0.28, 12, 12);
const canopy = new THREE.Mesh(canopyGeo, canopyMat);
canopy.position.set(0, 0.15, 0.5);
shipGroup.add(canopy);

const engineGlow = new THREE.PointLight(hexToInt(COLORS.accent), 0, 6);
engineGlow.position.set(0, 0, -1.3);
shipGroup.add(engineGlow);

const flameGeo = new THREE.ConeGeometry(0.22, 0.9, 8);
const flameMat = new THREE.MeshBasicMaterial({{ color: hexToInt(COLORS.accent), transparent: true, opacity: 0.9 }});
const flame = new THREE.Mesh(flameGeo, flameMat);
flame.rotation.x = -Math.PI / 2;
flame.position.set(0, 0, -1.5);
flame.visible = false;
shipGroup.add(flame);

scene.add(shipGroup);

// ground contact shadow
const shadowGeo = new THREE.CircleGeometry(0.9, 20);
const shadowMat = new THREE.MeshBasicMaterial({{ color: 0x000000, transparent: true, opacity: 0.35 }});
const groundShadow = new THREE.Mesh(shadowGeo, shadowMat);
groundShadow.rotation.x = -Math.PI / 2;
groundShadow.position.y = groundY + 0.02;
scene.add(groundShadow);

// thrust particles (small glowing sprites reused as a pool)
const trailMat = new THREE.SpriteMaterial({{ color: hexToInt(COLORS.secondary), transparent: true, opacity: 0.8 }});
let particles = [];

// obstacle pool helpers
function makeRock(size) {{
  const geo = new THREE.IcosahedronGeometry(size, 0);
  const mat = new THREE.MeshStandardMaterial({{
    color: hexToInt(COLORS.accent), roughness: 0.6, metalness: 0.3,
    emissive: hexToInt(COLORS.accent), emissiveIntensity: 0.15, flatShading: true
  }});
  return new THREE.Mesh(geo, mat);
}}
function makeDebris(w, h, d) {{
  const geo = new THREE.BoxGeometry(w, h, d);
  const mat = new THREE.MeshStandardMaterial({{
    color: hexToInt(COLORS.secondary), roughness: 0.5, metalness: 0.4,
    emissive: hexToInt(COLORS.secondary), emissiveIntensity: 0.2
  }});
  return new THREE.Mesh(geo, mat);
}}
function makeFlyer(size) {{
  const geo = new THREE.OctahedronGeometry(size, 0);
  const mat = new THREE.MeshStandardMaterial({{
    color: hexToInt(COLORS.primary), roughness: 0.5, metalness: 0.5,
    emissive: hexToInt(COLORS.primary), emissiveIntensity: 0.25, flatShading: true
  }});
  return new THREE.Mesh(geo, mat);
}}
function makeShooter(size) {{
  const geo = new THREE.DodecahedronGeometry(size, 0);
  const mat = new THREE.MeshStandardMaterial({{
    color: 0xff3355, roughness: 0.4, metalness: 0.6,
    emissive: 0xff3355, emissiveIntensity: 0.5, flatShading: true
  }});
  return new THREE.Mesh(geo, mat);
}}
function makePlayerBolt() {{
  const geo = new THREE.SphereGeometry(0.16, 8, 8);
  const mat = new THREE.MeshBasicMaterial({{ color: hexToInt(COLORS.secondary) }});
  const m = new THREE.Mesh(geo, mat);
  const light = new THREE.PointLight(hexToInt(COLORS.secondary), 0.8, 3);
  m.add(light);
  return m;
}}
function makeEnemyBolt() {{
  const geo = new THREE.SphereGeometry(0.18, 8, 8);
  const mat = new THREE.MeshBasicMaterial({{ color: 0xff3355 }});
  const m = new THREE.Mesh(geo, mat);
  const light = new THREE.PointLight(0xff3355, 0.8, 3);
  m.add(light);
  return m;
}}

function makeBoss() {{
  const g = new THREE.Group();
  const coreMat = new THREE.MeshStandardMaterial({{
    color: 0x1a0510, roughness: 0.35, metalness: 0.8,
    emissive: 0xff3355, emissiveIntensity: 0.35, flatShading: true
  }});
  const core = new THREE.Mesh(new THREE.IcosahedronGeometry(2.6, 1), coreMat);
  g.add(core);

  const eyeMat = new THREE.MeshBasicMaterial({{ color: 0xffe600 }});
  const eye = new THREE.Mesh(new THREE.SphereGeometry(0.55, 12, 12), eyeMat);
  eye.position.set(0, 0.2, 2.3);
  g.add(eye);
  const eyeLight = new THREE.PointLight(0xffe600, 1.5, 8);
  eyeLight.position.copy(eye.position);
  g.add(eyeLight);

  const spikeMat = new THREE.MeshStandardMaterial({{
    color: 0xff3355, roughness: 0.5, metalness: 0.6, emissive: 0xff3355, emissiveIntensity: 0.3
  }});
  for (let i = 0; i < 6; i++) {{
    const spike = new THREE.Mesh(new THREE.ConeGeometry(0.4, 1.6, 6), spikeMat);
    const ang = (i / 6) * Math.PI * 2;
    spike.position.set(Math.cos(ang) * 2.5, Math.sin(ang) * 2.5, 0);
    spike.lookAt(spike.position.x * 2, spike.position.y * 2, 0);
    spike.rotation.x += Math.PI / 2;
    g.add(spike);
  }}
  g.userData.core = core;
  g.userData.eye = eye;
  return g;
}}

// ---------- game state ----------
let player, obstacles, gameSpeed, score, running, gameOver, spawnTimer, elapsed, thrusting;
let steerLeft = false, steerRight = false;
let downHeld = false;
let playerBolts = [], enemyBolts = [];
let shootCooldown = 0;
let boss = null, bossSpawned = false, bossActive = false;
const BOSS_TRIGGER_SCORE = 1400;

function resetGame() {{
  player = {{ x: 0, y: groundY, vy: 0, vx: 0, sliding: false, tilt: 0, roll: 0 }};
  for (const o of obstacles || []) scene.remove(o.mesh);
  obstacles = [];
  for (const p of particles) scene.remove(p.sprite);
  particles = [];
  gameSpeed = 3.6;
  score = 0;
  spawnTimer = 30;
  elapsed = 0;
  running = false;
  gameOver = false;
  thrusting = false;
  steerLeft = false;
  steerRight = false;
  downHeld = false;
  for (const b of (playerBolts || [])) scene.remove(b.mesh);
  playerBolts = [];
  for (const b of (enemyBolts || [])) scene.remove(b.mesh);
  enemyBolts = [];
  shootCooldown = 0;
  if (boss) {{ scene.remove(boss.mesh); boss = null; }}
  bossSpawned = false;
  bossActive = false;
  bossBarWrap.style.display = 'none';
  shipGroup.position.set(0, groundY + 1.2, 0);
  shipGroup.rotation.set(0, Math.PI, 0);
  shipGroup.scale.set(1, 1, 1);
  camera.position.x = 0;
  camera.up.set(0, 1, 0);
}}
resetGame();

function flyStart() {{ if (running && !downHeld) thrusting = true; }}
function flyEnd() {{ thrusting = false; }}
function jumpImpulse() {{ if (running && !downHeld) player.vy = 4.4; }}
function slideStart() {{ if (running) {{ downHeld = true; thrusting = false; }} }}
function slideEnd() {{ downHeld = false; }}

function leftStart() {{ steerLeft = true; }}
function leftEnd() {{ steerLeft = false; }}
function rightStart() {{ steerRight = true; }}
function rightEnd() {{ steerRight = false; }}
function requestShoot() {{
  if (running && shootCooldown <= 0) {{
    spawnPlayerBolt();
    shootCooldown = 14;
  }}
}}

document.addEventListener('keydown', (e) => {{
  if (e.code === 'Space') {{ e.preventDefault(); if (!e.repeat) jumpImpulse(); }}
  if (e.code === 'ArrowUp') {{ e.preventDefault(); flyStart(); }}
  if (e.code === 'ArrowDown') {{ e.preventDefault(); slideStart(); }}
  if (e.code === 'ArrowLeft' || e.code === 'KeyA') {{ e.preventDefault(); leftStart(); }}
  if (e.code === 'ArrowRight' || e.code === 'KeyD') {{ e.preventDefault(); rightStart(); }}
  if (e.code === 'KeyF') {{ e.preventDefault(); if (!e.repeat) requestShoot(); }}
}});
document.addEventListener('keyup', (e) => {{
  if (e.code === 'ArrowUp') flyEnd();
  if (e.code === 'ArrowDown') slideEnd();
  if (e.code === 'ArrowLeft' || e.code === 'KeyA') leftEnd();
  if (e.code === 'ArrowRight' || e.code === 'KeyD') rightEnd();
}});
holder.addEventListener('touchstart', (e) => {{
  const rect = holder.getBoundingClientRect();
  const touchY = e.touches[0].clientY - rect.top;
  const touchX = e.touches[0].clientX - rect.left;
  if (touchX < rect.width / 3) leftStart();
  else if (touchX > rect.width * 2 / 3) rightStart();
  else if (touchY < rect.height / 2) flyStart(); else slideStart();
}});
holder.addEventListener('touchend', () => {{ flyEnd(); slideEnd(); leftEnd(); rightEnd(); }});
holder.addEventListener('mousedown', (e) => {{
  const rect = holder.getBoundingClientRect();
  const clickX = e.clientX - rect.left;
  const clickY = e.clientY - rect.top;
  if (clickX < rect.width / 3) leftStart();
  else if (clickX > rect.width * 2 / 3) rightStart();
  else if (clickY < rect.height / 2) flyStart(); else slideStart();
}});
holder.addEventListener('mouseup', () => {{ flyEnd(); slideEnd(); leftEnd(); rightEnd(); }});
shootBtn.addEventListener('click', (e) => {{ e.stopPropagation(); requestShoot(); }});
shootBtn.addEventListener('touchstart', (e) => {{ e.stopPropagation(); e.preventDefault(); requestShoot(); }});

function spawnObstacle() {{
  const r = Math.random();
  const spawnZ = -70;
  const laneX = (Math.random() - 0.5) * 15.5;
  let mesh, type, radius;
  if (r < 0.32) {{
    const size = 0.7 + Math.random() * 0.55;
    mesh = makeRock(size);
    mesh.position.set(laneX, groundY + size * 0.85, spawnZ);
    type = 'rock'; radius = size;
  }} else if (r < 0.54) {{
    mesh = makeDebris(2.1, 0.6, 0.6);
    mesh.position.set(laneX, groundY + 2.6, spawnZ);
    type = 'debris'; radius = 0.5;
  }} else if (r < 0.78) {{
    const size = 0.75 + Math.random() * 0.45;
    const minY = ceilingY - 1.5;
    const maxY = groundY + 1.6;
    const y = maxY + Math.random() * (minY - maxY);
    mesh = makeFlyer(size);
    mesh.position.set(laneX, y, spawnZ);
    type = 'flyer'; radius = size;
  }} else {{
    const size = 0.8;
    const minY = ceilingY - 1.5;
    const maxY = groundY + 1.6;
    const y = maxY + Math.random() * (minY - maxY);
    mesh = makeShooter(size);
    mesh.position.set(laneX, y, spawnZ);
    type = 'shooter'; radius = size;
  }}
  scene.add(mesh);
  obstacles.push({{ mesh, type, radius, z: spawnZ, x: laneX, fireTimer: 40 + Math.random() * 40, hp: 1 }});
}}

function spawnPlayerBolt() {{
  const mesh = makePlayerBolt();
  mesh.position.copy(shipGroup.position);
  mesh.position.z -= 1.4;
  scene.add(mesh);
  playerBolts.push({{ mesh }});
}}

function spawnEnemyBolt(fromObstacle) {{
  const mesh = makeEnemyBolt();
  mesh.position.copy(fromObstacle.mesh.position);
  scene.add(mesh);
  const dx = shipGroup.position.x - fromObstacle.mesh.position.x;
  const dy = shipGroup.position.y - fromObstacle.mesh.position.y;
  const dz = shipGroup.position.z - fromObstacle.mesh.position.z;
  const dist = Math.sqrt(dx*dx + dy*dy + dz*dz) || 1;
  enemyBolts.push({{ mesh, vx: dx / dist, vy: dy / dist, vz: dz / dist }});
}}

function spawnBossBoltFrom(originVec, spreadX) {{
  const mesh = makeEnemyBolt();
  mesh.position.copy(originVec);
  scene.add(mesh);
  const dx = (shipGroup.position.x + spreadX) - originVec.x;
  const dy = shipGroup.position.y - originVec.y;
  const dz = shipGroup.position.z - originVec.z;
  const dist = Math.sqrt(dx*dx + dy*dy + dz*dz) || 1;
  enemyBolts.push({{ mesh, vx: dx / dist, vy: dy / dist, vz: dz / dist }});
}}

function spawnBoss() {{
  bossSpawned = true;
  bossActive = true;
  // clear the trench of normal obstacles for a clean arena
  for (const o of obstacles) scene.remove(o.mesh);
  obstacles = [];
  const mesh = makeBoss();
  mesh.position.set(0, groundY + 4.5, -45);
  scene.add(mesh);
  boss = {{ mesh, hp: 10, maxHp: 10, z: -45, phase: Math.random() * Math.PI * 2, fireTimer: 90 }};
  bossBarWrap.style.display = 'block';
  bossBarFill.style.width = '100%';
}}

function spawnParticle() {{
  const sprite = new THREE.Sprite(trailMat.clone());
  sprite.scale.set(0.35, 0.35, 0.35);
  sprite.position.copy(shipGroup.position);
  sprite.position.z += 1.3;
  sprite.position.y += (Math.random() - 0.5) * 0.3;
  scene.add(sprite);
  particles.push({{ sprite, life: 24, maxLife: 24 }});
}}

function update(dt) {{
  if (!running) return;
  elapsed++;
  gameSpeed = Math.min(7.5, 3.6 + elapsed * 0.0008);
  score += Math.floor(gameSpeed / 3);
  scoreLabel.textContent = 'Score: ' + score;

  const shipBaseY = groundY + 1.2;
  const shipTopY = ceilingY - 0.8;
  const laneLimit = 9.2;

  // horizontal steering
  const steerAccel = 1.3;
  const steerMax = 13;
  const steerDamp = 0.82;
  if (steerLeft && !steerRight) {{
    player.vx -= steerAccel * dt;
  }} else if (steerRight && !steerLeft) {{
    player.vx += steerAccel * dt;
  }} else {{
    player.vx *= Math.pow(steerDamp, dt);
  }}
  player.vx = Math.max(-steerMax, Math.min(steerMax, player.vx));
  player.x += player.vx * dt * 0.09;
  if (player.x < -laneLimit) {{ player.x = -laneLimit; player.vx = 0; }}
  if (player.x > laneLimit) {{ player.x = laneLimit; player.vx = 0; }}

  const targetRoll = Math.max(-0.35, Math.min(0.35, -player.vx * 0.045));
  player.roll += (targetRoll - player.roll) * Math.min(1, 0.3 * dt);

  // determine sliding (crouch at ground) vs descending (falling toward ground while airborne)
  const atGround = player.y <= shipBaseY + 0.08;
  player.sliding = downHeld && atGround;
  const descending = downHeld && !atGround;
  if (downHeld) thrusting = false;

  if (player.sliding) {{
    player.y = shipBaseY;
    player.vy = 0;
  }} else {{
    const climbTarget = 7.2;
    const descendTarget = -7.2;
    const holdTarget = 0;
    let targetVy = holdTarget;
    let approachRate = 0.25; // releasing settles quickly to a stop, holds altitude
    if (descending) {{ targetVy = descendTarget; approachRate = 0.10; }}
    else if (thrusting) {{ targetVy = climbTarget; approachRate = 0.10; }}
    player.vy += (targetVy - player.vy) * Math.min(1, approachRate * dt);
    player.y += player.vy * dt * 0.09;
    if (player.y < shipBaseY) {{ player.y = shipBaseY; player.vy = 0; }}
    if (player.y > shipTopY) {{ player.y = shipTopY; player.vy = 0; }}

    if (running) spawnParticle();
  }}

  shipGroup.position.y = player.y;
  shipGroup.position.x = player.x;
  const altRatio = Math.max(0, Math.min(1, (player.y - shipBaseY) / (shipTopY - shipBaseY)));
  const targetTilt = Math.max(-0.4, Math.min(0.4, -player.vy * 0.05));
  player.tilt += (targetTilt - player.tilt) * Math.min(1, 0.25 * dt);
  shipGroup.rotation.x = -player.tilt;
  shipGroup.rotation.z = player.roll;
  const scaleY = player.sliding ? 0.55 : 1;
  shipGroup.scale.y += (scaleY - shipGroup.scale.y) * Math.min(1, 0.4 * dt);

  const camTargetX = player.x * 0.55;
  camera.position.x += (camTargetX - camera.position.x) * Math.min(1, 0.18 * dt);
  camera.up.set(Math.sin(player.roll * 0.15), Math.cos(player.roll * 0.15), 0);
  camera.lookAt(camTargetX * 0.7, 2.6, -14);

  engineGlow.intensity = thrusting ? 1.4 : 0;
  flame.visible = thrusting;
  if (thrusting) {{
    const flick = 0.85 + Math.random() * 0.3;
    flame.scale.set(flick, flick * (0.8 + Math.random() * 0.4), flick);
  }}

  groundShadow.position.x = shipGroup.position.x;
  groundShadow.position.z = shipGroup.position.z;
  const shadowScale = 1 - altRatio * 0.5;
  groundShadow.scale.set(shadowScale, shadowScale, shadowScale);
  groundShadow.material.opacity = 0.35 * (1 - altRatio * 0.7);

  // particles drift and fade
  for (const p of particles) {{
    p.sprite.position.z += gameSpeed * dt * 0.12;
    p.life -= dt;
    p.sprite.material.opacity = 0.8 * (p.life / p.maxLife);
    const sc = 0.35 * (p.life / p.maxLife);
    p.sprite.scale.set(sc, sc, sc);
  }}
  for (let i = particles.length - 1; i >= 0; i--) {{
    if (particles[i].life <= 0) {{ scene.remove(particles[i].sprite); particles.splice(i, 1); }}
  }}

  // boss trigger
  if (!bossSpawned && score >= BOSS_TRIGGER_SCORE) {{
    spawnBoss();
  }}

  // spawn (paused during boss fight)
  if (!bossActive) {{
    spawnTimer -= dt;
    if (spawnTimer <= 0) {{
      spawnObstacle();
      spawnTimer = Math.max(22, 40 - elapsed * 0.008) + Math.random() * 14;
    }}
  }}

  // move obstacles toward camera, check collision
  const shipZ = shipGroup.position.z;
  for (const o of obstacles) {{
    o.z += gameSpeed * dt * 0.12;
    o.mesh.position.z = o.z;
    o.mesh.rotation.x += 0.01 * dt;
    o.mesh.rotation.y += 0.015 * dt;

    if (o.type === 'shooter' && o.hp > 0 && o.z > -55 && o.z < -6) {{
      o.fireTimer -= dt;
      if (o.fireTimer <= 0) {{
        spawnEnemyBolt(o);
        o.fireTimer = 70 + Math.random() * 50;
      }}
    }}

    const dz = Math.abs(o.z - shipZ);
    const dx = Math.abs(o.x - shipGroup.position.x);
    const dy = Math.abs(o.mesh.position.y - shipGroup.position.y);
    if (o.hp > 0 && dz < 1.0 && dx < (o.radius + 0.85) && dy < (o.radius + 0.65)) {{
      endGame();
    }}
  }}
  obstacles = obstacles.filter(o => {{
    if (o.hp <= 0 || o.z > 6) {{ scene.remove(o.mesh); return false; }}
    return true;
  }});

  // player bolts: move forward, check obstacle hits
  for (const b of playerBolts) {{
    b.mesh.position.z -= 2.2 * dt;
  }}
  for (const b of playerBolts) {{
    for (const o of obstacles) {{
      if (o.hp <= 0) continue;
      const bdx = Math.abs(b.mesh.position.x - o.mesh.position.x);
      const bdy = Math.abs(b.mesh.position.y - o.mesh.position.y);
      const bdz = Math.abs(b.mesh.position.z - o.mesh.position.z);
      if (bdx < o.radius + 0.3 && bdy < o.radius + 0.3 && bdz < o.radius + 0.3) {{
        o.hp = 0;
        b.hit = true;
        score += 40;
      }}
    }}
  }}
  playerBolts = playerBolts.filter(b => {{
    if (b.hit || b.mesh.position.z < -72) {{ scene.remove(b.mesh); return false; }}
    return true;
  }});

  // enemy bolts: move toward last-known player direction, check player hit
  shootCooldown -= dt;
  for (const b of enemyBolts) {{
    b.mesh.position.x += b.vx * 0.55 * dt;
    b.mesh.position.y += b.vy * 0.55 * dt;
    b.mesh.position.z += b.vz * 0.55 * dt;
    const edx = Math.abs(b.mesh.position.x - shipGroup.position.x);
    const edy = Math.abs(b.mesh.position.y - shipGroup.position.y);
    const edz = Math.abs(b.mesh.position.z - shipGroup.position.z);
    if (edx < 0.8 && edy < 0.8 && edz < 0.8) {{
      endGame();
    }}
  }}
  enemyBolts = enemyBolts.filter(b => {{
    if (b.mesh.position.z > 6 || b.mesh.position.z < -75) {{ scene.remove(b.mesh); return false; }}
    return true;
  }});

  // boss behavior
  if (boss) {{
    boss.phase += 0.02 * dt;
    const targetBossZ = -32;
    boss.z += (targetBossZ - boss.z) * Math.min(1, 0.02 * dt);
    boss.mesh.position.z = boss.z;
    boss.mesh.position.x = Math.sin(boss.phase) * 6.5;
    boss.mesh.position.y = groundY + 4.5 + Math.sin(boss.phase * 0.7) * 1.2;
    boss.mesh.rotation.y += 0.006 * dt;
    boss.mesh.rotation.x += 0.003 * dt;
    const pulse = 1 + Math.sin(boss.phase * 3) * 0.04;
    boss.mesh.userData.eye.scale.set(pulse, pulse, pulse);

    boss.fireTimer -= dt;
    if (boss.fireTimer <= 0 && boss.z > -50) {{
      spawnBossBoltFrom(boss.mesh.position, -2.2);
      spawnBossBoltFrom(boss.mesh.position, 0);
      spawnBossBoltFrom(boss.mesh.position, 2.2);
      boss.fireTimer = 95 + Math.random() * 30;
    }}

    // player bolts vs boss
    for (const b of playerBolts) {{
      const bx = Math.abs(b.mesh.position.x - boss.mesh.position.x);
      const by = Math.abs(b.mesh.position.y - boss.mesh.position.y);
      const bz = Math.abs(b.mesh.position.z - boss.mesh.position.z);
      if (bx < 3 && by < 3 && bz < 3) {{
        b.hit = true;
        boss.hp -= 1;
        bossBarFill.style.width = Math.max(0, (boss.hp / boss.maxHp) * 100) + '%';
        if (boss.hp <= 0) {{
          score += 1500;
          scene.remove(boss.mesh);
          boss = null;
          bossActive = false;
          bossBarWrap.style.display = 'none';
          spawnTimer = 60;
        }}
      }}
    }}

    // boss direct collision with ship
    if (boss) {{
      const cdx = Math.abs(boss.mesh.position.x - shipGroup.position.x);
      const cdy = Math.abs(boss.mesh.position.y - shipGroup.position.y);
      const cdz = Math.abs(boss.mesh.position.z - shipGroup.position.z);
      if (cdx < 3.4 && cdy < 3.4 && cdz < 3.4) {{
        endGame();
      }}
    }}
  }}

  // scroll ground segments
  for (const seg of groundSegs) {{
    seg.position.z += gameSpeed * dt * 0.12;
    if (seg.position.z > segLen) seg.position.z -= segLen * segCount;
  }}

  // stars drift slowly
  stars.position.z += gameSpeed * dt * 0.02;
  if (stars.position.z > 30) stars.position.z = 0;
}}

let lastTime = null;
function loop(ts) {{
  if (lastTime === null) lastTime = ts;
  let dt = (ts - lastTime) / (1000 / 60);
  lastTime = ts;
  dt = Math.max(0.1, Math.min(dt, 2.5));
  update(dt);
  renderer.render(scene, camera);
  requestAnimationFrame(loop);
}}

function endGame() {{
  if (gameOver) return;
  running = false;
  gameOver = true;
  overlay.style.display = 'flex';
  const best = Math.max(score, parseInt(bestLabel.textContent.split(': ')[1]));
  bestLabel.textContent = 'Best: ' + best;
  startBtn.textContent = '↻ Run Again';
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

function handleResize() {{
  const w = holder.clientWidth, h = holder.clientHeight;
  if (w === 0 || h === 0) return;
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
  renderer.setSize(w, h);
}}
window.addEventListener('resize', handleResize);
setTimeout(handleResize, 50);

requestAnimationFrame(loop);
}})();
</script>
</body>
</html>
"""

components.html(game_html, height=460, scrolling=False)

components.html(game_html, height=460, scrolling=False)

st.markdown("""
<div style="text-align:center; margin-top: 14px; color: rgba(255,255,255,0.45); font-size: 13px;">
Controls: <b>Space</b> to jump, <b>hold ↑</b> to fly, <b>hold ↓</b> to slide, <b>← → / A D</b> to steer — or hold left/right/top/bottom thirds of the canvas on mobile.
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
