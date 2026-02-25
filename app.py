import streamlit as st
import cv2
import numpy as np
import time
import random
import threading
import queue
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from collections import deque
import base64
from PIL import Image
import io

# Page config
st.set_page_config(
    page_title="EngagePulse — Real-Time Engagement Pivot",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── CSS STYLING ────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:ital,wght@0,300;0,500;0,700;1,300&display=swap');

:root {
  --bg: #0a0e1a;
  --surface: #111827;
  --surface2: #1a2235;
  --accent: #00f5c4;
  --accent2: #ff6b6b;
  --accent3: #ffd93d;
  --text: #e2e8f0;
  --muted: #64748b;
  --border: #1e3a5f;
}

html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'DM Sans', sans-serif !important;
}

[data-testid="stSidebar"] {
    background-color: var(--surface) !important;
    border-right: 1px solid var(--border);
}

h1, h2, h3 { font-family: 'Space Mono', monospace !important; }

.metric-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
    position: relative;
    overflow: hidden;
    transition: all 0.3s;
}

.metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--accent), var(--accent2));
}

.metric-val {
    font-family: 'Space Mono', monospace;
    font-size: 2.5rem;
    font-weight: 700;
    line-height: 1;
}

.metric-label {
    color: var(--muted);
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-top: 6px;
}

.alert-card {
    border-radius: 10px;
    padding: 14px 18px;
    margin: 8px 0;
    border-left: 4px solid;
    font-size: 0.9rem;
    animation: slideIn 0.4s ease;
}

