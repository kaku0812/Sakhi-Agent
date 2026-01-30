# Sakhi - Women's Safety Monitoring System

An AI-powered safety ecosystem that provides proactive monitoring, real-time location tracking, and intelligent safety alerts for women's travel safety.

---

## 🚀 How It Works (End-to-End Flow)

### Setup
1. Install Kiro CLI
2. Copy custom prompts & agents from `.kiro/` to `~/.kiro/`
3. Install dependencies as per [QUICKSTART.md](QUICKSTART.md)
4. Verify all MCP servers load in Kiro

### Flow 1: Trip Planning & Proactive Alerts
```
@women-safety-trip-planner I am going to Mumbai from Delhi on Feb 5, 10:00 AM
```
**What happens:**
- Gathers safety news around destination
- Fetches weather info
- Sends preparedness plan to Telegram + generates HTML report
- Saves trip to `trips.json`

**Automation:** Run `python scheduler.py` in background — checks every 30 mins for upcoming trips. 4 hours before departure, auto-invokes `women-safety-guardian` agent → sends safety alert to Telegram.

### Flow 2: Real-Time Location Monitoring
Android app continuously stores snapshots (location, battery, network) locally and syncs to cloud.

**Query anytime via Kiro:**
```
> Tell me where she is right now
> What's the battery level?
```

### Flow 3: Emergency SOS Response
When SOS button is pressed on Android app:
1. Run `python sos_scheduler.py` in background (polls every 5 seconds)
2. Detects pending SOS → **beeps** → auto-invokes `uber-emergency-booker` agent
3. Agent books Uber ride from current location to safe destination + sends Telegram alert

**All flows work both automatically (via schedulers) and manually (via Kiro chat).**

---

## 🎯 What Is This?

**Sakhi** is a comprehensive safety system built with custom MCP (Model Context Protocol) servers that integrate with Kiro CLI. It combines weather intelligence, news analysis, location monitoring, and instant messaging to keep women safe during travel.

---

## 🔧 Core Components

### 1. Weather MCP Server (`sakhi-weather`)
Fetches real-time weather data for any location using OpenWeather API.
- Temperature, humidity, wind conditions
- Weather-based safety recommendations
- Travel planning assistance

### 2. News MCP Server (`sakhi-news`)
Aggregates news from 15+ Indian RSS feeds, classifies and clusters articles.
- Location-based article filtering
- Safety keyword classification (harassment, crime alerts)
- Source attribution with direct links

### 3. Telegram MCP Server (`sakhi-telegram`)
Sends instant alerts via Telegram bot (free alternative to SMS).
- Emergency notifications
- Trip safety reports
- Real-time status updates

### 4. Location Monitor MCP Server (`sakhi-location`)
Monitors device location, battery, and network status in real-time.
- GPS coordinates (latitude/longitude)
- Battery level monitoring
- Network connectivity status
- Cloud sync from Android app

---

## 🔗 Live Links & Resources

| Resource | Link | Description |
|----------|------|-------------|
| **PyPI Package** | https://pypi.org/project/hackathon-sakhi/ | Install via `uvx` |
| **Location API** | https://sakhi-location-api.onrender.com | Backend for location data |
| **SOS Server** | https://serverforridebooking.onrender.com | Emergency ride booking API |

---

## ⚡ Quick Setup

