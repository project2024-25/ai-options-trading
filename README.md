# AI Options Trading Agent

A hybrid AI-powered options trading system that combines N8N workflow orchestration with Python-based analytics, Google Sheets configuration management, React dashboard visualization, and Slack-based human approval workflows. The system integrates with Zerodha Kite API for trade execution, specifically focused on NIFTY and BANKNIFTY options trading.

## 🏗️ System Architecture

### Core Components
- **N8N Orchestration Engine** - Workflow management and integration hub
- **Python Analytics Services** - ML models, technical analysis, and data processing
- **Google Sheets Data Layer** - Configuration, monitoring, and manual overrides
- **React Dashboard** - Real-time visualization and controls
- **Slack Bot Interface** - Human-in-the-loop approval system
- **Zerodha Integration** - Trade execution via Kite API

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Docker and Docker Compose
- Node.js 18+
- Zerodha Kite API credentials
- Google Cloud account with Sheets API enabled
- Slack workspace and bot token

### Development Setup

1. **Clone and Setup**
   ```bash
   git clone <repository-url>
   cd ai-options-trading
   cp .env.template .env
   # Edit .env with your credentials
   ```

2. **Start Services**
   ```bash
   docker-compose up -d
   ```

3. **Initialize Database**
   ```bash
   python scripts/setup/init_database.py
   ```

4. **Start Development**
   ```bash
   # Start all services in development mode
   docker-compose -f docker-compose.dev.yml up
   ```

## 📊 Services Overview

### Data Acquisition Service
- **Port**: 8001
- **Purpose**: Market data collection, Zerodha API integration
- **Endpoints**: `/api/data/nifty-snapshot`, `/api/data/options-chain`

### Technical Analysis Service  
- **Port**: 8002
- **Purpose**: Technical indicators, support/resistance analysis
- **Endpoints**: `/api/analysis/indicators`, `/api/analysis/levels`

### ML Service
- **Port**: 8003
- **Purpose**: Machine learning predictions, pattern recognition
- **Endpoints**: `/api/ml/direction-prediction`, `/api/ml/volatility-forecast`

### Strategy Engine
- **Port**: 8004
- **Purpose**: Options strategy generation and selection
- **Endpoints**: `/api/strategy/signals`, `/api/strategy/backtest`

### Risk Management Service
- **Port**: 8005
- **Purpose**: Position sizing, risk calculations
- **Endpoints**: `/api/risk/position-sizing`, `/api/risk/portfolio-risk`

### Options Analytics Service
- **Port**: 8006
- **Purpose**: Greeks calculations, volatility analysis
- **Endpoints**: `/api/options/greeks`, `/api/options/iv-surface`

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the root directory:

```bash
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/options_trading
REDIS_URL=redis://localhost:6379

# Zerodha API
KITE_API_KEY=your_api_key
KITE_API_SECRET=your_api_secret
KITE_ACCESS_TOKEN=your_access_token

# Google Sheets
GOOGLE_SHEETS_CREDENTIALS_FILE=path/to/credentials.json
GOOGLE_SHEETS_SPREADSHEET_ID=your_spreadsheet_id

# Slack
SLACK_BOT_TOKEN=your_bot_token
SLACK_CHANNEL_ID=your_channel_id

# N8N
N8N_WEBHOOK_URL=http://localhost:5678
```

### Google Sheets Setup

1. Create a new Google Sheets document
2. Enable Google Sheets API in Google Cloud Console
3. Create service account credentials
4. Share the sheet with service account email
5. Copy the spreadsheet ID to your `.env` file

## 📈 Data Flow

1. **Market Data Collection** → Zerodha API → Data Acquisition Service → TimescaleDB
2. **Technical Analysis** → Technical Analysis Service → Indicators & Levels
3. **ML Predictions** → ML Service → Direction & Volatility Forecasts
4. **Strategy Generation** → Strategy Engine → Trading Signals
5. **Human Approval** → Slack Bot → User Decision → Trade Execution
6. **Risk Management** → Continuous Monitoring → Position Management

## 🗃️ Database Schema

### Key Tables
- `market_data_candles` - OHLCV data for NIFTY/BANKNIFTY
- `options_chain` - Options data with Greeks
- `trading_signals` - Generated trading recommendations
- `active_positions` - Current open positions
- `historical_trades` - Completed trade history
- `system_config` - Configuration parameters

