# Payvo - Smart Payment Routing System

A comprehensive payment routing system with GPS-first MCC prediction and enhanced location-based merchant categorization.

## 📁 Project Structure

```
Payvo-Middleware/
├── payvo-middleware/          # Backend FastAPI middleware
│   ├── app/                   # Main application code
│   ├── requirements.txt       # Python dependencies
│   ├── .env                   # Environment variables
│   └── README.md             # Middleware documentation
├── payvo-test-app/           # React Native test application
│   ├── src/                  # React Native source code
│   ├── package.json          # Node.js dependencies
│   └── README.md            # Mobile app documentation
├── docker-compose.yml        # Local development setup
├── Dockerfile               # Container configuration
├── railway.json             # Railway deployment config
├── vercel.json              # Vercel deployment config
└── DEPLOYMENT.md            # Deployment instructions
```

## 🚀 Quick Start

### Backend Middleware
```bash
cd payvo-middleware
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
python app/main.py
```

### Mobile Test App
```bash
cd payvo-test-app
npm install
npx react-native run-ios     # or run-android
```

### Docker Development
```bash
docker-compose up --build
```

## 🌟 Features

### Middleware (Backend)
- **Enhanced MCC Prediction** - Multi-source merchant category prediction with real-time data
- **GPS-First Location Services** - Building-level GPS accuracy with indoor mapping
- **Real Business District APIs** - Google Places & Foursquare integration
- **WiFi/BLE Fingerprinting** - Signal-based merchant identification
- **Terminal ID Analysis** - Comprehensive terminal lookup and categorization
- **Historical Pattern Learning** - Area-based transaction pattern analysis
- **Supabase Integration** - Scalable data persistence with real-time sync
- **Redis Caching** - High-performance session and prediction caching
- **RESTful API** - Comprehensive routing and prediction endpoints
- **Real-time Analytics** - Performance monitoring and prediction insights

### Test App (Mobile)
- **React Native** - Cross-platform mobile development
- **GPS Integration** - Real-time location services
- **API Testing** - Complete middleware integration
- **Transaction Simulation** - End-to-end testing capabilities

## 🔧 Configuration

### Environment Variables
Create `.env` files in respective directories:

**payvo-middleware/.env:**
```env
# Core Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
PAYVO_SECRET_KEY=your_secret_key
REDIS_URL=redis://localhost:6379

# Enhanced MCC Prediction APIs
GOOGLE_PLACES_API_KEY=your_google_places_api_key
GOOGLE_PLACES_ENABLED=true
GOOGLE_PLACES_RADIUS_METERS=200
GOOGLE_PLACES_MAX_RESULTS=20

FOURSQUARE_API_KEY=your_foursquare_api_key
FOURSQUARE_ENABLED=true
FOURSQUARE_RADIUS_METERS=200
FOURSQUARE_MAX_RESULTS=20

# Service Feature Flags
ENHANCED_LOCATION_ENABLED=true
ENHANCED_TERMINAL_ENABLED=true
ENHANCED_FINGERPRINT_ENABLED=true
ENHANCED_HISTORICAL_ENABLED=true

# Confidence Thresholds
MIN_LOCATION_CONFIDENCE=0.5
MIN_TERMINAL_CONFIDENCE=0.6
MIN_FINGERPRINT_CONFIDENCE=0.4
MIN_HISTORICAL_CONFIDENCE=0.5

# Analysis Settings
DEFAULT_SEARCH_RADIUS_METERS=200
MAX_SEARCH_RADIUS_METERS=1000
MIN_SEARCH_RADIUS_METERS=50

# Cache TTL (hours)
LOCATION_CACHE_TTL_HOURS=24
TERMINAL_CACHE_TTL_HOURS=12
FINGERPRINT_CACHE_TTL_HOURS=6
HISTORICAL_CACHE_TTL_HOURS=1

# Prediction Weights
LOCATION_WEIGHT=0.35
HISTORICAL_WEIGHT=0.25
TERMINAL_WEIGHT=0.20
WIFI_WEIGHT=0.10
BLE_WEIGHT=0.10
```

**payvo-test-app/.env:**
```env
API_BASE_URL=http://localhost:8000
```

### API Keys Setup

#### Google Places API
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Enable Places API
3. Create credentials (API Key)
4. Add to `GOOGLE_PLACES_API_KEY`

