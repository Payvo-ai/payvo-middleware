# Supabase Setup Guide for Payvo Middleware

This guide will help you configure Supabase as the database backend for the Payvo Middleware application.

## Prerequisites

1. **Supabase Account**: Create a free account at [supabase.com](https://supabase.com)
2. **Python 3.9+**: Make sure you have Python 3.9 or higher installed
3. **Payvo Middleware**: This guide assumes you have the Payvo Middleware code

## Step 1: Create a Supabase Project

1. Go to [supabase.com](https://supabase.com) and sign in
2. Click "New Project"
3. Choose your organization
4. Fill in project details:
   - **Name**: `payvo-middleware` (or your preferred name)
   - **Database Password**: Choose a strong password (save this!)
   - **Region**: Choose the closest region to your users
5. Click "Create new project"
6. Wait for the project to be created (this may take a few minutes)

## Step 2: Get Your Supabase Credentials

Once your project is ready:

1. Go to **Settings** → **API** in your Supabase dashboard
2. You'll need these values:
   - **Project URL**: `https://your-project.supabase.co`
   - **Project API Key**: The `anon` key (public)
   - **Service Role Key**: The `service_role` key (secret)

## Step 3: Configure Environment Variables

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file and add your Supabase credentials:
   ```env
   # Supabase Configuration
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_ANON_KEY=your-anon-key-here
   SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here
   ```

3. Also configure other required settings:
   ```env
   # API Configuration
   API_HOST=0.0.0.0
   API_PORT=8000
   DEBUG=true
   
   # Security
   SECRET_KEY=your-secret-key-here
   ```

## Step 4: Set Up the Database Schema

1. Go to your Supabase dashboard
2. Navigate to **SQL Editor**
3. Copy the contents of `app/database/schema.sql`
4. Paste it into the SQL Editor
5. Click "Run" to execute the schema

The schema will create the following tables:
- `transaction_feedback` - Stores transaction feedback for learning
- `mcc_predictions` - Stores MCC prediction results
- `card_performance` - Tracks card performance metrics
- `user_preferences` - Stores user preferences
- `terminal_cache` - Caches terminal-to-MCC mappings
- `location_cache` - Caches location-to-MCC mappings
- `wifi_cache` - Caches WiFi fingerprint mappings
- `ble_cache` - Caches BLE beacon mappings

## Step 5: Install Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

This will install:
- `supabase==2.0.2` - Supabase Python client
- `postgrest==0.13.2` - PostgREST client for Supabase
- All other existing dependencies

## Step 6: Test the Setup

Run the installation test script:

```bash
python test_installation.py
```

This will test:
- ✅ Import functionality
- ✅ Configuration loading
- ✅ Database connectivity
- ✅ Routing service functionality
- ✅ API structure

## Step 7: Start the Application

If all tests pass, start the Payvo Middleware:

```bash
python run.py
```

The application will start on `http://localhost:8000`

## Verifying Your Setup

### 1. Check API Health
Visit `http://localhost:8000/health` to see the system status.

### 2. Check Database Connection
The health endpoint will show:
```json
{
  "status": "healthy",
  "timestamp": "2024-...",
  "database": {
    "supabase_available": true,
    "postgres_available": false,
    "overall_status": "healthy"
  }
}
```

### 3. Test a Payment Request
Send a POST request to `http://localhost:8000/routing/process` with:
```json
{
  "user_id": "test_user",
  "amount": 100.00,
  "terminal_id": "TEST_001",
  "location": {
    "latitude": 37.7749,
    "longitude": -122.4194
  }
}
```

## Database Features

### Row Level Security (RLS)
The database schema includes RLS policies that:
- Allow the service role to access all data
- Protect user data when using anon key
- Enable secure multi-tenant access patterns

### Automatic Timestamps
Tables automatically update `updated_at` timestamps when records are modified.

### Performance Indexes
Optimized indexes for:
- User ID lookups
- Session ID tracking
- MCC predictions
- Location-based queries
- Time-based analytics

## Data Models

The application uses Pydantic models for data validation:
- `TransactionFeedback` - Transaction completion data
- `MCCPrediction` - MCC prediction results
- `CardPerformance` - Card usage statistics
- `UserPreferences` - User routing preferences
- Plus cache models for WiFi, BLE, terminals, and locations

## Troubleshooting

### Common Issues

1. **"Supabase client not available"**
   - Check your `SUPABASE_URL` and `SUPABASE_ANON_KEY`
   - Verify the project is active in Supabase dashboard

2. **"Database write test failed"**
   - Verify your `SUPABASE_SERVICE_ROLE_KEY` is correct
   - Check that the schema was created successfully
   - Ensure RLS policies are in place

3. **"Import failed"**
   - Run `pip install -r requirements.txt`
   - Check Python version with `python --version`

4. **Connection timeout errors**
   - Check your internet connection
   - Verify the Supabase project region
   - Try a different network if behind corporate firewall

### Debug Mode

Enable debug logging by setting:
```env
DEBUG=true
LOG_LEVEL=DEBUG
```

### Checking Logs

Monitor the application logs for detailed error information. Database operations are logged with full context.

## Scaling Considerations

### Production Deployment

1. **Use Environment Variables**: Never commit credentials to code
2. **Connection Pooling**: Supabase handles this automatically
3. **Rate Limiting**: Configure API rate limits as needed
4. **Monitoring**: Use Supabase dashboard for monitoring
5. **Backups**: Supabase provides automatic backups

### Performance Tips

1. **Indexes**: The schema includes optimized indexes
2. **Query Optimization**: Use appropriate LIMIT clauses
3. **Caching**: Implement Redis for frequently accessed data
4. **Analytics**: Use Supabase's built-in analytics

## Next Steps

1. **Configure Card Data**: Set up user preferences and card information
2. **External APIs**: Configure Google Maps, OpenAI, or other services
3. **Production Deploy**: Deploy to your preferred hosting platform
4. **Monitoring**: Set up application monitoring and alerting

## Support

- **Supabase Docs**: [docs.supabase.com](https://docs.supabase.com)
- **Payvo Issues**: Create issues in the project repository
- **Community**: Join the Supabase Discord for community support 