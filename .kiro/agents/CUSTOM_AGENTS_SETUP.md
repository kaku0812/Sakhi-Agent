# Custom Agents & Prompts Setup

This project showcases advanced Kiro CLI capabilities through custom agents and prompts.

## 🤖 Custom Agents

### 1. Women Safety Guardian
Analyzes trip safety using weather, news & location data; sends Telegram alerts.

### 2. Uber Emergency Booker  
Handles SOS requests and books emergency Uber rides via deep links.

## 📝 Custom Prompt

### Women Safety Trip Planner
Collects trip details (source, destination, time) and saves to `trips.json`.

---

## Setup Instructions

### Step 1: Copy Agents to Global Kiro Directory
```bash
# From project root
cp .kiro/agents/women-safety-guardian.json ~/.kiro/agents/
cp .kiro/agents/uber-emergency-booker.json ~/.kiro/agents/
```

### Step 2: Copy Custom Prompt
```bash
cp .kiro/prompts/women-safety-trip-planner.md ~/.kiro/prompts/
```

### Step 3: Verify Installation
```bash
ls ~/.kiro/agents/
ls ~/.kiro/prompts/
```

---

## Usage Examples

### Plan a Trip
```bash
kiro-cli chat
# Type: @women-safety-trip-planner
# Input: "I'm traveling from Delhi to Mumbai on Feb 5 at 10:00 AM"
```

### Interactive Safety Chat
```bash
kiro-cli --agent women-safety-guardian
# Try: "Is Noida safe for women?"
# Try: "Check my trips and send reminders"
```

### Emergency Ride Booking
```bash
kiro-cli --agent uber-emergency-booker
# Automatically handles pending SOS requests
# Or: "Book a ride from Koramangala to Indiranagar"
```

---

## Configuration

### Scheduler Settings
Edit `scheduler.py` to adjust:
- `CHECK_INTERVAL_MINUTES` — How often to check for trips (default: 30)
- `REMINDER_HOURS_BEFORE` — When to send reminder (default: 4 hours before)

### Uber Agent Settings
Edit `.kiro/agents/uber-emergency-booker.json` to customize:
- Safe destination calculation (default: `latitude + 0.01`)
- Common coordinates for your area

---

## Quick Test
```bash
# 1. Plan a trip
kiro-cli chat
# @women-safety-trip-planner Delhi to Mumbai tomorrow 3 PM

# 2. Run scheduler (checks every 30 mins, alerts 4 hrs before trip)
python scheduler.py

# 3. Check generated files
ls trips.json *.html
```



