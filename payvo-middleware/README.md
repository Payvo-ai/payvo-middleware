# Payvo Middleware - Backend API

A high-performance FastAPI middleware for intelligent payment routing with GPS-first MCC prediction and enhanced location-based merchant categorization.

## 🚀 Features

### Core Capabilities
- **GPS-First MCC Prediction** - Advanced merchant category prediction using location data
- **Enhanced Location Routing** - Multi-tier location analysis with indoor venue mapping
- **Real-time Decision Engine** - Intelligent card routing based on context and performance
- **Hierarchical Location Detection** - From precise GPS to building-level to area predictions
- **Indoor Mapping Support** - WiFi/BLE context for venue-specific routing

### Technical Features
- **FastAPI Framework** - High-performance async API with automatic documentation
- **Supabase Integration** - Scalable PostgreSQL database with real-time capabilities
- **Redis Caching** - In-memory caching for session management and performance
- **Comprehensive Logging** - Detailed request/response logging with performance metrics
- **Health Monitoring** - Built-in health checks and system status endpoints
- **Docker Ready** - Containerized deployment with optimized configuration

## 📁 Directory Structure

```
payvo-middleware/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI application entry point
│   ├── api/
│   │   └── routes.py             # API route definitions
│   ├── core/
│   │   └── config.py             # Configuration management
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection_manager.py  # Database connection handling
│   │   ├── models.py             # Database models
│   │   ├── schema.sql            # Database schema definitions
│   │   └── supabase_client.py    # Supabase client wrapper
│   ├── models/
│   │   └── schemas.py            # Pydantic models for API
│   └── services/
│       ├── ai_inference.py       # AI/ML inference engine
│       ├── card_routing.py       # Card routing logic
│       ├── context_collector.py  # Context collection service
│       ├── learning_engine.py    # Machine learning engine
│       ├── mcc_prediction.py     # MCC prediction service
│       ├── routing_orchestrator.py # Main routing orchestrator
│       └── token_provisioning.py # Token provisioning service
├── requirements.txt               # Python dependencies
├── .env                          # Environment variables
├── run.py                        # Development server runner
├── test_enhanced_mcc.py          # MCC prediction tests
├── test_installation.py         # Installation verification
├── simulate_real_transactions.py # Transaction simulation
├── database_schema.sql           # Database schema
├── STARTUP_GUIDE.md              # Quick start guide
└── SUPABASE_SETUP.md             # Database setup instructions
```

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.11+
- Redis Server
- Supabase Account

### Quick Start

1. **Clone and Navigate:**
   ```bash
   cd payvo-middleware
   ```

2. **Create Virtual Environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Start the Server:**
   ```bash
   python app/main.py
   # Or for development:
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Environment Variables

Create a `.env` file with the following configuration:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Redis Configuration
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=your-redis-password

# Application Settings
DEBUG=true
LOG_LEVEL=INFO
API_VERSION=v1
MAX_WORKERS=4

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# External APIs
OPENAI_API_KEY=your-openai-key  # Optional for AI features
```

## 📊 API Documentation

### Core Endpoints

#### Health & Status
```bash
GET /api/v1/health
GET /api/v1/status
```

#### Routing Services
```bash
# Start routing session
POST /api/v1/routing/session/start
{
  "user_id": "user123",
  "transaction_context": {...}
}

# Activate session
POST /api/v1/routing/session/{session_id}/activate
{
  "location": {
    "latitude": 40.7128,
    "longitude": -74.0060,
    "accuracy": 10.0
  }
}

# MCC Prediction
POST /api/v1/routing/predict-mcc
{
  "latitude": 40.7128,
  "longitude": -74.0060,
  "terminal_id": "term123",
  "context": {...}
}
```

#### Analytics & Monitoring
```bash
GET /api/v1/analytics/performance
GET /api/v1/analytics/usage
GET /api/v1/monitoring/metrics
```

### Interactive Documentation
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## 🧪 Testing

### Run Tests
```bash
# Basic installation test
python test_installation.py

# Enhanced MCC prediction test
python test_enhanced_mcc.py

# Transaction simulation
python simulate_real_transactions.py
```

### API Testing Examples

#### Health Check
```bash
curl http://localhost:8000/api/v1/health
```

#### MCC Prediction
```bash
curl -X POST http://localhost:8000/api/v1/routing/predict-mcc \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 40.7128,
    "longitude": -74.0060,
    "accuracy": 10.0,
    "terminal_id": "term_001"
  }'
```

#### Start Routing Session
```bash
curl -X POST http://localhost:8000/api/v1/routing/session/start \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "transaction_context": {
      "amount": 25.50,
      "currency": "USD"
    }
  }'
```

## 🔧 Configuration

### Database Setup
See [SUPABASE_SETUP.md](./SUPABASE_SETUP.md) for detailed database configuration.

### Redis Configuration
```bash
# Install Redis (macOS)
brew install redis

# Start Redis
redis-server

# Or using Docker
docker run -d -p 6379:6379 redis:7-alpine
```

### Performance Tuning
```python
# In app/core/config.py
class Settings:
    max_workers: int = 4
    redis_pool_size: int = 10
    database_pool_size: int = 20
    request_timeout: int = 30
```

## 📦 Deployment

### Docker
```bash
# Build image
docker build -t payvo-middleware .

# Run container
docker run -p 8000:8000 --env-file .env payvo-middleware
```

### Production Deployment
```bash
# Using Gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker

# Using Uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 🔍 Monitoring & Logging

### Log Levels
- `DEBUG` - Detailed diagnostic information
- `INFO` - General application flow
- `WARNING` - Unexpected behavior that doesn't stop the app
- `ERROR` - Serious problems that prevent function execution
- `CRITICAL` - Very serious errors that may abort the program

### Metrics Available
- Request/response times
- Error rates
- MCC prediction accuracy
- Database query performance
- Cache hit rates
- Memory and CPU usage

### Health Checks
The middleware provides comprehensive health checks:
- Database connectivity
- Redis connectivity
- External API availability
- System resource usage

## 🐛 Troubleshooting

### Common Issues

1. **Database Connection Errors**
   ```bash
   # Check Supabase credentials
   python -c "from app.database.supabase_client import supabase_client; print(supabase_client.is_available)"
   ```

2. **Redis Connection Issues**
   ```bash
   # Test Redis connection
   redis-cli ping
   ```

3. **Import Errors**
   ```bash
   # Verify Python path
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   ```

4. **Performance Issues**
   - Check Redis memory usage
   - Monitor database query performance
   - Review log files for bottlenecks

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python app/main.py
```

## 🤝 Contributing

1. Follow PEP 8 style guidelines
2. Add comprehensive tests for new features
3. Update documentation for API changes
4. Use type hints for all functions
5. Add logging for important operations

### Code Style
```bash
# Format code
black app/
isort app/

# Lint code
flake8 app/
mypy app/
```

## 📄 License

This project is proprietary software owned by Payvo-ai.

## 🆘 Support

For technical support:
- Check the [troubleshooting section](#troubleshooting)
- Review logs in debug mode
- Contact the development team
- Create an issue in the repository

---

**Built with ❤️ by the Payvo Team** 