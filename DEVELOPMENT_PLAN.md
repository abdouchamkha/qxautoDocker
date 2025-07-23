# Multi-User Trading Platform Development Plan

## Project Overview

Transform the current single-user trading bot into a comprehensive multi-user trading platform with API endpoints, user management, and subscription handling.

## Current System Analysis

### Existing Components:
- **Single-user trading bot** (`main.py`)
- **Quotex API integration** (`quotexapi/`)
- **Telegram signal processing**
- **Gale trading system** (loss recovery)
- **Basic configuration management**

### Key Trading Parameters Identified:
- **Account**: email, password, demo/real mode
- **Session**: trade_amount, gale_limit, stop_profit, stop_loss, current_gale_count
- **Statistics**: net_profit, total_trades, winning_trades, losing_trades, session_start_time

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Multi-User Trading Platform              │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │  Telegram Bot   │  │   CLI Client    │  │   Web API    │ │
│  │  (User Mgmt)    │  │  (Trading)      │  │  (Core)      │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                     REST API Layer                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │     Users       │  │   Accounts      │  │   Sessions   │ │
│  │   Management    │  │   Management    │  │   Trading    │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    Multi-Session Engine                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   Quotex API    │  │  Signal Handler │  │ Trade Engine │ │
│  │   Connections   │  │   (Telegram)    │  │ (Multi-User) │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                     Database Layer                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │     Users       │  │   Subscriptions │  │   Accounts   │ │
│  │   Sessions      │  │     Trades      │  │   Settings   │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Database Design & Core API Framework

### 1.1 Database Schema Design
**Location**: `qxautoDocker/database/`

#### Tables to Create:

```sql
-- Users table
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Subscriptions table
CREATE TABLE subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    subscription_type VARCHAR(50) NOT NULL, -- 'basic', 'premium', 'vip'
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    max_accounts INTEGER DEFAULT 1,
    max_sessions INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Quotex accounts table
CREATE TABLE quotex_accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    email VARCHAR(100) NOT NULL,
    password_encrypted TEXT NOT NULL,
    account_type VARCHAR(10) NOT NULL, -- 'demo' or 'real'
    account_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    last_balance DECIMAL(10,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Trading sessions table
CREATE TABLE trading_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    account_id INTEGER NOT NULL,
    session_name VARCHAR(100),
    trade_amount DECIMAL(10,2) NOT NULL,
    gale_limit INTEGER DEFAULT 1,
    stop_profit DECIMAL(10,2),
    stop_loss DECIMAL(10,2),
    is_active BOOLEAN DEFAULT FALSE,
    current_gale_count INTEGER DEFAULT 0,
    net_profit DECIMAL(10,2) DEFAULT 0,
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,
    session_start_time TIMESTAMP,
    session_end_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (account_id) REFERENCES quotex_accounts(id)
);

-- Trades history table
CREATE TABLE trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    asset VARCHAR(50) NOT NULL,
    direction VARCHAR(10) NOT NULL, -- 'call' or 'put'
    amount DECIMAL(10,2) NOT NULL,
    duration INTEGER NOT NULL,
    is_gale BOOLEAN DEFAULT FALSE,
    gale_sequence INTEGER DEFAULT 0,
    result VARCHAR(10), -- 'win', 'loss', 'pending'
    profit_loss DECIMAL(10,2) DEFAULT 0,
    open_time TIMESTAMP NOT NULL,
    close_time TIMESTAMP,
    signal_source VARCHAR(100), -- Telegram channel or manual
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES trading_sessions(id)
);

-- API tokens for authentication
CREATE TABLE api_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

#### Files to Create:
- `database/models.py` - SQLAlchemy models
- `database/init_db.py` - Database initialization
- `database/migrations/` - Database migration scripts

### 1.2 Core API Framework
**Location**: `qxautoDocker/api/`

#### Files to Create:
- `api/__init__.py` - Flask app initialization
- `api/config.py` - Configuration management
- `api/auth.py` - Authentication middleware
- `api/decorators.py` - Common decorators (auth_required, etc.)
- `api/utils.py` - Utility functions

#### Dependencies to Add:
```text
flask-sqlalchemy==3.0.5
flask-jwt-extended==4.5.2
bcrypt==4.0.1
cryptography==41.0.3
python-dotenv==1.0.0
```

---

## Phase 2: User Management & Authentication APIs

### 2.1 User Management Endpoints
**Location**: `qxautoDocker/api/routes/users.py`

#### Endpoints to Implement:
- `POST /api/v1/users/register` - User registration
- `POST /api/v1/users/login` - User authentication
- `POST /api/v1/users/logout` - User logout
- `GET /api/v1/users/profile` - Get user profile
- `PUT /api/v1/users/profile` - Update user profile
- `DELETE /api/v1/users/account` - Delete user account

#### Request/Response Examples:
```python
# POST /api/v1/users/register
{
    "username": "trader1",
    "email": "trader1@example.com",
    "password": "SecurePass123!"
}

