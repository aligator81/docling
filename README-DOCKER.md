# Docker Deployment Guide for Docling Application

This guide provides comprehensive instructions for deploying your Docling Document Q&A Assistant using Docker.

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- OpenAI API key

### Local Deployment

1. **Set up environment variables:**
   ```bash
   cp .env.example .env  # if you have an example file
   # Or create .env manually:
   echo "OPENAI_API_KEY=your_actual_openai_api_key_here" > .env
   ```

2. **Make the deployment script executable:**
   ```bash
   chmod +x deploy.sh
   ```

3. **Deploy the application:**
   ```bash
   ./deploy.sh
   ```

4. **Access the application:**
   Open your browser and go to `http://localhost:8501`

## Docker Commands

### Build and run manually:
```bash
# Build the image
docker build -t docling-app .

# Run the container
docker run -p 8501:8501 --env-file .env docling-app
```

### Using Docker Compose:
```bash
# Start the application
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the application
docker-compose down
```

## Cloud Platform Deployment

### Render.com
1. Connect your GitHub repository to Render
2. Set build command: `docker build -t docling-app .`
3. Set start command: `docker run -p 8501:8501 -e OPENAI_API_KEY=$OPENAI_API_KEY docling-app`
4. Add `OPENAI_API_KEY` environment variable in Render dashboard

### Railway
1. Connect your GitHub repository to Railway
2. Railway will automatically detect the Dockerfile
3. Add `OPENAI_API_KEY` environment variable in Railway dashboard

### Fly.io
```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Deploy
flyctl launch --now

# Set environment variable
flyctl secrets set OPENAI_API_KEY=your_actual_key_here
```

### Heroku
```bash
# Install Heroku CLI and login
heroku login

# Create app
heroku create your-app-name

# Add buildpacks
heroku buildpacks:add heroku/python

# Set environment variable
heroku config:set OPENAI_API_KEY=your_actual_key_here

# Deploy
git push heroku main
```

## Production Considerations

### 1. Environment Variables
Ensure these are set in production:
```bash
OPENAI_API_KEY=your_openai_api_key
# Optional: Add any other required environment variables
```

### 2. Data Persistence
The Docker setup uses bind mounts for:
- `./data` - Stores embeddings and processed data
- `./output` - Stores extracted document content

### 3. Resource Allocation
For production, ensure adequate resources:
```yaml
# In docker-compose.yml, add resource limits:
deploy:
  resources:
    limits:
      memory: 2G
      cpus: '2'
```

### 4. Reverse Proxy & SSL (Recommended)
Add Nginx for production:
```nginx
# nginx.conf
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://docling-app:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 5. Monitoring
Add health checks and monitoring:
```bash
# Check container health
docker ps --format "table {{.Names}}\t{{.Status}}"

# View resource usage
docker stats
```

## Troubleshooting

### Common Issues

1. **Port already in use:**
   ```bash
   # Change port in docker-compose.yml
   ports:
     - "8502:8501"
   ```

2. **Missing system libraries:**
   The Dockerfile includes all required system dependencies for Docling.

3. **OpenAI API errors:**
   Verify your `OPENAI_API_KEY` is correctly set in the `.env` file.

4. **Build failures:**
   ```bash
   # Clear Docker cache and rebuild
   docker-compose build --no-cache
   ```

5. **ModuleNotFoundError: No module named 'sklearn':**
   ```bash
   # Ensure scikit-learn is in requirements.txt
   # Rebuild the Docker image after adding it:
   docker-compose build --no-cache
   docker-compose up -d
   ```

### Logs and Debugging
```bash
# View application logs
docker-compose logs docling-app

# View detailed logs
docker-compose logs -f --tail=100

# Enter container for debugging
docker-compose exec docling-app bash
```

## Performance Optimization

### Multi-stage Build
The Dockerfile uses multi-stage builds to:
- Reduce final image size (~500MB vs ~1.2GB)
- Separate build dependencies from runtime
- Improve security by removing build tools

### Layer Caching
The Dockerfile is optimized for layer caching:
- Dependencies are installed before copying application code
- Frequent changes (application code) are in later layers

### Resource Management
```bash
# Monitor resource usage
docker stats

# Set memory limits if needed
docker run -m 2g -p 8501:8501 docling-app
```

## Security Best Practices

1. **Use .dockerignore** to exclude sensitive files
2. **Never commit .env files** to version control
3. **Use Docker secrets** for sensitive data in production
4. **Regularly update base images** for security patches
5. **Scan images for vulnerabilities:**
   ```bash
   docker scan docling-app
   ```

## Backup and Recovery

### Data Backup
```bash
# Backup data directory
tar -czf backup-$(date +%Y%m%d).tar.gz data/ output/

# Restore from backup
tar -xzf backup-20231201.tar.gz
```

### Database Backup (if using LanceDB)
The embeddings are stored in `data/embeddings.json` which is backed up through the volume mount.

## Scaling

### Horizontal Scaling
For high traffic, consider:
- Load balancing with multiple instances
- Redis for session management
- Database optimization

### Vertical Scaling
Increase resources in `docker-compose.yml`:
```yaml
deploy:
  resources:
    limits:
      memory: 4G
      cpus: '4'
```

## Support

For issues with:
- Docker setup: Check Docker logs and documentation
- Docling functionality: Refer to the main README.md
- OpenAI integration: Verify API key and quotas

## License

This deployment setup is provided as-is. Refer to the main project for licensing information.