#### Foursquare API
1. Go to [Foursquare Developers](https://developer.foursquare.com/)
2. Create an app
3. Get API key from app dashboard
4. Add to `FOURSQUARE_API_KEY`

## 📦 Deployment

### Railway (Recommended)
```bash
# Deploy from GitHub
railway login
railway up
```

### Docker
```bash
docker build -t payvo-middleware .
docker run -p 8000:8000 payvo-middleware
```

### Vercel (Serverless)
```bash
vercel --prod
```

## 📚 Documentation

- **[Middleware README](./payvo-middleware/README.md)** - Backend API documentation
- **[Mobile App README](./payvo-test-app/README.md)** - React Native setup guide
- **[Deployment Guide](./DEPLOYMENT.md)** - Comprehensive deployment instructions
- **[Supabase Setup](./payvo-middleware/SUPABASE_SETUP.md)** - Database configuration

## 🧪 Testing

### API Health Check
```bash
curl http://localhost:8000/api/v1/health
```

### Enhanced MCC Prediction Test
```bash
# Basic location-based prediction
curl -X POST http://localhost:8000/api/mcc/predict \
  -H "Content-Type: application/json" \
  -d '{
    "location": {"latitude": 40.7128, "longitude": -74.0060},
    "amount": 25.50
  }'

# Comprehensive prediction with all data sources
curl -X POST http://localhost:8000/api/mcc/predict \
  -H "Content-Type: application/json" \
  -d '{
    "location": {"latitude": 40.7128, "longitude": -74.0060},
    "terminal_id": "SQ12345678",
    "amount": 45.20,
    "wifi_networks": [
      {"ssid": "Starbucks WiFi", "bssid": "aa:bb:cc:dd:ee:ff", "rssi": -45}
    ],
    "ble_beacons": [
      {"uuid": "e2c56db5-dffb-48d2-b060-d0f5a71096e0", "major": 1, "minor": 100, "rssi": -60}
    ],
    "merchant_name": "Coffee Shop Downtown"
  }'

# Test prediction scenarios
curl -X POST http://localhost:8000/api/mcc/test-scenarios

# Check service configuration
curl http://localhost:8000/api/mcc/config

# Health check for enhanced services
curl http://localhost:8000/api/mcc/health
```

### Legacy MCC Prediction (Original)
```bash
curl -X POST http://localhost:8000/api/v1/routing/predict-mcc \
  -H "Content-Type: application/json" \
  -d '{"latitude": 40.7128, "longitude": -74.0060}'
```

## 🔍 Enhanced MCC Prediction System

The system now includes **LLM-powered enhancement** for intelligent merchant category code prediction:

### 🧠 LLM Enhancement Features

- **Intelligent Merchant Analysis**: Uses OpenAI GPT models to analyze merchant names, business descriptions, and context
- **Conflict Resolution**: Automatically resolves conflicting predictions from multiple sources using AI reasoning
- **Contextual Understanding**: Considers transaction patterns, location data, and business characteristics
- **Confidence Scoring**: Provides detailed confidence analysis with reasoning explanations
- **Continuous Learning**: Stores LLM analyses for future improvement and pattern recognition

### Prediction Sources

1. **🌍 Real-time Location APIs** - Google Places & Foursquare venue data
2. **🏪 Terminal ID Analysis** - Pattern recognition and processor identification
3. **📡 WiFi/BLE Fingerprinting** - Device-based location and business identification
4. **📊 Historical Patterns** - Area-based transaction analysis and learning
5. **🤖 LLM Enhancement** - AI-powered reasoning and conflict resolution

### Key Improvements

- **85-95% Confidence** predictions using multi-source consensus
- **Intelligent Reasoning** for ambiguous or conflicting cases
- **Real-time Data** integration from multiple business directories
- **Historical Learning** that improves predictions over time
- **Contextual Analysis** considering transaction patterns and merchant characteristics

### LLM Configuration

```bash
# Enable LLM enhancement
LLM_ENHANCEMENT_ENABLED=true
LLM_DEFAULT_MODEL=gpt-4o-mini
LLM_MAX_TOKENS=1000
LLM_TEMPERATURE=0.3
```

### Testing Enhanced Predictions

**Comprehensive MCC Prediction:**
```bash
curl -X POST "http://localhost:8000/mcc/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 40.7589,
    "longitude": -73.9851,
    "merchant_name": "Joe'\''s Coffee Shop",
    "use_llm_enhancement": true,
    "include_alternatives": true
  }'
```

**LLM Merchant Name Analysis:**
```bash
curl -X POST "http://localhost:8000/mcc/analyze/merchant-name" \
  -H "Content-Type: application/json" \
  -d '{
    "merchant_name": "Tony'\''s Pizzeria & Italian Restaurant",
    "additional_info": {"location": "New York", "type": "dining"}
  }'
```

**Conflict Resolution:**
```bash
curl -X POST "http://localhost:8000/mcc/resolve/conflicts" \
  -H "Content-Type: application/json" \
  -d '{
    "conflicting_predictions": [
      {"mcc": "5812", "confidence": 0.7, "method": "location"},
      {"mcc": "5814", "confidence": 0.6, "method": "fingerprint"}
    ],
    "context": {"merchant_name": "Quick Eats", "transaction_amount": 12.50}
  }'
```

### Expected Response Format

```json
{
  "predicted_mcc": "5812",
  "confidence": 0.92,
  "method": "llm_enhanced_consensus",
  "prediction_sources": [
    {
      "method": "location_analysis",
      "mcc": "5812",
      "confidence": 0.85,
      "source": "google_places"
    },
    {
      "method": "llm_analysis", 
      "predicted_mcc": "5812",
      "confidence": 0.94,
      "reasoning": "Based on the merchant name 'Joe's Coffee Shop' and location data, this is clearly a coffee shop/cafe establishment, which falls under MCC 5812 for eating places and restaurants.",
      "enhancement_applied": true
    }
  ],
  "consensus_score": 0.89,
  "processing_time_ms": 1250,
  "llm_analysis": {
    "reasoning": "Detailed AI analysis...",
    "key_factors": ["merchant_name_indicators", "location_context"],
    "certainty_level": "high"
  },
  "enhancement_applied": true
}
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is proprietary software owned by Payvo AI.