# Response
{
    "success": True,
    "message": "User registered successfully",
    "user_id": 1,
    "token": "jwt_token_here"
}
```

### 2.2 Subscription Management
**Location**: `qxautoDocker/api/routes/subscriptions.py`

#### Endpoints to Implement:
- `GET /api/v1/subscriptions` - Get user subscriptions
- `POST /api/v1/subscriptions` - Create new subscription
- `PUT /api/v1/subscriptions/{id}` - Update subscription
- `DELETE /api/v1/subscriptions/{id}` - Cancel subscription

---

## Phase 3: Quotex Account Management APIs

### 3.1 Account CRUD Operations
**Location**: `qxautoDocker/api/routes/accounts.py`

#### Endpoints to Implement:
- `GET /api/v1/accounts` - List user's Quotex accounts
- `POST /api/v1/accounts` - Add new Quotex account
- `PUT /api/v1/accounts/{id}` - Update Quotex account
- `DELETE /api/v1/accounts/{id}` - Remove Quotex account
- `POST /api/v1/accounts/{id}/test` - Test account connection
- `GET /api/v1/accounts/{id}/balance` - Get account balance

#### Request/Response Examples:
```python
# POST /api/v1/accounts
{
    "account_name": "My Demo Account",
    "email": "trader@quotex.com",
    "password": "QuotexPass123!",
    "account_type": "demo"
}

# Response
{
    "success": True,
    "message": "Account added successfully",
    "account_id": 1,
    "balance": 10000.00,
    "connection_status": "connected"
}
```

### 3.2 Security Implementation
- Encrypt passwords using Fernet (symmetric encryption)
- Store encryption key in environment variables
- Implement password validation and strength requirements

---

## Phase 4: Trading Session Management APIs

### 4.1 Session CRUD Operations
**Location**: `qxautoDocker/api/routes/sessions.py`

#### Endpoints to Implement:
- `GET /api/v1/sessions` - List user's trading sessions
- `POST /api/v1/sessions` - Create new trading session
- `PUT /api/v1/sessions/{id}` - Update session settings
- `DELETE /api/v1/sessions/{id}` - Delete session
- `POST /api/v1/sessions/{id}/start` - Start trading session
- `POST /api/v1/sessions/{id}/stop` - Stop trading session
- `GET /api/v1/sessions/{id}/status` - Get session status and stats

#### Request/Response Examples:
```python
# POST /api/v1/sessions
{
    "session_name": "EUR/USD Session",
    "account_id": 1,
    "trade_amount": 5.00,
    "gale_limit": 2,
    "stop_profit": 100.00,
    "stop_loss": 50.00
}

# GET /api/v1/sessions/{id}/status
{
    "session_id": 1,
    "is_active": True,
    "current_balance": 10250.00,
    "net_profit": 250.00,
    "total_trades": 45,
    "winning_trades": 28,
    "losing_trades": 17,
    "win_rate": 62.22,
    "session_duration": "2h 35m",
    "current_gale_count": 0,
    "last_trade": {
        "asset": "EURUSD",
        "direction": "call",
        "amount": 5.00,
        "result": "win",
        "profit": 4.00,
        "timestamp": "2024-01-15T10:30:00Z"
    }
}
```

---

## Phase 5: Multi-User Trading Engine

### 5.1 Trading Engine Core
**Location**: `qxautoDocker/engine/`

#### Files to Create:
- `engine/trading_engine.py` - Main trading engine
- `engine/session_manager.py` - Manage multiple sessions
- `engine/quotex_connection_pool.py` - Manage Quotex API connections
- `engine/signal_processor.py` - Process Telegram signals
- `engine/trade_executor.py` - Execute individual trades
- `engine/risk_manager.py` - Risk management and limits

#### Key Features:
```python
class TradingEngine:
    def __init__(self):
        self.active_sessions = {}
        self.quotex_connections = {}
        self.signal_processor = SignalProcessor()
        self.risk_manager = RiskManager()
    
    async def start_session(self, session_id: int):
        """Start a trading session"""
        
    async def stop_session(self, session_id: int):
        """Stop a trading session"""
        
    async def process_signal(self, signal_data: dict):
        """Process incoming trading signal for all active sessions"""
        
    async def execute_trade(self, session_id: int, trade_data: dict):
        """Execute a trade for a specific session"""
