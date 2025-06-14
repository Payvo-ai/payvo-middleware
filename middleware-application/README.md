# Payvo Middleware Application - React Native Client

A comprehensive React Native test application for the Payvo Middleware, featuring GPS-based merchant detection, real-time MCC prediction, intelligent payment routing simulation, and continuous background location tracking.

## 🚀 Features

### Core Functionality
- **Real-time GPS Integration** - Continuous location tracking and merchant detection
- **Background Location Tracking** - Monitors location every 3-5 seconds even when app is closed
- **MCC Prediction Testing** - Live testing of merchant category code predictions
- **Payment Routing Simulation** - End-to-end card routing workflow testing
- **Smart Session Management** - Automatic session creation and lifecycle management
- **Transaction Analytics** - Detailed performance metrics and success rates
- **Interactive UI** - Intuitive interface for testing all middleware features

### Advanced Features
- **Adaptive Radius System** - Intelligent search radius optimization (1m to 10m)
- **Multi-API Integration** - Google Places and Foursquare data aggregation
- **Session Persistence** - Maintains tracking across app restarts
- **Battery Optimization** - Smart power management for extended tracking
- **Offline Capability** - Queues location updates when offline
- **Error Recovery** - Automatic retry mechanisms and fallback strategies
- **Analytics Integration** - Comprehensive tracking and performance metrics

### Technical Features
- **React Native 0.72+** - Cross-platform mobile development
- **TypeScript** - Type-safe development with full IntelliSense
- **React Navigation** - Smooth navigation with stack and tab navigators
- **Async Storage** - Persistent local data storage
- **Real-time Updates** - WebSocket integration for live data
- **Geolocation Services** - High-accuracy GPS with background tracking
- **Network State Management** - Robust API integration with error handling

## 📁 Project Structure

```
middleware-application/
├── src/
│   ├── components/           # Reusable UI components
│   │   ├── LocationCard.tsx
│   │   ├── MCCDisplay.tsx
│   │   ├── PaymentCard.tsx
│   │   └── TransactionHistory.tsx
│   ├── screens/             # Main application screens
│   │   ├── HomeScreen.tsx
│   │   ├── LocationScreen.tsx
│   │   ├── RoutingScreen.tsx
│   │   ├── AnalyticsScreen.tsx
│   │   ├── SettingsScreen.tsx
│   │   └── BackgroundLocationDemo.tsx  # Background tracking demo
│   ├── services/            # API and external services
│   │   ├── PayvoAPI.ts                 # Enhanced API with background endpoints
│   │   ├── LocationService.ts
│   │   ├── BackgroundLocationService.ts # Background tracking service
│   │   ├── StorageService.ts
│   │   └── NetworkService.ts
│   ├── navigation/          # Navigation configuration
│   │   ├── AppNavigator.tsx
│   │   └── TabNavigator.tsx
│   ├── hooks/              # Custom React hooks
│   │   ├── useLocation.ts
│   │   ├── useBackgroundLocation.ts    # Background tracking hook
│   │   ├── usePayvoAPI.ts
│   │   └── useNetworkState.ts
│   ├── types/              # TypeScript type definitions
│   │   ├── api.ts
│   │   ├── location.ts
│   │   └── navigation.ts
│   ├── utils/              # Utility functions
│   │   ├── formatting.ts
│   │   ├── validation.ts
│   │   └── constants.ts
│   └── styles/             # Global styles and themes
│       ├── colors.ts
│       ├── typography.ts
│       └── spacing.ts
├── android/                # Android-specific configuration
├── ios/                    # iOS-specific configuration
├── __tests__/              # Test files
├── package.json            # Dependencies and scripts
├── tsconfig.json           # TypeScript configuration
├── metro.config.js         # Metro bundler configuration
├── babel.config.js         # Babel configuration
└── app.json               # Expo/React Native configuration
```

## 🛠️ Installation & Setup

### Prerequisites
- **Node.js 18+** - JavaScript runtime
- **React Native CLI** - React Native command line tools
- **Xcode** (iOS development) - macOS only
- **Android Studio** (Android development)
- **CocoaPods** (iOS dependencies) - macOS only

