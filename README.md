# CYRO - Crime Yield & Reporting Overview

**An explainable crime risk prediction system for the Capital Region, New York**

CYRO uses environmental factors, temporal patterns, and real-world data to predict crime risk across 400 hexagonal grid cells covering Albany, Schenectady, Rensselaer, and Saratoga counties.

---

## Features

- **Real-time Risk Visualization**: Interactive map showing high/medium/low risk zones
- **24-Hour Risk Trend Chart**: Shows how risk varies throughout the day
- **Environmental Context**: 74 police station locations across 4 counties
- **Address Search**: Geocode any location and see risk scores with dynamic map zoom
- **Explainable AI**: Risk scores based on transparent, weighted environmental factors
- **Real Data Integration**: Environmental features from OpenStreetMap (260 bars, 253 liquor stores, 4,685 street lights)

---

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **PostgreSQL + PostGIS** - Spatial database for geographic queries
- **SQLAlchemy** - Database ORM and session management
- **H3** - Uber's hexagonal hierarchical geospatial indexing system
- **Scikit-learn** - Machine learning for risk prediction
- **Overpass API** - Real environmental data from OpenStreetMap

### Frontend
- **React** - UI framework
- **React-Leaflet** - Interactive map visualization
- **Recharts** - 24-hour risk trend charts
- **Axios** - HTTP client for API requests
- **Space Grotesk** - Custom Google Font

---

## Installation

### Prerequisites
- Python 3.8+
- Node.js 16+
- PostgreSQL 12+ with PostGIS extension
- Conda (recommended)

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/nsbehackathon.git
cd nsbehackathon
```

### 2. Backend Setup
```bash
cd backend

# Create conda environment
conda create -n crime_risk python=3.10
conda activate crime_risk

# Install dependencies
pip install -r requirements.txt

# Create .env file with database credentials
echo "DATABASE_URL=postgresql://username:password@localhost:5432/crime_risk_db" > .env
```

### 3. Frontend Setup
```bash
cd ../frontend
npm install
```

---

## Database Setup

### 1. Create PostgreSQL Database
```bash
psql -U postgres
CREATE DATABASE crime_risk_db;
\c crime_risk_db
CREATE EXTENSION postgis;
\q
```

### 2. Initialize Database Schema & Data
Run these scripts in order:

```bash
cd backend

# 1. Create tables and load police stations
python scripts/init_database.py

# 2. Generate 24,000+ synthetic crime incidents
python scripts/generate_synthetic_crimes.py

# 3. Train logistic regression model
python scripts/train_model.py

# 4. Enrich with real OSM data (bars, lights, etc.)
python scripts/enrich_with_overpass.py
```

**Expected Output:**
- ✓ 400 grid cells (H3 resolution 9)
- ✓ 74 police stations across 4 counties
- ✓ 24,561 synthetic crime records
- ✓ Real environmental features: 260 bars, 253 liquor stores, 4,685 street lights

### 3. Verify Database
```bash
python check_db.py
```

You should see:
```
Grid Cells:      400
Grid Features:   400
Police Stations: 74
✓ Database is fully populated!
```

---

## Running the Application

### Start Backend Server
```bash
cd backend
python run.py
```
Backend runs on `http://localhost:8000`

### Start Frontend Development Server
```bash
cd frontend
npm run dev
```
Frontend runs on `http://localhost:5173`

### View API Documentation
Visit `http://localhost:8000/docs` for interactive Swagger UI

---

## API Endpoints

### `GET /api/risk-zones`
Get risk scores for grid cells within a radius of a point.

**Parameters:**
- `lat` (float): Latitude (42.0-43.0)
- `lon` (float): Longitude (-74.5 to -73.5)
- `radius` (float): Search radius in miles (0.5-50)
- `prediction_time` (datetime, optional): ISO timestamp for prediction
- `hour` (int, optional): Hour of day (0-23) for prediction

