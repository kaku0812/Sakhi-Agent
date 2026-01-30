#!/usr/bin/env python3
"""
SAKHI - Uber Emergency Ride Booker Scheduler
Polls SOS server every 30 seconds and invokes uber-emergency-booker agent for pending requests.
Just run: python sos_scheduler.py
"""

import json
import subprocess
import shutil
import os
import sys
import time
import signal
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

# Sound alert for Windows
def play_alert_sound():
    """Play alert sound on SOS detection"""
    try:
        if sys.platform == 'win32':
            import winsound
            # Play 3 beeps for emergency alert
            for _ in range(3):
                winsound.Beep(1000, 300)
                time.sleep(0.1)
        else:
            # Unix: use system bell
            print('\a')
    except:
        pass  # Sound is optional

# Configuration
SOS_SERVER_URL = "https://serverforridebooking.onrender.com"
AGENT_NAME = "uber-emergency-booker"
CHECK_INTERVAL_SECONDS = 30  # How often to poll for SOS (configurable)

# WSL kiro-cli path - UPDATE THIS to your WSL kiro-cli location
# Find your path by running in WSL: which kiro-cli
KIRO_CLI_WSL_PATH = "/home/YOUR_WSL_USERNAME/.local/bin/kiro-cli"

# Track running state
running = True

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    global running
    print("\n🛑 SOS Scheduler stopped.")
    running = False
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def find_kiro_cli():
    """Find kiro-cli executable across all platforms"""
    # Check if we're on Windows and need to use WSL
    if sys.platform == 'win32':
        # On Windows, use WSL to run kiro-cli
        return "wsl"
    
    kiro_path = shutil.which("kiro-cli")
    if kiro_path:
        return kiro_path
    
    # Also check for 'kiro' command
    kiro_path = shutil.which("kiro")
    if kiro_path:
        return kiro_path
    
    home = Path.home()
    common_paths = [
        # Linux/Mac
        home / ".cargo" / "bin" / "kiro-cli",
        home / ".local" / "bin" / "kiro-cli",
        Path("/usr/local/bin/kiro-cli"),
    ]
    
    for p in common_paths:
        if p.exists():
            return str(p)
    
    return "kiro-cli"

def get_kiro_command(agent_query):
    """Get the full kiro command as a list"""
    if sys.platform == 'win32':
        # Run through WSL with full path
        escaped_query = agent_query.replace("'", "'\\''")
        return [
            "wsl", "bash", "-c",
            f"{KIRO_CLI_WSL_PATH} chat --agent {AGENT_NAME} --no-interactive --trust-all-tools '{escaped_query}'"
        ]
    else:
        return [
            find_kiro_cli(), "chat",
            "--agent", AGENT_NAME,
            "--no-interactive",
            "--trust-all-tools",
            agent_query
        ]

def log(message):
    """Print with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def get_pending_requests():
    """Fetch pending SOS requests from server"""
    try:
        url = f"{SOS_SERVER_URL}/pending"
        req = urllib.request.Request(url, headers={'User-Agent': 'SAKHI-SOS-Scheduler'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            return data if isinstance(data, list) else []
    except urllib.error.URLError as e:
        log(f"⚠️ Network error: {e.reason}")
        return []
    except Exception as e:
        log(f"❌ Error fetching pending requests: {e}")
        return []

def mark_completed(request_id):
    """Mark a request as completed on the server"""
    try:
        url = f"{SOS_SERVER_URL}/complete/{request_id}"
        req = urllib.request.Request(url, method='POST', headers={'User-Agent': 'SAKHI-SOS-Scheduler'})
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.status == 200
    except Exception as e:
        log(f"⚠️ Could not mark {request_id} as complete: {e}")
        return False

def process_sos_request(request):
    """Invoke uber-emergency-booker agent for a single SOS request"""
    
    # Play alert sound
    play_alert_sound()
    
    request_id = request.get('id', 'unknown')
    lat = request.get('latitude', 0)
    lon = request.get('longitude', 0)
    user_id = request.get('user_id', 'emergency_user')
    timestamp = request.get('timestamp', '')
    
    log(f"🚨 EMERGENCY REQUEST #{request_id}")
    log(f"   📍 Location: {lat}, {lon}")
    log(f"   👤 User: {user_id}")
    
    # Build agent query
    agent_query = f"""URGENT EMERGENCY RIDE REQUEST!

