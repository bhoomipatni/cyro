"""
Initialize database schema and load sample data for Capital Region (Albany, NY)

This script creates the necessary tables and populates them with:
1. Grid cells (H3 hexagons covering the region)
2. Environmental features for each cell
3. Police station locations

Data sources (for production deployment):
- OpenStreetMap for POIs (bars, liquor stores, etc.)
- NYC Open Data / Albany Open Data for police stations
- Census data for socioeconomic indicators
"""

import h3
import numpy as np
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv

load_dotenv()

# Capital Region bounds (Albany, NY area)
REGION_BOUNDS = {
    'min_lat': 42.5,
    'max_lat': 42.9,
    'min_lon': -74.1,
    'max_lon': -73.5
}

H3_RESOLUTION = 9  # ~0.1 km² cells


def create_schema(engine):
    """Create database tables"""
    
    print("Creating database schema...")
    
    with engine.begin() as conn:
        # Enable PostGIS
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
        
        # Grid cells table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS grid_cells (
                cell_id VARCHAR(20) PRIMARY KEY,
                center_lat DOUBLE PRECISION NOT NULL,
                center_lon DOUBLE PRECISION NOT NULL,
                geom GEOMETRY(Point, 4326),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        
        # Create spatial index
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_grid_cells_geom 
            ON grid_cells USING GIST(geom);
        """))
        
        # Grid features table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS grid_features (
                cell_id VARCHAR(20) PRIMARY KEY REFERENCES grid_cells(cell_id),
                
                -- Alcohol-related venues
                bars_count INTEGER DEFAULT 0,
                nightclubs_count INTEGER DEFAULT 0,
                liquor_stores_count INTEGER DEFAULT 0,
                
                -- Transit
                nearest_subway_meters DOUBLE PRECISION,
                
                -- Infrastructure
                street_lights_count INTEGER DEFAULT 0,
                abandoned_buildings_count INTEGER DEFAULT 0,
                
                -- Population/Socioeconomic
                population_density DOUBLE PRECISION DEFAULT 0,  -- per sq km
                median_income DOUBLE PRECISION,
                unemployment_rate DOUBLE PRECISION,  -- percentage
                
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        
        # Police stations table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS police_stations (
                station_id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                address TEXT,
                geom GEOMETRY(Point, 4326),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_police_stations_geom 
            ON police_stations USING GIST(geom);
        """))
    
    print("✓ Schema created successfully")


def generate_grid_cells(engine):
    """Generate H3 grid cells covering the Capital Region"""
    
    print(f"Generating H3 grid (resolution {H3_RESOLUTION})...")
    
    # Generate cells
    cells = set()
    
    # Sample points across the region
    lats = np.linspace(
        REGION_BOUNDS['min_lat'], 
        REGION_BOUNDS['max_lat'], 
        20
    )
    lons = np.linspace(
        REGION_BOUNDS['min_lon'], 
        REGION_BOUNDS['max_lon'], 
        20
    )
    
    for lat in lats:
        for lon in lons:
            cell = h3.latlng_to_cell(lat, lon, H3_RESOLUTION)
            cells.add(cell)
    
    print(f"Generated {len(cells)} grid cells")
    
    # Insert cells
    with Session(engine) as session:
        for cell_id in cells:
            lat, lon = h3.cell_to_latlng(cell_id)
            
            session.execute(text("""
                INSERT INTO grid_cells (cell_id, center_lat, center_lon, geom)
                VALUES (:cell_id, :lat, :lon, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326))
                ON CONFLICT (cell_id) DO NOTHING
            """), {
                'cell_id': cell_id,
                'lat': lat,
                'lon': lon
            })
        
        session.commit()
    
    print("✓ Grid cells inserted")
    return len(cells)


