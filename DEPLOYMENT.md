# 🚀 Payvo Middleware Deployment Guide

## Current Status
✅ **Local Network Access**: `http://10.0.0.207:8000`  
✅ **Enhanced GPS-First MCC Prediction Active**  
✅ **Indoor Mapping Capabilities Enabled**  

---

## 🌐 Deployment Options

### Option 1: Local Network (Current Setup)
**Best for**: Testing on same WiFi network

```bash
# Your middleware is already running at:
http://10.0.0.207:8000

# Test endpoints:
curl http://10.0.0.207:8000/api/v1/health
curl -X POST http://10.0.0.207:8000/api/v1/routing/initiate -H "Content-Type: application/json" -d '{"user_id": "test_user"}'
```

### Option 2: Railway (Recommended Cloud - Free Tier)
**Best for**: Production deployment with database

1. **Sign up**: [railway.app](https://railway.app)
2. **Deploy**:
   ```bash
   # Install Railway CLI
   npm install -g @railway/cli
   
   # Login and deploy
   railway login
   railway deploy
   ```
3. **Set Environment Variables**:
   - `SUPABASE_URL`: Your Supabase URL
   - `SUPABASE_KEY`: Your Supabase anon key
   - `DATABASE_URL`: Auto-configured by Railway

### Option 3: Render (Free Tier Available)
**Best for**: Simple deployment

1. **Connect GitHub**: Link your repository to [render.com](https://render.com)
2. **Auto-Deploy**: Render will detect the Dockerfile and deploy automatically
3. **Free Tier**: 750 hours/month free

### Option 4: Vercel (Serverless)
**Best for**: Serverless deployment

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
vercel --prod
```

### Option 5: Docker (Local/Server)
**Best for**: Self-hosting on VPS/server

```bash
# Build and run with Docker Compose
docker-compose up -d

# Or build and run manually
docker build -t payvo-middleware .
docker run -p 8000:8000 payvo-middleware
```

### Option 6: Heroku
**Best for**: Traditional PaaS deployment

```bash
# Install Heroku CLI and login
heroku create your-payvo-middleware
git push heroku main
```

---

## 🔧 Quick Setup Commands

### For Local Development:
```bash
cd middleware
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### For Production (Current Directory):
```bash
# Using Docker Compose (Recommended)
docker-compose up -d

# Or using Python directly
cd middleware && python app/main.py
```

---

## 🌍 Environment Variables

Create a `.env` file in the middleware directory:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/payvo_db
REDIS_URL=redis://localhost:6379

# Supabase
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=false
LOG_LEVEL=info

# Security
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

---

## 📱 Testing After Deployment

Once deployed, test these endpoints:

```bash
# Health check
curl https://your-domain.com/api/v1/health

# Create session
curl -X POST https://your-domain.com/api/v1/routing/initiate \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user"}'

# Activate payment (get session_id from above)
curl -X POST https://your-domain.com/api/v1/routing/{session_id}/activate \
  -H "Content-Type: application/json" \
  -d '{}'
```

---

## 🔒 Security Considerations

For production deployment:

1. **Use HTTPS**: Always deploy with SSL/TLS
2. **Environment Variables**: Never commit secrets to git
3. **Database Security**: Use strong passwords and connection encryption
4. **API Rate Limiting**: Implement rate limiting for production
5. **CORS**: Configure CORS for your frontend domains

---

## 📊 Monitoring & Logs

### Health Check Endpoint:
- **URL**: `/api/v1/health`
- **Response**: System status, cache stats, component health

### Performance Metrics:
- **URL**: `/api/v1/metrics`
- **Response**: Prediction accuracy, response times, success rates

---

## 🆘 Troubleshooting

### Common Issues:

1. **Port already in use**:
   ```bash
   lsof -i :8000
   kill -9 <PID>
   ```

2. **Database connection failed**:
   - Check DATABASE_URL environment variable
   - Ensure database is running and accessible

3. **Module not found errors**:
   ```bash
   pip install -r requirements.txt
   ```

4. **CORS errors**:
   - Add your frontend domain to CORS settings in main.py

---

## 🚀 Quick Deploy (Railway - Recommended)

1. Fork/clone this repo
2. Sign up at [railway.app](https://railway.app)
3. Connect GitHub repo
4. Deploy automatically
5. Set environment variables in Railway dashboard
6. Your API will be live at: `https://your-app.railway.app`

**Total setup time**: ~5 minutes
**Cost**: Free tier available (up to $5/month usage)

---

## 💡 Need Help?

- **Local Network Issues**: Check firewall settings
- **Cloud Deployment**: Verify environment variables
- **Performance**: Monitor logs and health endpoints
- **Scaling**: Consider Redis for session storage in production

Your Enhanced GPS-First MCC Prediction System is ready for the world! 🌍 