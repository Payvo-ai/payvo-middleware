# Payvo Middleware - Advanced MCC-based Card Routing System

## Overview

Payvo Middleware is a sophisticated payment routing system that uses Machine Learning and contextual intelligence to predict Merchant Category Codes (MCC) and automatically select the optimal payment card for maximum rewards and transaction success.

## 🚀 Key Features

### Multi-Layer MCC Detection Engine
- **Pre-Tap Context Collection**: Gathers location, Wi-Fi, Bluetooth, and terminal data
- **Layered Prediction System**: Combines multiple detection methods for high accuracy
- **AI-Powered Fallback**: Uses LLM inference when traditional methods fail
- **Continuous Learning**: Improves predictions based on transaction feedback

### Intelligent Card Routing
- **Rewards Optimization**: Automatically selects cards with highest reward rates
- **Success Rate Analysis**: Considers historical transaction success rates
- **Network Acceptance**: Factors in payment network acceptance rates
- **User Preferences**: Respects user-defined card preferences and restrictions

### Advanced Token Provisioning
- **Multi-Platform Support**: Works with Apple Pay, Google Pay, Samsung Pay
- **Secure Token Management**: Handles payment tokens with enterprise-grade security
- **Dynamic Activation**: Activates tokens only when needed for transactions
- **Automatic Cleanup**: Manages token lifecycle and cleanup

### Privacy-First Architecture
- **Local Processing**: All sensitive data processed locally on device
- **User Consent**: Explicit consent required for all data collection
- **Data Minimization**: Collects only necessary data for functionality
- **Secure Communication**: End-to-end encryption for all API communications

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Payvo Middleware                         │
├─────────────────────────────────────────────────────────────┤
│  Pre-Tap Context    │  MCC Prediction   │  Card Routing     │
│  Collector          │  Engine           │  Engine           │
│  ┌─────────────┐    │  ┌─────────────┐  │  ┌─────────────┐  │
│  │ Location    │    │  │ Rule-based  │  │  │ Rewards     │  │
│  │ Wi-Fi       │────┼─▶│ ML Models   │──┼─▶│ Success     │  │
│  │ Bluetooth   │    │  │ AI Fallback │  │  │ Preferences │  │
│  │ Terminal    │    │  └─────────────┘  │  └─────────────┘  │
│  └─────────────┘    │                   │                   │
├─────────────────────────────────────────────────────────────┤
│  Token Provisioning │  Learning &       │  API Layer        │
│  Layer              │  Feedback Loop    │                   │
│  ┌─────────────┐    │  ┌─────────────┐  │  ┌─────────────┐  │
│  │ Apple Pay   │    │  │ Feedback    │  │  │ REST API    │  │
│  │ Google Pay  │    │  │ Processing  │  │  │ WebSocket   │  │
│  │ Samsung Pay │    │  │ Pattern     │  │  │ GraphQL     │  │
│  │ HCE/SE      │    │  │ Learning    │  │  │ Webhooks    │  │
│  └─────────────┘    │  └─────────────┘  │  └─────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 🛠️ Installation

### Prerequisites
- Python 3.9+
- pip or poetry
- Redis (for caching)
- PostgreSQL (optional, for persistent storage)

### Quick Start

1. **Clone the repository**
```bash
git clone https://github.com/your-org/payvo-middleware.git
cd payvo-middleware
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set environment variables**
```bash
export PAYVO_SECRET_KEY="your-secret-key-here"
export PAYVO_DEBUG=true
export PAYVO_LOG_LEVEL=INFO
```

4. **Run the application**
```bash
python -m app.main
```

The API will be available at `http://localhost:8000`

### Docker Setup

```bash
# Build the image
docker build -t payvo-middleware .

# Run the container
docker run -p 8000:8000 -e PAYVO_SECRET_KEY="your-secret-key" payvo-middleware
```

## 📚 API Documentation

### Core Endpoints

#### Initiate Card Routing
```http
POST /api/v1/routing/initiate
Content-Type: application/json

{
  "user_id": "user123",
  "platform": "ios",
  "wallet_type": "apple_pay",
  "device_id": "device456",
  "transaction_amount": 25.50
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "session_id": "session_abc123",
    "predicted_mcc": "5812",
    "confidence": 0.89,
    "selected_card": {
      "card_id": "card_xyz789",
      "last_four": "1234",
      "network": "visa",
      "expected_rewards": 3.2
    },
    "token": {
      "provisioned": true,
      "expires_at": "2024-01-15T10:30:00Z"
    }
  }
}
```

#### Activate Payment Token
```http
POST /api/v1/routing/{session_id}/activate
```

#### Complete Transaction
```http
POST /api/v1/routing/{session_id}/complete
Content-Type: application/json

{
  "transaction_successful": true,
  "actual_mcc": "5812",
  "merchant_name": "Starbucks",
  "transaction_amount": 25.50,
  "rewards_earned": 3.2,
  "transaction_time": "2024-01-15T10:35:00Z"
}
```

