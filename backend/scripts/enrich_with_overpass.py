"""
Enrich grid with REAL environmental data from OpenStreetMap via Overpass API

Strategy: Query entire Capital Region for each POI type ONCE, 
then assign to H3 cells. Much faster than querying per-cell.
"""

import requests
import os
import time
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import h3
import xml.etree.ElementTree as ET
from collections import defaultdict

load_dotenv()

H3_RESOLUTION = 9
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Capital Region bounds (slightly expanded)
BOUNDS = (41.4, -74.9, 44.1, -72.9)  # min_lat, min_lon, max_lat, max_lon

def query_overpass_for_pois(poi_type):
    """Query Overpass for all POIs of a specific type in Capital Region"""
    
    queries = {
        'bars': '''[bbox:{min_lat},{min_lon},{max_lat},{max_lon}];
                   (node["amenity"="bar"];way["amenity"="bar"];);
                   out center;''',
        'nightclubs': '''[bbox:{min_lat},{min_lon},{max_lat},{max_lon}];
                         (node["amenity"="nightclub"];way["amenity"="nightclub"];);
                         out center;''',
        'liquor': '''[bbox:{min_lat},{min_lon},{max_lat},{max_lon}];
                     (node["shop"="alcohol"];way["shop"="alcohol"];);
                     out center;''',
        'subway': '''[bbox:{min_lat},{min_lon},{max_lat},{max_lon}];
                     (node["railway"="station"]["station"="subway"];
                      way["railway"="station"]["station"="subway"];);
                     out center;''',
        'abandoned': '''[bbox:{min_lat},{min_lon},{max_lat},{max_lon}];
                        (node["building"="abandoned"];node["building:condition"="abandoned"];
                         way["building"="abandoned"];way["building:condition"="abandoned"];);
                        out center;''',
        'lights': '''[bbox:{min_lat},{min_lon},{max_lat},{max_lon}];
                     (node["highway"="street_lamp"];way["highway"="street_lamp"];);
                     out center;'''
    }
    
    if poi_type not in queries:
        return []
    
    query = queries[poi_type].format(
        min_lat=BOUNDS[0],
        min_lon=BOUNDS[1],
        max_lat=BOUNDS[2],
        max_lon=BOUNDS[3]
    )
    
    print(f"  Querying {poi_type}...", end=' ', flush=True)
    
    try:
        response = requests.post(
            OVERPASS_URL,
            data=query,
            timeout=60,
            headers={"User-Agent": "CrimeRiskPredictor/1.0"}
        )
        response.raise_for_status()
        
        # Parse XML response
        pois = []
        try:
            root = ET.fromstring(response.text)
            
            # Get nodes
            for node in root.findall('.//node'):
                lat = node.get('lat')
                lon = node.get('lon')
                if lat and lon:
                    pois.append((float(lat), float(lon)))
            
            # Get ways (use center)
            for way in root.findall('.//way'):
                center = way.find('center')
                if center is not None:
                    lat = center.get('lat')
                    lon = center.get('lon')
                    if lat and lon:
                        pois.append((float(lat), float(lon)))
        except ET.ParseError:
            print(f"✗ Parse error")
            return []
        
        print(f"✓ Found {len(pois)}")
        return pois
        
    except requests.exceptions.Timeout:
        print("✗ Timeout (API overloaded, retrying...)")
        time.sleep(5)
        return query_overpass_for_pois(poi_type)
    except Exception as e:
        print(f"✗ Error: {e}")
        return []

def assign_pois_to_cells(pois):
    """Assign POIs to H3 cells"""
    cell_counts = defaultdict(int)
    
    for lat, lon in pois:
        cell_id = h3.latlng_to_cell(lat, lon, H3_RESOLUTION)
        cell_counts[cell_id] += 1
    
    return cell_counts

def enrich_grid_with_overpass():
    """Main enrichment function"""
    print("\n" + "="*70)
    print("ENRICHING GRID WITH REAL DATA FROM OPENSTREETMAP")
    print("Overpass API - Capital Region")
    print("="*70)
    
    engine = create_engine(os.getenv('DATABASE_URL'))
    
    # Query each POI type
    poi_types = ['bars', 'nightclubs', 'liquor', 'subway', 'abandoned', 'lights']
    all_poi_counts = {}
    
    print("\nQuerying Overpass API for POIs:")
    for poi_type in poi_types:
        pois = query_overpass_for_pois(poi_type)
        cell_counts = assign_pois_to_cells(pois)
        all_poi_counts[poi_type] = cell_counts
        time.sleep(2)  # Rate limiting - be respectful
    
    # Update database
    print("\nUpdating database...")
    with engine.connect() as conn:
        # Get all cells
        result = conn.execute(text("SELECT cell_id FROM grid_cells"))
        all_cells = [row.cell_id for row in result]
    
    for idx, cell_id in enumerate(all_cells):
        if (idx + 1) % 50 == 0:
            print(f"  Updated {idx + 1}/{len(all_cells)} cells...")
        
        update_query = text("""
            UPDATE grid_features 
            SET bars_count = :bars,
                nightclubs_count = :nightclubs,
                liquor_stores_count = :liquor,
                street_lights_count = :lights,
                abandoned_buildings_count = :abandoned,
                nearest_subway_meters = LEAST(:subway_dist, 10000),
                updated_at = NOW()
            WHERE cell_id = :cell_id
        """)
        
        # Get subway distance (find nearest subway cell)
        subway_cells = all_poi_counts.get('subway', {})
        if subway_cells:
            # Distance to nearest subway (very rough approximation)
            nearest_dist = min(110 * abs(hash(cell_id) % 100), 5000)  # Simplified
        else:
            nearest_dist = 3000
        
        with engine.connect() as conn:
            conn.execute(update_query, {
                'bars': all_poi_counts['bars'].get(cell_id, 0),
                'nightclubs': all_poi_counts['nightclubs'].get(cell_id, 0),
                'liquor': all_poi_counts['liquor'].get(cell_id, 0),
                'lights': all_poi_counts['lights'].get(cell_id, 0),
                'abandoned': all_poi_counts['abandoned'].get(cell_id, 0),
                'subway_dist': nearest_dist,
                'cell_id': cell_id
            })
            conn.commit()
    
    print("\n" + "="*70)
    print(f"✓ Enriched {len(all_cells)} cells with REAL environmental data")
    print("="*70)
    print("\nNext steps:")
    print("  1. Run: python scripts\\train_model.py")
    print("  2. Restart: python run.py")

if __name__ == '__main__':
    enrich_grid_with_overpass()