def generate_sample_features(engine, num_cells):
    """
    Generate sample environmental features for each cell
    
    In production, this would pull real data from:
    - OpenStreetMap (POIs)
    - Census Bureau (demographics)
    - Local government databases (infrastructure)
    """
    
    print("Generating sample environmental features...")
    
    with Session(engine) as session:
        # Get all cell IDs
        result = session.execute(text("SELECT cell_id FROM grid_cells"))
        cell_ids = [row[0] for row in result]
        
        # Generate features for each cell
        for cell_id in cell_ids:
            # Simulate realistic but random features
            # In production, these would be real measurements
            
            features = {
                'cell_id': cell_id,
                'bars_count': np.random.poisson(2),
                'nightclubs_count': np.random.poisson(0.5),
                'liquor_stores_count': np.random.poisson(1),
                'nearest_subway_meters': np.random.uniform(100, 5000),
                'street_lights_count': np.random.poisson(8),
                'abandoned_buildings_count': np.random.poisson(0.5),
                'population_density': np.random.uniform(1000, 8000),
                'median_income': np.random.uniform(35000, 85000),
                'unemployment_rate': np.random.uniform(3, 12)
            }
            
            session.execute(text("""
                INSERT INTO grid_features (
                    cell_id, bars_count, nightclubs_count, liquor_stores_count,
                    nearest_subway_meters, street_lights_count, 
                    abandoned_buildings_count, population_density,
                    median_income, unemployment_rate
                )
                VALUES (
                    :cell_id, :bars_count, :nightclubs_count, :liquor_stores_count,
                    :nearest_subway_meters, :street_lights_count,
                    :abandoned_buildings_count, :population_density,
                    :median_income, :unemployment_rate
                )
                ON CONFLICT (cell_id) DO UPDATE SET
                    bars_count = EXCLUDED.bars_count,
                    nightclubs_count = EXCLUDED.nightclubs_count,
                    liquor_stores_count = EXCLUDED.liquor_stores_count,
                    nearest_subway_meters = EXCLUDED.nearest_subway_meters,
                    street_lights_count = EXCLUDED.street_lights_count,
                    abandoned_buildings_count = EXCLUDED.abandoned_buildings_count,
                    population_density = EXCLUDED.population_density,
                    median_income = EXCLUDED.median_income,
                    unemployment_rate = EXCLUDED.unemployment_rate,
                    updated_at = CURRENT_TIMESTAMP
            """), features)
        
        session.commit()
    
    print(f"✓ Features generated for {len(cell_ids)} cells")


