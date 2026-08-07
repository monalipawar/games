import streamlit as st
import streamlit.components.v1 as components
import json
import os
from datetime import datetime

# [Keep your existing Config, load_scores, save_scores, and THEMES code here]
# (Included in the block below for completeness)

st.set_page_config(page_title="OrbitParkour", page_icon="🪐", layout="wide", initial_sidebar_state="collapsed")
SCORES_FILE = "orbitparkour_scores.json"

def load_scores():
    if os.path.exists(SCORES_FILE):
        try:
            with open(SCORES_FILE, "r") as f: return json.load(f)
        except: return {"high_score": 0, "history": []}
    return {"high_score": 0, "history": []}

def save_scores(data):
    with open(SCORES_FILE, "w") as f: json.dump(data, f, indent=2)

if "scores" not in st.session_state: st.session_state.scores = load_scores()
THEMES = {"Default": {"primary": "#7C4DFF", "secondary": "#00E5FF", "accent": "#FF4DA6", "bg1": "#0a0e27", "bg2": "#1a1445"}}
t = THEMES["Default"]

game_html = f"""
<!DOCTYPE html>
<html>
<!-- [Keep your existing CSS/Head here] -->
<body>
<div id="wrap">
  <div id="gameCanvasHolder"></div>
</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
(function() {{
// ... [Keep all your existing setup, scene, ship, and helper functions here] ...

// REPLACE YOUR EXISTING FUNCTIONS WITH THESE:

function requestShoot() {{
  if (running && shootCooldown <= 0) {{
    let target = null;
    let minDist = 60; // Targeting radius

    // Auto-Targeting Logic: Find nearest obstacle in front
    for (const o of obstacles) {{
      if (o.hp > 0 && o.z < -2 && o.z > -65) {{
        const d = Math.abs(o.z - shipGroup.position.z);
        if (d < minDist) {{ minDist = d; target = o; }}
      }}
    }}
    spawnPlayerBolt(target);
    shootCooldown = 14;
  }}
}}

function spawnPlayerBolt(target) {{
  const mesh = makePlayerBolt();
  mesh.position.copy(shipGroup.position);
  mesh.position.z -= 1.4;

  // Default forward velocity
  let vel = {{ x: 0, y: 0, vz: -4.5 }}; 

  if (target) {{
    // Calculate direction vector toward the targeted obstacle
    const dx = target.mesh.position.x - mesh.position.x;
    const dy = target.mesh.position.y - mesh.position.y;
    const dz = target.mesh.position.z - mesh.position.z;
    const mag = Math.sqrt(dx*dx + dy*dy + dz*dz) || 1;
    vel = {{ x: (dx/mag)*5, y: (dy/mag)*5, vz: (dz/mag)*5 }};
  }}

  scene.add(mesh);
  playerBolts.push({{ mesh, vx: vel.x, vy: vel.y, vz: vel.vz }});
}}

// ... [Inside your update(dt) loop, replace the bolt movement section] ...
// Look for the "player bolts" section and update to this:

  for (const b of playerBolts) {{
    b.mesh.position.x += b.vx * dt;
    b.mesh.position.y += b.vy * dt;
    b.mesh.position.z += b.vz * dt;
  }}

// ... [Keep the rest of your original loop and game logic exactly as it was] ...
}})();
</script>
</body>
</html>
"""

components.html(game_html, height=460)
