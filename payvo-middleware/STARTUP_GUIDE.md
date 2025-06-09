# 🚀 Complete Startup Guide for Payvo Middleware

## 🔒 **SECURITY FIRST - IMMEDIATE ACTIONS REQUIRED**

Since you previously shared database credentials, you MUST complete these security steps before running the project:

### 1. Change Supabase Password
1. Go to [Supabase Dashboard](https://supabase.com/dashboard)
2. Select your project: `wwnakavxuejqltflzqhr`
3. Go to **Settings** → **Database**
4. Click **"Change database password"**
5. Generate a new strong password and save it securely

### 2. Regenerate API Keys (Recommended)
1. Go to **Settings** → **API**
2. Click **"Regenerate"** for both keys:
   - `anon` key (public)
   - `service_role` key (secret)
3. Update your `.env` file with the new keys

---

## 📋 Prerequisites

### 1. Python Environment
```bash
# Check Python version (3.9+ required)
python --version

# If you don't have Python 3.9+, install it:
# macOS: brew install python@3.9
# Windows: Download from python.org
# Linux: sudo apt install python3.9
```

### 2. Install Dependencies
```bash
# Install all required packages
pip install -r requirements.txt

# If you encounter issues, try:
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
```

### 3. Set Up Database Schema
1. Go to your Supabase dashboard
2. Navigate to **SQL Editor**
3. Copy the contents of `app/database/schema.sql`
4. Paste and run in the SQL Editor

---

## 🔧 Configuration

### 1. Verify Your .env File
Your `.env` file should look like this (with your actual credentials):

```env
# Payvo Middleware Configuration
PAYVO_SECRET_KEY=d8f3c2b1a9e7f6d5c4b3a2e1f9d8c7b6a5e4d3c2b1a9f8e7d6c5b4a3e2f1
PAYVO_DEBUG=true
PAYVO_LOG_LEVEL=INFO

# Server Configuration
PAYVO_HOST=0.0.0.0
PAYVO_PORT=8000

# Supabase Configuration (Update with your NEW credentials)
SUPABASE_URL=https://wwnakavxuejqltflzqhr.supabase.co
SUPABASE_ANON_KEY=your-new-anon-key-here
SUPABASE_SERVICE_ROLE_KEY=your-new-service-role-key-here

# Security
SECRET_KEY=d8f3c2b1a9e7f6d5c4b3a2e1f9d8c7b6a5e4d3c2b1a9f8e7d6c5b4a3e2f1
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 2. Generate New Secret Keys (Optional but Recommended)
```bash
# Generate a new secret key
python -c "import secrets; print('PAYVO_SECRET_KEY=' + secrets.token_urlsafe(32))"
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"
```

---

## 🧪 Test Installation

Before starting the server, run the test suite:

```bash
python test_installation.py
```

Expected output:
```
🚀 Starting Payvo Middleware Installation Tests

==================================================
Running Import Test
==================================================
Testing imports...
✓ Core configuration imported
✓ Database components imported
✓ Routing orchestrator imported
✓ FastAPI app imported

==================================================
Running Configuration Test
==================================================
Testing configuration...
✓ API_HOST configured: 0.0.0.0
✓ API_PORT configured: 8000
✓ DEBUG configured: True
✓ SUPABASE_URL configured
✓ SUPABASE_ANON_KEY configured
✓ SUPABASE_SERVICE_ROLE_KEY configured
✓ Supabase configuration appears complete

==================================================
Running Database Test
==================================================
Testing database connectivity...
✓ Supabase client is available
✓ Database write test successful
✓ Connection manager status: healthy

==================================================
Running Routing Service Test
==================================================
Testing routing service...
✓ Payment request processed successfully
  - Session ID: session_1234567890123
  - Predicted MCC: 5999
  - Confidence: 0.3
  - Recommended Card: default_card
✓ Analytics retrieval successful

==================================================
Running API Structure Test
==================================================
Testing API structure...
✓ FastAPI app created: Payvo Middleware
✓ API routes configured:
  - GET /
  - GET /ping
  - GET /version
  - ... and more

==================================================
TEST SUMMARY
==================================================
Import Test: ✓ PASSED
Configuration Test: ✓ PASSED
Database Test: ✓ PASSED
Routing Service Test: ✓ PASSED
API Structure Test: ✓ PASSED

Overall: 5/5 tests passed
🎉 All tests passed! Payvo Middleware is ready to use.
```

---

## 🚀 Start the Application

### Method 1: Using the Startup Script (Recommended)
```bash
python run.py
```

### Method 2: Direct Uvicorn
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Expected Startup Output:
```
2024-01-XX XX:XX:XX - __main__ - INFO - 🚀 Starting Payvo Middleware...
2024-01-XX XX:XX:XX - __main__ - INFO - 📡 Server Configuration:
2024-01-XX XX:XX:XX - __main__ - INFO -    Host: 0.0.0.0
2024-01-XX XX:XX:XX - __main__ - INFO -    Port: 8000
2024-01-XX XX:XX:XX - __main__ - INFO -    Debug: True
2024-01-XX XX:XX:XX - __main__ - INFO -    Supabase: ✅ Configured
2024-01-XX XX:XX:XX - __main__ - INFO - 🌐 Access your application at:
2024-01-XX XX:XX:XX - __main__ - INFO -    Main: http://0.0.0.0:8000
2024-01-XX XX:XX:XX - __main__ - INFO -    Docs: http://0.0.0.0:8000/docs
2024-01-XX XX:XX:XX - __main__ - INFO -    Health: http://0.0.0.0:8000/api/v1/health
INFO:     Started server process [XXXX]
INFO:     Waiting for application startup.
INFO:     Initializing Routing Orchestrator...
INFO:     Routing Orchestrator initialized successfully
INFO:     Starting background tasks...
INFO:     Background tasks started
INFO:     Payvo Middleware started successfully
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

---

## 🌐 Accessing Your Application

Once the server is running, you can access:

### 1. Main Application
- **URL**: http://localhost:8000
- **Description**: Root endpoint with system information

### 2. API Documentation (Development Only)
- **URL**: http://localhost:8000/docs
- **Description**: Interactive Swagger UI documentation

### 3. Health Check
- **URL**: http://localhost:8000/api/v1/health
- **Description**: System health and status

### 4. Quick Test
- **URL**: http://localhost:8000/ping
- **Description**: Simple ping endpoint

---

## 🧪 Testing the API

### 1. Health Check
```bash
curl http://localhost:8000/api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-XX...",
  "database": {
    "supabase_available": true,
    "overall_status": "healthy"
  }
}
```

### 2. Process a Payment Request
```bash
curl -X POST "http://localhost:8000/api/v1/routing/process" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "amount": 100.00,
    "terminal_id": "TEST_001",
    "location": {
      "latitude": 37.7749,
      "longitude": -122.4194
    }
  }'
```

Expected response:
```json
{
  "session_id": "session_1234567890123",
  "recommended_card": {
    "card_id": "default_card",
    "network": "visa",
    "reason": "Default card - no user cards configured",
    "estimated_rewards": 0
  },
  "predicted_mcc": "5999",
  "confidence": 0.3,
  "prediction_method": "fallback",
  "routing_reason": "Default card - no user cards configured",
  "estimated_rewards": 0,
  "timestamp": "2024-01-XX..."
}
```

---

## ❌ Troubleshooting

### Common Issues

#### 1. "ModuleNotFoundError"
```bash
# Solution: Install dependencies
pip install -r requirements.txt

# Or install specific missing packages:
pip install fastapi uvicorn supabase
```

#### 2. "Supabase client not available"
- Check your `SUPABASE_URL` and `SUPABASE_ANON_KEY` in `.env`
- Verify your Supabase project is active
- Make sure you've set up the database schema

#### 3. "Database write test failed"
- Verify your `SUPABASE_SERVICE_ROLE_KEY` is correct
- Check that the database schema was created successfully
- Ensure your project has the correct RLS policies

#### 4. "Port already in use"
```bash
# Find and kill the process using port 8000
lsof -ti:8000 | xargs kill -9

# Or use a different port
export PAYVO_PORT=8001
python run.py
```

#### 5. "Permission denied" on macOS/Linux
```bash
# Make the script executable
chmod +x run.py
python run.py
```

### Debug Mode

Enable detailed logging:
```bash
export PAYVO_DEBUG=true
export PAYVO_LOG_LEVEL=DEBUG
python run.py
```

### Check Configuration
```bash
python -c "
from app.core.config import settings
print('Supabase URL:', settings.SUPABASE_URL)
print('Supabase configured:', settings.use_supabase)
print('Debug mode:', settings.DEBUG)
print('Port:', settings.PORT)
"
```

---

## 🛡️ Production Deployment

### Before Going to Production:

1. **Security Checklist**:
   - [ ] Changed all default passwords
   - [ ] Generated production API keys
   - [ ] Set `PAYVO_DEBUG=false`
   - [ ] Configured HTTPS
   - [ ] Set proper `ALLOWED_HOSTS`
   - [ ] Reviewed `CORS_ORIGINS`

2. **Environment Variables**:
```env
PAYVO_DEBUG=false
PAYVO_LOG_LEVEL=WARNING
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

3. **Production Command**:
```bash
python run.py
```

---

## 📞 Getting Help

### If Tests Fail:
1. Check your Python version: `python --version`
2. Reinstall dependencies: `pip install -r requirements.txt --force-reinstall`
3. Verify Supabase configuration
4. Check the `SECURITY.md` file for security best practices

### If Server Won't Start:
1. Check port availability: `lsof -i :8000`
2. Verify `.env` file exists and has correct format
3. Check file permissions
4. Review startup logs for specific error messages

### For Database Issues:
1. Verify Supabase project is active
2. Check API keys are valid and not expired
3. Ensure database schema was created correctly
4. Test connection with simple query in Supabase dashboard

---

## 🎉 Success!

If everything is working, you should see:
- ✅ All tests passing
- ✅ Server starting without errors
- ✅ Health check returning "healthy"
- ✅ API documentation accessible
- ✅ Payment processing endpoint working

Your Payvo Middleware is now ready for card routing and MCC prediction! 