```

### 5.2 Connection Pool Management
- Manage multiple Quotex API connections
- Handle connection failures and reconnection
- Load balancing for demo vs real accounts
- Session isolation and thread safety

### 5.3 Signal Processing Enhancement
- Parse Telegram signals for multiple sessions
- Filter signals based on user preferences
- Queue management for simultaneous trades
- Rate limiting and spam protection

---

## Phase 6: Trade Execution & Management APIs

### 6.1 Trade Management Endpoints
**Location**: `qxautoDocker/api/routes/trades.py`

#### Endpoints to Implement:
- `GET /api/v1/trades` - Get trading history
- `POST /api/v1/trades/manual` - Execute manual trade
- `GET /api/v1/trades/{id}` - Get trade details
- `GET /api/v1/trades/statistics` - Get trading statistics
- `POST /api/v1/trades/signals/subscribe` - Subscribe to signal source
- `DELETE /api/v1/trades/signals/unsubscribe` - Unsubscribe from signals

#### Request/Response Examples:
```python
# POST /api/v1/trades/manual
{
    "session_id": 1,
    "asset": "EURUSD",
    "direction": "call",
    "amount": 5.00,
    "duration": 60
}

# GET /api/v1/trades/statistics
{
    "session_id": 1,
    "period": "last_30_days",
    "total_trades": 450,
    "winning_trades": 275,
    "losing_trades": 175,
    "win_rate": 61.11,
    "net_profit": 1250.00,
    "best_day": {
        "date": "2024-01-10",
        "profit": 85.00,
        "trades": 12
    },
    "worst_day": {
        "date": "2024-01-03",
        "loss": -45.00,
        "trades": 8
    }
}
```

---

## Phase 7: Python CLI Client (`cmdClient/`)

### 7.1 CLI Client Structure
**Location**: `cmdClient/`

#### Files to Create:
- `cmdClient/client.py` - Main CLI application
- `cmdClient/api_client.py` - API communication class
- `cmdClient/commands/` - Command modules
- `cmdClient/config.py` - Configuration management
- `cmdClient/utils.py` - Utility functions

#### Commands to Implement:
```bash
# Authentication
qxtrade login --username trader1 --password pass123
qxtrade logout

# Account management
qxtrade accounts list
qxtrade accounts add --email quotex@email.com --password pass --type demo
qxtrade accounts test --id 1
qxtrade accounts balance --id 1

# Session management
qxtrade sessions list
qxtrade sessions create --name "EUR Session" --account 1 --amount 5
qxtrade sessions start --id 1
qxtrade sessions stop --id 1
qxtrade sessions status --id 1

