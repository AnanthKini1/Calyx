# Calyx: Remote Wound Intelligence

**The clinical middleman turning wound photos into life-saving data.**

**[Devpost](https://devpost.com/software/calyx-7hnod6)**

---

## What is Calyx?

30% of chronic wounds lead to hospital readmission because warning signs are invisible at home. **Calyx** is a remote wound monitoring platform that serves as the critical link between patients and their medical teams — replacing passive "photo galleries" with a quantitative clinical reasoning engine.

Calyx uses **computer vision** to measure wound area and tissue health from a photo, then cross-references those measurements with a **clinical knowledge graph** to surface alerts when a patient's biomarkers — like elevated blood glucose or low albumin — are actively stalling their recovery.

---

## Capabilities

### For Patients

- **Wound Scanning** — Upload a wound photo or run a demo scan. Calyx uses OpenCV and K-Means clustering to segment the image into Red (granulation), Yellow (slough), and Black (eschar) tissue zones and calculates wound area in cm².
- **AI Clinical Assessment** — Every scan is passed through a knowledge graph that factors in the patient's comorbidities, blood glucose, serum albumin, mobility score, and post-operative day to generate a clinical priority rating (OK → CRITICAL), a list of active alerts, and a recommended action.
- **Scan History** — A full log of all saved scans, showing area, tissue composition, area change over time, and an estimated priority per scan.
- **Healing Trend** — Interactive charts showing wound area over time and how the tissue composition (granulation vs. slough vs. eschar) has shifted across scans.
- **Patient Profile** — Patients can register with optional clinical parameters (blood glucose, serum albumin, mobility score, days since surgery, comorbidities) and optionally link to a supervising doctor at registration.

### For Doctors

- **Clinical Dashboard** — A real-time overview of all assigned patients, sorted by clinical priority, with per-patient wound area, area delta, tissue bars, and last scan date visible at a glance.
- **Patient Management** — Doctors can search the full patient registry and add or remove patients from their dashboard at any time — no need to coordinate at registration.
- **Active Alerts** — A dedicated alerts view that surfaces only patients rated CRITICAL or HIGH, with their full alert list visible without clicking through.
- **Patient Detail** — Clicking any patient opens a detailed view with their full wound history, latest scan analysis, AI reasoning, active risk factors from the knowledge graph, and recommended clinical action.

---

## How It Works

### Computer Vision Pipeline

- A **calibration coin** in the wound photo acts as a real-world size reference, enabling precise wound area measurement in cm² regardless of camera distance or zoom.
- **K-Means clustering** segments wound pixels into three clinical tissue categories based on HSV colour space, producing RYB (Red/Yellow/Black) tissue ratios.
- A synthetic annotated image is generated overlaying the segmentation result on the original photo.

### Clinical Knowledge Graph

- Built with **NetworkX**, the knowledge graph maps relationships between patient biomarkers (e.g. hyperglycaemia, malnutrition, low mobility) and wound healing outcomes.
- Each scan triggers a **BFS traversal** of the graph, activating risk nodes based on the patient's current health data and wound metrics.
- The traversal produces a priority rating, a set of specific clinical alerts, a reasoning summary, and a recommended action — all without requiring a doctor to be online.

### Architecture

| Layer | Technology |
|---|---|
| Frontend | React 19 + TypeScript + Vite + Tailwind CSS |
| Backend | FastAPI + Uvicorn |
| Computer Vision | OpenCV + scikit-learn (K-Means) |
| Knowledge Graph | NetworkX |
| Auth | SHA-256 password hashing, role-based access (patient/doctor) |
| Data | JSON file store (patients, doctors) |
| Animation | Framer Motion |
| Charts | Recharts |
| Deployment | Railway (nixpacks) |

---

## Running Calyx

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the backend (port 8000)

```bash
uvicorn api.main:app --reload --port 8000
```

### 3. Start the frontend (port 5173)

```bash
cd app
npm run dev
```

### 4. Open the app

Navigate to [http://localhost:5173](http://localhost:5173).

---

## What's Next for Calyx

- **Live Capture** — Real-time webcam wound scanning with instant calibration feedback, replacing static file uploads.
- **3D Depth Analysis** — Video-based wound volume tracking to complement the current 2D area measurement.
- **Longitudinal Alerts** — Trend-based alerting that flags wounds not healing at the expected rate over time, even when individual scans look acceptable.
- **EHR Integration** — Pulling live biomarker data (CGM readings, lab results) directly from electronic health records rather than relying on manually entered values.
