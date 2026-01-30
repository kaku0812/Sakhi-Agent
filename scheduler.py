#!/usr/bin/env python3
"""
Women Safety Guardian - Cross-Platform Scheduler
Works on Windows, Mac, and Linux without crontab setup.
Just run: python scheduler.py

Judges can simply run this script and it handles everything automatically.
"""

import json
import subprocess
import shutil
import os
import sys
import time
import signal
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
TRIPS_FILE = Path(__file__).parent / "trips.json"
AGENT_NAME = "women-safety-guardian"
CHECK_INTERVAL_MINUTES = 30  # How often to check for trips (configurable)
REMINDER_HOURS_BEFORE = 4

# WSL kiro-cli path - UPDATE THIS TO YOUR WSL USERNAME
# Find your path by running in WSL: which kiro-cli
KIRO_CLI_WSL_PATH = "/home/YOUR_WSL_USERNAME/.local/bin/kiro-cli"

# Telegram config - UPDATE THESE WITH YOUR OWN VALUES
# Get bot token from @BotFather, chat ID from @userinfobot
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "YOUR_TELEGRAM_CHAT_ID")

# Track running state
running = True

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    global running
    print("\n🛑 Scheduler stopped.")
    running = False
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def get_kiro_command(agent_query):
    """Get the full kiro command as a list - same pattern as sos_scheduler"""
    if sys.platform == "win32":
        # Run through WSL with full path - same as sos_scheduler
        escaped_query = agent_query.replace("'", "'\\''")
        # Convert Windows path to WSL path for workspace
        # UPDATE THIS PATH to your workspace location
        wsl_workspace = "/mnt/c/Users/YOUR_USERNAME/path/to/hackathon-project"
        # Use bash -lc (login shell) to load PATH properly for uvx
        return [
            "wsl", "bash", "-lc",
            f"cd {wsl_workspace} && {KIRO_CLI_WSL_PATH} chat --agent {AGENT_NAME} --no-interactive --trust-all-tools '{escaped_query}'"
        ]
    else:
        # On Linux/Mac, try to find kiro-cli
        kiro_path = shutil.which("kiro-cli")
        if not kiro_path:
            kiro_path = str(Path.home() / ".local" / "bin" / "kiro-cli")
        return [
            kiro_path, "chat",
            "--agent", AGENT_NAME,
            "--no-interactive",
            "--trust-all-tools",
            agent_query
        ]

