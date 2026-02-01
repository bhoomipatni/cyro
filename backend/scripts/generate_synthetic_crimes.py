"""
Generate realistic synthetic crime data for Capital Region (11 counties)

This creates training data for the C.Y.R.O. model with realistic patterns:
- Geographic distribution (higher crime in urban areas)
- Temporal patterns (more crime at night)
- Crime type variety
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

# Capital Region counties with centers and relative crime rates
COUNTIES = {
    'Albany': {'lat': 42.6526, 'lon': -73.7562, 'crime_rate': 0.75},
    'Schenectady': {'lat': 42.8142, 'lon': -73.9411, 'crime_rate': 0.70},
    'Rensselaer': {'lat': 42.7335, 'lon': -73.4521, 'crime_rate': 0.55},
    'Saratoga': {'lat': 43.0881, 'lon': -73.7863, 'crime_rate': 0.35},
    'Columbia': {'lat': 42.3642, 'lon': -73.5830, 'crime_rate': 0.40},
    'Greene': {'lat': 42.3333, 'lon': -74.1667, 'crime_rate': 0.30},
    'Montgomery': {'lat': 43.2000, 'lon': -74.2667, 'crime_rate': 0.25},
    'Fulton': {'lat': 43.5500, 'lon': -74.9000, 'crime_rate': 0.28},
    'Schoharie': {'lat': 42.6833, 'lon': -74.3333, 'crime_rate': 0.20},
    'Warren': {'lat': 43.6500, 'lon': -73.6500, 'crime_rate': 0.22},
    'Washington': {'lat': 43.3000, 'lon': -73.4000, 'crime_rate': 0.25},
}

CRIME_TYPES = [
    'assault', 'burglary', 'theft', 'robbery', 'drug possession',
    'vandalism', 'vehicle theft', 'harassment', 'disorderly conduct',
    'trespassing', 'grand larceny', 'petit larceny', 'stolen property'
]

def generate_crime_location(county_info):
    """Generate random location within county"""
    lat = county_info['lat'] + np.random.normal(0, 0.3)
    lon = county_info['lon'] + np.random.normal(0, 0.3)
    return lat, lon

def generate_temporal_pattern(hour):
    """Return crime probability multiplier for given hour"""
    # More crime at night (1-5 AM peak)
    pattern = {
        0: 1.3, 1: 1.5, 2: 1.4, 3: 1.2, 4: 1.0,
        5: 0.6, 6: 0.5, 7: 0.6, 8: 0.7, 9: 0.8,
        10: 0.85, 11: 0.9, 12: 0.95, 13: 1.0, 14: 1.1,
        15: 1.2, 16: 1.3, 17: 1.4, 18: 1.4, 19: 1.3,
        20: 1.3, 21: 1.3, 22: 1.2, 23: 1.2
    }
    return pattern.get(hour, 1.0)

def generate_synthetic_crimes(num_crimes=27000):
    """Generate synthetic crime data with realistic patterns"""
    print("\n" + "="*60)
    print("C.Y.R.O. - Synthetic Crime Data Generator (EXPANDED)")
    print("Capital Region (11 Counties)")
    print("="*60)
    
    print(f"\nGenerating {num_crimes:,} synthetic crime incidents...")
    
    crimes = []
    start_date = datetime.now() - timedelta(days=365)
    
    for i in range(num_crimes):
        if (i + 1) % 5000 == 0:
            print(f"  Generated {i + 1:,} incidents...")
        
        # Select county weighted by crime rate
        county_name = np.random.choice(
            list(COUNTIES.keys()),
            p=[COUNTIES[c]['crime_rate'] / sum(COUNTIES[c]['crime_rate'] for c in COUNTIES)
               for c in COUNTIES]
        )
        county_info = COUNTIES[county_name]
        
        # Generate location
        lat, lon = generate_crime_location(county_info)
        
        # Generate date/time with temporal pattern
        days_offset = np.random.randint(0, 365)
        hour = np.random.randint(0, 24)
        minute = np.random.randint(0, 60)
        
        crime_date = start_date + timedelta(days=days_offset, hours=hour, minutes=minute)
        
        # Apply temporal weighting (more crime at night)
        temporal_mult = generate_temporal_pattern(hour)
        if np.random.random() > temporal_mult:
            continue  # Skip some based on temporal pattern
        
        # Select crime type
        crime_type = np.random.choice(CRIME_TYPES)
        
        crimes.append({
            'latitude': lat,
            'longitude': lon,
            'crime_date': crime_date.strftime('%Y-%m-%d %H:%M:%S'),
            'crime_type': crime_type,
            'county': county_name
        })
    
    # Create DataFrame
    df = pd.DataFrame(crimes)
    
    # Create directory if needed
    os.makedirs('data/raw', exist_ok=True)
    
    # Save to CSV
    csv_path = 'data/raw/historical_crimes.csv'
    df.to_csv(csv_path, index=False)
    
    print(f"\n✓ Generated {len(crimes):,} incidents")
    print(f"✓ Saved to: {csv_path}")
    
    # Statistics
    print("\n" + "="*60)
    print("SYNTHETIC DATA STATISTICS")
    print("="*60)
    
    print(f"\nTotal incidents: {len(df)}")
    print("\nIncidents by county:")
    print(df['county'].value_counts())
    
    print("\nIncidents by crime type:")
    print(df['crime_type'].value_counts())
    
    date_range = pd.to_datetime(df['crime_date'])
    print(f"\nDate range: {date_range.min()} to {date_range.max()}")
    
    print(f"\nGeographic bounds:")
    print(f"  Latitude:  {df['latitude'].min():.4f} to {df['latitude'].max():.4f}")
    print(f"  Longitude: {df['longitude'].min():.4f} to {df['longitude'].max():.4f}")
    
    print("\n" + "="*60)
    print("✓ Ready to train model!")
    print("Run: python scripts\\train_model.py")
    print("="*60)

if __name__ == '__main__':
    generate_synthetic_crimes(num_crimes=27000)
