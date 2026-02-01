"""
FastAPI endpoints for Crime Risk API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import h3
import httpx
import asyncio

from ..core.database import get_db
from ..services.risk_calculator import risk_calculator

router = APIRouter()

# --- Response Models ---

class RiskZone(BaseModel):
    cell_id: str
    center_lat: float
    center_lon: float
    risk_score: float
    risk_level: str
    confidence: float
    prediction_time: datetime

class RiskFactors(BaseModel):
    cell_id: str
    alcohol_contribution: float
    transit_contribution: float
    lighting_contribution: float
    vacancy_contribution: float
    population_contribution: float
    socioeconomic_contribution: float
    temporal_contribution: float
    explanation: str

class PoliceStation(BaseModel):
    station_id: int
    name: str
    latitude: float
    longitude: float
    address: Optional[str]

class RiskAtPoint(BaseModel):
    cell_id: str
    center_lat: float
    center_lon: float
    risk_score: float
    risk_level: str
    distance_meters: float

# --- Helper Functions ---

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in miles"""
    from math import radians, sin, cos, sqrt, atan2
    
    R = 3959  # Earth radius in miles
    
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    return R * c

# --- Endpoints ---

@router.get("/risk-zones", response_model=List[RiskZone])
async def get_risk_zones(
    lat: float = Query(..., ge=42.0, le=43.0),
    lon: float = Query(..., ge=-74.5, le=-73.5),
    radius: float = Query(1.0, ge=0.5, le=50.0),
    prediction_time: Optional[datetime] = None,
    hour: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Get predicted risk zones within radius of a point
    
    Args:
        lat: Center latitude
        lon: Center longitude
        radius: Radius in miles (0.5-50.0)
        prediction_time: Time to predict for (default: 1 hour from now)
        hour: Hour of day (0-23) to predict for
        
    Returns:
        List of risk zones with scores
    """
    if prediction_time is None:
        if hour is not None:
            # Use specified hour with today's date
            now = datetime.now()
            prediction_time = now.replace(hour=hour, minute=0, second=0, microsecond=0)
        else:
            # Default: 1 hour from now
            prediction_time = datetime.now() + timedelta(hours=1)
    
    # Get H3 cell at center
    center_h3 = h3.latlng_to_cell(lat, lon, 9)
    
    # Get k-ring (approximate number of rings needed)
    k = int(radius * 3)
    cell_ids = list(h3.grid_disk(center_h3, k))
    
    # Query grid cells
    query = text("""
        SELECT cell_id, center_lat, center_lon
        FROM grid_cells
        WHERE cell_id = ANY(:cell_ids)
    """)
    
    result = db.execute(query, {"cell_ids": cell_ids})
    cells = result.fetchall()
    
    # Filter by exact distance and calculate risk
    risk_zones = []
    
    for cell in cells:
        distance = haversine_distance(
            lat, lon,
            cell.center_lat, cell.center_lon
        )
        
        if distance <= radius:
            # Get features for this cell
            features_query = text("""
                SELECT * FROM grid_features WHERE cell_id = :cell_id
            """)
            features_result = db.execute(
                features_query,
                {"cell_id": cell.cell_id}
            ).fetchone()
            
            if features_result:
                features_dict = dict(features_result._mapping)
                
                # Calculate risk
                risk_data = risk_calculator.calculate_risk(
                    features_dict,
                    prediction_time
                )
                
                risk_zones.append(RiskZone(
                    cell_id=cell.cell_id,
                    center_lat=cell.center_lat,
                    center_lon=cell.center_lon,
                    risk_score=risk_data['risk_score'],
                    risk_level=risk_data['risk_level'],
                    confidence=0.75,
                    prediction_time=prediction_time
                ))
    
    return risk_zones


@router.get("/risk-factors/{cell_id}", response_model=RiskFactors)
async def get_risk_factors(
    cell_id: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed risk factor breakdown for a specific cell
    
    Args:
        cell_id: H3 cell identifier
        
    Returns:
        Detailed factor contributions and explanation
    """
    # Get cell features
    query = text("""
        SELECT * FROM grid_features WHERE cell_id = :cell_id
    """)
    
    result = db.execute(query, {"cell_id": cell_id}).fetchone()
    
    if not result:
        raise HTTPException(status_code=404, detail="Cell not found")
    
    features = dict(result._mapping)
    
    # Calculate risk with current time
    risk_data = risk_calculator.calculate_risk(
        features,
        datetime.now()
    )
    
    contributions = risk_data['contributions']
    
    # Generate explanation
    sorted_factors = sorted(
        contributions.items(),
        key=lambda x: abs(x[1]),
        reverse=True
    )[:3]
    
    explanation = "Primary risk factors: " + ", ".join([
        f"{factor[0].replace('_', ' ')} ({factor[1]:.1f}%)"
        for factor in sorted_factors
    ])
    
    return RiskFactors(
        cell_id=cell_id,
        alcohol_contribution=contributions.get('alcohol_density', 0),
        transit_contribution=contributions.get('transit_proximity', 0),
        lighting_contribution=contributions.get('lighting', 0),
        vacancy_contribution=contributions.get('vacancy', 0),
        population_contribution=contributions.get('population', 0),
        socioeconomic_contribution=contributions.get('socioeconomic', 0),
        temporal_contribution=contributions.get('temporal', 0),
        explanation=explanation
    )


@router.get("/risk-at-point", response_model=RiskAtPoint)
async def get_risk_at_point(
    lat: float = Query(...),
    lon: float = Query(...),
    prediction_time: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """
    Get risk for the nearest grid cell to a specific point
    """
    if prediction_time is None:
        prediction_time = datetime.now() + timedelta(hours=1)

    nearest_query = text("""
        SELECT
            cell_id,
            center_lat,
            center_lon,
            ST_Distance(
                geom::geography,
                ST_SetSRID(ST_Point(:lon, :lat), 4326)::geography
            ) AS distance
        FROM grid_cells
        ORDER BY distance
        LIMIT 1
    """)

    nearest = db.execute(nearest_query, {"lat": lat, "lon": lon}).fetchone()

    if not nearest:
        raise HTTPException(status_code=404, detail="No nearby grid cell found")

    features_query = text("""
        SELECT * FROM grid_features WHERE cell_id = :cell_id
    """)
    features_result = db.execute(features_query, {"cell_id": nearest.cell_id}).fetchone()

    if not features_result:
        raise HTTPException(status_code=404, detail="Grid cell features not found")

    features_dict = dict(features_result._mapping)
    risk_data = risk_calculator.calculate_risk(features_dict, prediction_time)

    return RiskAtPoint(
        cell_id=nearest.cell_id,
        center_lat=nearest.center_lat,
        center_lon=nearest.center_lon,
        risk_score=risk_data['risk_score'],
        risk_level=risk_data['risk_level'],
        distance_meters=float(nearest.distance)
    )


@router.get("/police-stations", response_model=List[PoliceStation])
async def get_police_stations(
    min_lat: float = Query(...),
    max_lat: float = Query(...),
    min_lon: float = Query(...),
    max_lon: float = Query(...),
    db: Session = Depends(get_db)
):
    """
    Get police stations within bounding box
    """
    query = text("""
        SELECT 
            station_id,
            name,
            ST_Y(geom) as latitude,
            ST_X(geom) as longitude,
            address
        FROM police_stations
        WHERE ST_Contains(
            ST_MakeEnvelope(:min_lon, :min_lat, :max_lon, :max_lat, 4326),
            geom
        )
    """)
    
    result = db.execute(query, {
        "min_lat": min_lat,
        "max_lat": max_lat,
        "min_lon": min_lon,
        "max_lon": max_lon
    })
    
    stations = []
    for row in result:
        stations.append(PoliceStation(
            station_id=row.station_id,
            name=row.name,
            latitude=row.latitude,
            longitude=row.longitude,
            address=row.address
        ))
    
    return stations


@router.get("/health")
async def health_check():
    """API health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "version": "1.0.0"
    }


@router.get("/geocode")
async def geocode_address(q: str = Query(...)):
    """
    Geocode an address using Nominatim
    Backend proxy to avoid CORS issues
    
    Args:
        q: Address query string
        
    Returns:
        List of location results with lat/lon
    """
    try:
        async with httpx.AsyncClient() as client:
            # Try multiple query formats
            queries = [
                f"{q}, New York, USA",
                f"{q}, NY, USA",
                q
            ]
            
            results = []
            for query_str in queries:
                response = await client.get(
                    "https://nominatim.openstreetmap.org/search",
                    params={
                        "q": query_str,
                        "format": "json",
                        "limit": 5,
                        "countrycodes": "us",
                        "viewbox": "-74.9865,41.4775,-72.9322,44.0081",  # Capital Region bounds
                        "bounded": "1"
                    },
                    headers={"User-Agent": "CrimeRiskPredictor/1.0"},
                    timeout=10.0
                )
                response.raise_for_status()
                results = response.json()
                if results:
                    break
            
            print(f"Geocoding '{q}': found {len(results)} results")
            return results
    except httpx.HTTPError as e:
        print(f"HTTP Error during geocoding: {e}")
        raise HTTPException(status_code=502, detail="Geocoding service unavailable")
    except Exception as e:
        print(f"Geocoding error: {e}")
        raise HTTPException(status_code=500, detail=f"Geocoding failed: {str(e)}")