### Utility Endpoints

#### Health Check
```http
GET /api/v1/health
```

#### Performance Metrics
```http
GET /api/v1/metrics
```

#### MCC Information
```http
GET /api/v1/mcc/5812/info
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PAYVO_SECRET_KEY` | Secret key for encryption | Required |
| `PAYVO_DEBUG` | Enable debug mode | `false` |
| `PAYVO_HOST` | Server host | `0.0.0.0` |
| `PAYVO_PORT` | Server port | `8000` |
| `PAYVO_LOG_LEVEL` | Logging level | `INFO` |
| `PAYVO_RATE_LIMIT_PER_MINUTE` | Rate limit per IP | `100` |

### Advanced Configuration

Create a `.env` file in the project root:

```env
# Core Settings
PAYVO_SECRET_KEY=your-super-secret-key-here
PAYVO_DEBUG=true
PAYVO_LOG_LEVEL=DEBUG

# API Settings
PAYVO_HOST=0.0.0.0
PAYVO_PORT=8000
PAYVO_RATE_LIMIT_PER_MINUTE=100

# Security
PAYVO_ALLOWED_HOSTS=["localhost", "127.0.0.1", "your-domain.com"]
PAYVO_CORS_ORIGINS=["http://localhost:3000", "https://your-app.com"]

# AI/ML Settings
PAYVO_OPENAI_API_KEY=your-openai-key
PAYVO_MODEL_NAME=gpt-4
PAYVO_MAX_TOKENS=150
PAYVO_TEMPERATURE=0.1

# External Services
PAYVO_REDIS_URL=redis://localhost:6379
PAYVO_DATABASE_URL=postgresql://user:pass@localhost/payvo
```

## 🧪 Testing

### Run Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_mcc_prediction.py
```

### Load Testing
```bash
# Install locust
pip install locust

# Run load tests
locust -f tests/load_test.py --host=http://localhost:8000
```

## 📊 Monitoring & Observability

### Metrics Available
- Request/response times
- MCC prediction accuracy
- Card routing success rates
- Token provisioning statistics
- Error rates and types

### Logging
The system provides structured logging with the following levels:
- `DEBUG`: Detailed debugging information
- `INFO`: General operational messages
- `WARNING`: Warning messages for potential issues
- `ERROR`: Error messages for failures
- `CRITICAL`: Critical system failures

### Health Checks
- `/ping` - Simple health check
- `/api/v1/health` - Detailed system health
- `/api/v1/metrics` - Performance metrics

## 🔒 Security

### Data Protection
- All sensitive data encrypted at rest and in transit
- PCI DSS compliance considerations
- GDPR compliance for EU users
- SOC 2 Type II controls

### Authentication & Authorization
- API key authentication
- JWT token support
- Role-based access control
- Rate limiting and DDoS protection

### Privacy Features
- Local data processing
- Minimal data collection
- User consent management
- Data retention policies

## 🚀 Deployment

### Production Deployment

1. **Environment Setup**
```bash
# Set production environment variables
export PAYVO_DEBUG=false
export PAYVO_LOG_LEVEL=WARNING
export PAYVO_SECRET_KEY="production-secret-key"
```

2. **Database Migration**
```bash
# Run database migrations
alembic upgrade head
```

3. **Start with Gunicorn**
```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: payvo-middleware
spec:
  replicas: 3
  selector:
    matchLabels:
      app: payvo-middleware
  template:
    metadata:
      labels:
        app: payvo-middleware
    spec:
      containers:
      - name: payvo-middleware
        image: payvo-middleware:latest
        ports:
        - containerPort: 8000
        env:
        - name: PAYVO_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: payvo-secrets
              key: secret-key
```

## 📈 Performance

### Benchmarks
- **MCC Prediction**: < 50ms average response time
- **Card Routing**: < 100ms average response time
- **Token Provisioning**: < 200ms average response time
- **Throughput**: 1000+ requests/second per instance

### Optimization Tips
- Enable Redis caching for frequently accessed data
- Use connection pooling for database connections
- Implement proper indexing for database queries
- Use CDN for static assets

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

### Code Style
- Follow PEP 8 guidelines
- Use type hints for all functions
- Add docstrings for all public methods
- Maintain test coverage above 90%

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Documentation
- [API Reference](docs/api.md)
- [Architecture Guide](docs/architecture.md)
- [Deployment Guide](docs/deployment.md)

### Community
- [GitHub Issues](https://github.com/your-org/payvo-middleware/issues)
- [Discussions](https://github.com/your-org/payvo-middleware/discussions)
- [Discord Community](https://discord.gg/payvo)

### Commercial Support
For enterprise support and custom implementations, contact us at support@payvo.com

---

**Built with ❤️ by the Payvo Team** 