An SOS alert has been triggered. Book an Uber ride IMMEDIATELY.

Emergency Details:
- Request ID: {request_id}
- Current Location: Latitude {lat}, Longitude {lon}
- User ID: {user_id}
- Timestamp: {timestamp}

REQUIRED ACTIONS:
1. Open Uber website using Playwright browser
2. Navigate to https://m.uber.com/looking
3. Set pickup location to: {lat}, {lon}
4. Set destination to the nearest safe location (police station, hospital, or public place)
5. Select the fastest available ride option
6. Complete the booking process
7. Report back the ride details (driver name, ETA, vehicle info)

This is a real emergency - act quickly and efficiently!"""

    try:
        log(f"🤖 Invoking {AGENT_NAME} agent via WSL...")
        
        cmd = get_kiro_command(agent_query)
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=180,  # 3 minutes timeout for Uber booking
            env={**os.environ, "KIRO_AUTO_APPROVE": "true"},
            encoding='utf-8',
            errors='replace'
        )
        
        if result.returncode == 0:
            log(f"✅ Agent completed for request #{request_id}")
            # Mark as completed on server
            if mark_completed(request_id):
                log(f"✅ Request #{request_id} marked as completed")
            return True
        else:
            log(f"❌ Agent error: {result.stderr[:200] if result.stderr else 'unknown'}")
            return False
            
    except subprocess.TimeoutExpired:
        log(f"⏰ Agent timed out for request #{request_id}")
        return False
    except Exception as e:
        log(f"❌ Error: {e}")
        return False

def check_and_process_sos():
    """Main loop - check for pending SOS requests and process them"""
    
    pending = get_pending_requests()
    
    if not pending:
        return
    
    log(f"🚨 {len(pending)} PENDING SOS REQUEST(S)!")
    
    for request in pending:
        if not running:
            break
        process_sos_request(request)
        
        # Small delay between requests to avoid overwhelming the system
        if running and len(pending) > 1:
            time.sleep(2)

def run_once():
    """Run a single check"""
    log("🔄 Running single SOS check...")
    check_and_process_sos()
    log("✅ Check complete")

def run_daemon():
    """Run continuously as a background scheduler"""
    global running
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║        🚨 SAKHI - Uber Emergency Ride Booker Scheduler       ║
║                                                              ║
║  Polling SOS server every 30 seconds                         ║
║  Press Ctrl+C to stop                                        ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    log(f"🌐 SOS Server: {SOS_SERVER_URL}")
    log(f"⏰ Check interval: {CHECK_INTERVAL_SECONDS} seconds")
    log(f"🤖 Agent: {AGENT_NAME}")
    
    while running:
        pending = get_pending_requests()
        
        if pending:
            log(f"🚨 {len(pending)} PENDING SOS REQUEST(S)!")
            
            for request in pending:
                if not running:
                    break
                process_sos_request(request)
                if running and len(pending) > 1:
                    time.sleep(2)
        else:
            log("✓ No pending SOS requests")
        
        if not running:
            break
        
        # Sleep in small intervals for quick Ctrl+C response
        for _ in range(CHECK_INTERVAL_SECONDS):
            if not running:
                break
            time.sleep(1)

def print_help():
    """Print usage help"""
    print("""
🚨 SAKHI SOS Scheduler - Uber Emergency Ride Booker

Usage:
  python sos_scheduler.py              Run continuously (daemon mode)
  python sos_scheduler.py --once       Run single check and exit
  python sos_scheduler.py --help       Show this help

Configuration:
  Edit the constants at the top of this file:
  - SOS_SERVER_URL                    SOS ride request server
  - CHECK_INTERVAL_SECONDS = 30       How often to check (in seconds)
  - AGENT_NAME                        Kiro agent to invoke

SOS Server Endpoints:
  GET  /pending          - List pending SOS requests
  POST /complete/:id     - Mark request as completed
  GET  /                 - Dashboard view
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