### 1. Install UV
```powershell
# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Mac/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Configure Kiro MCP (`~/.kiro/settings/mcp.json`)
```json
{
  "mcpServers": {
    "sakhi-weather": {
      "command": "uvx",
      "args": ["--from", "hackathon-sakhi", "sakhi-weather"],
      "env": { "OPENWEATHER_API_KEY": "your-api-key" }
    },
    "sakhi-news": {
      "command": "uvx",
      "args": ["--from", "hackathon-sakhi", "sakhi-news"]
    },
    "sakhi-telegram": {
      "command": "uvx",
      "args": ["--from", "hackathon-sakhi", "sakhi-telegram"],
      "env": {
        "TELEGRAM_BOT_TOKEN": "your-bot-token",
        "TELEGRAM_CHAT_ID": "your-chat-id"
      }
    },
    "sakhi-location": {
      "command": "uvx",
      "args": ["--from", "hackathon-sakhi", "sakhi-location"],
      "env": { "LOCATION_API_URL": "https://sakhi-location-api.onrender.com" }
    }
  }
}
```

### 3. Get API Keys
- **OpenWeather**: https://openweathermap.org/api (free tier)
- **Telegram Bot**: Create via [@BotFather](https://t.me/BotFather) on Telegram

### 4. Test in Kiro
```bash
kiro-cli chat
> What's the weather in Delhi?
> Show me safety news for Mumbai
> Send a test message via Telegram
> Get current location status
```

---

## 📱 Android App

A companion Kotlin app that continuously stores **location snapshots** (latitude, longitude, battery %, network status) locally using Room Database, then syncs to the cloud when connected.

**Key Features:**
- **Offline-First** — GPS works without internet; data stored locally in SQLite
- **Auto-Sync** — Pushes snapshots to FastAPI backend when network available
- **SOS Button** — One-tap emergency button triggers ride booking + Telegram alert
- **Background Service** — Foreground service ensures continuous monitoring

**Backend API:** https://sakhi-location-api.onrender.com  
⚠️ *Free tier — may have cold start delay of ~30 seconds*

**APK Location**: `kotlin-app/app/build/outputs/apk/debug/app-debug.apk`  
📱 **Try Online:** [Appetize.io Demo](https://appetize.io/) *(upload link after release)*

---

## ⏰ Automation & Schedulers

Two Python schedulers run locally and poll continuously:

- **`scheduler.py`** — Checks `trips.json` every 30 mins; triggers safety analysis 4 hours before departure
- **`sos_scheduler.py`** — Polls SOS endpoint every 30 seconds; plays **beep sound** on new SOS; invokes `uber-emergency-booker` agent

> ⚙️ **Configuration:** Edit `CHECK_INTERVAL_MINUTES` in `scheduler.py` or `CHECK_INTERVAL_SECONDS` in `sos_scheduler.py` to adjust polling frequency. Also update `KIRO_CLI_WSL_PATH` with your kiro-cli path.

**SOS Endpoint:** https://serverforridebooking.onrender.com  
⚠️ *Free tier — may have cold start delay*

**How it works:**
1. User taps SOS on Android → POST to SOS endpoint
2. Scheduler detects pending request → beep alert
3. Agent auto-books Uber ride + sends Telegram notification

**Query data anytime** via Kiro CLI:
```bash
kiro-cli chat
> Tell me where she is right now. Give time in IST.
> What's her battery level?
> Is she connected to network?
```
*(Location API stores timestamps in UTC; agents can convert to IST)*

---

## 🤖 Custom Agents & Prompts

Located in `.kiro/` directory:

**Agents:**
- **`women-safety-guardian`** — Analyzes trip safety using weather, news & location data; sends Telegram alerts
- **`uber-emergency-booker`** — Handles SOS requests and books emergency Uber rides via deep links
  > ⚙️ Default destination offset: `latitude + 0.01`. Edit the agent prompt in `.kiro/agents/uber-emergency-booker.json` to customize safe destination coordinates.

**Prompts:**
- **`women-safety-trip-planner`** — Collects trip details (source, destination, time) and saves to `trips.json`

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| [QUICKSTART.md](QUICKSTART.md) | Quick 2-minute setup |
| [SETUP_GUIDE.md](SETUP_GUIDE.md) | Comprehensive setup guide |
| [DEVLOG.md](DEVLOG.md) | Development timeline & decisions |
| [ARCHITECTURE.html](ARCHITECTURE.html) | Visual flow diagrams |

---

## 🏗️ Architecture Overview

📐 **[View Architecture Diagrams](ARCHITECTURE.html)** — Open in browser for professional flow diagrams

---

**Built with ❤️ for the Kiro Hackathon**
