# 🧠 EngagePulse — Real-Time Engagement Pivot System

> CPU-optimised, cloud-deployable proctoring intelligence for detecting engagement drops and delivering actionable interventions in real time.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![OpenCV](https://img.shields.io/badge/opencv-headless-green.svg)](https://opencv.org)

---

## 📌 Overview

**EngagePulse** is a real-time engagement analysis system for online proctoring and remote learning. It analyses non-verbal cues from video feeds and audio silence patterns to detect engagement drops, then automatically suggests targeted interventions — all using CPU-only processing suitable for Streamlit Cloud.

---

## 🔬 Detection Signals

| Signal | Method | CPU Cost |
|---|---|---|
| **Face Detection** | OpenCV Haar Cascade (frontal face) | Very Low |
| **Eye Openness / Drowsiness** | Eye Cascade + Eye Aspect Ratio (EAR) | Very Low |
| **Head Pose / Tilt** | Bounding box geometry | Minimal |
| **Gaze Deviation** | Face center offset from frame center | Minimal |
| **Expression Estimation** | Pixel brightness + edge density heuristics | Low |
| **Posture Proxy** | Face-area-to-frame-area ratio | Minimal |
| **Audio Silence** | Amplitude threshold pattern detection | Minimal |

---

## 🚦 Engagement States

| State | Score Range | Description |
|---|---|---|
| ✅ Engaged | 75–100% | Active, focused, eyes open |
| ⚠️ Distracted | 55–74% | Gaze wandering, mild disengagement |
| ❓ Confused | 35–54% | Expression signals confusion |
| 😴 Drowsy | 20–34% | Eyes closing, slowed response |
| ❌ Disengaged | 0–19% | Face absent or fully disengaged |

---

## ⚡ Intervention System

For each detected state, the system suggests:
- **Immediate** actions (< 1 min): Attention check, alert ping, quick poll
- **Short-term** actions (1–5 min): Energy break, Q&A pause, peer discussion
- **Medium-term** actions (5–15 min): Modality change, resource share, gamification

---

## 🚀 Deployment

### 1. Clone & Push to GitHub

```bash
git clone https://github.com/YOUR_USERNAME/engagement-pivot.git
cd engagement-pivot

# Customise and then push
git add .
git commit -m "Deploy EngagePulse"
git push origin main
```

### 2. Deploy on Streamlit Cloud

1. Visit [share.streamlit.io](https://share.streamlit.io)
2. Click **New App**
3. Select repository: `YOUR_USERNAME/engagement-pivot`
4. Main file: `app.py`
5. Click **Deploy!** 🎉

### 3. Local Development

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## 📁 Project Structure

```
engagement-pivot/
├── app.py                  # Main Streamlit application
├── requirements.txt        # Python dependencies
├── .streamlit/
│   └── config.toml        # Theme and server settings
└── README.md              # This file
```

---

## 🏗️ Architecture

```
Video Input (Webcam / Demo)
        │
        ▼
┌─────────────────────────┐
│  Frame Preprocessing    │  OpenCV BGR→Gray
│  Haar Face Detection    │  detectMultiScale
│  Eye Detection          │  Eye Cascade
│  EAR Computation        │  Geometry
│  Head Pose Estimation   │  BBox Analysis  
│  Expression Heuristics  │  Brightness+Edges
└─────────────┬───────────┘
              │
              ▼
┌─────────────────────────┐
│  Engagement Scoring     │  Weighted signal fusion
│  State Classification   │  5-level taxonomy
│  Trend Analysis         │  Rolling window
└─────────────┬───────────┘
              │
              ▼
┌─────────────────────────┐
│  Alert Engine           │  Cooldown-aware alerting
│  Intervention Selector  │  State-matched actions
│  Analytics Dashboard    │  Plotly visualisations
└─────────────────────────┘
```

---

## ⚙️ Configuration

Adjust via the sidebar:
- **Detection Sensitivity** (0.3 – 1.0)
- **Silence Alert Threshold** (5 – 60 seconds)
- **Alert Cooldown** (10 – 120 seconds)
- **Demo Scenarios**: engaged, distracted, drowsy, confused, disengaged

---

## 📊 Analytics & Export

- Live engagement score timeline
- State distribution pie chart
- Multi-signal overlay (gaze, posture, silence)
- CSV export of session data and alert log

---

## ⚖️ Privacy Notes

- All processing is **local / in-browser** — no video is stored or transmitted
- Demo mode uses synthetically generated frames (no camera required)
- For production: add consent flows and data minimisation

---

## 📄 License

MIT License — Free to use, modify, and deploy.

---

*Built with ❤️ using Streamlit + OpenCV — optimised for CPU-only cloud environments*