### Quick Start

1. **Navigate to the App Directory:**
   ```bash
   cd middleware-application
   ```

2. **Install Dependencies:**
   ```bash
   npm install
   # or
   yarn install
   ```

3. **iOS Setup (macOS only):**
   ```bash
   cd ios && pod install && cd ..
   ```

4. **Configure Environment:**
   ```bash
   # Create environment configuration
   cp .env.example .env
   # Edit .env with your settings
   ```

5. **Start Metro Bundler:**
   ```bash
   npx react-native start
   ```

6. **Run the App:**
   ```bash
   # iOS (requires macOS and Xcode)
   npx react-native run-ios
   
   # Android (requires Android Studio)
   npx react-native run-android
   ```

### Environment Configuration

Create a `.env` file in the project root:

```env
# Payvo Middleware API - now deployed on Railway
API_BASE_URL=https://payvo-middleware-production.up.railway.app
API_VERSION=v1
API_TIMEOUT=30000

# Location Services
LOCATION_ACCURACY=high
LOCATION_TIMEOUT=15000
BACKGROUND_LOCATION=true

# Background Location Tracking
BACKGROUND_UPDATE_INTERVAL=4000    # 4 seconds
BACKGROUND_MIN_DISTANCE=5          # 5 meters
BACKGROUND_SESSION_DURATION=30     # 30 minutes
BACKGROUND_ENABLE_WHEN_CLOSED=true

# Development Settings
DEBUG_MODE=true
LOG_LEVEL=debug
MOCK_API=false

# Optional Features
ENABLE_ANALYTICS=true
ENABLE_CRASH_REPORTING=false
```

## 📱 App Features & Screens

### Home Screen
- **Current Location Display** - Real-time GPS coordinates and address
- **Middleware Connection Status** - Live connection indicator to Railway deployment
- **Quick Actions** - Access to main features
- **Recent Transactions** - Last 10 transaction attempts
- **Background Tracking Status** - Current tracking session information

### Location Screen
- **Interactive Map** - Real-time location with merchant markers
- **Venue Detection** - Indoor/outdoor venue identification
- **MCC Prediction Panel** - Live MCC predictions with confidence scores
- **Location History** - Previously visited locations
- **Adaptive Radius Visualization** - Shows current search radius

### Routing Screen
- **Card Selection Interface** - Available payment methods
- **Routing Simulation** - Step-by-step routing process
- **Success Rate Display** - Historical routing performance
- **Token Management** - Payment token status and lifecycle

### Analytics Screen
- **Performance Metrics** - API response times and success rates
- **Prediction Accuracy** - MCC prediction performance charts
- **Usage Statistics** - App usage patterns and trends
- **Background Tracking Analytics** - Session performance and battery usage
- **Export Options** - Data export for analysis

### Settings Screen
- **API Configuration** - Middleware endpoint settings (Railway deployment)
- **Location Preferences** - GPS accuracy and update frequency
- **Background Tracking Settings** - Update intervals and session duration
- **Privacy Settings** - Data collection and storage preferences
- **Debug Tools** - Developer utilities and diagnostics

### Background Location Demo Screen
- **Real-time Tracking Control** - Start/stop background tracking
- **Session Management** - View active sessions and extend duration
- **Live Location Updates** - Real-time location and MCC predictions
- **Optimal MCC Display** - Best MCC based on session history
- **Performance Metrics** - Tracking accuracy and battery usage
- **Configuration Panel** - Adjust tracking parameters

## 🔌 API Integration

### Payvo Middleware Endpoints

#### Health Check
```bash
curl https://payvo-middleware-production.up.railway.app/api/v1/health
```

#### Start Routing Session
```bash
curl -X POST https://payvo-middleware-production.up.railway.app/api/v1/routing/initiate \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "platform": "ios",
    "wallet_type": "apple_pay",
    "transaction_amount": 25.50
  }'
```

#### MCC Prediction Test
```bash
curl -X POST https://payvo-middleware-production.up.railway.app/api/v1/routing/predict-mcc \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 40.7128,
    "longitude": -74.0060,
    "terminal_id": "term123"
  }'
```

