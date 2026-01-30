#!/usr/bin/env python3

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from datetime import datetime
from sqlalchemy.orm import Session
from database import get_db, create_tables, engine
from models import snapshots, metadata
import sqlalchemy

# Create tables on startup
metadata.create_all(bind=engine)

class SnapshotPayload(BaseModel):
    local_id: int
    timestamp: int  # milliseconds
    battery: int
    network: bool
    lat: float
    lng: float

app = FastAPI(title="Location Snapshot API", version="1.0")

@app.post("/sync/snapshots")
async def upload_snapshots(payload: List[SnapshotPayload], db: Session = Depends(get_db)):
    """Receive location snapshots from mobile app."""
    acked_ids = []
    
    for snap in payload:
        # Insert into database
        query = snapshots.insert().values(
            local_id=snap.local_id,
            timestamp=datetime.fromtimestamp(snap.timestamp / 1000),
            battery=snap.battery,
            network=snap.network,
            lat=snap.lat,
            lng=snap.lng
        )
        
        with engine.connect() as conn:
            conn.execute(query)
            conn.commit()
        
        acked_ids.append(snap.local_id)
    
    return {"acked_ids": acked_ids}

@app.get("/snapshots")
async def get_snapshots():
    """Get all stored snapshots."""
    with engine.connect() as conn:
        result = conn.execute(snapshots.select().order_by(snapshots.c.timestamp.desc()).limit(100))
        snapshots_list = []
        
        for row in result:
            snapshots_list.append({
                "id": row.id,
                "local_id": row.local_id,
                "timestamp": row.timestamp.isoformat(),
                "battery": row.battery,
                "network": row.network,
                "lat": row.lat,
                "lng": row.lng
            })
    
    return snapshots_list

@app.get("/")
async def root():
    """Health check endpoint."""
    with engine.connect() as conn:
        count_result = conn.execute(sqlalchemy.text("SELECT COUNT(*) FROM snapshots"))
        count = count_result.scalar()
        
        latest_result = conn.execute(
            snapshots.select().order_by(snapshots.c.timestamp.desc()).limit(1)
        )
        latest_row = latest_result.fetchone()
        
        latest_snapshot = None
        if latest_row:
            latest_snapshot = {
                "timestamp": latest_row.timestamp.isoformat(),
                "battery": latest_row.battery,
                "location": {"lat": latest_row.lat, "lng": latest_row.lng}
            }
    
    return {
        "status": "running",
        "snapshots_count": count,
        "latest_snapshot": latest_snapshot
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
