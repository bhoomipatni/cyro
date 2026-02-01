# C.Y.R.O. Data & Model Training Workflow

## Overview
This document explains how to populate C.Y.R.O. with real data and train the risk prediction model.

---

## Phase 1: Get Real Environmental Data (Overpass API)

### Step 1a: Install dependencies
```powershell
pip install requests
```

### Step 1b: Run enrichment script
```powershell
cd backend

# Test with 10 cells first (takes ~10-15 minutes)
python scripts\enrich_with_overpass.py 10

# After testing, run on all cells (takes several hours)
python scripts\enrich_with_overpass.py
```

This will query Overpass API for:
- ✅ Bars, nightclubs, liquor stores
- ✅ Subway/transit stations
- ✅ Abandoned/vacant buildings
- ✅ Street lights

Database gets updated with **real counts** for each grid cell.

---

## Phase 2: Train Model on Historical Crime Data

### Step 2a: Prepare historical crime data

Create a CSV file: `backend/data/raw/historical_crimes.csv`

**Required format:**
```csv
latitude,longitude,crime_date,crime_type
42.6526,-73.7562,2023-01-15,assault
42.6530,-73.7565,2023-01-16,theft
42.6520,-73.7560,2023-01-17,burglary
...
```

**Data sources for Albany/Capital Region:**
- NYC Open Data: https://data.cityofnewyork.us/
- Albany Police Department
- Crime reports from local news archives
- Any police department open data portal

### Step 2b: Create data folder
```powershell
mkdir backend\data\raw
```

### Step 2c: Add your crime data
Place your `historical_crimes.csv` in `backend/data/raw/`

### Step 2d: Run training script
```powershell
python scripts\train_model.py
```

This will:
1. Load historical crimes
2. Aggregate to grid cells (1 = crime, 0 = safe)
3. Train logistic regression model
4. **Learn optimal feature weights** from actual data
5. Output `trained_weights.json`

---

## Phase 3: Update Risk Calculator with Learned Weights

### Step 3a: Check training output
After training, you'll see something like:

```
LEARNED FEATURE WEIGHTS
────────────────────────────────────────
bars_count:                 0.523410
nightclubs_count:           0.412850
liquor_stores_count:        0.389120
nearest_subway_meters:      0.001234
street_lights_count:       -0.234560
abandoned_buildings_count:  0.876543
population_density:         0.023456
unemployment_rate:          0.456789
median_income:             -0.000123
```

### Step 3b: Update risk_calculator.py

In `backend/app/services/risk_calculator.py`, replace the WEIGHTS dict:

```python
WEIGHTS = {
    'bars_count': 0.523410,
    'nightclubs_count': 0.412850,
    'liquor_stores_count': 0.389120,
    'nearest_subway_meters': 0.001234,
    'street_lights_count': -0.234560,
    'abandoned_buildings_count': 0.876543,
    'population_density': 0.023456,
    'unemployment_rate': 0.456789,
    'median_income': -0.000123,
}
```

### Step 3c: Restart backend
```powershell
# Press Ctrl+C to stop
# Restart:
python run.py
```

---

## Complete Workflow Summary

```
1. Initialize Database
   └─ python scripts\init_database.py

2. Enrich with Real Data (Overpass API)
   └─ python scripts\enrich_with_overpass.py

3. Prepare Historical Crime Data
   └─ Create backend/data/raw/historical_crimes.csv

4. Train Model
   └─ python scripts\train_model.py

5. Update Weights
   └─ Edit backend/app/services/risk_calculator.py

6. Restart Backend
   └─ python run.py

7. Test Frontend
   └─ Search for addresses → See REAL risk scores
```

---

## API Rate Limits

### Overpass API
- **Rate**: Queries take time (1-2 seconds each)
- **Limit**: ~10,000 requests per day per IP
- **Cost**: FREE
- **Workaround**: Run at night or stagger requests

### Your System
- 400 grid cells × 6 POI types = 2,400 queries
- Expected time: 1-2 hours with built-in delays
- One-time cost (run once, cache results)

---

## What Happens After Setup

When a user enters an address:

```
User: "Albany, NY"
  ↓
1. Geocode → Get lat/lon
  ↓
2. Find nearby grid cells
  ↓
3. Look up REAL environmental features from database
  ├─ Real bar count (from Overpass)
  ├─ Real subway proximity (from Overpass)
  ├─ Real abandoned buildings (from Overpass)
  ├─ Real street lighting (from Overpass)
  └─ Real population/unemployment (Census data)
  ↓
4. Apply LEARNED weights (from your crime model)
  ↓
5. Adjust for time-of-day
  ↓
6. Return risk score with explanations
```

---

## Troubleshooting

### Overpass API timing out
- Try again later (server might be busy)
- Run fewer cells at a time: `python scripts\enrich_with_overpass.py 5`

### No crime data available
- Use mock data for now (random CSV)
- Model will still train but weights may be less accurate

### Model training fails
- Check CSV format is correct
- Ensure database has grid cells

### Risk scores not changing
- Verify weights were updated
- Check backend restarted after weight update

---

## Next Steps

1. **Get historical crime data** - This is the critical piece
2. **Run Overpass enrichment** - Get real POI data
3. **Train the model** - Learn from your local data
4. **Verify results** - Test with real addresses

The power of C.Y.R.O. comes from **your local historical data**!