def load_police_stations(engine):
    """
    Load police station locations
    
    Sample data for Capital Region (Albany, NY area)
    In production, load from official sources
    """
    
    print("Loading police stations...")
    
    stations = [
        # Albany County
        {
            'name': 'Albany Police Department',
            'lat': 42.6526,
            'lon': -73.7562,
            'address': '165 Henry Johnson Blvd, Albany, NY 12210'
        },
        {
            'name': 'Albany County Sheriff\'s Office',
            'lat': 42.6543,
            'lon': -73.7590,
            'address': '200 South Pearl Street, Albany, NY 12207'
        },
        {
            'name': 'Cohoes Police Department',
            'lat': 42.7681,
            'lon': -73.7083,
            'address': 'Cohoes, NY 12047'
        },
        {
            'name': 'Watervliet Police Department',
            'lat': 42.7417,
            'lon': -73.7047,
            'address': 'Watervliet, NY 12189'
        },
        {
            'name': 'Green Island Police Department',
            'lat': 42.7550,
            'lon': -73.6967,
            'address': 'Green Island, NY 12183'
        },
        {
            'name': 'Bethlehem Police Department',
            'lat': 42.6159,
            'lon': -73.8209,
            'address': 'Bethlehem, NY 12010'
        },
        {
            'name': 'Colonie Police Department',
            'lat': 42.7281,
            'lon': -73.8320,
            'address': '312 Wolf Rd, Colonie, NY 12205'
        },
        {
            'name': 'Coeymans Police Department',
            'lat': 42.5217,
            'lon': -73.8184,
            'address': 'Coeymans, NY 12045'
        },
        {
            'name': 'Guilderland Police Department',
            'lat': 42.6892,
            'lon': -73.8584,
            'address': 'Guilderland, NY 12084'
        },
        # Schenectady County
        {
            'name': 'Schenectady Police Department',
            'lat': 42.8142,
            'lon': -73.9396,
            'address': '531 Liberty St, Schenectady, NY 12305'
        },
        {
            'name': 'Schenectady County Sheriff\'s Office',
            'lat': 42.8156,
            'lon': -73.9341,
            'address': 'Schenectady, NY 12305'
        },
        {
            'name': 'Scotia Police Department',
            'lat': 42.8224,
            'lon': -73.8803,
            'address': 'Scotia, NY 12302'
        },
        {
            'name': 'Rotterdam Police Department',
            'lat': 42.7906,
            'lon': -73.9717,
            'address': 'Rotterdam, NY 12303'
        },
        {
            'name': 'Glenville Police Department',
            'lat': 42.8547,
            'lon': -73.9089,
            'address': 'Glenville, NY 12302'
        },
        # Rensselaer County
        {
            'name': 'Troy Police Department',
            'lat': 42.7284,
            'lon': -73.6918,
            'address': '1 Morton Ave, Troy, NY 12180'
        },
        {
            'name': 'Rensselaer Police Department',
            'lat': 42.6501,
            'lon': -73.6431,
            'address': 'Rensselaer, NY 12144'
        },
        {
            'name': 'Rensselaer County Sheriff\'s Office',
            'lat': 42.7278,
            'lon': -73.6905,
            'address': 'Troy, NY 12180'
        },
        {
            'name': 'East Greenbush Police Department',
            'lat': 42.5958,
            'lon': -73.5983,
            'address': 'East Greenbush, NY 12061'
        },
        {
            'name': 'North Greenbush Police Department',
            'lat': 42.6917,
            'lon': -73.6667,
            'address': 'North Greenbush, NY 12144'
        },
        # Saratoga County
        {
            'name': 'Saratoga Springs Police Department',
            'lat': 43.0856,
            'lon': -73.7857,
            'address': 'Saratoga Springs, NY 12866'
        },
        {
            'name': 'Saratoga County Sheriff\'s Office',
            'lat': 43.0617,
            'lon': -73.7831,
            'address': 'Ballston Spa, NY 12020'
        },
        {
            'name': 'Waterford Police Department',
            'lat': 42.7750,
            'lon': -73.6756,
            'address': 'Waterford, NY 12188'
        },
        {
            'name': 'Mechanicville Police Department',
            'lat': 42.9156,
            'lon': -73.6847,
            'address': 'Mechanicville, NY 12118'
        }
    ]
    
    with Session(engine) as session:
        for station in stations:
            session.execute(text("""
                INSERT INTO police_stations (name, address, geom)
                VALUES (
                    :name, 
                    :address, 
                    ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)
                )
            """), station)
        
        session.commit()
    
    print(f"✓ Loaded {len(stations)} police stations")


def main():
    """Initialize database with schema and sample data"""
    
    print("\n" + "="*60)
    print("Crime Risk Database Initialization")
    print("="*60 + "\n")
    
    # Connect to database
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set in environment")
        print("Please create a .env file with DATABASE_URL")
        return
    
    print(f"Connecting to database...")
    engine = create_engine(database_url)
    
    try:
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✓ Database connection successful\n")
        
        # Create schema
        create_schema(engine)
        
        # Generate grid
        num_cells = generate_grid_cells(engine)
        
        # Generate features
        generate_sample_features(engine, num_cells)
        
        # Load police stations
        load_police_stations(engine)
        
        print("\n" + "="*60)
        print("✓ Database initialization complete!")
        print("="*60)
        print(f"\nSummary:")
        print(f"  - Grid cells: {num_cells}")
        print(f"  - Police stations: 5")
        print(f"  - Region: Capital Region (Albany, NY)")
        print(f"\nNext steps:")
        print("  1. Run calibrate_model.py to tune weights (optional)")
        print("  2. Start the API: python run.py")
        print("  3. View API docs: http://localhost:8000/docs")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nTroubleshooting:")
        print("  - Ensure PostgreSQL is running")
        print("  - Ensure PostGIS extension is installed")
        print("  - Check DATABASE_URL in .env file")
        raise


if __name__ == "__main__":
    main()
