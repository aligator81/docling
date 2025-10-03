# Coolify Deployment Troubleshooting Guide

## Issue: Chat Not Working in Coolify Deployment

### Root Cause Analysis
The chat functionality works locally but fails in Coolify deployment due to:

1. **Environment Variables Not Loaded**: `.env` file is not loaded in Coolify containers
2. **Missing Environment Configuration**: Coolify requires explicit environment variable configuration
3. **Database Connection Issues**: Neon database connection string not properly configured

### Solution Steps

## Step 1: Configure Environment Variables in Coolify

In your Coolify dashboard, navigate to your application's **Environment Variables** section and add:

```
OPENAI_API_KEY=your_openai_api_key_here
MISTRAL_API_KEY=your_mistral_api_key_here
EMBEDDING_PROVIDER=openai
NEON_CONNECTION_STRING=your_neon_connection_string_here
```

## Step 2: Verify Database Connection

Test your Neon database connection:

```bash
# Test connection from Coolify container
psql "postgresql://neondb_owner:npg_N7vynH6dQCer@ep-gentle-moon-aeeiaefq-pooler.c-2.us-east-2.aws.neon.tech/neondb?channel_binding=require&sslmode=require"
```

## Step 3: Check Application Logs

In Coolify dashboard, check the application logs for:
- Environment variable loading errors
- Database connection errors
- API key validation errors

## Step 4: Update Application for Production

### Fix 1: Enhanced Environment Variable Loading

Update your main application to handle missing environment variables gracefully:

```python
import os
from dotenv import load_dotenv

# Load .env file for local development
load_dotenv()

# Check for required environment variables
required_vars = ['NEON_CONNECTION_STRING', 'OPENAI_API_KEY']
missing_vars = [var for var in required_vars if not os.getenv(var)]

if missing_vars:
    print(f"❌ Missing required environment variables: {missing_vars}")
    print("Please configure these in your Coolify environment variables")
```

### Fix 2: Add Health Check Endpoint

Add a health check endpoint to verify all services are working:

```python
@app.route('/health')
def health_check():
    status = {
        'database': check_database_connection(),
        'openai': check_openai_connection(),
        'mistral': check_mistral_connection()
    }
    return jsonify(status)
```

## Step 5: Deployment Verification Checklist

- [ ] Environment variables configured in Coolify
- [ ] Database connection working
- [ ] API keys validated
- [ ] Application logs show no errors
- [ ] Health check endpoint returns success

## Common Coolify Issues

### Issue 1: Environment Variables Not Loading
**Solution**: Ensure variables are set in Coolify dashboard, not just in `.env` file

### Issue 2: Database Connection Timeout
**Solution**: Check if Neon database allows connections from Coolify's IP range

### Issue 3: API Rate Limits
**Solution**: Monitor API usage and consider upgrading plans if needed

### Issue 4: Container Resource Limits
**Solution**: Increase memory/CPU allocation in Coolify if needed

## Debug Commands

```bash
# Check environment variables in container
docker exec -it <container_id> env

# Check application logs
docker logs <container_id>

# Test database connection
docker exec -it <container_id> python -c "import psycopg2; conn = psycopg2.connect('your_connection_string'); print('✅ Database connected')"
```

## Quick Fix Tools

### Diagnostic Tool
Run this in your Coolify container to identify issues:

```bash
python diagnose_deployment.py
```

### Quick Fix Tool
Run this in your Coolify container to automatically fix common issues:

```bash
python quick_deployment_fix.py
```

## How to Run Tools in Coolify Container

1. **Access Coolify Dashboard**
2. **Navigate to your application**
3. **Open Terminal/Console** for the container
4. **Run the diagnostic tool**:
   ```bash
   python diagnose_deployment.py
   ```
5. **Run the fix tool** if issues are found:
   ```bash
   python quick_deployment_fix.py
   ```
6. **Restart the application** after fixes

## Common Error Messages and Solutions

### "Environment variables not set"
**Solution**: Configure all required environment variables in Coolify dashboard

### "Database connection failed"
**Solution**:
- Verify NEON_CONNECTION_STRING is correct
- Check if database allows connections from Coolify's IP
- Ensure pgvector extension is installed

### "API key validation failed"
**Solution**:
- Verify API keys are valid and not expired
- Check API rate limits and quotas
- Ensure correct API endpoints are accessible

## Support

If issues persist:
1. Run `diagnose_deployment.py` to identify specific issues
2. Run `quick_deployment_fix.py` to apply automatic fixes
3. Check Coolify documentation
4. Verify Neon database status
5. Contact Coolify support
6. Review application logs for specific error messages