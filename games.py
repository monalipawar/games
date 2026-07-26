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
    background: linear-gradient(180deg, {['bg2']} 0%, {t['bg1']} 100%);
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
  <div id="overlay">
    <h1>🪐 ORBITPARKOUR</h1>
    <p>Jump asteroids. Slide under debris. Dodge flyers. Don't crash.</p>
    <button id="startBtn">▶ Start Run</button>
    <p class="hint">SPACE = Jump &nbsp;•&nbsp; Hold ↑ / Tap-top = Fly &nbsp;•&nbsp; Hold ↓ / Tap-bottom = Slide</p>
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

const BASE_W = 900, BASE_H = 420;

// ---------- scene setup ----------
const scene = new THREE.Scene();
scene.fog = new THREE.Fog(hexToInt(COLORS.bg1), 20, 95);

const camera = new THREE.PerspectiveCamera(58, BASE_W / BASE_H, 0.1, 200);
camera.position.set(0, 5.4, 11.5);
camera.lookAt(0, 3, -10);

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
for (let i = 0; i < segCount; i++) {{
  const g = new THREE.Group();
  const planeGeo = new THREE.PlaneGeometry(16, segLen);
  const planeMat = new THREE.MeshStandardMaterial({{
    color: hexToInt(COLORS.bg2), roughness: 0.8, metalness: 0.2,
    emissive: hexToInt(COLORS.primary), emissiveIntensity: 0.06
  }});
  const plane = new THREE.Mesh(planeGeo, planeMat);
  plane.rotation.x = -Math.PI / 2;
  g.add(plane);
  const gridHelper = new THREE.GridHelper(16, 8, hexToInt(COLORS.secondary), hexToInt(COLORS.primary));
  gridHelper.material.transparent = true;
  gridHelper.material.opacity = 0.35;
  g.add(gridHelper);
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

// ---------- game state ----------
let player, obstacles, gameSpeed, score, running, gameOver, spawnTimer, elapsed, thrusting;

function resetGame() {{
  player = {{ y: groundY, vy: 0, sliding: false, tilt: 0 }};
  for (const o of obstacles || []) scene.remove(o.mesh);
  obstacles = [];
  for (const p of particles) scene.remove(p.sprite);
  particles = [];
  gameSpeed = 3.6;
  score = 0;
  spawnTimer = 48;
  elapsed = 0;
  running = false;
  gameOver = false;
  thrusting = false;
  shipGroup.position.set(0, groundY + 1.2, 0);
  shipGroup.rotation.set(0, Math.PI, 0);
  shipGroup.scale.set(1, 1, 1);
}}
resetGame();

function flyStart() {{ if (running && !player.sliding) thrusting = true; }}
function flyEnd() {{ thrusting = false; }}
function jumpImpulse() {{ if (running && !player.sliding) player.vy = -(-9.5) * -1 * 0 + 4.4; }}
function slideStart() {{ if (running && player.y <= groundY + 1.2 + 0.05) player.sliding = true; }}
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
holder.addEventListener('touchstart', (e) => {{
  const rect = holder.getBoundingClientRect();
  const touchY = e.touches[0].clientY - rect.top;
  if (touchY < rect.height / 2) flyStart(); else slideStart();
}});
holder.addEventListener('touchend', () => {{ flyEnd(); slideEnd(); }});
holder.addEventListener('mousedown', (e) => {{
  const rect = holder.getBoundingClientRect();
  const clickY = e.clientY - rect.top;
  if (clickY < rect.height / 2) flyStart(); else slideStart();
}});
holder.addEventListener('mouseup', () => {{ flyEnd(); slideEnd(); }});

function spawnObstacle() {{
  const r = Math.random();
  const spawnZ = -70;
  let mesh, type, radius;
  if (r < 0.4) {{
    const size = 0.7 + Math.random() * 0.55;
    mesh = makeRock(size);
    mesh.position.set(0, groundY + size * 0.85, spawnZ);
    type = 'rock'; radius = size;
  }} else if (r < 0.65) {{
    mesh = makeDebris(2.1, 0.6, 0.6);
    mesh.position.set(0, groundY + 2.6, spawnZ);
    type = 'debris'; radius = 0.5;
  }} else {{
    const size = 0.75 + Math.random() * 0.45;
    const minY = ceilingY - 1.5;
    const maxY = groundY + 1.6;
    const y = maxY + Math.random() * (minY - maxY);
    mesh = makeFlyer(size);
    mesh.position.set(0, y, spawnZ);
    type = 'flyer'; radius = size;
  }}
  scene.add(mesh);
  obstacles.push({{ mesh, type, radius, z: spawnZ }});
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

  if (!player.sliding) {{
    if (thrusting) {{
      player.vy -= 0.85 * dt;
      if (player.vy < -5.5) player.vy = -5.5;
    }} else {{
      player.vy += 0.85 * dt;
      if (player.vy > 9) player.vy = 9;
    }}
    player.y += player.vy * dt * 0.09;
    if (player.y < shipBaseY) {{ player.y = shipBaseY; player.vy = 0; }}
    if (player.y > shipTopY) {{ player.y = shipTopY; player.vy = 0; }}

    if (running) spawnParticle();
  }} else {{
    player.y = shipBaseY;
    player.vy = 0;
  }}

  shipGroup.position.y = player.y;
  const altRatio = Math.max(0, Math.min(1, (player.y - shipBaseY) / (shipTopY - shipBaseY)));
  const targetTilt = Math.max(-0.4, Math.min(0.4, -player.vy * 0.05));
  player.tilt += (targetTilt - player.tilt) * Math.min(1, 0.25 * dt);
  shipGroup.rotation.x = -player.tilt;
  const scaleY = player.sliding ? 0.55 : 1;
  shipGroup.scale.y += (scaleY - shipGroup.scale.y) * Math.min(1, 0.4 * dt);

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

  // spawn
  spawnTimer -= dt;
  if (spawnTimer <= 0) {{
    spawnObstacle();
    spawnTimer = Math.max(38, 65 - elapsed * 0.01) + Math.random() * 22;
  }}

  // move obstacles toward camera, check collision
  const shipZ = shipGroup.position.z;
  for (const o of obstacles) {{
    o.z += gameSpeed * dt * 0.12;
    o.mesh.position.z = o.z;
    o.mesh.rotation.x += 0.01 * dt;
    o.mesh.rotation.y += 0.015 * dt;

    const dz = Math.abs(o.z - shipZ);
    const dy = Math.abs(o.mesh.position.y - shipGroup.position.y);
    if (dz < 1.0 && dy < (o.radius + 0.65)) {{
      endGame();
    }}
  }}
  obstacles = obstacles.filter(o => {{
    if (o.z > 6) {{ scene.remove(o.mesh); return false; }}
    return true;
  }});

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
