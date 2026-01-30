# Render Deployment Changes Tracker
# Last Updated: 2026-01-26

## Overview
This file tracks all changes made for Render deployment of the Location Monitor.

## New Files Created (Nothing Modified!)

### 1. Backend (FastAPI for Render)
Location: `mcp-servers/location-monitor/render/`

| File | Purpose |
|------|---------|
| `app_render.py` | FastAPI server with PostgreSQL support |
| `requirements_render.txt` | Dependencies for Render |
| `Dockerfile` | Container configuration |
| `render.yaml` | Render deployment blueprint |
| `README_RENDER.md` | Deployment guide |
| `location_mcp_render.py` | MCP server that connects to Render API |
| `.gitignore` | Ignore local files |

### 2. Android App
Location: `kotlin-app/app/src/main/java/com/example/combinedflow/network/`

| File | Purpose |
|------|---------|
| `Api.kt` | Alternative Api.kt with Render URL |

### 3. PyPI Package
Location: `src/hackathon_sakhi/`

| File | Purpose |
|------|---------|
| `location_v2.py` | Updated location MCP for PyPI |


## Deployment Steps

### Step 1: Deploy to Render
1. Go to https://render.com and sign up
2. Create PostgreSQL database (free tier)
3. Deploy web service from `mcp-servers/location-monitor/render/`
4. Note your URL: `https://sakhi-location-api.onrender.com`

### Step 2: Update Android App
Replace content of `Api.kt` with `Api_Render.kt`:
- Change: `const val BASE_URL = "https://sakhi-location-api.onrender.com/"`
- Rebuild app

### Step 3: Update PyPI Package
1. Update `pyproject.toml` to use `location_v2.py`
2. Bump version to 0.2.0
3. Rebuild and upload to PyPI

### Step 4: Test
```bash
# Test API directly
curl https://sakhi-location-api.onrender.com/health

# Test MCP server
LOCATION_API_URL=https://sakhi-location-api.onrender.com uvx --from hackathon-sakhi sakhi-location
```

## Environment Variables

### For MCP Server
```
LOCATION_API_URL=https://sakhi-location-api.onrender.com
```

### For Render (auto-configured)

## API Endpoints (Render)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/` | API info |
| POST | `/sync/snapshots` | Upload from Android |
| GET | `/snapshots` | Get recent (100) |
| GET | `/snapshots/recent?hours=24` | Get by time |
| GET | `/status` | Device status |
| DELETE | `/snapshots/clear` | Clear all data |


## Notes
- Free tier spins down after 15 min inactivity (30s cold start)
- PostgreSQL free tier: 1GB, 30 days

