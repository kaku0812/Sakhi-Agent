#!/usr/bin/env python3
"""
Designed to work with the Render-hosted FastAPI backend.
Can be published to PyPI as part of hackathon-sakhi package.

Environment Variables:
    LOCATION_API_URL: URL of the Render-hosted API (required)
    
Usage:
    LOCATION_API_URL=https://sakhi-location-api.onrender.com uvx --from hackathon-sakhi sakhi-location
"""

import os
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import json

import requests
from mcp.server.fastmcp import FastMCP

# ============================================================================

DEFAULT_API_URL = "https://sakhi-location-api.onrender.com"

logging.basicConfig(
    level=logging.INFO,
    format='%(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class LocationSnapshot:
    """Location snapshot from the device"""
    timestamp: datetime
    battery: int
    network: bool
    lat: float
    lng: float
    local_id: Optional[int] = None


@dataclass
class EmergencyAlert:
    """Emergency alert based on device conditions"""
    alert_type: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    message: str
    location: Dict[str, float]
    timestamp: datetime


# ============================================================================
# Location API Client
# ============================================================================

class LocationAPIClient:
    """Client for the Render-hosted Location API"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.timeout = 30  # Render free tier can be slow on cold start
        logger.info(f"Location API Client initialized with URL: {self.base_url}")
    
    def _make_request(self, endpoint: str, method: str = "GET", **kwargs) -> Optional[dict]:
        """Make HTTP request to the API"""
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.request(method, url, timeout=self.timeout, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            logger.warning(f"Request to {url} timed out (cold start?)")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request to {url} failed: {e}")
            return None
    
    def get_snapshots(self, limit: int = 100) -> List[LocationSnapshot]:
        """Fetch recent snapshots"""
        data = self._make_request(f"/snapshots?limit={limit}")
        if not data:
            return []
        
        snapshots = []
        for item in data:
            try:
                timestamp = datetime.fromisoformat(item['timestamp'].replace('Z', ''))
                snapshots.append(LocationSnapshot(
                    timestamp=timestamp,
                    battery=item['battery'],
                    network=item['network'],
                    lat=item['lat'],
                    lng=item['lng'],
                    local_id=item.get('local_id')
                ))
            except Exception as e:
                logger.warning(f"Error parsing snapshot: {e}")
        
        return snapshots
    
    def get_recent_snapshots(self, hours: int = 24, limit: int = 100) -> List[LocationSnapshot]:
        """Fetch snapshots from last N hours"""
        data = self._make_request(f"/snapshots/recent?hours={hours}&limit={limit}")
        if not data:
            return []
        
        snapshots = []
        for item in data:
            try:
                timestamp = datetime.fromisoformat(item['timestamp'].replace('Z', ''))
                snapshots.append(LocationSnapshot(
                    timestamp=timestamp,
                    battery=item['battery'],
                    network=item['network'],
                    lat=item['lat'],
                    lng=item['lng'],
                    local_id=item.get('local_id')
                ))
            except Exception as e:
                logger.warning(f"Error parsing snapshot: {e}")
        
        return snapshots
    
    def get_status(self) -> Dict[str, Any]:
        """Get device status from API"""
        data = self._make_request("/status")
        if not data:
            return {"status": "error", "message": "Could not connect to API"}
        return data
    
    def health_check(self) -> bool:
        """Check if API is healthy"""
        data = self._make_request("/health")
        return data is not None and data.get("status") == "healthy"


# ============================================================================
# Emergency Detection
# ============================================================================

class EmergencyDetector:
    """Detects emergency conditions from location data"""
    
    THRESHOLDS = {
        "battery_critical": 10,
        "battery_low": 20,
        "location_timeout_minutes": 30,
        "rapid_battery_drain_percent_per_hour": 30,
    }
    
    def check_conditions(self, snapshots: List[LocationSnapshot]) -> List[EmergencyAlert]:
        """Check for emergency conditions based on snapshots"""
        if not snapshots:
            return []
        
        alerts = []
        latest = snapshots[0]
        
        # Battery checks
        if latest.battery <= self.THRESHOLDS['battery_critical']:
            alerts.append(EmergencyAlert(
                alert_type="BATTERY_CRITICAL",
                severity="CRITICAL",
                message=f"Battery critically low at {latest.battery}%! Device may shut down soon.",
                location={"lat": latest.lat, "lng": latest.lng},
                timestamp=latest.timestamp
            ))
        elif latest.battery <= self.THRESHOLDS['battery_low']:
            alerts.append(EmergencyAlert(
                alert_type="BATTERY_LOW",
                severity="HIGH",
                message=f"Battery low at {latest.battery}%",
                location={"lat": latest.lat, "lng": latest.lng},
                timestamp=latest.timestamp
            ))
        
        # Network check
        if not latest.network:
            alerts.append(EmergencyAlert(
                alert_type="NETWORK_LOST",
                severity="MEDIUM",
                message="Device has lost network connectivity",
                location={"lat": latest.lat, "lng": latest.lng},
                timestamp=latest.timestamp
            ))
        
        # Location timeout
        minutes_since = (datetime.now() - latest.timestamp).total_seconds() / 60
        if minutes_since > self.THRESHOLDS['location_timeout_minutes']:
            alerts.append(EmergencyAlert(
                alert_type="LOCATION_TIMEOUT",
                severity="HIGH",
                message=f"No location update for {minutes_since:.0f} minutes",
                location={"lat": latest.lat, "lng": latest.lng},
                timestamp=latest.timestamp
            ))
        
        # Rapid battery drain (if we have enough data)
        if len(snapshots) >= 2:
            oldest = snapshots[-1]
            time_diff_hours = (latest.timestamp - oldest.timestamp).total_seconds() / 3600
            if time_diff_hours > 0:
                battery_drain_rate = (oldest.battery - latest.battery) / time_diff_hours
                if battery_drain_rate > self.THRESHOLDS['rapid_battery_drain_percent_per_hour']:
                    alerts.append(EmergencyAlert(
                        alert_type="RAPID_BATTERY_DRAIN",
                        severity="MEDIUM",
                        message=f"Battery draining rapidly at {battery_drain_rate:.1f}%/hour",
                        location={"lat": latest.lat, "lng": latest.lng},
                        timestamp=latest.timestamp
                    ))
        
        return alerts


# ============================================================================
# MCP Server
# ============================================================================

# Initialize
mcp = FastMCP("hackathon-location-monitor")
api_client: Optional[LocationAPIClient] = None
emergency_detector = EmergencyDetector()


def get_api_client() -> LocationAPIClient:
    """Get or create API client"""
    global api_client
    if api_client is None:
        url = os.getenv("LOCATION_API_URL", DEFAULT_API_URL)
        api_client = LocationAPIClient(url)
    return api_client


@mcp.tool()
def get_hackathon_recent_snapshots(limit: int = 10, hours_back: int = 24) -> str:
    """
    Get recent location snapshots from the tracked device.
    
    Use this to check where the person has been and their device status.
    
    Args:
        limit: Maximum number of snapshots to retrieve (default 10)
        hours_back: How many hours back to look (default 24)
        
    Returns:
        JSON with location snapshots including timestamp, battery, network status, and coordinates
    """
    logger.info(f"Tool called: get_hackathon_recent_snapshots(limit={limit}, hours_back={hours_back})")
    
    client = get_api_client()
    snapshots = client.get_recent_snapshots(hours=hours_back, limit=limit)
    
    result = {
        "snapshots": [
            {
                "timestamp": snap.timestamp.isoformat(),
                "battery": snap.battery,
                "network": snap.network,
                "location": {"lat": snap.lat, "lng": snap.lng}
            }
            for snap in snapshots
        ],
        "count": len(snapshots),
        "latest_timestamp": snapshots[0].timestamp.isoformat() if snapshots else None,
        "api_url": client.base_url
    }
    
    return json.dumps(result, indent=2)


@mcp.tool()
def check_hackathon_emergency_conditions() -> str:
    """
    Check if current device status indicates any emergency conditions.
    
    This analyzes battery level, network connectivity, and location updates
    to detect potential emergencies like:
    - Battery critically low (device may die)
    - Network lost (can't be reached)
    - No location updates (device may be off or person in trouble)
    - Rapid battery drain (unusual activity)
    
    Returns:
        JSON with emergency analysis and any detected alerts
    """
    logger.info("Tool called: check_hackathon_emergency_conditions")
    
    client = get_api_client()
    snapshots = client.get_recent_snapshots(hours=2, limit=10)
    alerts = emergency_detector.check_conditions(snapshots)
    status = client.get_status()
    
    result = {
        "emergency_detected": len(alerts) > 0,
        "alert_count": len(alerts),
        "alerts": [
            {
                "type": alert.alert_type,
                "severity": alert.severity,
                "message": alert.message,
                "location": alert.location,
                "timestamp": alert.timestamp.isoformat()
            }
            for alert in alerts
        ],
        "current_status": status,
        "recommendation": _get_recommendation(alerts)
    }
    
    return json.dumps(result, indent=2)


@mcp.tool()
def get_hackathon_device_status() -> str:
    """
    Get current device status including battery, network, and last known location.
    
    Quick way to check if the tracked person's device is online and healthy.
    
    Returns:
        JSON with device status summary
    """
    logger.info("Tool called: get_hackathon_device_status")
    
    client = get_api_client()
    status = client.get_status()
    
    # Add human-readable interpretation
    if status.get("status") == "active":
        status["interpretation"] = "Device is actively sending updates. Person appears to be safe."
    elif status.get("status") == "stale":
        mins = status.get("minutes_since_update", 0)
        status["interpretation"] = f"No updates for {mins:.0f} minutes. May need to check on the person."
    else:
        status["interpretation"] = "No data available. Device may be offline or not set up."
    
    return json.dumps(status, indent=2)


@mcp.tool()
def get_hackathon_location_history(hours: int = 6) -> str:
    """
    Get location history to see the person's movement pattern.
    
    Useful for understanding where the person has traveled recently.
    
    Args:
        hours: How many hours of history to retrieve (default 6)
        
    Returns:
        JSON with location history and movement summary
    """
    logger.info(f"Tool called: get_hackathon_location_history(hours={hours})")
    
    client = get_api_client()
    snapshots = client.get_recent_snapshots(hours=hours, limit=100)
    
    if not snapshots:
        return json.dumps({
            "history": [],
            "summary": "No location history available"
        })
    
    # Group by approximate location
    locations = {}
    for snap in snapshots:
        # Round to ~100m precision for grouping
        key = (round(snap.lat, 3), round(snap.lng, 3))
        if key not in locations:
            locations[key] = {
                "lat": snap.lat,
                "lng": snap.lng,
                "first_seen": snap.timestamp,
                "last_seen": snap.timestamp,
                "count": 0
            }
        locations[key]["count"] += 1
        if snap.timestamp < locations[key]["first_seen"]:
            locations[key]["first_seen"] = snap.timestamp
        if snap.timestamp > locations[key]["last_seen"]:
            locations[key]["last_seen"] = snap.timestamp
    
    # Convert to list
    location_list = [
        {
            "location": {"lat": loc["lat"], "lng": loc["lng"]},
            "first_seen": loc["first_seen"].isoformat(),
            "last_seen": loc["last_seen"].isoformat(),
            "duration_minutes": (loc["last_seen"] - loc["first_seen"]).total_seconds() / 60,
            "data_points": loc["count"]
        }
        for loc in sorted(locations.values(), key=lambda x: x["last_seen"], reverse=True)
    ]
    
    result = {
        "history": location_list,
        "total_locations": len(location_list),
        "time_range": {
            "from": snapshots[-1].timestamp.isoformat(),
            "to": snapshots[0].timestamp.isoformat()
        },
        "summary": f"Person visited {len(location_list)} distinct locations in the last {hours} hours"
    }
    
    return json.dumps(result, indent=2)


def _get_recommendation(alerts: List[EmergencyAlert]) -> str:
    """Generate recommendation based on alerts"""
    if not alerts:
        return "No immediate concerns. Device status appears normal."
    
    severities = [a.severity for a in alerts]
    
    if "CRITICAL" in severities:
        return "URGENT: Critical condition detected. Consider contacting the person immediately or emergency services."
    elif "HIGH" in severities:
        return "WARNING: High severity issue detected. Recommend checking on the person soon."
    elif "MEDIUM" in severities:
        return "NOTICE: Some concerns detected. Monitor the situation."
    else:
        return "Minor issues detected. Keep monitoring."


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Main entry point for the MCP server"""
    logger.info("Starting Hackathon Location Monitor MCP Server...")
    
    # Check API connectivity
    client = get_api_client()
    if client.health_check():
        logger.info(f"✓ Connected to Location API at {client.base_url}")
    else:
        logger.warning(f"⚠ Could not connect to Location API at {client.base_url}")
        logger.warning("  The API may be starting up (cold start) or URL may be incorrect")
    
    # Run MCP server
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
