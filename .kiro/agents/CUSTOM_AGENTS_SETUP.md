# Custom Agents & Prompts Setup for Judges

This hackathon project showcases advanced Kiro CLI capabilities through custom agents and prompts.

## 🤖 Custom Agent: Women Safety Guardian

**Purpose**: Advanced women's safety guardian with comprehensive news analysis and professional reporting:
1. **Scheduled Mode**: Automatic trip reminders via cron with MANDATORY Telegram alerts
2. **Interactive Mode**: On-demand safety analysis via chat
3. **Multi-Source News**: Uses RSS feeds + web search + additional sources with clickable links
4. **Professional Reports**: Clean, corporate-style HTML reports inspired by modern web design

### Setup Instructions

#### Step 1: Copy Agent to Global Kiro Directory
```bash
# Copy the custom agent
cp ./hackathon-project/.kiro/agents/women-safety-guardian.json ~/.kiro/agents/

# Verify installation
ls ~/.kiro/agents/women-safety-guardian.json
```

#### Step 2: Copy Custom Prompt
```bash
# Copy the trip planning prompt
cp ./hackathon-project/.kiro/prompts/women-safety-trip-planner.md ~/.kiro/prompts/safety-trip-planner.md

# Verify installation  
ls ~/.kiro/prompts/safety-trip-planner.md
```

## 📝 Usage Examples

### 1. Plan a Trip (Creates trips.json)
```bash
kiro-cli chat
# Then use the custom prompt:
@safety-trip-planner

# Example input:
# \"I'm traveling from Delhi to Mumbai on Jan 25, 2026 at 2:00 PM. 
# My emergency contact bot token is 123456:ABC and chat ID is 987654321\"
```

### 2. Interactive Safety Chat
```bash
kiro-cli --agent women-safety-guardian

# Try these queries:
# \"Is Noida safe for women?\"
# \"Check my trips\"
# \"Tell me about safety in Gurgaon\"
```

### 3. Scheduled Reminders (Cron Setup)
```bash
# Add to crontab for automatic reminders
crontab -e

# Add this line (runs every hour):
0 * * * * cd /path/to/hackathon-project && kiro-cli --agent women-safety-guardian --input \"Check pending trips and send reminders\"
```

## 🔧 Key Improvements

### Advanced News Analysis:
- ✅ **Multi-Source Search**: RSS feeds + web search + additional queries
- ✅ **Source Attribution**: Every news item includes clickable source links
- ✅ **Comprehensive Coverage**: Harassment, eve teasing, crime reports, police advisories
- ✅ **Real-time Data**: Not limited to RSS feeds, searches current web content

### Professional Design:
- ✅ **Corporate Aesthetic**: Clean, minimal design inspired by modern B2B websites
- ✅ **Consistent Colors**: Professional color scheme (no rainbow colors)
- ✅ **Card-based Layout**: Modern grid layout with hover effects
- ✅ **Responsive Design**: Works on all devices
- ✅ **Source Links**: Clickable news source buttons in each card

### Telegram Integration:
- ✅ **Mandatory Alerts**: NEVER skips sending Telegram messages for scheduled trips
- ✅ **Comprehensive Messages**: Weather, news, maps, booking links, safety checklist
- ✅ **Fallback Tokens**: Uses MCP server defaults if no custom tokens provided
- ✅ **Emergency Mode**: Instant alerts for emergency situations

## 📊 Demo Workflow for Judges

1. **Plan Trip**: Use `@safety-trip-planner` to create a trip
2. **Review Report**: Open generated HTML safety report in browser (professional design)
3. **Interactive Chat**: Ask agent about destination safety
4. **Scheduled Alert**: See how automatic Telegram reminders work
5. **Emergency Mode**: Test emergency response capabilities
6. **Source Verification**: Click on news source links in HTML report

## 🎯 Hackathon Innovation Points

- **Advanced News Intelligence**: Multi-source analysis beyond RSS feeds
- **Professional UI/UX**: Corporate-grade HTML reports with source attribution
- **Reliable Automation**: Guaranteed Telegram alerts for scheduled trips
- **Creative Kiro Usage**: Custom agents + prompts showcase platform flexibility
- **Real-World Impact**: Addresses women's safety through comprehensive technology solution
- **Judge-Friendly**: Easy setup with clear documentation and professional presentation

## 🚀 Quick Test Commands

```bash
# Test the complete workflow
cd hackathon-project

# 1. Plan a trip
kiro-cli chat
# Type: @safety-trip-planner
# Input: \"Delhi to Noida tomorrow 3 PM\"

# 2. Chat with improved SAKHI
kiro-cli --agent women-safety-guardian
# Type: \"Is Noida safe?\"

# 3. Check generated files
ls *.json *.html
# Open HTML file in browser to see professional design
```

This demonstrates advanced Kiro CLI usage with professional-grade output! 🎉
