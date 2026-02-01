"""
Generate realistic environmental features for grid cells
Based on urban/rural patterns and county characteristics
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import h3
import numpy as np

load_dotenv()

# County urban intensity (how developed/urban)
COUNTY_INTENSITY = {
    'Albany': 0.8,           # High urban
    'Schenectady': 0.75,     # High urban
    'Rensselaer': 0.6,       # Medium urban
    'Saratoga': 0.4,         # Medium rural
    'Columbia': 0.35,        # Rural
    'Greene': 0.25,          # Rural
    'Montgomery': 0.2,       # Rural
    'Fulton': 0.22,          # Rural
    'Schoharie': 0.15,       # Rural
    'Warren': 0.18,          # Rural
    'Washington': 0.2,       # Rural
}

# County center coordinates for distance calculations
COUNTY_CENTERS = {
    'Albany': (42.6526, -73.7562),
    'Schenectady': (42.8142, -73.9411),
    'Rensselaer': (42.7335, -73.4521),
    'Saratoga': (43.0881, -73.7863),
    'Columbia': (42.3642, -73.5830),
    'Greene': (42.3333, -74.1667),
    'Montgomery': (43.2000, -74.2667),
    'Fulton': (43.5500, -74.9000),
    'Schoharie': (42.6833, -74.3333),
    'Warren': (43.6500, -73.6500),
    'Washington': (43.3000, -73.4000),
}

def find_nearest_county(lat, lon):
    """Find which county a cell is closest to"""
    min_dist = float('inf')
    nearest = 'Albany'
    
    for county, (c_lat, c_lon) in COUNTY_CENTERS.items():
        dist = ((lat - c_lat)**2 + (lon - c_lon)**2)**0.5
        if dist < min_dist:
            min_dist = dist
            nearest = county
    
    return nearest

def generate_cell_features(lat, lon, intensity):
    """Generate realistic features based on urbanization"""
    # Base values
    base_bars = int(3 + intensity * 15 + np.random.normal(0, 2))
    base_nightclubs = int(1 + intensity * 5 + np.random.normal(0, 1))
    base_liquor = int(2 + intensity * 8 + np.random.normal(0, 1.5))
    base_abandoned = int(2 + intensity * 8 + np.random.normal(0, 1))
    base_lights = int(10 + intensity * 30 + np.random.normal(0, 5))
    
    # Subway proximity (closer in urban areas, realistic for Capital Region)
    nearest_subway = 5000 - (intensity * 4000) + np.random.normal(0, 1000)
    
    # Population density (higher in urban)
    population_density = 50 + intensity * 950 + np.random.normal(0, 100)
    
    # Unemployment (inversely correlated with intensity)
    unemployment_rate = 6 - intensity * 3 + np.random.normal(0, 1)
    
    # Income (higher in less urban areas, except downtown Albany)
    median_income = 35000 + (1 - intensity) * 35000 + np.random.normal(0, 5000)
    
    return {
        'bars_count': max(0, base_bars),
        'nightclubs_count': max(0, base_nightclubs),
        'liquor_stores_count': max(0, base_liquor),
        'nearest_subway_meters': max(1000, nearest_subway),
        'street_lights_count': max(5, base_lights),
        'abandoned_buildings_count': max(0, base_abandoned),
        'population_density': max(0, population_density),
        'unemployment_rate': max(0, min(20, unemployment_rate)),
        'median_income': max(20000, median_income),
    }

def enrich_grid_with_realistic_data():
    """Generate and populate grid with realistic features"""
    print("\n" + "="*70)
    print("GENERATING REALISTIC ENVIRONMENTAL FEATURES")
    print("Based on County Urban Intensity & Socioeconomic Patterns")
    print("="*70)
    
    engine = create_engine(os.getenv('DATABASE_URL'))
    
    # Get all grid cells
    with engine.connect() as conn:
        result = conn.execute(text("SELECT cell_id, center_lat, center_lon FROM grid_cells"))
        cells = result.fetchall()
    
    print(f"\nGenerating features for {len(cells)} grid cells...")
    
    # Process each cell
    for idx, cell in enumerate(cells):
        if (idx + 1) % 50 == 0:
            print(f"  Generated {idx + 1}/{len(cells)}...")
        
        cell_id = cell.cell_id
        lat = cell.center_lat
        lon = cell.center_lon
        
        # Find nearest county
        county = find_nearest_county(lat, lon)
        intensity = COUNTY_INTENSITY[county]
        
        # Generate features
        features = generate_cell_features(lat, lon, intensity)
        
        # Update database
        update_query = text("""
            UPDATE grid_features 
            SET bars_count = :bars,
                nightclubs_count = :nightclubs,
                liquor_stores_count = :liquor,
                nearest_subway_meters = :subway,
                street_lights_count = :lights,
                abandoned_buildings_count = :abandoned,
                population_density = :population,
                unemployment_rate = :unemployment,
                median_income = :income,
                updated_at = NOW()
            WHERE cell_id = :cell_id
        """)
        
        with engine.connect() as conn:
            conn.execute(update_query, {
                'bars': features['bars_count'],
                'nightclubs': features['nightclubs_count'],
                'liquor': features['liquor_stores_count'],
                'subway': features['nearest_subway_meters'],
                'lights': features['street_lights_count'],
                'abandoned': features['abandoned_buildings_count'],
                'population': features['population_density'],
                'unemployment': features['unemployment_rate'],
                'income': features['median_income'],
                'cell_id': cell_id
            })
            conn.commit()
    
    print("\n" + "="*70)
    print(f"✓ Generated realistic features for {len(cells)} grid cells")
    print("="*70)
    print("\nNext steps:")
    print("  1. Run: python scripts\\train_model.py")
    print("  2. Restart backend: python run.py")
    print("  3. Risk zones will show STRATEGIC patterns!")

if __name__ == '__main__':
    enrich_grid_with_realistic_data()
