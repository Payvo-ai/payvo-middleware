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

The enhanced system combines multiple data sources for highly accurate merchant categorization:

### **Prediction Sources**
1. **Real Business Data** - Google Places & Foursquare APIs
2. **Historical Patterns** - Area-based transaction learning
3. **Terminal Analysis** - ID pattern recognition & behavior analysis
4. **WiFi Fingerprinting** - Brand detection from network SSIDs
5. **BLE Beacons** - Proximity-based merchant identification

### **Key Improvements**
- **Higher Accuracy**: 85-95% confidence vs 50-70% baseline
- **Real-time Data**: Live business verification
- **Multi-factor Analysis**: Weighted consensus from 5+ sources
- **Learning System**: Improves over time with transaction data
- **Fallback Protection**: Graceful degradation when APIs unavailable

### **Confidence Scoring**
- **0.9-0.95**: High confidence (exact matches, strong patterns)
- **0.7-0.89**: Good confidence (multiple source agreement)
- **0.5-0.69**: Moderate confidence (single source or partial match)
- **0.3-0.49**: Low confidence (pattern-based inference)
- **0.2-0.29**: Fallback (default categorization)

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is proprietary software owned by Payvo AI.