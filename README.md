# Payvo Middleware Testing Platform

**Internal Testing Platform for Payvo AI Employees**

A comprehensive testing environment for the Payvo Middleware backend system, designed for MCC prediction, merchant detection, and future payment processing capabilities. This platform enables Payvo AI team members to test, validate, and iterate on features that will power the production Payvo app.

## **Project Purpose**

This repository serves as an **internal testing and development platform** for Payvo AI employees to:

- **Test Payvo Middleware APIs** - Validate MCC prediction and merchant detection systems
- **Prototype App Features** - Experiment with location-based payment routing
- **Validate Business Logic** - Test payment intelligence algorithms before production
- **Demo Capabilities** - Showcase middleware functionality to stakeholders
- **Develop Future Features** - Build and test payment processing enhancements

### **For Payvo AI Team**
This platform is specifically designed for internal use by Payvo AI engineers, product managers, and stakeholders to test middleware capabilities that will eventually power the consumer-facing Payvo application.

## **Payvo Middleware Overview**

The **Payvo Middleware** is the core backend system that will power:

1. **MCC (Merchant Category Code) Prediction** - AI-powered merchant categorization
2. **Location-Based Merchant Detection** - GPS-first venue identification  
3. **Payment Routing Intelligence** - Optimal card selection algorithms
4. **Future Payment Processing** - Transaction handling and optimization

This testing platform provides a complete environment to validate these capabilities before integration into the production Payvo app.

## **Testing Platform Architecture**

```
Payvo-Middleware-Testing/
├── middleware-system/          # Core Middleware Backend (Production-Ready)
│   ├── app/                   # FastAPI application
│   │   ├── api/              # REST API endpoints
│   │   ├── services/         # Business logic (MCC, routing, etc.)
│   │   ├── database/         # Supabase integration
│   │   └── core/             # Configuration
│   └── README.md            # Backend testing documentation
│
├── middleware-application/     # Testing Mobile App (React Native)
│   ├── src/                  # Test app source code
│   │   ├── screens/         # Testing UI screens
│   │   ├── services/        # Middleware API integration
│   │   └── components/      # Testing components
│   └── README.md           # Mobile testing documentation
│
├── docker-compose.yml       # Production deployment simulation
└── README.md              # This overview (testing guide)
```

## **Core Middleware Capabilities Being Tested**

### **MCC Prediction Engine**
- **GPS-First Approach**: Location-based merchant categorization
- **Multi-Source Integration**: Google Places + Foursquare APIs
- **AI Enhancement**: OpenAI-powered prediction refinement
- **85-95% Accuracy**: High-confidence category predictions
- **Real-time Processing**: Sub-200ms response times

### **Location Intelligence**
- **Precision Tracking**: 1-10 meter GPS accuracy
- **Background Monitoring**: Continuous location updates
- **Venue Detection**: Indoor/outdoor merchant identification
- **Spatial Analysis**: Geographic pattern recognition

### **Payment Routing Logic**
- **Context-Aware Selection**: Multi-factor card routing
- **Reward Optimization**: Maximize cashback/points
- **Risk Management**: Minimize transaction failures
- **Learning Engine**: Improves over time

### **Real-time Processing**
- **Live API Testing**: Real-time middleware validation
- **Session Management**: Stateful transaction handling
- **Background Processing**: Continuous data analysis
- **Performance Monitoring**: Response time tracking

## **Getting Started (Payvo AI Team)**

### **Prerequisites for Testing**
- **Python 3.11+** (Middleware backend)
- **Node.js 18+** (Testing app)
- **Docker** (Deployment simulation)
- **Supabase Access** (Internal database)
- **API Keys** (Google Places, Foursquare, OpenAI)

### **Quick Setup for Testing**

1. **Clone the Testing Platform:**
```bash
   git clone https://github.com/Payvo-ai/payvo-middleware.git
cd payvo-middleware
```

2. **Start Middleware Backend:**
```bash
   cd middleware-system
   pip install -r requirements.txt
   cp .env.example .env
   # Add your API keys to .env
   python run.py
   ```

3. **Launch Testing App:**
```bash
   cd middleware-application
   npm install
   cd ios && pod install && cd ..  # iOS
   npx react-native run-ios        # or run-android
   ```

4. **Docker Testing Environment:**
```bash
   docker-compose up -d  # Full stack testing
   ```

## **Live Testing Environment**

### **Production-Ready Middleware API**
- **URL**: https://payvo-middleware-production.up.railway.app
- **Health Check**: `/api/v1/health`
- **API Documentation**: `/docs`
- **Real-time Testing**: WebSocket endpoints available

### **Key Testing Endpoints**
```bash
# Test MCC Prediction
POST /api/v1/routing/predict-mcc

# Test Payment Routing
POST /api/v1/routing/initiate

# Test Location Intelligence
POST /api/v1/background-location/start

# Test User Management
POST /api/v1/auth/login
```

## **Testing Mobile Application**

The React Native app provides a comprehensive interface for testing all middleware capabilities:

### **Testing Screens**
- **Location Testing**: GPS accuracy and venue detection
- **MCC Prediction**: Real-time merchant categorization
- **Payment Routing**: Card selection algorithms
- **Analytics**: Performance metrics and success rates
- **Background Tracking**: Continuous location monitoring

### **Validation Features**
- **Real-time API Integration**: Live middleware testing
- **Performance Monitoring**: Response time analysis
- **Success Rate Tracking**: Prediction accuracy metrics
- **Edge Case Testing**: Offline scenarios, poor GPS, etc.

## **Testing Scenarios**

### **For Engineers**
- API endpoint validation
- Performance benchmarking
- Error handling verification
- Integration testing

### **For Product Managers**
- Feature demonstration
- User experience validation
- Business logic verification
- Stakeholder presentations

### **For Stakeholders**
- Capability showcasing
- ROI demonstration
- Technical feasibility proof
- Market readiness assessment

## **Testing Metrics & Analytics**

The platform provides comprehensive analytics for evaluating middleware performance:

- **Prediction Accuracy**: MCC categorization success rates
- **Response Times**: API performance metrics
- **Location Precision**: GPS accuracy measurements
- **Success Rates**: Transaction routing effectiveness
- **Error Analysis**: Failure pattern identification

## **Internal Access & Security**

This testing platform is designed for **internal Payvo AI use only**:

- **Employee Authentication**: Secure access for team members
- **API Key Management**: Internal credential handling
- **Data Privacy**: Test data isolation and protection
- **Audit Logging**: Complete activity tracking

## **Future Roadmap**

As the Payvo Middleware evolves, this testing platform will expand to include:

- **Payment Processing**: Transaction handling and settlement
- **Enhanced AI Models**: Advanced prediction algorithms  
- **Merchant Partnerships**: Direct integration testing
- **Consumer App Features**: Production-ready capabilities
- **Scalability Testing**: Load and performance validation

## **Internal Support**

For Payvo AI team members:
- **Technical Issues**: Contact the engineering team
- **Feature Requests**: Submit via internal channels  
- **API Questions**: Reference the `/docs` endpoint
- **Testing Guidance**: See individual README files in subdirectories