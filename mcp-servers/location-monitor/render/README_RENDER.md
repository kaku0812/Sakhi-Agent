# Location Monitor - Render Deployment Guide

## Overview
This folder contains everything needed to deploy the Location Monitor backend to Render.

## Architecture
```
┌─────────────────┐     ┌──────────────────────┐     ┌─────────────────┐
│  Android App    │────▶│  Render FastAPI      │◀────│  MCP Server     │
│  (Kotlin)       │     │  + PostgreSQL        │     │  (sakhi-location)│
└─────────────────┘     └──────────────────────┘     └─────────────────┘
     Sends snapshots         Stores data              Reads data for AI
```

## Files Created
- `app_render.py` - FastAPI server optimized for Render
- `requirements_render.txt` - Dependencies including psycopg2
- `Dockerfile` - Container configuration
- `render.yaml` - Render deployment blueprint

## Deployment Steps

### Step 1: Create Render Account
1. Go to https://render.com
2. Sign up with GitHub

### Step 2: Create PostgreSQL Database
1. Dashboard → New → PostgreSQL
2. Name: `sakhi-location-db`
3. Region: Oregon (US West) or closest to you
4. Plan: Free
5. Click "Create Database"
6. **Copy the "Internal Database URL"** (starts with `postgres://`)

### Step 3: Deploy FastAPI Web Service
1. Dashboard → New → Web Service
2. Choose "Deploy from a Git repository" OR "Deploy from Docker"
3. If using Git:
   - Connect your GitHub repo
   - Root directory: `mcp-servers/location-monitor/render`
4. If using Docker:
   - Use the Dockerfile in this folder
5. Settings:
   - Name: `sakhi-location-api`
   - Region: Same as database
   - Plan: Free
   - Environment Variables:
     - `DATABASE_URL` = (paste Internal Database URL from Step 2)
6. Click "Create Web Service"

### Step 4: Get Your URL
After deployment, you'll get a URL like:
```
https://sakhi-location-api.onrender.com
```

### Step 5: Update Android App
Change `Api.kt` BASE_URL to your Render URL:
```kotlin
const val BASE_URL: String = "https://sakhi-location-api.onrender.com/"
```

### Step 6: Update MCP Server
Set environment variable:
```
FASTAPI_BASE_URL=https://sakhi-location-api.onrender.com
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/sync/snapshots` | Upload location snapshots from Android |
| GET | `/snapshots` | Get recent snapshots (limit 100) |
| GET | `/snapshots/recent` | Get snapshots from last N hours |
| GET | `/status` | Get device status summary |
| GET | `/health` | Health check |
| DELETE | `/snapshots/clear` | Clear all snapshots (fresh start) |

## Testing the Deployment

```bash
# Health check
curl https://sakhi-location-api.onrender.com/health

# Get snapshots
curl https://sakhi-location-api.onrender.com/snapshots

# Get status
curl https://sakhi-location-api.onrender.com/status
```

## Notes
- Free tier spins down after 15 mins of inactivity (first request takes ~30s)
- PostgreSQL free tier: 1GB storage, 30 days retention


## Troubleshooting

### "Connection refused"
- Wait 30 seconds for cold start on free tier

### "Database connection error"
- Check DATABASE_URL environment variable
- Ensure PostgreSQL is in same region

### Android app not sending data
- Check the BASE_URL in Api.kt matches Render URL
- Ensure URL ends with `/`
