# SAKHI - Judges Quick Start Guide

📦 **PyPI Package:** https://pypi.org/project/hackathon-sakhi/

**Important:** Open this project folder (`hackathon-project`) in Kiro. The agent reads `trips.json` from the workspace directory.

## Prerequisites

### 1. Install Kiro IDE
```
Download from: https://kiro.dev/
```

### 2. Install uv (Python package runner)
```bash
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Mac/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 3. Install Node.js (for Playwright MCP)
```
Download from: https://nodejs.org/
```

### 4. Verify installations
```bash
uvx --version
npx --version
```

---

## Setup MCP Servers

### 1. Copy mcp.json to Kiro global settings

**Windows:**
```powershell
Copy-Item ".kiro\settings\mcp.json" "$env:USERPROFILE\.kiro\settings\mcp.json"
```

**Mac/Linux:**
```bash
cp .kiro/settings/mcp.json ~/.kiro/settings/mcp.json
```

### 2. Install Playwright MCP (for browser automation)
```bash
npx playwright install
```
Playwright MCP is already configured in the agent files (`.kiro/agents/*.json`). 
Configure it in the same way globally.

### 3. Update uvx paths in mcp.json (IMPORTANT for scheduler/automation)

The MCP servers use `uvx` to run. If you plan to use the **automated schedulers** (`scheduler.py`, `sos_scheduler.py`), you need to update the `uvx` path in `.kiro/settings/mcp.json`.

**Find your uvx path:**
```bash
# Windows (PowerShell)
(Get-Command uvx).Source

# Mac/Linux
which uvx
```

**Update mcp.json:**

Open `.kiro/settings/mcp.json` and replace all instances of:
```json
"command": "uvx"
```

With YOUR full uvx path (if using schedulers):
```json
"command": "C:\\Users\\YourName\\.local\\bin\\uvx.exe"   // Windows
"command": "/home/yourname/.local/bin/uvx"              // Linux
"command": "/Users/yourname/.local/bin/uvx"             // Mac
```

**Why?** The schedulers run agents in non-interactive mode where PATH may not be loaded. Using the full path ensures `uvx` is found.

> **Note:** If you only use Kiro IDE interactively (not the schedulers), you can skip this step - Kiro handles PATH automatically.

### 4. Set environment variables

Create a `.env` file from the example:
```bash
cp .env.example .env
```

Edit `.env` with your values:
- **OPENWEATHER_API_KEY** - Get from https://openweathermap.org/api
- **TELEGRAM_BOT_TOKEN** - Create bot via https://t.me/BotFather
- **TELEGRAM_CHAT_ID** - Get your chat ID from https://t.me/userinfobot

Then set them before launching Kiro:

**Windows (PowerShell):**
```powershell
Get-Content .env | ForEach-Object { if ($_ -match "^([^=]+)=(.*)$") { [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process") } }
```

**Mac/Linux:**
```bash
export $(cat .env | xargs)
```

**Important:** Kiro must be launched AFTER setting these variables, or restart Kiro after setting them.

---

## Test MCP Servers

```bash
# Weather
uvx --from hackathon-sakhi sakhi-weather

# News
uvx --from hackathon-sakhi sakhi-news

# Telegram
uvx --from hackathon-sakhi sakhi-telegram

# Location
uvx --from hackathon-sakhi sakhi-location
```

---

## Dev Note: MCP Servers on PyPI

`mcp_env/` and `mcp-servers/` were our local development setup. We packaged and published them to PyPI:

```bash
# Build & publish (what we did)
pip install build twine
python -m build
twine upload dist/*
```

**Package:** https://pypi.org/project/hackathon-sakhi/ — Judges just run `uvx --from hackathon-sakhi <server>` (no local setup needed).

---

## Dev Note: Render Backend Deployment

Both backends are deployed on Render (free tier):

| Service | URL | Purpose |
|---------|-----|---------|
| Location API | https://sakhi-location-api.onrender.com | Android app sends location snapshots |
| SOS Server | https://serverforridebooking.onrender.com | Android SOS button triggers ride booking |

**⚠️ Free tier notes (applies to BOTH):**
- Servers spin down after 15min inactivity. **Wake them up first:** visit `/health` endpoints before testing.
- Database expires 30 days from creation (Feb 2026). Redeploy if expired.

**Location API files:** `mcp-servers/location-monitor/render/`
**SOS Server:** Deployed separately (simple Express server).

---

## Demo 1: Trip Safety Reminder

### Option A: Manual (recommended for demo)
```
/agent swap>> women-safety-guardian
@women-safety-guardian Check my trips and send reminders
```

### Option B: Automated scheduler
```bash
python scheduler.py  # Runs every 30min, sends reminders 4hr before trip
```

### Expected output
- Safety news gathered from RSS + web search
- Weather fetched
- Telegram message sent
- HTML report: `trip-safety-report-{destination}-{date}.html`

---

## Optional: Use Reusable Prompt

Copy the prompt file for trip planning:
```powershell
# Windows
Copy-Item ".kiro\prompts\women-safety-trip-planner.md" "$env:USERPROFILE\.kiro\prompts\"
```

Then use in Kiro: `@women-safety-trip-planner`

---

## Demo 2: SOS Emergency Ride Booking (Optional)

### 1. Update kiro-cli path (Windows only)
Edit `sos_scheduler.py` line ~27:
```python
KIRO_CLI_WSL_PATH = "/home/YOUR_WSL_USERNAME/.local/bin/kiro-cli"
```
Find your path by running in WSL: `which kiro-cli`

### 2. Start the SOS scheduler (auto-polls every 30s)
```bash
python sos_scheduler.py
```

### 3. Trigger a test SOS request
```powershell
Invoke-RestMethod -Uri "https://serverforridebooking.onrender.com/book-ride" -Method POST -ContentType "application/json" -Body '{"latitude": 12.9352, "longitude": 77.6245, "user_id": "test_user"}'
```

### 4. Expected output
- 🔊 Alert beeps play
- Scheduler detects pending request within 30s
- Invokes `uber-emergency-booker` agent automatically
- Agent opens Uber deep link and books ride
- Request marked as completed

**Note:** Requires WSL with `kiro-cli` installed for auto-invocation.

---

## Android App (Optional)

To enable emergency features, update these phone numbers:

1. **Emergency SMS alerts** (your phone receives SOS messages):
   - File: `kotlin-app/.../emergency/EmergencySmsManager.kt`
   - Field: `EMERGENCY_PHONE = ""`

2. **Kiro Agent SMS** (for SMS-based ride requests):
   - File: `kotlin-app/.../emergency/UberRideRequestManager.kt`
   - Field: `KIRO_AGENT_PHONE = ""`