def send_telegram_message(message):
    """Send message directly via Telegram Bot API"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = urllib.parse.urlencode({
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }).encode('utf-8')
        
        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode())
            return result.get("ok", False)
    except Exception as e:
        log(f"⚠️ Telegram error: {e}")
        return False

def log(message):
    """Print with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def check_and_send_reminders():
    """Check trips.json and send reminders for upcoming trips"""
    
    if not TRIPS_FILE.exists():
        log("📋 No trips.json found - nothing to check")
        return
    
    try:
        with open(TRIPS_FILE, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError:
        log("❌ Error reading trips.json")
        return
    
    # Handle both formats: {"trips": [...]} or [...]
    if isinstance(data, dict):
        trips = data.get("trips", [])
    else:
        trips = data
    
    if not trips:
        log("📋 No trips scheduled")
        return
    
    now = datetime.now()
    updated = False
    
    log(f"🔍 Checking {len(trips)} trip(s)...")
    
    for i, trip in enumerate(trips):
        # Skip if reminder already sent
        if trip.get("reminder_sent", False):
            continue
        
        # Parse trip datetime
        try:
            trip_time = datetime.fromisoformat(trip["datetime"])
        except (KeyError, ValueError) as e:
            log(f"⚠️ Invalid datetime for trip {i+1}: {e}")
            continue
        
        # Calculate reminder time (4 hours before trip)
        reminder_time = trip_time - timedelta(hours=REMINDER_HOURS_BEFORE)
        
        # Check if we're in the reminder window
        if now >= reminder_time and now < trip_time:
            log(f"🚨 REMINDER TIME! Trip: {trip['source']} → {trip['destination']}")
            
            # Build agent query - Telegram FIRST to ensure it sends
            agent_query = f"""URGENT: Send SAKHI safety reminder for upcoming trip.

Trip: {trip['source']} → {trip['destination']}
Date: {trip.get('date', trip['datetime'][:10])} at {trip.get('time', trip['datetime'][11:16])}

STEP 1 - SEND TELEGRAM IMMEDIATELY:
Use sakhi-telegram send_message tool to send this alert:
"🛡️ SAKHI REMINDER - Trip to {trip['destination']} in 4 hours! 📍 Route: https://www.google.com/maps/dir/{trip['source']}/{trip['destination']} Stay safe! 💪"

STEP 2 - Get weather using sakhi-weather for {trip['destination']}

STEP 3 - Get safety news using sakhi-news for {trip['destination']}

STEP 4 - Create HTML report: trip-safety-report-{trip['destination']}-{trip.get('date', trip['datetime'][:10])}.html

TELEGRAM IS MANDATORY - DO NOT SKIP!"""
            
            try:
                log(f"🤖 Invoking {AGENT_NAME} agent via WSL...")
                
                # Get command - same pattern as sos_scheduler
                cmd = get_kiro_command(agent_query)
                log(f"📝 Command: {cmd[0]} {cmd[1]} {cmd[2][:50]}...")
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300,
                    env={**os.environ, "KIRO_AUTO_APPROVE": "true"},
                    encoding='utf-8',
                    errors='replace'
                )
                
                log(f"📤 Return code: {result.returncode}")
                if result.stdout:
                    log(f"📤 Stdout (first 500 chars): {result.stdout[:500]}")
                if result.stderr:
                    log(f"📤 Stderr (first 500 chars): {result.stderr[:500]}")
                
                if result.returncode == 0:
                    # Mark as sent
                    trips[i]["reminder_sent"] = True
                    trips[i]["reminder_sent_at"] = datetime.now().isoformat()
                    updated = True
                    log(f"✅ Agent completed!")
                    
                    # Send Telegram directly as backup (agent may not send in non-interactive mode)
                    log(f"📱 Sending Telegram notification directly...")
                    maps_link = f"https://www.google.com/maps/dir/{urllib.parse.quote(trip['source'])}/{urllib.parse.quote(trip['destination'])}"
                    telegram_msg = f"""🛡️ <b>SAKHI SAFETY REMINDER</b>

📍 <b>Trip:</b> {trip['source']} → {trip['destination']}
📅 <b>Date:</b> {trip.get('date', trip['datetime'][:10])}
⏰ <b>Time:</b> {trip.get('time', trip['datetime'][11:16])}

🗺️ <a href="{maps_link}">View Route on Google Maps</a>

✅ Safety report generated! Stay safe! 💪"""
                    
                    if send_telegram_message(telegram_msg):
                        log(f"✅ Telegram sent successfully!")
                    else:
                        log(f"⚠️ Telegram send failed - check bot token/chat ID")
                else:
                    log(f"❌ Agent returned error: {result.stderr[:200] if result.stderr else 'unknown'}")
                
            except subprocess.TimeoutExpired:
                log("⏰ Agent timed out after 5 minutes")
            except FileNotFoundError:
                log(f"❌ kiro-cli not found. Update KIRO_CLI_WSL_PATH in scheduler.py")
                log(f"   Current path: {KIRO_CLI_WSL_PATH}")
            except Exception as e:
                log(f"❌ Error: {e}")
        
        elif now < reminder_time:
            time_until = reminder_time - now
            hours, remainder = divmod(int(time_until.total_seconds()), 3600)
            minutes = remainder // 60
            log(f"⏳ Trip to {trip['destination']}: reminder in {hours}h {minutes}m")
    
    # Save updated trips
    if updated:
        with open(TRIPS_FILE, 'w') as f:
            json.dump(trips, f, indent=2)
        log("💾 trips.json updated")

def run_once():
    """Run a single check"""
    log("🔄 Running single check...")
    check_and_send_reminders()
    log("✅ Check complete")

def run_daemon():
    """Run continuously as a background scheduler"""
    global running
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║          🛡️  SAKHI - Women Safety Guardian Scheduler         ║
║                                                              ║
║  Running in daemon mode - checking every 30 minutes          ║
║  Press Ctrl+C to stop                                        ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    log(f"📁 Watching: {TRIPS_FILE}")
    log(f"⏰ Check interval: {CHECK_INTERVAL_MINUTES} minutes")
    log(f"🔔 Reminder window: {REMINDER_HOURS_BEFORE} hours before trip")
    
    while running:
        check_and_send_reminders()
        
        if not running:
            break
            
        log(f"💤 Sleeping for {CHECK_INTERVAL_MINUTES} minutes...")
        
        # Sleep in small intervals to allow quick Ctrl+C response
        for _ in range(CHECK_INTERVAL_MINUTES * 60):
            if not running:
                break
            time.sleep(1)

def print_help():
    """Print usage help"""
    print("""
🛡️  SAKHI Scheduler - Women Safety Guardian

Usage:
  python scheduler.py              Run continuously (daemon mode)
  python scheduler.py --once       Run single check and exit
  python scheduler.py --help       Show this help

Environment:
  KIRO_AUTO_APPROVE=true          Auto-approve all tool calls (set automatically)

Configuration:
  Edit the constants at the top of this file:
  - CHECK_INTERVAL_MINUTES = 30   How often to check (in minutes)
  - REMINDER_HOURS_BEFORE = 4     Send reminder X hours before trip
""")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ["--once", "-o", "once"]:
            run_once()
        elif arg in ["--help", "-h", "help"]:
            print_help()
        else:
            print(f"Unknown argument: {arg}")
            print_help()
    else:
        run_daemon()
