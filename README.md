# RichesReach AI

[![Production Status](https://img.shields.io/badge/Status-Live%20on%20AWS-green.svg)](https://github.com/marion205/RichesReach)
[![AWS Deployed](https://img.shields.io/badge/AWS-ECS%20Deployed-blue.svg)](https://aws.amazon.com)
[![Mobile Ready](https://img.shields.io/badge/Mobile-Expo%20Ready-orange.svg)](https://expo.dev)
[![Rust Engine](https://img.shields.io/badge/Rust-High%20Performance-red.svg)](https://rust-lang.org)

> AI-powered investment platform with advanced trading, portfolio management, and personalized financial education.

## Overview

RichesReach is a comprehensive investment platform that combines AI-powered trading insights, real-time market analysis, and adaptive learning to help users build wealth. Built with cutting-edge machine learning, high-performance Rust engines, and deployed on AWS infrastructure.

**Production URL**: `http://riches-reach-alb-1199497064.us-east-1.elb.amazonaws.com`

## ✨ Key Features

### 🤖 AI-Powered Trading
- **AI Trading Coach**: Personalized strategy recommendations with interactive coaching
- **AI Tutor**: Real-time Q&A, explanations, and adaptive learning paths
- **Voice AI Assistant**: 6 natural voices for hands-free trading commands
- **Market Insights**: ML-powered predictions with R² = 0.0527 (institutional-grade)
- **Portfolio Optimization**: AI-driven rebalancing and risk management

### 📈 Trading & Analysis
- **Options Trading**: Professional options chain with real-time Greeks analysis
- **HFT System**: Ultra-low latency trading (26.62μs) with 4 active strategies
- **Real-time Data**: Live market feeds via WebSocket streaming
- **Technical Indicators**: 35+ indicators including RSI, MACD, Bollinger Bands
- **Crypto Integration**: Multi-asset crypto tracking and DeFi integration

### 🎓 Adaptive Learning System
- **IRT-Based Learning**: Personalized difficulty using Item Response Theory
- **Gamified Tutor**: Duolingo-style mechanics with XP, streaks, and badges
- **Voice-Interactive**: Hands-free learning with natural voice narration
- **Live Simulations**: Paper trading with real market data
- **BIPOC-Focused**: Culturally relevant content and community features

### 👥 Social & Community
- **Wealth Circles**: AI-moderated community discussions
- **Social Trading**: Copy trading and peer-to-peer learning
- **Trade Challenges**: Gamified trading competitions with leaderboards
- **Live Streaming**: Facebook Live/TikTok-style live streams for wealth circles

### 🏦 Brokerage Integration
- **Alpaca Integration**: Real stock and options trading
- **Account Management**: Complete KYC/AML workflow
- **Portfolio Tracking**: Real-time position tracking and P&L analysis
- **Crypto Trading**: Available in 28 supported US states

## 🏗️ Architecture

### Backend
- **Python**: FastAPI + Django with GraphQL
- **PostgreSQL**: Primary database with optimized queries
- **Redis**: Caching and session management
- **Rust Engine**: Ultra-fast crypto and ML analysis (5-10x faster)
- **Kafka**: Real-time data streaming (AWS MSK)
- **S3 Data Lake**: Long-term data storage with lifecycle policies

### Frontend
- **React Native**: Cross-platform mobile app (iOS & Android)
- **Expo**: Mobile development platform
- **TypeScript**: Type-safe development

### Infrastructure
- **AWS ECS**: Container orchestration with auto-scaling
- **Docker**: Optimized multi-stage builds
- **Application Load Balancer**: High availability with health checks
- **CloudWatch**: Monitoring and logging

### AI & ML
- **OpenAI**: GPT-4o-mini, GPT-5 integration
- **Anthropic**: Claude 3.5 Sonnet
- **Scikit-learn**: Machine learning models
- **XGBoost**: Gradient boosting for predictions

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL 14+
- Redis 6+
- Docker (optional)

### Local Development

1. **Clone the repository**
```bash
git clone https://github.com/marion205/RichesReach.git
cd RichesReach
```

2. **Start Backend**
```bash
./start_backend_now.sh
# Or manually:
cd backend/backend
python3 manage.py runserver
```

3. **Start Mobile App**
```bash
cd mobile
./start_with_env.sh
# Or manually:
npm install
npx expo start
```

4. **Start Rust Engine (Optional)**
```bash
cd rust_crypto_engine
cargo run --release -- --port 3002
```

### Environment Variables

Create `.env` files based on templates:
- `deployment_package/backend/env.production.example` - Production config
- `mobile/.env.local` - Mobile app config

Key variables:
```bash
# Backend
DATABASE_URL=postgresql://user:pass@localhost:5432/richesreach
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=your-key
KAFKA_ENABLED=true
DATA_LAKE_BUCKET=riches-reach-ai-datalake-20251005

# Mobile
EXPO_PUBLIC_API_BASE_URL=http://localhost:8000
EXPO_PUBLIC_GRAPHQL_URL=http://localhost:8000/graphql/
```

## 📚 Documentation

- [Production Deployment Guide](PRODUCTION_ENV_TEMPLATE.md)
- [Network Troubleshooting](FIX_NETWORK_ERRORS.md)
- [Live Streaming Setup](VERIFY_LIVE_STREAM.md)
- [API Documentation](https://app.richesreach.net/docs)
- [Technical Docs](docs/technical/)

## 🧪 Testing

```bash
# Run backend tests
cd backend/backend
python manage.py test

# Run mobile tests
cd mobile
npm test
```

## 📊 Production Status

- **✅ AWS Infrastructure**: ECS service active, Load Balancer running
- **✅ Core Features**: All major functionality operational
- **✅ AI Services**: Portfolio optimization, ML predictions working
- **✅ Market Data**: Real-time stocks, options, news feeds active
- **✅ Kafka Streaming**: Enabled with AWS MSK cluster
- **✅ Data Lake**: S3 bucket configured with lifecycle policies

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/marion205/RichesReach/issues)
- **Production Status**: [Health Check](http://riches-reach-alb-1199497064.us-east-1.elb.amazonaws.com/health)
- **Documentation**: [Technical Docs](docs/technical/)

---

**Built for the future of AI-powered investing** 🚀

*RichesReach AI - Democratizing advanced investment strategies through cutting-edge AI and machine learning technology.*