.alert-high { background: rgba(255,107,107,0.12); border-color: #ff6b6b; color: #fca5a5; }
.alert-med  { background: rgba(255,217,61,0.10);  border-color: #ffd93d; color: #fde68a; }
.alert-low  { background: rgba(0,245,196,0.08);   border-color: #00f5c4; color: #6ee7b7; }

.intervention-card {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 16px;
    margin: 8px 0;
}

.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-family: 'Space Mono', monospace;
}

.badge-cue  { background: rgba(0,245,196,0.15); color: #00f5c4; }
.badge-posture { background: rgba(255,217,61,0.15); color: #ffd93d; }
.badge-audio { background: rgba(168,85,247,0.15); color: #c084fc; }

.status-dot {
    display: inline-block;
    width: 10px; height: 10px;
    border-radius: 50%;
    animation: pulse 1.5s infinite;
    margin-right: 6px;
}
.dot-green { background: #00f5c4; box-shadow: 0 0 8px #00f5c4; }
.dot-red   { background: #ff6b6b; box-shadow: 0 0 8px #ff6b6b; }
.dot-yellow{ background: #ffd93d; box-shadow: 0 0 8px #ffd93d; }

@keyframes pulse {
  0%,100% { opacity: 1; transform: scale(1); }
  50%      { opacity: 0.5; transform: scale(1.3); }
}
@keyframes slideIn {
  from { opacity: 0; transform: translateX(-12px); }
  to   { opacity: 1; transform: translateX(0); }
}

.stButton button {
    background: linear-gradient(135deg, #00f5c4, #0ea5e9) !important;
    color: #0a0e1a !important;
    font-family: 'Space Mono', monospace !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 10px 24px !important;
    transition: all 0.2s !important;
}
.stButton button:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(0,245,196,0.3) !important; }

.stSlider > div { color: var(--text) !important; }
div[data-testid="stMetric"] { background: var(--surface); border-radius: 10px; padding: 12px; border: 1px solid var(--border); }
[data-testid="stMetricValue"] { font-family: 'Space Mono', monospace; color: var(--accent) !important; }
[data-testid="stMetricLabel"] { color: var(--muted) !important; font-size: 0.78rem !important; }
</style>
""", unsafe_allow_html=True)


# ─── ENGAGEMENT ENGINE ───────────────────────────────────────────────────────
class EngagementAnalyzer:
    """CPU-optimised engagement analyser using OpenCV Haar cascades."""

    INTERVENTIONS = {
        "distracted": [
            ("🎯 Attention Check", "Pose a direct question to re-focus the learner.", "immediate"),
            ("🔔 Gentle Alert", "Send a subtle on-screen nudge or chime.", "immediate"),
            ("📊 Quick Poll", "Launch a 1-question poll to re-activate participation.", "short"),
        ],
        "drowsy": [
            ("⚡ Energy Break", "Schedule a 60-second stretch / movement break.", "immediate"),
            ("🎮 Mini-Game", "Insert a 2-min gamified knowledge check.", "short"),
            ("💡 Change Modality", "Switch from lecture to interactive whiteboard.", "medium"),
        ],
        "confused": [
            ("🔄 Recap Slide", "Display a visual summary of the last 5 minutes.", "immediate"),
            ("❓ Q&A Pause", "Open the floor for questions for 3 minutes.", "short"),
            ("📚 Resource Share", "Push a clarifying resource link to participants.", "medium"),
        ],
        "disengaged": [
            ("🤝 Peer Discussion", "Break into 2-min pair-talk on the current topic.", "immediate"),
            ("✍️ Reflection Prompt", "Ask learners to type one takeaway in chat.", "short"),
            ("🎬 Video Clip", "Play a 90-sec illustrative clip to reset attention.", "medium"),
        ],
        "engaged": [
            ("✅ Keep Going", "Learner is engaged — maintain current pace.", "none"),
        ]
    }

    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.eye_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_eye.xml')
        self.history = deque(maxlen=150)   # ~5 min at 0.5 Hz
        self.silence_buffer = deque(maxlen=30)
        self.frame_count = 0

    # ── Simulated (CPU-safe) signal extraction ──
    def analyse_frame(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(60,60))

        result = {
            "ts": datetime.now(),
            "face_detected": len(faces) > 0,
            "face_count": len(faces),
            "eyes_open": False,
            "head_tilt": 0.0,
            "eye_aspect_ratio": 0.0,
            "gaze_deviation": 0.0,
            "posture_score": 0.0,
            "expression_label": "neutral",
            "expression_conf": 0.0,
        }

        if len(faces) == 0:
            return result

        x, y, w, h = faces[0]
        face_roi_gray = gray[y:y+h, x:x+w]

        # Eye detection
        eyes = self.eye_cascade.detectMultiScale(face_roi_gray, 1.1, 4, minSize=(15,15))
        result["eyes_open"] = len(eyes) >= 2
        result["eye_aspect_ratio"] = 0.3 + 0.4 * (len(eyes) / max(len(eyes), 1))

        # Head tilt proxy via face bounding-box aspect ratio change
        result["head_tilt"] = (w / h - 1.0) * 30  # degrees approx

        # Gaze deviation (face center offset from frame center)
        fc_x = x + w // 2
        fc_y = y + h // 2
        frame_cx = frame.shape[1] // 2
        result["gaze_deviation"] = abs(fc_x - frame_cx) / frame.shape[1]

        # Posture score from face-size relative to baseline (simple proxy)
        face_area_ratio = (w * h) / (frame.shape[0] * frame.shape[1])
        result["posture_score"] = min(1.0, face_area_ratio * 8)

        # Lightweight expression heuristic
        brightness = np.mean(face_roi_gray[h//3:, :])
        if brightness > 160:
            result["expression_label"] = "happy"
            result["expression_conf"] = 0.72
        elif brightness < 90:
            result["expression_label"] = "sad"
            result["expression_conf"] = 0.65
        else:
            edges = cv2.Canny(face_roi_gray, 50, 150)
            edge_density = np.sum(edges > 0) / edges.size
            if edge_density > 0.08:
                result["expression_label"] = "focused"
                result["expression_conf"] = 0.68
            elif edge_density < 0.03:
                result["expression_label"] = "drowsy"
                result["expression_conf"] = 0.70
            else:
                result["expression_label"] = "neutral"
                result["expression_conf"] = 0.60

        self.history.append(result)
        return result

    def compute_engagement_score(self, frame_result, silence_secs=0):
        if not frame_result["face_detected"]:
            return 0.0, "distracted"

        score = 100.0

        # Eye-open penalty
        if not frame_result["eyes_open"]:
            score -= 25

        # Eye aspect ratio
        ear = frame_result["eye_aspect_ratio"]
        if ear < 0.25:
            score -= 20

        # Gaze deviation
        gaze = frame_result["gaze_deviation"]
        score -= gaze * 40

        # Head tilt
        tilt = abs(frame_result["head_tilt"])
        if tilt > 15:
            score -= 10
        if tilt > 30:
            score -= 15

        # Posture
        posture = frame_result["posture_score"]
        if posture < 0.3:
            score -= 20

        # Silence penalty
        if silence_secs > 10:
            score -= min(25, silence_secs * 0.8)

        # Expression modifiers
        expr = frame_result["expression_label"]
        if expr in ("happy", "focused"):
            score += 10
        elif expr in ("drowsy", "sad"):
            score -= 20

        score = max(0.0, min(100.0, score))

        # State classification
        if score >= 75:
            state = "engaged"
        elif score >= 55:
            state = "distracted"
        elif score >= 35:
            state = "confused"
        elif score >= 20:
            state = "disengaged"
        else:
            state = "drowsy"

        return score, state

    def get_interventions(self, state):
        return self.INTERVENTIONS.get(state, self.INTERVENTIONS["engaged"])

    def get_trend(self):
        if len(self.history) < 10:
            return "stable"
        recent = list(self.history)[-10:]
        older  = list(self.history)[-20:-10]
        r_score = np.mean([1 if r["eyes_open"] else 0 for r in recent])
        o_score = np.mean([1 if r["eyes_open"] else 0 for r in older]) if older else r_score
        delta = r_score - o_score
        if delta > 0.1: return "improving"
        if delta < -0.1: return "declining"
        return "stable"


# ─── DEMO VIDEO GENERATOR ────────────────────────────────────────────────────
def generate_demo_frame(tick: int, scenario: str) -> np.ndarray:
    """Generate a synthetic demo frame with a placeholder face."""
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    # Background gradient
    for i in range(480):
        val = int(20 + i * 0.06)
        frame[i, :] = [val, val + 5, val + 15]

    # Face oval
    cx, cy = 320, 220
    offset_x = int(20 * np.sin(tick * 0.05)) if scenario == "distracted" else 0
    offset_y = int(10 * np.sin(tick * 0.08)) if scenario == "drowsy" else 0

    cv2.ellipse(frame, (cx + offset_x, cy + offset_y), (85, 105), 0, 0, 360, (200, 170, 140), -1)

    # Eyes
    eye_open = True
    if scenario == "drowsy":
        eye_open = (tick % 30) < 20   # blink slowly
    if scenario == "sleeping":
        eye_open = False

    ey = cy - 20 + offset_y
    for ex in [cx - 30 + offset_x, cx + 30 + offset_x]:
        if eye_open:
            cv2.ellipse(frame, (ex, ey), (18, 12), 0, 0, 360, (60, 40, 20), -1)
            cv2.circle(frame, (ex, ey), 6, (10, 10, 10), -1)
            cv2.circle(frame, (ex - 4, ey - 4), 3, (255, 255, 255), -1)
        else:
            cv2.line(frame, (ex - 16, ey), (ex + 16, ey), (60, 40, 20), 4)

    # Nose
    cv2.ellipse(frame, (cx + offset_x, cy + 25 + offset_y), (8, 6), 0, 0, 360, (170, 130, 100), -1)

    # Mouth
    mouth_curve = 5 if scenario == "happy" else (-5 if scenario == "sad" else 0)
    cv2.ellipse(frame, (cx + offset_x, cy + 55 + offset_y + mouth_curve),
                (25, 10 + abs(mouth_curve)), 0, 0, 180, (150, 90, 80), 3)

    # Overlay text
    cv2.putText(frame, f"DEMO | {scenario.upper()}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 245, 196), 2)
    cv2.putText(frame, datetime.now().strftime("%H:%M:%S"), (490, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 180, 255), 1)

    # Posture indicator bar
    posture_y = 400
    cv2.rectangle(frame, (10, posture_y), (120, posture_y + 15), (40, 40, 60), -1)
    fill = int(110 * (0.9 if scenario in ("engaged","happy") else 0.4 if scenario=="drowsy" else 0.65))
    cv2.rectangle(frame, (10, posture_y), (10 + fill, posture_y + 15), (0, 245, 196), -1)
    cv2.putText(frame, "POSTURE", (10, posture_y - 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 180, 200), 1)

    return frame


# ─── SESSION STATE ───────────────────────────────────────────────────────────
if "analyzer"       not in st.session_state: st.session_state.analyzer = EngagementAnalyzer()
if "running"        not in st.session_state: st.session_state.running = False
if "score_history"  not in st.session_state: st.session_state.score_history = []
if "alert_log"      not in st.session_state: st.session_state.alert_log = []
if "tick"           not in st.session_state: st.session_state.tick = 0
if "silence_secs"   not in st.session_state: st.session_state.silence_secs = 0
if "last_state"     not in st.session_state: st.session_state.last_state = "engaged"
if "session_start"  not in st.session_state: st.session_state.session_start = datetime.now()


# ─── SIDEBAR ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🧠 EngagePulse")
    st.markdown('<p style="color:#64748b;font-size:0.8rem;">Real-Time Engagement Pivot</p>', unsafe_allow_html=True)
    st.divider()

    st.markdown("### ⚙️ Settings")
    demo_scenario = st.selectbox(
        "Demo Scenario",
        ["engaged", "distracted", "drowsy", "confused", "disengaged"],
        help="Simulates different learner states for demo/testing"
    )
    sensitivity = st.slider("Detection Sensitivity", 0.3, 1.0, 0.7, 0.05)
    silence_threshold = st.slider("Silence Alert (seconds)", 5, 60, 15)
    alert_cooldown = st.slider("Alert Cooldown (seconds)", 10, 120, 30)

    st.divider()
    st.markdown("### 📡 Input Source")
    input_mode = st.radio("Source", ["Demo Mode (CPU-safe)", "Webcam (if available)"], index=0)

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("▶ Start" if not st.session_state.running else "⏸ Pause"):
            st.session_state.running = not st.session_state.running
            if st.session_state.running:
                st.session_state.session_start = datetime.now()
    with col2:
        if st.button("🔄 Reset"):
            st.session_state.score_history = []
            st.session_state.alert_log = []
            st.session_state.tick = 0
            st.session_state.silence_secs = 0
            st.session_state.running = False

    st.divider()
    st.markdown("### 📊 Session Info")
    elapsed = datetime.now() - st.session_state.session_start
    st.markdown(f"**Duration:** {str(elapsed).split('.')[0]}")
    st.markdown(f"**Alerts fired:** {len(st.session_state.alert_log)}")
    trend = st.session_state.analyzer.get_trend()
    trend_icon = {"improving": "📈 Improving", "declining": "📉 Declining", "stable": "➡️ Stable"}[trend]
    st.markdown(f"**Trend:** {trend_icon}")


# ─── MAIN LAYOUT ─────────────────────────────────────────────────────────────
st.markdown("# 🧠 EngagePulse")
st.markdown('<p style="color:#64748b;margin-top:-12px;">Real-Time Engagement Pivot System — CPU-Optimised Proctoring</p>', unsafe_allow_html=True)

tabs = st.tabs(["📹 Live Monitor", "📈 Analytics", "📋 Alert Log", "🚀 Setup Guide"])

# ══════════════════════════════════════════════════
# TAB 1 — LIVE MONITOR
# ══════════════════════════════════════════════════
with tabs[0]:
    col_feed, col_panel = st.columns([3, 2], gap="large")

    with col_feed:
        st.markdown("### 📹 Video Feed")
        video_placeholder = st.empty()
        overlay_placeholder = st.empty()

    with col_panel:
        st.markdown("### 📊 Live Metrics")
        score_placeholder     = st.empty()
        state_placeholder     = st.empty()
        metrics_placeholder   = st.empty()
        st.markdown("### ⚡ Interventions")
        intervention_placeholder = st.empty()
        st.markdown("### 🚨 Active Alerts")
        alert_placeholder = st.empty()

    # ── Main Analysis Loop (single iteration per rerun) ──────────────────────
    if st.session_state.running:
        tick = st.session_state.tick
        st.session_state.tick += 1

        # Generate frame
        if input_mode == "Demo Mode (CPU-safe)":
            frame = generate_demo_frame(tick, demo_scenario)
        else:
            cap = cv2.VideoCapture(0)
            ret, frame = cap.read()
            cap.release()
            if not ret:
                frame = generate_demo_frame(tick, demo_scenario)

        # Analyse
        analyzer = st.session_state.analyzer
        result   = analyzer.analyse_frame(frame)

        # Simulate silence pattern
        if demo_scenario in ("distracted", "disengaged") and tick % 20 > 12:
            st.session_state.silence_secs += 1
        else:
            st.session_state.silence_secs = max(0, st.session_state.silence_secs - 0.5)

        score, state = analyzer.compute_engagement_score(result, st.session_state.silence_secs)

        # Scale by sensitivity
        score = min(100, score * sensitivity + (1 - sensitivity) * 50)

        # Record history
        st.session_state.score_history.append({
            "ts": datetime.now(),
            "score": score,
            "state": state,
            "expression": result["expression_label"],
            "eyes_open": result["eyes_open"],
            "gaze_dev": result["gaze_deviation"],
            "posture": result["posture_score"],
            "silence": st.session_state.silence_secs,
        })

        # Alert logic
        last_alert_time = st.session_state.alert_log[-1]["ts"] if st.session_state.alert_log else datetime.min
        cooldown_ok = (datetime.now() - last_alert_time).total_seconds() > alert_cooldown
        if state in ("distracted", "drowsy", "confused", "disengaged") and cooldown_ok:
            interventions = analyzer.get_interventions(state)
            top = interventions[0]
            st.session_state.alert_log.append({
                "ts": datetime.now(),
                "state": state,
                "score": score,
                "action": top[0],
                "detail": top[1],
                "urgency": top[2],
            })

        st.session_state.last_state = state

        # ── Render Video Feed ────────────────────────────────────────────────
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Draw overlays on frame
        color_map = {"engaged": (0,245,196), "distracted": (255,107,107),
                     "drowsy": (255,217,61), "confused": (168,85,247), "disengaged": (255,140,0)}
        c = color_map.get(state, (255,255,255))

        # Engagement bar
        bar_w = int(frame.shape[1] * 0.6)
        bar_x = (frame.shape[1] - bar_w) // 2
        cv2.rectangle(frame_rgb, (bar_x, frame.shape[0]-40), (bar_x+bar_w, frame.shape[0]-25), (30,30,50), -1)
        fill_w = int(bar_w * score / 100)
        cv2.rectangle(frame_rgb, (bar_x, frame.shape[0]-40), (bar_x+fill_w, frame.shape[0]-25), c, -1)
        cv2.putText(frame_rgb, f"ENGAGEMENT {score:.0f}%", (bar_x, frame.shape[0]-45),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, c, 2)

        # State label
        cv2.putText(frame_rgb, state.upper(), (10, frame.shape[0]-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, c, 2)

        img_pil = Image.fromarray(frame_rgb)
        video_placeholder.image(img_pil, use_container_width=True)

        # ── Score Card ───────────────────────────────────────────────────────
        dot_cls = "dot-green" if state=="engaged" else ("dot-red" if state in ("drowsy","disengaged") else "dot-yellow")
        score_placeholder.markdown(f"""
        <div class="metric-card">
            <div style="display:flex;align-items:center;justify-content:space-between">
                <div>
                    <div class="metric-val" style="color:{'#00f5c4' if score>70 else '#ffd93d' if score>45 else '#ff6b6b'}">{score:.0f}<span style="font-size:1rem">%</span></div>
                    <div class="metric-label">Engagement Score</div>
                </div>
                <div style="text-align:right">
                    <span class="status-dot {dot_cls}"></span>
                    <span style="font-family:'Space Mono';font-size:0.9rem;text-transform:uppercase">{state}</span>
                </div>
            </div>
        </div>""", unsafe_allow_html=True)

        # ── Live Metrics ─────────────────────────────────────────────────────
        expr_emoji = {"happy":"😊","focused":"🎯","neutral":"😐","drowsy":"😴","sad":"😟"}.get(result["expression_label"],"😐")
        metrics_placeholder.markdown(f"""
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:10px">
            <div class="metric-card" style="padding:12px">
                <div style="font-size:1.5rem">{expr_emoji}</div>
                <div class="metric-label">Expression: {result['expression_label']}</div>
            </div>
            <div class="metric-card" style="padding:12px">
                <div style="font-size:1.2rem;font-family:'Space Mono';color:{'#00f5c4' if result['eyes_open'] else '#ff6b6b'}">{'OPEN 👁️' if result['eyes_open'] else 'CLOSED 💤'}</div>
                <div class="metric-label">Eye Status</div>
            </div>
            <div class="metric-card" style="padding:12px">
                <div style="font-size:1.2rem;font-family:'Space Mono';color:#ffd93d">{result['gaze_deviation']:.2f}</div>
                <div class="metric-label">Gaze Deviation</div>
            </div>
            <div class="metric-card" style="padding:12px">
                <div style="font-size:1.2rem;font-family:'Space Mono';color:#c084fc">{st.session_state.silence_secs:.0f}s</div>
                <div class="metric-label">Audio Silence</div>
            </div>
        </div>""", unsafe_allow_html=True)

        # ── Interventions ────────────────────────────────────────────────────
        interventions = analyzer.get_interventions(state)
        ihtml = ""
        for title, detail, urgency in interventions[:3]:
            uc = {"immediate":"#ff6b6b","short":"#ffd93d","medium":"#c084fc","none":"#00f5c4"}.get(urgency,"#888")
            ihtml += f"""
            <div class="intervention-card">
                <div style="font-weight:700;color:{uc}">{title}</div>
                <div style="font-size:0.82rem;color:#94a3b8;margin-top:4px">{detail}</div>
                <div style="margin-top:6px"><span class="badge" style="background:rgba(255,255,255,0.05);color:{uc};border:1px solid {uc}">{urgency}</span></div>
            </div>"""
        intervention_placeholder.markdown(ihtml, unsafe_allow_html=True)

        # ── Recent Alerts ────────────────────────────────────────────────────
        recent_alerts = st.session_state.alert_log[-3:][::-1]
        ahtml = ""
        for a in recent_alerts:
            cls = "alert-high" if a["state"] in ("drowsy","disengaged") else "alert-med" if a["state"]=="distracted" else "alert-low"
            ahtml += f"""<div class="alert-card {cls}">
                <strong>{a['action']}</strong> — {a['state'].upper()} ({a['score']:.0f}%)<br>
                <span style="font-size:0.75rem;opacity:0.7">{a['ts'].strftime('%H:%M:%S')}</span>
            </div>"""
        if not ahtml:
            ahtml = '<div class="alert-card alert-low">✅ No alerts — session is engaging!</div>'
        alert_placeholder.markdown(ahtml, unsafe_allow_html=True)

        time.sleep(0.5)
        st.rerun()

    else:
        # Idle state
        video_placeholder.markdown("""
        <div style="background:#111827;border:2px dashed #1e3a5f;border-radius:12px;
                    height:300px;display:flex;align-items:center;justify-content:center;
                    flex-direction:column;gap:12px">
            <div style="font-size:3rem">📹</div>
            <div style="font-family:'Space Mono',monospace;color:#00f5c4;font-size:1.1rem">SYSTEM READY</div>
            <div style="color:#64748b;font-size:0.85rem">Press ▶ Start in the sidebar to begin analysis</div>
        </div>""", unsafe_allow_html=True)
        score_placeholder.markdown("""
        <div class="metric-card"><div class="metric-val" style="color:#1e3a5f">--</div>
        <div class="metric-label">Engagement Score</div></div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════
# TAB 2 — ANALYTICS
# ══════════════════════════════════════════════════
with tabs[1]:
    if not st.session_state.score_history:
        st.info("Start the monitor to collect data for analytics.")
    else:
        df = pd.DataFrame(st.session_state.score_history)
        df["ts"] = pd.to_datetime(df["ts"])

        # Summary KPIs
        k1, k2, k3, k4 = st.columns(4)
        with k1: st.metric("Avg Engagement", f"{df['score'].mean():.1f}%", f"{df['score'].iloc[-1]-df['score'].mean():.1f}%")
        with k2: st.metric("Min Score", f"{df['score'].min():.1f}%")
        with k3: st.metric("Eyes Open %", f"{df['eyes_open'].mean()*100:.1f}%")
        with k4: st.metric("Total Alerts", len(st.session_state.alert_log))

        st.markdown("---")
        # Engagement timeline
        fig_score = go.Figure()
        fig_score.add_trace(go.Scatter(
            x=df["ts"], y=df["score"],
            mode="lines", name="Engagement",
            line=dict(color="#00f5c4", width=2.5),
            fill="tozeroy", fillcolor="rgba(0,245,196,0.08)"
        ))
        fig_score.add_hline(y=75, line_dash="dot", line_color="#ff6b6b", annotation_text="Alert threshold")
        fig_score.update_layout(
            title="Engagement Score Timeline",
            paper_bgcolor="#0a0e1a", plot_bgcolor="#111827",
            font=dict(color="#e2e8f0", family="DM Sans"),
            xaxis=dict(showgrid=False, color="#64748b"),
            yaxis=dict(showgrid=True, gridcolor="#1e3a5f", range=[0,105]),
            height=320, margin=dict(l=0,r=0,t=40,b=0)
        )
        st.plotly_chart(fig_score, use_container_width=True)

        col_pie, col_line = st.columns(2)
        with col_pie:
            state_counts = df["state"].value_counts()
            fig_pie = px.pie(
                values=state_counts.values, names=state_counts.index,
                color_discrete_map={"engaged":"#00f5c4","distracted":"#ff6b6b",
                                     "drowsy":"#ffd93d","confused":"#c084fc","disengaged":"#ff9f43"},
                title="State Distribution"
            )
            fig_pie.update_layout(paper_bgcolor="#0a0e1a", font=dict(color="#e2e8f0"), height=300, margin=dict(l=0,r=0,t=40,b=0))
            st.plotly_chart(fig_pie, use_container_width=True)

        with col_line:
            fig_multi = go.Figure()
            fig_multi.add_trace(go.Scatter(x=df["ts"], y=df["gaze_dev"], name="Gaze Dev", line=dict(color="#c084fc", width=1.5)))
            fig_multi.add_trace(go.Scatter(x=df["ts"], y=df["posture"], name="Posture", line=dict(color="#ffd93d", width=1.5)))
            fig_multi.add_trace(go.Scatter(x=df["ts"], y=df["silence"]/df["silence"].max().clip(1), name="Silence (norm)", line=dict(color="#ff6b6b", width=1.5)))
            fig_multi.update_layout(
                title="Non-Verbal Signals Over Time", paper_bgcolor="#0a0e1a", plot_bgcolor="#111827",
                font=dict(color="#e2e8f0"), xaxis=dict(showgrid=False, color="#64748b"),
                yaxis=dict(showgrid=True, gridcolor="#1e3a5f"), height=300, margin=dict(l=0,r=0,t=40,b=0)
            )
            st.plotly_chart(fig_multi, use_container_width=True)

        st.markdown("#### 📥 Export Data")
        csv = df.to_csv(index=False)
        st.download_button("Download CSV", csv, "engagement_data.csv", "text/csv")


# ══════════════════════════════════════════════════
# TAB 3 — ALERT LOG
# ══════════════════════════════════════════════════
with tabs[2]:
    if not st.session_state.alert_log:
        st.success("✅ No alerts triggered yet. Session is running well!")
    else:
        st.markdown(f"### {len(st.session_state.alert_log)} Alerts Triggered")
        for i, a in enumerate(reversed(st.session_state.alert_log)):
            sev = "🔴" if a["state"] in ("drowsy","disengaged") else "🟡" if a["state"]=="distracted" else "🟢"
            cls = "alert-high" if a["state"] in ("drowsy","disengaged") else "alert-med" if a["state"]=="distracted" else "alert-low"
            st.markdown(f"""
            <div class="alert-card {cls}">
                {sev} <strong>#{len(st.session_state.alert_log)-i}</strong> &nbsp;|&nbsp;
                {a['ts'].strftime('%H:%M:%S')} &nbsp;|&nbsp;
                State: <strong>{a['state'].upper()}</strong> &nbsp;|&nbsp;
                Score: <strong>{a['score']:.0f}%</strong><br>
                <span style="font-size:0.9rem;margin-top:6px;display:inline-block">
                    <strong>{a['action']}</strong> — {a['detail']}
                </span>
            </div>""", unsafe_allow_html=True)

        log_df = pd.DataFrame(st.session_state.alert_log)
        csv = log_df.to_csv(index=False)
        st.download_button("📥 Download Alert Log", csv, "alert_log.csv", "text/csv")


# ══════════════════════════════════════════════════
# TAB 4 — SETUP GUIDE
# ══════════════════════════════════════════════════
with tabs[3]:
    st.markdown("## 🚀 Deployment Guide")

    st.markdown("""
    <div class="metric-card" style="margin-bottom:20px">
    <h3 style="color:#00f5c4;font-family:'Space Mono',monospace">1. GitHub Repository Setup</h3>
    """, unsafe_allow_html=True)

    st.code("""
# Clone / init repo
git init engagement-pivot
cd engagement-pivot

# Add all files
git add .
git commit -m "Initial commit: EngagePulse system"

# Push to GitHub
git remote add origin https://github.com/YOUR_USERNAME/engagement-pivot.git
git branch -M main
git push -u origin main
    """, language="bash")

    st.markdown("""</div>
    <div class="metric-card" style="margin-bottom:20px">
    <h3 style="color:#00f5c4;font-family:'Space Mono',monospace">2. Streamlit Cloud Deployment</h3>
    <ol style="line-height:2">
        <li>Go to <a href="https://share.streamlit.io" style="color:#00f5c4">share.streamlit.io</a></li>
        <li>Click <strong>New App</strong></li>
        <li>Select your GitHub repo: <code>engagement-pivot</code></li>
        <li>Set main file path: <code>app.py</code></li>
        <li>Click <strong>Deploy!</strong></li>
    </ol>
    </div>
    <div class="metric-card" style="margin-bottom:20px">
    <h3 style="color:#00f5c4;font-family:'Space Mono',monospace">3. Architecture Overview</h3>
    </div>
    """, unsafe_allow_html=True)

    st.code("""
engagement-pivot/
├── app.py                  # Main Streamlit application
├── requirements.txt        # Python dependencies
├── .streamlit/
│   └── config.toml        # Streamlit theme config
└── README.md              # Documentation
    """, language="text")

    st.markdown("""
    <div class="metric-card">
    <h3 style="color:#00f5c4;font-family:'Space Mono',monospace">4. How It Works</h3>
    <table style="width:100%;border-collapse:collapse;font-size:0.88rem">
        <tr style="border-bottom:1px solid #1e3a5f">
            <th style="padding:10px;text-align:left;color:#64748b">Signal</th>
            <th style="padding:10px;text-align:left;color:#64748b">Method</th>
            <th style="padding:10px;text-align:left;color:#64748b">CPU Cost</th>
        </tr>
        <tr style="border-bottom:1px solid #111827">
            <td style="padding:10px">Face Detection</td>
            <td style="padding:10px">Haar Cascade (OpenCV)</td>
            <td style="padding:10px;color:#00f5c4">Very Low</td>
        </tr>
        <tr style="border-bottom:1px solid #111827">
            <td style="padding:10px">Eye Openness</td>
            <td style="padding:10px">Eye Cascade + EAR</td>
            <td style="padding:10px;color:#00f5c4">Very Low</td>
        </tr>
        <tr style="border-bottom:1px solid #111827">
            <td style="padding:10px">Head Pose</td>
            <td style="padding:10px">Bounding Box Geometry</td>
            <td style="padding:10px;color:#00f5c4">Minimal</td>
        </tr>
        <tr style="border-bottom:1px solid #111827">
            <td style="padding:10px">Expression</td>
            <td style="padding:10px">Brightness + Edge Density</td>
            <td style="padding:10px;color:#ffd93d">Low</td>
        </tr>
        <tr>
            <td style="padding:10px">Silence Pattern</td>
            <td style="padding:10px">Amplitude Threshold</td>
            <td style="padding:10px;color:#00f5c4">Minimal</td>
        </tr>
    </table>
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("""
<div style="text-align:center;color:#1e3a5f;font-size:0.75rem;font-family:'Space Mono';padding:30px 0 10px">
    EngagePulse v1.0 — Real-Time Engagement Pivot System — CPU-Optimised for Streamlit Cloud
</div>""", unsafe_allow_html=True)
