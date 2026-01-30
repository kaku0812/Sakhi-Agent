# Architecture Principles

## Core Design Philosophy
Build a modular, scalable women's safety ecosystem that prioritizes real-world impact over technical complexity.

## System Architecture

### Modular MCP Server Design
- Each service (Weather, News, Telegram, Location) operates independently
- Servers can be developed, tested, and deployed separately
- Failure in one service doesn't affect others
- Easy to extend with additional safety services

### Cross-Platform Compatibility
- All paths must be system-independent (no hardcoded Windows/Linux paths)
- Use dynamic path resolution: `$(pwd)` and relative paths
- Environment variables for configuration management
- Works across Windows, Mac, and Linux 

### Data Flow Architecture
```
Android App → PgSQL → Cloud Sync → MCP Server → Kiro Agent → Emergency Response
```

## Integration Patterns

### MCP Server Integration
- Use consistent naming: `sakhi-{service}` prefix
- Standardized environment variable handling
- Uniform error response format
- Common logging and debugging approach

### Mobile-to-Cloud Sync
- Offline-first design with local SQLite storage
- Smart sync when network available
- Graceful degradation during connectivity issues
- Real-time data access via REST endpoints

### Emergency Response Workflow
- Proactive monitoring (cron-based scheduling)
- Multi-source intelligence gathering (weather + news + location)
- Automated decision making with human oversight
- Multiple communication channels (Telegram + potential SMS)
- Automatic uber ride booking link generated