**Response:**
```json
[
  {
    "cell_id": "89...",
    "center_lat": 42.6526,
    "center_lon": -73.7562,
    "risk_score": 67.5,
    "risk_level": "Medium",
    "confidence": 0.75,
    "prediction_time": "2026-02-01T14:00:00"
  }
]
```

### Other Endpoints
- `GET /api/risk-at-point` - Get risk for nearest cell to a point
- `GET /api/risk-factors/{cell_id}` - Detailed risk factor breakdown
- `GET /api/police-stations` - Police stations within bounding box
- `GET /api/geocode` - Geocode an address

---

## How It Works

### Risk Calculation
Risk scores are calculated using weighted environmental factors:

**Positive Risk Factors** (increase crime likelihood):
- Bars & nightclubs (+0.25, +0.20)
- Liquor stores (+0.15)
- Abandoned buildings (+0.30)
- Population density (+0.35)
- Unemployment rate (+0.18)

**Negative Risk Factors** (decrease crime likelihood):
- Street lights (-0.12)
- Higher median income (-0.20)
- Transit proximity (-0.15)

### Time-of-Day Multipliers
Risk varies by hour:
- **1-2 AM**: 1.4× (peak risk)
- **6 AM**: 0.6× (lowest risk)
- **12 PM**: 1.0× (baseline)
- **10 PM - 12 AM**: 1.2-1.25× (elevated)

### Percentile-Based Normalization
Scores are normalized so that:
- Bottom 33% of cells → Low Risk (green)
- Middle 33% → Medium Risk (orange)
- Top 34% → High Risk (red)

---

## UI Features

### Dark Theme Interface
- Black control panels (#1a1a1a)
- White text for readability
- Custom logo display
- Space Grotesk font

### Interactive Map
- Click anywhere to set search center
- Radius slider (0.5-50 miles)
- Dynamic zoom based on search radius
- Police station markers with popups
- Heatmap/Zones toggle

### 24-Hour Risk Trend Chart
- Shows how risk changes throughout the day
- Red line indicating risk intensity
- Parallel API requests for fast loading
- Finds closest zone to searched location

---

##  Disclaimer

This system predicts risk based **solely on environmental factors** (time, venue density, lighting, etc.). It does **NOT**:
- Profile individuals
- Predict specific crimes
- Replace professional law enforcement analysis

Use for awareness and resource allocation only.

---

## Data Sources

- **Grid Cells**: Generated using H3 geospatial indexing (resolution 9)
- **Environmental Features**: OpenStreetMap via Overpass API
- **Crime Data**: Synthetic data with geographic/temporal patterns
- **Police Stations**: Real locations across Albany, Schenectady, Rensselaer, and Saratoga counties

---

## 🏗️ Project Structure

```
nsbehackathon/
├── backend/
│   ├── app/
│   │   ├── api/endpoints.py          # FastAPI routes
│   │   ├── core/database.py          # SQLAlchemy config
│   │   └── services/risk_calculator.py  # Risk scoring
│   ├── scripts/
│   │   ├── init_database.py          # DB initialization
│   │   ├── generate_synthetic_crimes.py
│   │   ├── train_model.py
│   │   └── enrich_with_overpass.py   # OSM data
│   └── run.py
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── MapView.jsx
│   │   │   ├── ControlPanel.jsx
│   │   │   ├── RiskTrendChart.jsx
│   │   │   └── Legend.jsx
│   │   └── App.jsx
│   └── package.json
└── README.md
```

---

## 👥 Contributors

Built for the NSBE Hackathon 2026
Bhoomi Patni
Nikita Amin

---

## 📄 License

This project is licensed under the MIT License.

---

## 🙏 Acknowledgments

- **H3** by Uber Technologies for geospatial indexing
- **OpenStreetMap** contributors for environmental data
- **Leaflet** for mapping capabilities
- **FastAPI** for the Python web framework
