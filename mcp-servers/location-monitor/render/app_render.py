#!/usr/bin/env python3
"""
FastAPI server for Location Monitor - Render Deployment Version
This is a NEW file - original fastapi_server.py is unchanged.

Optimized for:
- PostgreSQL (Render's free database)
- Production deployment
- CORS for mobile apps
- Health checks for Render
"""

import os
import logging
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import databases
import sqlalchemy
from sqlalchemy import Table, Column, Integer, Float, Boolean, DateTime, MetaData

# ============================================================================
# Configuration
# ============================================================================

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sakhi_snapshots.db")

# Render uses postgres:// but SQLAlchemy needs postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# Database Setup
# ============================================================================

database = databases.Database(DATABASE_URL)
metadata = MetaData()

snapshots = Table(
    "snapshots",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("local_id", Integer, nullable=False),
    Column("timestamp", DateTime, nullable=False, default=datetime.utcnow),
    Column("battery", Integer, nullable=False),
    Column("network", Boolean, nullable=False),
    Column("lat", Float, nullable=False),
    Column("lng", Float, nullable=False),
    Column("created_at", DateTime, default=datetime.utcnow),
)

engine = sqlalchemy.create_engine(
    DATABASE_URL,
    # SQLite specific settings (ignored for PostgreSQL)
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# Create tables
metadata.create_all(engine)

# ============================================================================
# Pydantic Models
# ============================================================================

class SnapshotPayload(BaseModel):
    """Payload from Android app"""
    local_id: int
    timestamp: int  # milliseconds since epoch
    battery: int
    network: bool
    lat: float
    lng: float


class SnapshotResponse(BaseModel):
    """Response format for snapshots"""
    id: int
    local_id: int
    timestamp: str
    battery: int
    network: bool
    lat: float
    lng: float


class SyncResponse(BaseModel):
    """Response after syncing snapshots"""
    acked_ids: List[int]
    count: int


class StatusResponse(BaseModel):
    """Device status summary"""
    status: str
    total_snapshots: int
    latest_snapshot: Optional[dict]
    battery_level: Optional[int]
    network_connected: Optional[bool]
    last_update: Optional[str]
    minutes_since_update: Optional[float]


# ============================================================================
# FastAPI App
# ============================================================================

app = FastAPI(
    title="Sakhi Location Monitor API",
    description="Backend for women safety location tracking - Hackathon Sakhi Project",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS - Allow Android app and web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for hackathon demo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Lifecycle Events
# ============================================================================

@app.on_event("startup")
async def startup():
    """Connect to database on startup"""
    logger.info(f"Connecting to database...")
    await database.connect()
    logger.info("Database connected!")


@app.on_event("shutdown")
async def shutdown():
    """Disconnect from database on shutdown"""
    await database.disconnect()
    logger.info("Database disconnected")


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint for Render"""
    return {"status": "healthy", "service": "sakhi-location-api"}


@app.get("/")
async def root():
    """Root endpoint with API info"""
    query = snapshots.select().order_by(snapshots.c.timestamp.desc()).limit(1)
    latest = await database.fetch_one(query)
    
    count_query = sqlalchemy.select(sqlalchemy.func.count()).select_from(snapshots)
    count = await database.fetch_val(count_query)
    
    return {
        "service": "Sakhi Location Monitor API",
        "version": "2.0.0",
        "status": "running",
        "total_snapshots": count,
        "latest_snapshot": {
            "timestamp": latest["timestamp"].isoformat() if latest else None,
            "battery": latest["battery"] if latest else None,
            "location": {"lat": latest["lat"], "lng": latest["lng"]} if latest else None
        } if latest else None,
        "endpoints": {
            "sync": "POST /sync/snapshots",
            "get_snapshots": "GET /snapshots",
            "get_recent": "GET /snapshots/recent?hours=24",
            "get_status": "GET /status",
            "clear": "DELETE /snapshots/clear"
        }
    }


@app.post("/sync/snapshots", response_model=SyncResponse)
async def upload_snapshots(payload: List[SnapshotPayload]):
    """
    Receive location snapshots from Android app.
    This is the main endpoint the Kotlin app calls.
    """
    acked_ids = []
    
    for snap in payload:
        try:
            query = snapshots.insert().values(
                local_id=snap.local_id,
                timestamp=datetime.fromtimestamp(snap.timestamp / 1000),
                battery=snap.battery,
                network=snap.network,
                lat=snap.lat,
                lng=snap.lng,
                created_at=datetime.utcnow()
            )
            await database.execute(query)
            acked_ids.append(snap.local_id)
            logger.info(f"Snapshot {snap.local_id} saved: battery={snap.battery}%, location=({snap.lat}, {snap.lng})")
        except Exception as e:
            logger.error(f"Error saving snapshot {snap.local_id}: {e}")
    
    return SyncResponse(acked_ids=acked_ids, count=len(acked_ids))


@app.get("/snapshots", response_model=List[SnapshotResponse])
async def get_snapshots(limit: int = 100):
    """Get recent snapshots (default last 100)"""
    query = snapshots.select().order_by(snapshots.c.timestamp.desc()).limit(limit)
    rows = await database.fetch_all(query)
    
    return [
        SnapshotResponse(
            id=row["id"],
            local_id=row["local_id"],
            timestamp=row["timestamp"].isoformat(),
            battery=row["battery"],
            network=row["network"],
            lat=row["lat"],
            lng=row["lng"]
        )
        for row in rows
    ]


@app.get("/snapshots/recent", response_model=List[SnapshotResponse])
async def get_recent_snapshots(hours: int = 24, limit: int = 100):
    """Get snapshots from the last N hours"""
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    
    query = (
        snapshots.select()
        .where(snapshots.c.timestamp > cutoff)
        .order_by(snapshots.c.timestamp.desc())
        .limit(limit)
    )
    rows = await database.fetch_all(query)
    
    return [
        SnapshotResponse(
            id=row["id"],
            local_id=row["local_id"],
            timestamp=row["timestamp"].isoformat(),
            battery=row["battery"],
            network=row["network"],
            lat=row["lat"],
            lng=row["lng"]
        )
        for row in rows
    ]


@app.get("/status", response_model=StatusResponse)
async def get_status():
    """Get device status summary - used by MCP server"""
    # Get count
    count_query = sqlalchemy.select(sqlalchemy.func.count()).select_from(snapshots)
    total = await database.fetch_val(count_query)
    
    if total == 0:
        return StatusResponse(
            status="no_data",
            total_snapshots=0,
            latest_snapshot=None,
            battery_level=None,
            network_connected=None,
            last_update=None,
            minutes_since_update=None
        )
    
    # Get latest
    query = snapshots.select().order_by(snapshots.c.timestamp.desc()).limit(1)
    latest = await database.fetch_one(query)
    
    minutes_since = (datetime.utcnow() - latest["timestamp"]).total_seconds() / 60
    
    return StatusResponse(
        status="active" if minutes_since < 30 else "stale",
        total_snapshots=total,
        latest_snapshot={
            "timestamp": latest["timestamp"].isoformat(),
            "location": {"lat": latest["lat"], "lng": latest["lng"]},
            "battery": latest["battery"],
            "network": latest["network"]
        },
        battery_level=latest["battery"],
        network_connected=latest["network"],
        last_update=latest["timestamp"].isoformat(),
        minutes_since_update=round(minutes_since, 1)
    )


@app.delete("/snapshots/clear")
async def clear_snapshots():
    """Clear all snapshots - useful for fresh start"""
    query = snapshots.delete()
    await database.execute(query)
    logger.info("All snapshots cleared")
    return {"status": "cleared", "message": "All snapshots deleted"}


# ============================================================================
# Run with Uvicorn
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
