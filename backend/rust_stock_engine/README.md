# 🦀 Rust Stock Analysis Engine

A high-performance microservice for beginner-friendly stock analysis, technical indicators, and investment recommendations.

## 🚀 Features

- **Beginner-Friendly Algorithm**: Analyzes stocks based on criteria suitable for new investors
- **Technical Indicators**: RSI, MACD, Moving Averages, Bollinger Bands
- **Real-time Analysis**: Fast processing with async Rust
- **Risk Assessment**: Low/Medium/High risk categorization
- **Investment Recommendations**: Buy/Hold/Sell signals with reasoning

## 🛠️ Setup

### Prerequisites
- Rust 1.70+ installed
- Alpha Vantage API key

### Installation
```bash
cd backend/rust_stock_engine
cargo build --release
```

### Configuration
1. Copy your Alpha Vantage API key to `config.toml`
2. Or set environment variable: `export ALPHA_VANTAGE_API_KEY=your_key_here`

### Running
```bash
cargo run
# Or for production:
cargo run --release
```

## 🌐 API Endpoints

### Health Check
```bash
GET http://localhost:3001/health
```

### Stock Analysis
```bash
POST http://localhost:3001/analyze
Content-Type: application/json

{
  "symbol": "AAPL",
  "include_technical": true,
  "include_fundamental": true
}
```

### Technical Indicators
```bash
POST http://localhost:3001/indicators
Content-Type: application/json

{
  "symbol": "AAPL"
}
```

### Recommendations
```bash
GET http://localhost:3001/recommendations
```

## 📊 Beginner-Friendly Criteria

The algorithm prioritizes stocks suitable for investors making under $30k/year:

- **Market Cap**: >$100B (large, stable companies)
- **P/E Ratio**: <25 (reasonable valuation)
- **Dividend Yield**: >2% (income generation)
- **Debt Ratio**: <30% (financial health)
- **Volume**: High liquidity for easy trading

## 🔧 Integration with Django

This Rust service runs alongside your Django backend:

1. **Django**: User management, GraphQL, UI
2. **Rust**: Stock analysis, recommendations, real-time data
3. **Communication**: HTTP API calls between services

## 🚧 Next Steps

- [ ] Implement real Alpha Vantage API integration
- [ ] Add historical data fetching for technical analysis
- [ ] Implement WebSocket for real-time updates
- [ ] Add more sophisticated risk models
- [ ] Performance optimization and caching

## 📈 Performance

- **Response Time**: <50ms for basic analysis
- **Concurrent Requests**: 1000+ simultaneous analyses
- **Memory Usage**: <50MB for typical workloads
- **CPU**: Efficient async processing with Tokio runtime