#### Background Location Tracking
```bash
# Start background tracking session
curl -X POST https://payvo-middleware-production.up.railway.app/api/v1/background-location/start \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "session_duration_minutes": 30
  }'

# Update location
curl -X POST https://payvo-middleware-production.up.railway.app/api/v1/background-location/update \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "session123",
    "location": {
      "latitude": 40.7128,
      "longitude": -74.0060,
      "accuracy": 5.0
    },
    "mcc_prediction": {
      "mcc": "5812",
      "confidence": 0.95
    }
  }'
```

## 🎯 Background Location Tracking System

### Core Components

#### 1. BackgroundLocationService
**File**: `src/services/BackgroundLocationService.ts`

Core service that handles:
- Background location tracking
- Session lifecycle management
- Location update queuing
- Battery optimization
- App state transitions

```typescript
// Key methods
startBackgroundTracking(userId: string, config: BackgroundLocationConfig)
stopBackgroundTracking()
updateLocation(location: LocationData)
predictMCC(location: LocationData)
```

#### 2. Enhanced PayvoAPI Service
**File**: `src/services/PayvoAPI.ts`

Enhanced API service with background location endpoints:
- Session management
- Location updates
- MCC predictions
- Optimal MCC calculation

```typescript
// New endpoints
startBackgroundTracking(request: StartBackgroundTrackingRequest)
updateBackgroundLocation(sessionId: string, update: BackgroundLocationUpdate)
getOptimalMCC(sessionId: string, location: LocationData)
```

#### 3. useBackgroundLocation Hook
**File**: `src/hooks/useBackgroundLocation.ts`

React hook providing:
- State management
- Session tracking
- Location predictions
- Error handling

```typescript
const {
  isTracking,
  currentSession,
  recentPredictions,
  startTracking,
  stopTracking,
  getOptimalMCC
} = useBackgroundLocation(userId, config);
```

### Usage Examples

#### Starting Background Tracking

```typescript
import { useBackgroundLocation } from '../hooks/useBackgroundLocation';

const MyComponent = () => {
  const { startTracking, isTracking } = useBackgroundLocation('user123', {
    updateInterval: 4000,      // 4 seconds
    minDistanceFilter: 5,      // 5 meters
    sessionDuration: 30,       // 30 minutes
    enableWhenClosed: true     // Track when app closed
  });

  const handleStart = async () => {
    const sessionId = await startTracking();
    console.log('Session started:', sessionId);
  };

  return (
    <TouchableOpacity onPress={handleStart} disabled={isTracking}>
      <Text>{isTracking ? 'Tracking Active' : 'Start Tracking'}</Text>
    </TouchableOpacity>
  );
};
```

#### Monitoring Session Status

```typescript
const {
  currentSession,
  hasActiveSession,
  isSessionValid,
  locationsCount,
  lastUpdate,
  error
} = useBackgroundLocation(userId, config);

// Real-time status display
<View>
  <Text>Session Active: {hasActiveSession ? 'Yes' : 'No'}</Text>
  <Text>Locations Captured: {locationsCount}</Text>
  <Text>Last Update: {lastUpdate?.toLocaleTimeString()}</Text>
  {error && <Text style={{color: 'red'}}>Error: {error}</Text>}
</View>
```

#### Getting Optimal MCC

```typescript
const { getOptimalMCC } = useBackgroundLocation(userId, config);

const handleGetMCC = async () => {
  const result = await getOptimalMCC();
  if (result) {
    console.log(`Optimal MCC: ${result.mcc}`);
    console.log(`Confidence: ${result.confidence * 100}%`);
    console.log(`Method: ${result.method}`);
  }
};
```

## 🔧 Configuration Options

### BackgroundLocationConfig

