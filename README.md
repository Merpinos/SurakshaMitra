# SurakshaMitra — Hazardous Industrial Facility Threat Zone Visualizer

**SurakshaMitra** is a rapid hazard assessment tool developed for **Smart India Hackathon 2026 (SIH-2026)**, addressing problem statement **SIH260205** by the **Ministry of Home Affairs (MHA)**.

It models and visualizes explosion threat zones, BLEVE fireball thermal radiation radii, and downwind gas dispersion plumes around petroleum storage facilities (refineries, LPG storage terminals, crude storage tanks) on an interactive map.

---

## 📌 Key Validation Case: Jaipur IOCL Fire (October 2009)

- **Facility**: Jaipur Indian Oil Corporation Ltd. (IOCL) Terminal
- **Coordinates**: `26.8505° N, 75.8069° E`
- **Fuel**: LPG (TNT Equivalence Factor: 0.70)
- **Mass**: 2,700,000 kg (2.7 Kilotons equivalent)
- **Results**:
  - **Fireball Radius**: ~475 meters
  - **Lethal Zone (> 83 kPa)**: ~272 meters
  - **Severe Zone (> 34 kPa)**: ~433 meters
  - **Moderate Zone (> 7 kPa)**: ~841 meters

---

## 🛠️ Project Architecture

```
SurakshaMitra/
├── backend/
│   ├── main.py                # FastAPI app with POST /compute-zone
│   ├── generate_fallback.py   # Offline fallback dataset generator
│   ├── models/
│   │   ├── __init__.py
│   │   ├── blast.py           # TNT Equivalence & Hopkinson scaling blast model
│   │   └── thermal.py         # BLEVE Fireball thermal radiation radius model
│   └── requirements.txt       # Python backend dependencies
├── frontend/
│   ├── index.html             # UI + Leaflet map + Controls (no npm/build needed)
│   └── data/
│       └── jaipur_demo.json   # Pre-baked offline fallback GeoJSON
└── README.md                  # Documentation & Quickstart guide
```

---

## 🚀 Quickstart Guide

### 1. Install Backend Dependencies

```bash
pip install -r backend/requirements.txt
```

### 2. Generate Fallback Dataset (Optional)

Run the generator script to populate `frontend/data/jaipur_demo.json`:

```bash
python -m backend.generate_fallback
```

### 3. Start FastAPI Backend

Launch the API server with Uvicorn:

```bash
uvicorn backend.main:app --reload
```

The API server will run at `http://localhost:8000`. Interactive API documentation is available at `http://localhost:8000/docs`.

### 4. Open Frontend

Simply open `frontend/index.html` in your web browser (double click or open via browser).

> **Offline Fallback Feature**: If the FastAPI backend server is not running or unreachable, the frontend automatically and silently loads the pre-baked `frontend/data/jaipur_demo.json` file so you can demonstrate the Jaipur IOCL case offline without any setup!

---

## 💥 Threat Zone Models

1. **Fireball Radius (Thermal BLEVE)**
   - Formula: $R_{\text{fireball}} = 3.86 \times m^{0.325}$ (in meters)
   - Visual: Bright Red Circle (50% opacity)

2. **Lethal Threat Zone (> 83 kPa)**
   - Overpressure threshold causing total structural destruction & fatalities.
   - Formula: $R_{\text{lethal}} = 2.2 \times W_{\text{TNT}}^{1/3}$
   - Visual: Red Circle (35% opacity)

3. **Severe Threat Zone (> 34 kPa)**
   - Overpressure causing heavy structural damage & severe injuries.
   - Formula: $R_{\text{severe}} = 3.5 \times W_{\text{TNT}}^{1/3}$
   - Visual: Orange Circle (35% opacity)

4. **Moderate Threat Zone (> 7 kPa)**
   - Overpressure causing minor structural damage & glass breakage.
   - Formula: $R_{\text{moderate}} = 6.8 \times W_{\text{TNT}}^{1/3}$
   - Visual: Yellow Circle (35% opacity)

5. **Dispersion Plume**
   - Elongated, rotated ellipse aligned downwind based on wind speed & direction.
   - Visual: Blue Translucent Ellipse (30% opacity)

---

## 🏢 Included Preset Facilities

1. **Jaipur IOCL** — `26.8505° N, 75.8069° E` — LPG — 2,700,000 kg
2. **Vizag HPCL** — `17.6868° N, 83.2185° E` — Crude — 5,000,000 kg
3. **Mangalore MRPL** — `12.8916° N, 74.8430° E` — Petrol — 3,500,000 kg
4. **Bina BPCL** — `24.1700° N, 78.1800° E` — LPG — 1,800,000 kg
