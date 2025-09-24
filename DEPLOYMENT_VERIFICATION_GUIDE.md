# 🔍 Coolify Deployment Verification Guide

## How to Check if Your App is Deployed Correctly

### Step 1: Check Coolify Dashboard Status

**In Coolify Dashboard:**
1. Go to your project → **Deployments** tab
2. Look for status indicators:
   - ✅ **Green checkmark** = Deployment successful
   - 🔄 **Spinning icon** = Still deploying
   - ❌ **Red X** = Deployment failed
   - ⚠️ **Yellow warning** = Issues detected

3. **Check deployment logs** for:
   - "Build successful" message
   - "Container started" confirmation
   - No error messages at the end

### Step 2: Verify Application Accessibility

**Test your application URL:**
```
http://your-coolify-server-ip:8501
```

**Expected behavior:**
- ✅ Page loads without errors
- ✅ Streamlit interface appears
- ✅ API configuration screen shows up
- ✅ No "Connection refused" errors

### Step 3: Health Check Endpoints

**Test health endpoints:**
```
# Streamlit health check
http://your-coolify-server-ip:8501/_stcore/health

# Custom health check (if implemented)
http://your-coolify-server-ip:8501/health
```

**Expected response:** HTTP 200 status code

### Step 4: Check Application Logs

**In Coolify Dashboard:**
1. Go to your project → **Logs** tab
2. Look for:
   - ✅ "Streamlit app started successfully"
   - ✅ No Python traceback errors
   - ✅ Database connection established
   - ✅ API clients initialized

### Step 5: Functional Testing

**Test each feature:**
1. **API Configuration**
   - Can you enter API keys?
   - Do they validate successfully?

2. **Document Upload**
   - Try uploading a test PDF/document
   - Check if it appears in uploaded documents

3. **Database Connection**
   - Check if database operations work
   - Verify no connection errors

### Step 6: Resource Monitoring

**Check resource usage in Coolify:**
- CPU usage (should be stable)
- Memory usage (should not be maxed out)
- Disk usage (should have free space)

## 🚨 Common Deployment Issues & Solutions

### Issue 1: Application Not Accessible
**Symptoms:** Connection refused, timeout
**Solutions:**
- Check if port 8501 is open on server
- Verify Coolify proxy configuration
- Check firewall settings

### Issue 2: Build Failed
**Symptoms:** Red X in deployment status
**Solutions:**
- Check build logs for specific errors
- Verify Dockerfile syntax
- Check requirements.txt compatibility

### Issue 3: Application Crashes
**Symptoms:** Page loads but shows errors
**Solutions:**
- Check application logs for Python errors
- Verify environment variables are set
- Test database connection

### Issue 4: Memory Issues
**Symptoms:** Container restarts frequently
**Solutions:**
- Increase memory allocation in Coolify
- Check for memory leaks in code
- Monitor resource usage

## ✅ Success Indicators

### Green Flags (Everything Working):
- ✅ Application loads at correct URL
- ✅ No errors in Coolify logs
- ✅ All features functional
- ✅ Stable resource usage
- ✅ Health checks pass

### Quick Test Script

Create a test script on your local machine:
```bash
#!/bin/bash
SERVER_IP="your-coolify-server-ip"

echo "Testing deployment..."
curl -s "http://$SERVER_IP:8501/_stcore/health"
if [ $? -eq 0 ]; then
    echo "✅ Health check PASSED"
else
    echo "❌ Health check FAILED"
fi

# Test main application
curl -s "http://$SERVER_IP:8501" | head -n 10
echo "Application response received"
```

## 📊 Monitoring Tools

### Coolify Built-in Monitoring:
- Real-time logs
- Resource usage graphs
- Deployment history
- Health status indicators

### External Monitoring (Optional):
- Uptime monitoring services
- Application performance monitoring
- Database connection monitoring

## 🎯 Final Verification Checklist

- [ ] Coolify deployment shows green checkmark
- [ ] Application URL loads successfully
- [ ] Health check endpoints respond
- [ ] No errors in application logs
- [ ] API configuration works
- [ ] Document upload functional
- [ ] Database operations successful
- [ ] Resource usage stable

## 🔧 Troubleshooting Commands

**On Coolify Server (if you have SSH access):**
```bash
# Check running containers
docker ps

# Check container logs
docker logs [container-name]

# Check resource usage
docker stats

# Test port accessibility
netstat -tulpn | grep 8501
```

Your application should be fully functional if all these checks pass! 🎉