"""
Train C.Y.R.O. risk prediction model using historical crime data

This script:
1. Loads historical crime incidents from CSV
2. Aggregates crimes to grid cells
3. Trains a logistic regression model
4. Learns optimal feature weights based on actual crime patterns
5. Exports weights for use in risk_calculator.py

Required data format: CSV with columns:
- latitude (float)
- longitude (float)
- crime_date (YYYY-MM-DD or timestamp)
- crime_type (string, optional)
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
import h3
import os
from dotenv import load_dotenv
import json

load_dotenv()

H3_RESOLUTION = 9


def load_historical_crimes(csv_path):
    """
    Load historical crime data from CSV
    
    Required columns: latitude, longitude, crime_date
    Optional: crime_type, severity
    """
    print(f"\nLoading historical crimes from: {csv_path}")
    
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Crime data file not found: {csv_path}")
    
    crimes = pd.read_csv(csv_path)
    print(f"✓ Loaded {len(crimes)} crime records")
    
    # Validate required columns
    required = ['latitude', 'longitude']
    missing = [col for col in required if col not in crimes.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    return crimes


def aggregate_crimes_to_grid(crimes, database_url):
    """
    Aggregate crime incidents to grid cells
    Creates binary labels: 1 = crime occurred, 0 = no crime
    """
    print("\nAggregating crimes to grid cells...")
    
    # Get all grid cells from database
    engine = create_engine(database_url)
    with Session(engine) as session:
        result = session.execute(text("SELECT cell_id FROM grid_cells"))
        all_cells = set(row[0] for row in result)
    
    print(f"Total grid cells: {len(all_cells)}")
    
    # Map crimes to cells
    crime_cells = set()
    for idx, crime in crimes.iterrows():
        lat = crime['latitude']
        lon = crime['longitude']
        cell_id = h3.latlng_to_cell(lat, lon, H3_RESOLUTION)
        crime_cells.add(cell_id)
    
    print(f"Cells with crime incidents: {len(crime_cells)}")
    
    # Create binary labels for all cells
    labels = {}
    for cell_id in all_cells:
        labels[cell_id] = 1 if cell_id in crime_cells else 0
    
    return labels


def prepare_training_data(database_url, labels):
    """
    Get features and labels for model training
    """
    print("\nPreparing training data...")
    
    engine = create_engine(database_url)
    
    with Session(engine) as session:
        result = session.execute(text("""
            SELECT 
                gc.cell_id,
                gf.bars_count,
                gf.nightclubs_count,
                gf.liquor_stores_count,
                gf.nearest_subway_meters,
                gf.street_lights_count,
                gf.abandoned_buildings_count,
                gf.population_density,
                gf.median_income,
                gf.unemployment_rate
            FROM grid_cells gc
            LEFT JOIN grid_features gf ON gc.cell_id = gf.cell_id
        """))
        
        data = []
        cell_ids = []
        for row in result:
            cell_id = row[0]
            if cell_id in labels:
                data.append({
                    'bars_count': row[1] or 0,
                    'nightclubs_count': row[2] or 0,
                    'liquor_stores_count': row[3] or 0,
                    'nearest_subway_meters': row[4] or 5000,
                    'street_lights_count': row[5] or 0,
                    'abandoned_buildings_count': row[6] or 0,
                    'population_density': row[7] or 0,
                    'median_income': row[8] or 50000,
                    'unemployment_rate': row[9] or 5.0,
                })
                cell_ids.append(cell_id)
        
        df = pd.DataFrame(data)
        y = np.array([labels[cell_id] for cell_id in cell_ids])
    
    print(f"✓ Prepared {len(df)} samples")
    print(f"  - Crime cells: {np.sum(y)}")
    print(f"  - Safe cells: {len(y) - np.sum(y)}")
    
    return df, y


def train_model(X, y):
    """
    Train logistic regression model
    """
    print("\nTraining logistic regression model...")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train model
    model = LogisticRegression(max_iter=1000, random_state=42)
    model.fit(X_train_scaled, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test_scaled)
    y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
    
    print("\n" + "="*60)
    print("MODEL PERFORMANCE")
    print("="*60)
    print(f"\nAccuracy: {model.score(X_test_scaled, y_test):.4f}")
    print(f"ROC-AUC: {roc_auc_score(y_test, y_pred_proba):.4f}")
    
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=['Safe', 'Crime']))
    
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred))
    
    # Extract weights
    feature_names = X.columns
    weights = model.coef_[0]
    
    print("\n" + "="*60)
    print("LEARNED FEATURE WEIGHTS")
    print("="*60)
    
    weight_dict = {}
    for name, weight in zip(feature_names, weights):
        weight_dict[name] = float(weight)
        print(f"{name:30s}: {weight:8.6f}")
    
    return model, scaler, weight_dict


def main():
    """
    Main training pipeline
    """
    print("\n" + "="*60)
    print("C.Y.R.O. MODEL TRAINING")
    print("Crime Yield & Reporting Overview")
    print("="*60)
    
    # Check for crime data
    crime_data_path = "data/raw/historical_crimes.csv"
    
    if not os.path.exists(crime_data_path):
        print(f"\n❌ ERROR: Crime data not found at {crime_data_path}")
        print("\nTo train the model, you need:")
        print("1. Create folder: backend/data/raw/")
        print("2. Add file: historical_crimes.csv")
        print("\nCSV format required:")
        print("  - latitude (float)")
        print("  - longitude (float)")
        print("  - crime_date (YYYY-MM-DD or timestamp)")
        print("  - crime_type (optional)")
        return
    
    try:
        # Load crimes
        crimes = load_historical_crimes(crime_data_path)
        
        # Get database connection
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL not set in .env")
        
        # Aggregate to grid
        labels = aggregate_crimes_to_grid(crimes, database_url)
        
        # Prepare data
        X, y = prepare_training_data(database_url, labels)
        
        # Train model
        model, scaler, weights = train_model(X, y)
        
        # Save weights
        output_path = "trained_weights.json"
        with open(output_path, 'w') as f:
            json.dump(weights, f, indent=2)
        
        print(f"\n✓ Weights saved to: {output_path}")
        print("\nTo use these weights, update risk_calculator.py:")
        print("  WEIGHTS = " + str(weights))
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        raise


if __name__ == "__main__":
    main()
