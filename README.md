# Crime Risk Prediction System

An explainable, ethics-first crime risk prediction system that estimates relative risk zones (Low/Medium/High) for the next 24 hours using only public, non-identifying environmental data.

## 🎯 Key Features

### Ethical Design
- **No individual profiling** - focuses on places, not people
- **Explainable predictions** - every risk score can be traced to specific environmental factors
- **Transparent model** - simple weighted scoring system, not a "black box"
- **Non-identifying data only** - uses environmental indicators (bars, lighting, etc.)

### Backend
- Python FastAPI with explainable risk-scoring model
- Linear weighted combination of environmental features
- Time-of-day adjustments based on historical patterns
- PostgreSQL with PostGIS for geospatial data
- H3 hexagonal grid system for uniform coverage

### Frontend
- Interactive React map interface
- Heatmap visualization of risk zones
- Address search with autocomplete
- Adjustable search radius (0.5-5 miles)
- Police station markers
- Real-time risk calculations

## 📊 Risk Factors

The system considers these environmental indicators:

1. **Alcohol Density** - Bars, nightclubs, liquor stores
2. **Transit Proximity** - Distance to subway/transit stations
3. **Infrastructure** - Street lighting, abandoned buildings
4. **Population** - Population density
5. **Socioeconomic** - Median income, unemployment rate
6. **Temporal** - Time of day patterns

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- PostgreSQL 13+ with PostGIS extension
- Node.js 16+
- npm or yarn

### Backend Setup

1. **Install PostgreSQL and PostGIS**
   ```powershell
   # Install PostgreSQL from https://www.postgresql.org/download/windows/
   # Enable PostGIS extension in your database
   ```

2. **Create database**
   ```sql
   CREATE DATABASE crime_risk_db;
   \c crime_risk_db
   CREATE EXTENSION postgis;
   ```

3. **Configure environment**
   ```powershell
   cd backend
   cp .env.example .env
   # Edit .env and set your DATABASE_URL
   ```

4. **Install dependencies**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

5. **Initialize database**
   ```powershell
   python scripts\init_database.py
   ```

6. **Start the API**
   ```powershell
   python run.py
   ```

   API will be available at: http://localhost:8000
   
   API docs: http://localhost:8000/docs

### Frontend Setup

1. **Install dependencies**
   ```powershell
   cd frontend
   npm install
   ```

2. **Start development server**
   ```powershell
   npm run dev
   ```

   Frontend will be available at: http://localhost:3000

## 📁 Project Structure

```
nsbehackathon/
├── backend/
│   ├── app/
│   │   ├── api/              # API endpoints
│   │   │   └── endpoints.py
│   │   ├── core/             # Core configuration
│   │   │   ├── config.py
│   │   │   └── database.py
│   │   ├── services/         # Business logic
│   │   │   └── risk_calculator.py  # Explainable risk model
│   │   └── main.py           # FastAPI application
│   ├── scripts/
│   │   ├── init_database.py  # Database setup
│   │   └── calibrate_model.py # Model weight tuning
│   ├── requirements.txt
│   ├── .env.example
│   └── run.py
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── MapView.jsx        # Main map component
│   │   │   ├── HeatmapLayer.jsx   # Heatmap visualization
│   │   │   ├── ControlPanel.jsx   # Search & controls
│   │   │   └── Legend.jsx         # Risk level legend
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
└── README.md
```

## 🔧 API Endpoints

### `GET /api/risk-zones`
Get predicted risk zones within radius of a point.

**Parameters:**
- `lat` - Center latitude
- `lon` - Center longitude
- `radius` - Search radius in miles (0.5-5.0)
- `prediction_time` - Optional ISO datetime (default: 1 hour from now)

**Response:**
```json
[
  {
    "cell_id": "89283082837ffff",
    "center_lat": 42.6526,
    "center_lon": -73.7562,
    "risk_score": 45.3,
    "risk_level": "Medium",
    "confidence": 0.75,
    "prediction_time": "2026-01-31T15:00:00"
  }
]
```

### `GET /api/risk-factors/{cell_id}`
Get detailed risk factor breakdown for a specific cell.

**Response:**
```json
{
  "cell_id": "89283082837ffff",
  "alcohol_contribution": 25.3,
  "transit_contribution": 18.7,
  "lighting_contribution": -8.2,
  "vacancy_contribution": 15.1,
  "population_contribution": 12.5,
  "socioeconomic_contribution": 10.3,
  "temporal_contribution": 20.0,
  "explanation": "Risk Level: Medium for evening/night..."
}
```