## 🤖 N8N Workflows

### Data Collection Workflows
- Market data collection (every 5 minutes)
- Options chain updates (every 5 minutes)
- VIX data collection (every 15 minutes)

### Signal Generation Workflows
- Multi-timeframe analysis
- Strategy signal generation
- Human approval process

### Position Management Workflows
- Real-time P&L monitoring
- Exit signal generation
- Risk limit monitoring

## 📱 React Dashboard

Access the dashboard at `http://localhost:3000`

### Key Views
- **Market Overview** - Live NIFTY/BANKNIFTY data, VIX, key levels
- **Strategy Signals** - Current recommendations and confidence scores
- **Portfolio Management** - Active positions, P&L, Greeks exposure
- **Options Analysis** - Options chain, IV surface, Greeks simulation

## 💬 Slack Integration

### Commands
- `/positions` - View current positions
- `/pnl` - Today's P&L summary
- `/risk` - Portfolio risk metrics
- `/signals` - Latest trading signals
- `/pause` - Pause signal generation

### Notifications
- New trading signals requiring approval
- Position alerts (stop-loss, profit targets)
- System health notifications
- Daily performance summaries

## 🔍 Monitoring & Alerts

### Health Checks
- Service availability: `http://localhost:800X/health`
- Database connectivity
- External API status
- System resource usage

### Performance Metrics
- API response times
- Data collection success rates
- Signal generation accuracy
- Trade execution speed

## 🧪 Testing

```bash
# Run unit tests
python -m pytest tests/unit/

# Run integration tests  
python -m pytest tests/integration/

# Run all tests with coverage
python -m pytest --cov=services tests/
```

## 📚 Documentation

- [API Documentation](docs/api/README.md)
- [Architecture Guide](docs/architecture/README.md)
- [Deployment Guide](docs/deployment/README.md)
- [User Guide](docs/user-guide/README.md)

## 🚨 Risk Management

### Built-in Safety Features
- Maximum 2% risk per trade
- Portfolio risk limit of 10%
- Daily loss limits
- Position concentration limits
- Emergency stop mechanisms

### Compliance
- SEBI guidelines adherence
- Transaction audit trails
- Risk disclosure documentation
- Position limit enforcement

## 🛠️ Development

### Project Structure
```
services/          # Microservices (Python FastAPI)
n8n-workflows/     # N8N workflow definitions
react-dashboard/   # Frontend dashboard (React)
google-sheets/     # Sheet templates and scripts
slack-bot/         # Slack integration
docker/           # Docker configurations
docs/             # Documentation
tests/            # Test suites
scripts/          # Utility scripts
```

### Adding New Features

1. Create feature branch: `git checkout -b feature/new-feature`
2. Implement changes in relevant service
3. Add tests for new functionality
4. Update documentation
5. Create pull request

### Coding Standards
- Python: Follow PEP 8, use type hints
- JavaScript: Use ESLint and Prettier
- API: RESTful design, proper error handling
- Testing: Minimum 80% code coverage

## 📋 Roadmap

### Phase 1: Foundation (Weeks 1-3) ✅
- Basic infrastructure setup
- Data acquisition service
- Technical analysis engine
- Google Sheets integration

### Phase 2: Intelligence (Weeks 4-7)
- Machine learning models
- Advanced analytics
- Strategy engine
- Risk management

### Phase 3: Interface (Weeks 8-11)
- React dashboard
- Real-time visualizations
- Portfolio management
- Options analysis tools

### Phase 4: Integration (Weeks 12-15)
- Slack bot development
- Zerodha integration
- N8N advanced workflows
- Human-in-the-loop system

### Phase 5: Production (Weeks 16-18)
- Production deployment
- Security implementation
- Performance optimization
- Go-live preparation

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Submit pull request
5. Follow code review process

## 📄 License

This project is for personal use only. Not for commercial distribution.

## ⚠️ Disclaimer

This system is for educational and personal trading purposes only. Past performance does not guarantee future results. Trading involves substantial risk of loss. Always consult with financial advisors before making trading decisions.

## 📞 Support

For issues and questions:
1. Check documentation in `/docs`
2. Search existing issues
3. Create new issue with detailed description
4. Include logs and error messages

---

**Status**: Phase 1 Development
**Last Updated**: November 2024
**Version**: 0.1.0