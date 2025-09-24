# RichesReach Backend Server

## Current Server Setup

### Primary Server: `final_complete_server.py`
This is the main production server with:
- ✅ Real FinnHub API integration for live stock data
- ✅ Complete GraphQL schema with all required queries
- ✅ Portfolio management and analytics
- ✅ AI recommendations with real market data
- ✅ User authentication and profiles
- ✅ Watchlist and social features
- ✅ Error handling and fallback mechanisms

### How to Run
```bash
cd /Users/marioncollins/RichesReach/backend
python3 final_complete_server.py
```

The server will start on `http://localhost:8000` with GraphQL endpoint at `http://localhost:8000/graphql`

### Features
- **Real Stock Data**: Live prices from FinnHub API
- **AI Recommendations**: Dynamic buy/sell recommendations based on real market data
- **Portfolio Analytics**: Real-time portfolio metrics and performance
- **User Management**: Complete user profiles and authentication
- **Social Features**: Following, discussions, and social feed
- **Error Handling**: Graceful fallbacks when APIs are unavailable

### API Keys Required
- `FINNHUB_KEY`: For real stock data and company information
- `ALPHA_VANTAGE_KEY`: For additional market data (optional)

### Cleanup Completed
Removed outdated server files that contained mock data or incomplete implementations:
- alpha_vantage_server.py
- beginner_server.py
- complete_demo_server.py
- complete_server.py
- demo_server.py
- discussion_server.py
- final_server.py
- finnhub_server.py
- fixed_complete_server.py
- live_data_server.py
- minimal_server.py
- optimized_finnhub_server.py
- production_server.py
- simple_*.py files
- unified_production_server.py
- working_*.py files
- websocket_main.py
- local_production_server.py
- aws_production_server.py
- main.py
- auth_main.py

All functionality is now consolidated in `final_complete_server.py` with real data integration.
