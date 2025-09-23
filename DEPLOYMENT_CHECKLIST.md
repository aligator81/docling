# 🚀 Coolify Deployment Checklist

## ✅ Files Created for Deployment

### Configuration Files
- [x] `Dockerfile` - Container configuration
- [x] `coolify.yml` - Coolify deployment settings
- [x] `.dockerignore` - Files to exclude from Docker build
- [x] `README.md` - Updated with deployment instructions
- [x] `deploy.sh` - Linux/Mac deployment script
- [x] `deploy.bat` - Windows deployment script

### Directory Structure
- [x] `data/uploads/.gitkeep` - Upload directory placeholder
- [x] `output/.gitkeep` - Output directory placeholder
- [x] `cache/.gitkeep` - Cache directory placeholder

## 🔧 Deployment Steps

### Step 1: Prepare Your Repository
```bash
# Add all files to git
git add .
git commit -m "Add Coolify deployment configuration"
git push origin main
```

### Step 2: Set Up Coolify Server
1. **Provision a VPS/Server** (Ubuntu 22.04 recommended)
   - Minimum: 2GB RAM, 2 vCPUs, 20GB SSD
   - Providers: DigitalOcean, Vultr, AWS, etc.

2. **Install Coolify**
   ```bash
   curl -fsSL https://get.coolify.io | bash
   ```

3. **Access Coolify Dashboard**
   - Open: `http://your-server-ip:3000`
   - Complete initial setup wizard

### Step 3: Configure Deployment in Coolify

1. **Add Project**
   - Click "Add Project"
   - Select your Git provider (GitHub, GitLab, Bitbucket)
   - Connect your repository

2. **Application Settings**
   - **Build Method**: Dockerfile
   - **Build Path**: `/` (root directory)
   - **Port**: 8501
   - **Branch**: main

3. **Environment Variables** (Required)
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   MISTRAL_API_KEY=your_mistral_api_key_here
   NEON_CONNECTION_STRING=your_neon_connection_string
   EMBEDDING_PROVIDER=openai  # Optional, default: openai
   ```

4. **Resources** (Recommended)
   - Memory: 1GB
   - CPU: 0.5 cores
   - Storage: Use volume for `/app/data`

### Step 4: Deploy
- Click "Deploy" in Coolify dashboard
- Monitor build logs in real-time
- Wait for deployment to complete

## 🌐 Access Your Application

Your application will be available at:
```
http://your-coolify-server-ip:8501
```

## 🔍 Health Check

The application includes health checks at:
```
http://your-coolify-server-ip:8501/_stcore/health
```

## 🐛 Troubleshooting

### Common Issues

1. **Build Fails**
   - Check Dockerfile syntax
   - Verify all dependencies in requirements.txt
   - Review build logs in Coolify

2. **Application Crashes**
   - Check application logs in Coolify
   - Verify environment variables are set correctly
   - Ensure Neon database connection is working

3. **Memory Issues**
   - Increase memory allocation in Coolify (1GB minimum)
   - Check for memory leaks in subprocess calls

4. **Database Connection Issues**
   - Verify Neon connection string
   - Check if database tables exist
   - Test connection locally first

### Logs Location
- **Build Logs**: Coolify deployment logs
- **Application Logs**: Coolify application logs
- **Database Logs**: Neon dashboard

## 📊 Application Features

Your deployed application includes:
- ✅ Document upload (PDF, DOCX, images, etc.)
- ✅ Text extraction (Docling/Mistral OCR)
- ✅ Intelligent chunking
- ✅ Embedding generation (OpenAI/Mistral)
- ✅ Semantic search
- ✅ Q&A chat interface
- ✅ Database management interface

## 🔄 Updates

To update your application:
1. Make changes to your code
2. Commit and push to main branch
3. Coolify will automatically redeploy (if auto-deploy is enabled)
4. Or manually trigger deployment in Coolify dashboard

## 📞 Support

If you encounter issues:
1. Check Coolify documentation: https://coolify.io/docs
2. Review application logs in Coolify
3. Test locally first to isolate issues
4. Check Neon database connection

---
**🎉 Your Document Q&A Assistant is ready for deployment!**