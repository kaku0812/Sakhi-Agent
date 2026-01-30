# Coding Standards

## Development Approach

### Kiro CLI-Driven Development
- Use Kiro CLI for code generation, refactoring, and debugging
- Leverage AI assistance for learning new technologies (Android/Kotlin)
- Iterative development with continuous AI feedback
- Code review and optimization through AI collaboration

### SOLID Principles Implementation
- **Single Responsibility**: Each MCP server handles one specific domain
- **Open/Closed**: Extensible design for adding new RSS feeds, keywords
- **Liskov Substitution**: Consistent interfaces across all MCP servers
- **Interface Segregation**: Minimal, focused API endpoints
- **Dependency Inversion**: Configuration-driven dependencies

## Naming Conventions

### MCP Servers
- Prefix: `sakhi-{service-name}`
- Examples: `sakhi-weather`, `sakhi-news-dashboard`
- Avoids conflicts with existing global MCP servers

### File Structure
```
mcp-servers/
├── weather/
│   ├── weather_server.py
│   └── .env
├── news-dashboard/
│   ├── news_server.py
│   ├── sources.py
│   ├── processor.py
│   └── clustering.py
```

## Code Quality Standards

### Error Handling
```python
try:
    # Operation
    result = api_call()
    return {"success": True, "data": result}
except SpecificException as e:
    return {"success": False, "error": str(e)}
except Exception as e:
    return {"success": False, "error": "Unexpected error occurred"}
```

### Environment Configuration
- All API keys in `.env` files
- No hardcoded credentials in source code

## Mobile Development Standards

### Android Best Practices
- Foreground services for location tracking
- Room database for local storage
- Work Manager for background tasks
- Proper permission handling

### Code Refactoring with Kiro
- Regular code review sessions with AI
- Performance optimization suggestions
- Bug fixing and debugging assistance
- Architecture improvement recommendations

## Testing Standards

### Mobile App Testing
- Battery usage optimization
- Network connectivity scenarios
- Permission handling validation

### Code Review Process
- AI-assisted code review through Kiro CLI
- Focus on security, performance, and maintainability
- Documentation updates with code changes
- Testing verification before commits