### `GET /api/police-stations`
Get police stations within bounding box.

## 🧮 Model Explanation

### Risk Calculation

The system uses a **transparent weighted linear model**:

```
base_score = Σ(feature_value × feature_weight)
adjusted_score = base_score × time_multiplier
normalized_score = normalize(adjusted_score, 0-100)
```

### Feature Weights

Learned from historical crime data using logistic regression:

```python
WEIGHTS = {
    'bars_count': 0.18,              # More bars = higher risk
    'nightclubs_count': 0.15,
    'liquor_stores_count': 0.12,
    'nearest_subway_meters': -0.0001, # Closer to transit = higher risk
    'street_lights_count': -0.05,     # More lights = lower risk
    'abandoned_buildings_count': 0.20,
    'population_density': 0.08,
    'unemployment_rate': 0.15,
    'median_income': -0.00001         # Higher income = lower risk
}
```

### Time Multipliers

Based on historical crime patterns:

- **Late night (1-3 AM)**: 1.3-1.4× (Peak risk)
- **Morning (6-11 AM)**: 0.7-0.8× (Lower risk)
- **Evening (6-11 PM)**: 1.1-1.3× (Rising risk)

### Risk Categories

- **Low**: Score 0-33
- **Medium**: Score 34-66
- **High**: Score 67-100

## 📊 Data Sources

For production deployment, use:

1. **OpenStreetMap** - POIs (bars, liquor stores, transit)
2. **US Census Bureau** - Demographics, socioeconomic data
3. **Municipal Open Data** - Police stations, infrastructure
4. **Historical Crime Data** - For weight calibration only (not prediction)

Sample data included for demonstration.

## 🔐 Ethical Considerations

### What This System Does:
✅ Predicts risk levels for **geographic areas**  
✅ Uses **environmental factors only**  
✅ Provides **explainable predictions**  
✅ Helps allocate resources efficiently  

### What This System Does NOT Do:
❌ Profile individuals or groups  
❌ Predict who will commit crimes  
❌ Use demographic characteristics  
❌ Make real-time crime detection  

### Bias Mitigation:
- No race, ethnicity, or individual demographics used
- Transparent feature weights
- Regular audits of predictions
- Focus on modifiable environmental factors

## 🛠️ Customization

### Calibrating Model Weights

To tune weights using your historical crime data:

1. Place crime data in `backend/data/raw/historical_crimes.csv`
2. Run calibration:
   ```powershell
   cd backend
   python scripts\calibrate_model.py
   ```
3. Update weights in `backend/app/services/risk_calculator.py`

### Changing Region

Edit `backend/app/core/config.py`:

```python
REGION_MIN_LAT: float = 42.5
REGION_MAX_LAT: float = 42.9
REGION_MIN_LON: float = -74.1
REGION_MAX_LON: float = -73.5
```

Update center in `frontend/src/App.jsx`:

```javascript
const [center, setCenter] = useState({ lat: YOUR_LAT, lng: YOUR_LON })
```

## 🧪 Testing

### Backend Tests
```powershell
cd backend
pytest
```

### Frontend Tests
```powershell
cd frontend
npm test
```

## 📦 Deployment

### Backend (Production)

1. Use production database
2. Set `DEBUG=False` in .env
3. Deploy with Gunicorn:
   ```powershell
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
   ```

### Frontend (Production)

1. Build for production:
   ```powershell
   npm run build
   ```
2. Serve `dist/` directory with nginx or similar

### Docker

Coming soon!

## 🤝 Contributing

Contributions welcome! Please:

1. Maintain ethical design principles
2. Keep model explainable
3. Add tests for new features
4. Update documentation

## ⚠️ Disclaimer

This system is for educational and research purposes. Predictions should not be the sole basis for law enforcement decisions. Always combine with human judgment and local knowledge.

## 🆘 Troubleshooting

### Backend won't start
- ✅ Check PostgreSQL is running
- ✅ Verify DATABASE_URL in .env
- ✅ Ensure PostGIS extension is installed

### Frontend shows errors
- ✅ Check backend is running (http://localhost:8000)
- ✅ Verify CORS settings in main.py
- ✅ Clear browser cache

### No data showing
- ✅ Run `python scripts\init_database.py`
- ✅ Check database has grid_cells table
- ✅ Verify region bounds in config

## 📞 Support

For questions or issues:
- Open an issue on GitHub
- Check API docs: http://localhost:8000/docs

---

**Built for NSBEHackathon 2026**  
*Ethical, Explainable, Environmental-focused Crime Risk Prediction*