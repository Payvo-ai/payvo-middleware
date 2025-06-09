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
- **GPS-First MCC Prediction** - Smart merchant category prediction
- **Enhanced Location Routing** - Indoor mapping and venue detection
- **Supabase Integration** - Scalable data persistence
- **Redis Caching** - High-performance session management
- **RESTful API** - Comprehensive routing endpoints
- **Real-time Analytics** - Performance monitoring and insights

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
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
REDIS_URL=redis://localhost:6379
```

**payvo-test-app/.env:**
```env
API_BASE_URL=http://localhost:8000
```

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

### MCC Prediction Test
```bash
curl -X POST http://localhost:8000/api/v1/routing/predict-mcc \
  -H "Content-Type: application/json" \
  -d '{"latitude": 40.7128, "longitude": -74.0060}'
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is proprietary software owned by Payvo AI.