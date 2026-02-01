from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

try:
    # Count records
    cells = db.execute(text("SELECT COUNT(*) as count FROM grid_cells;")).fetchone()
    features = db.execute(text("SELECT COUNT(*) as count FROM grid_features;")).fetchone()
    stations = db.execute(text("SELECT COUNT(*) as count FROM police_stations;")).fetchone()

    print("=" * 50)
    print("DATABASE STATUS")
    print("=" * 50)
    print(f"Grid Cells:      {cells.count}")
    print(f"Grid Features:   {features.count}")
    print(f"Police Stations: {stations.count}")
    print("=" * 50)
    
    if cells.count == 400 and features.count == 400:
        print("✓ Database is fully populated!")
    else:
        print("⚠ Database may not be fully populated")
        
except Exception as e:
    print(f"Error connecting to database: {e}")
    
finally:
    db.close()