# Trading
qxtrade trade --session 1 --asset EURUSD --direction call --amount 5
qxtrade history --session 1 --limit 50
qxtrade stats --session 1
```

### 7.2 Configuration Management
```json
{
    "api_base_url": "http://localhost:5000/api/v1",
    "auth_token": "jwt_token_here",
    "default_session": 1,
    "output_format": "table",
    "auto_login": true
}
```

---

## Phase 8: Telegram Bot (`telegramBot/`)

### 8.1 Telegram Bot Structure
**Location**: `telegramBot/`

#### Files to Create:
- `telegramBot/bot.py` - Main bot application
- `telegramBot/handlers/` - Command and callback handlers
- `telegramBot/keyboards.py` - Inline keyboards
- `telegramBot/api_client.py` - API communication
- `telegramBot/config.py` - Bot configuration

#### Bot Commands to Implement:
```
/start - Welcome and registration
/register - User registration
/login - User login
/profile - View profile
/accounts - Manage Quotex accounts
/sessions - Manage trading sessions
/balance - Check account balances
/stats - View trading statistics
/help - Help and documentation
/support - Contact support
```

### 8.2 Inline Keyboard Menus
- Main menu navigation
- Account management interface
- Session control panel
- Real-time statistics display
- Quick trade execution

### 8.3 Subscription Management
- Subscription status checking
- Payment processing integration
- Feature access control
- Renewal notifications

---

## Phase 9: Advanced Features & Monitoring

### 9.1 Real-time Monitoring
**Location**: `qxautoDocker/monitoring/`

#### Features to Implement:
- WebSocket connections for real-time updates
- System health monitoring
- Trading session monitoring
- Alert system for critical events
- Performance metrics collection

### 9.2 Risk Management
- Position sizing algorithms
- Drawdown protection
- Maximum daily loss limits
- Account balance monitoring
- Emergency stop mechanisms

### 9.3 Reporting & Analytics
- Detailed trading reports
- Performance analytics
- Risk assessment reports
- Export functionality (CSV, PDF)
- Custom date range reporting

---

## Phase 10: Testing & Deployment

### 10.1 Testing Strategy
**Location**: `qxautoDocker/tests/`

#### Test Types:
- Unit tests for all API endpoints
- Integration tests for trading engine
- End-to-end tests for complete workflows
- Load testing for multiple simultaneous sessions
- Security testing for authentication and data protection

### 10.2 Deployment Setup
- Docker containerization
- Environment configuration
- Database migration scripts
- Monitoring and logging setup
- Backup and recovery procedures

---

## Implementation Timeline

### Week 1-2: Foundation
- **Phase 1**: Database design and core API framework
- **Phase 2**: User management and authentication

### Week 3-4: Core Features
- **Phase 3**: Quotex account management
- **Phase 4**: Trading session management

### Week 5-6: Trading Engine
- **Phase 5**: Multi-user trading engine
- **Phase 6**: Trade execution APIs

### Week 7-8: Client Applications
- **Phase 7**: CLI client development
- **Phase 8**: Telegram bot development

### Week 9-10: Advanced Features
- **Phase 9**: Monitoring and analytics
- **Phase 10**: Testing and deployment

---

## Technical Requirements

### Dependencies
```text
# Core API
flask==2.3.3
flask-sqlalchemy==3.0.5
flask-jwt-extended==4.5.2
flask-cors==4.0.0

# Database
sqlite3 (development)
postgresql (production)

# Security
bcrypt==4.0.1
cryptography==41.0.3

# Async support
asyncio
aiohttp==3.8.5

# Existing dependencies
requests==2.31.0
telethon==1.28.5
python-telegram-bot==20.3
pyfiglet==0.8.post1
colorama==0.4.6
pytz==2023.3

# CLI client
click==8.1.6
rich==13.5.2
tabulate==0.9.0

# Testing
pytest==7.4.0
pytest-asyncio==0.21.1
```

### Environment Variables
```bash
# Database
DATABASE_URL=sqlite:///trading_platform.db
DATABASE_ENCRYPTION_KEY=your-encryption-key-here

# API
FLASK_ENV=development
JWT_SECRET_KEY=your-jwt-secret-here
API_HOST=0.0.0.0
API_PORT=5000

# Telegram
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHANNEL_ID=-1002526280469

# Quotex
QUOTEX_API_TIMEOUT=30
QUOTEX_RECONNECT_ATTEMPTS=3
```

---

## Security Considerations

1. **Password Security**
   - Encrypt Quotex passwords using Fernet
   - Store encryption keys securely
   - Implement password strength requirements

2. **API Security**
   - JWT token authentication
   - Rate limiting on all endpoints
   - Input validation and sanitization
   - CORS configuration

3. **Database Security**
   - Encrypted sensitive data
   - Prepared statements for SQL injection prevention
   - Regular security audits

4. **Trading Security**
   - Session isolation
   - Balance validation before trades
   - Maximum loss limits
   - Account verification

---

## Next Steps

1. **Start with Phase 1**: Set up the database schema and core API framework
2. **Create development environment**: Set up Flask application with basic structure
3. **Implement user authentication**: Build the foundation for user management
4. **Test each phase**: Ensure each component works before moving to the next
5. **Document as you go**: Maintain API documentation and setup instructions

This plan provides a comprehensive roadmap for transforming your single-user trading bot into a full-featured multi-user trading platform. Each phase builds upon the previous one, ensuring a solid foundation for the final system. 