```typescript
interface BackgroundLocationConfig {
  updateInterval: number;        // Update frequency in milliseconds (default: 4000)
  minDistanceFilter: number;     // Minimum distance for updates in meters (default: 5)
  sessionDuration: number;       // Session duration in minutes (default: 30)
  enableWhenClosed: boolean;     // Track when app is closed (default: true)
  batteryOptimization: boolean;  // Enable battery optimization (default: true)
  adaptiveRadius: boolean;       // Use adaptive search radius (default: true)
  minRadius: number;            // Minimum search radius in meters (default: 1)
  maxRadius: number;            // Maximum search radius in meters (default: 10)
  confidenceThreshold: number;  // Minimum confidence for predictions (default: 0.7)
}
```

### Default Configuration

```typescript
const defaultConfig: BackgroundLocationConfig = {
  updateInterval: 4000,          // 4 seconds
  minDistanceFilter: 5,          // 5 meters
  sessionDuration: 30,           // 30 minutes
  enableWhenClosed: true,        // Track when closed
  batteryOptimization: true,     // Optimize battery
  adaptiveRadius: true,          // Use adaptive radius
  minRadius: 1,                  // 1 meter minimum
  maxRadius: 10,                 // 10 meters maximum
  confidenceThreshold: 0.7       // 70% confidence minimum
};
```

## 📊 Performance Metrics

### Background Location Tracking
- **Update Frequency**: 3-5 seconds (configurable)
- **Location Accuracy**: 1-10 meters (GPS dependent)
- **Session Duration**: Configurable (default 30 minutes)
- **Battery Impact**: Optimized for minimal drain
- **Offline Capability**: Queue updates when offline
- **Error Recovery**: Automatic retry with exponential backoff

### MCC Prediction Accuracy
- **GPS-based**: 85-95% confidence
- **Multi-source**: 90-98% confidence
- **Historical learning**: Improves over time
- **Response time**: <200ms average
- **Adaptive radius**: 1-10 meter precision

## 🧪 Testing & Development

### Running Tests
```bash
# Run all tests
npm test

# Run tests with coverage
npm run test:coverage

# Run specific test file
npm test -- LocationService.test.ts
```

### Development Scripts
```bash
# Start development server
npm start

# Run on iOS simulator
npm run ios

# Run on Android emulator
npm run android

# Build for production
npm run build

# Lint code
npm run lint

# Format code
npm run format
```

### Debug Mode
```bash
# Enable debug logging
export DEBUG_MODE=true
npm start
```

## 🔒 Security & Privacy

### Data Protection
- **Location Encryption**: All location data encrypted locally
- **Session Security**: Secure session tokens with expiration
- **API Authentication**: Bearer token authentication
- **Data Retention**: Configurable retention policies
- **Privacy Controls**: User consent and opt-out mechanisms

### Permissions
- **Location Services**: Required for GPS tracking
- **Background App Refresh**: Required for background tracking
- **Network Access**: Required for API communication
- **Storage Access**: Required for session persistence

### Compliance
- **iOS App Store Guidelines**: Compliant with location usage policies
- **Google Play Store**: Compliant with background location requirements
- **GDPR**: Data protection and user rights
- **Privacy by Design**: Minimal data collection principles

## 🛠️ Troubleshooting

### Common Issues

#### Location Services Not Working
```bash
# Check permissions
Settings > Privacy & Security > Location Services > Your App

# Verify configuration
console.log('Location config:', LocationService.getConfig());
```

#### Background Tracking Stops
```bash
# Check background app refresh
Settings > General > Background App Refresh

# Verify session status
const session = await BackgroundLocationService.getCurrentSession();
console.log('Session status:', session);
```

#### API Connection Issues
```bash
# Test API connectivity
curl https://payvo-middleware-production.up.railway.app/api/v1/health

# Check network status
const networkState = await NetworkService.getNetworkState();
console.log('Network:', networkState);
```

### Debug Tools
- **React Native Debugger** - For debugging React components
- **Flipper** - For network and performance debugging
- **Xcode Instruments** - For iOS performance profiling
- **Android Studio Profiler** - For Android performance analysis

## 📞 Support

For technical support and questions:
- **Documentation**: Check the inline code documentation
- **Issues**: Report bugs and feature requests via GitHub issues
- **Performance**: Monitor app metrics via the Analytics screen
- **Logs**: Check device logs for detailed error information

## 📄 License

This mobile application is part of the Payvo payment platform. All rights reserved.
