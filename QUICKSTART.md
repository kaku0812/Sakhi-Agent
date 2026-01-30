# 🚀 Hackathon Sakhi - Judge Setup Guide

**Time to setup: ~2 minutes**

---

## Step 1: Install UV (One-time)

UV is a fast Python package runner. Install it:

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Mac/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Verify installation:
```bash
uvx --version
```

---

## Step 2: Add MCP Servers to Kiro

Add this to your Kiro MCP config file:

**Location:** `~/.kiro/settings/mcp.json` (create if doesn't exist)

```json
{
  "mcpServers": {
    "sakhi-weather": {
      "command": "uvx",
      "args": ["--from", "hackathon-sakhi", "sakhi-weather"],
      "env": {
        "OPENWEATHER_API_KEY": "YOUR_OPENWEATHER_API_KEY"
      }
    },
    "sakhi-news": {
      "command": "uvx",
      "args": ["--from", "hackathon-sakhi", "sakhi-news"]
    },
    "sakhi-telegram": {
      "command": "uvx",
      "args": ["--from", "hackathon-sakhi", "sakhi-telegram"],
      "env": {
        "TELEGRAM_BOT_TOKEN": "YOUR_BOT_TOKEN",
        "TELEGRAM_CHAT_ID": "YOUR_CHAT_ID"
      }
    },
    "sakhi-location": {
      "command": "uvx",
      "args": ["--from", "hackathon-sakhi", "sakhi-location"],
      "env": {
        "FASTAPI_BASE_URL": "https://sakhi-location-api.onrender.com"
      }
    }
  }
}
```

> **Note:** Get your free OpenWeather API key from https://openweathermap.org/api. For Telegram, create your own bot via [@BotFather](https://t.me/BotFather).

---

## Step 3: Verify in Kiro

```bash
kiro-cli chat
```

Then type:
```
/mcp
```

You should see: `sakhi-weather`, `sakhi-news`, `sakhi-telegram`

---

## Step 4: Test the Servers

Try these queries in Kiro:

```
What's the weather in Mumbai?
```

```
Show me women safety news for Delhi
```

```
Send a Telegram message saying "Hello from Sakhi!"
```

---

## Available Tools

| Server | Tool | Description |
|--------|------|-------------|
| sakhi-weather | `get_hackathon_weather(city)` | Get weather for any city |
| sakhi-news | `hackathon_women_safety_news_dashboard(location?)` | Get clustered safety news |
| sakhi-telegram | `send_hackathon_telegram_message(message)` | Send Telegram alerts |
| sakhi-location | `get_hackathon_device_status()` | Get tracked device status |
| sakhi-location | `get_hackathon_recent_snapshots()` | Get location history |
| sakhi-location | `check_hackathon_emergency_conditions()` | Detect emergencies |

---

## Quick Test (Without Kiro)

Test directly in terminal:

```powershell
# Test Weather (set your API key first)
$env:OPENWEATHER_API_KEY="YOUR_OPENWEATHER_API_KEY"
uvx --from hackathon-sakhi sakhi-weather

# Test News (no env vars needed)
uvx --from hackathon-sakhi sakhi-news
```

The server will start and wait for MCP input. Press `Ctrl+C` to stop.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `uvx: command not found` | Restart terminal after installing UV |
| Server doesn't start | Check environment variables are set |
| No tools showing in Kiro | Restart Kiro after editing mcp.json |

---

## Package Info

- **PyPI:** https://pypi.org/project/hackathon-sakhi/
- **Version:** 0.2.0
- **Location API:** https://sakhi-location-api.onrender.com
- **No Python installation required** - UV handles everything automatically
