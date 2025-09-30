# Systemd Service Setup for Docling Streamlit Application

This guide explains how to set up your Docling Streamlit application as a systemd service for production deployment.

## Files Created

1. **`docling-streamlit.service`** - The systemd service configuration file
2. **`deploy-systemd.sh`** - Automated deployment script
3. **`SYSTEMD_DEPLOYMENT_README.md`** - This documentation

## Quick Start

### Option 1: Automated Setup (Recommended)

1. **Copy files to your Linux server:**
   ```bash
   # Upload these files to your server:
   # - All your application files (5-chat.py, requirements.txt, etc.)
   # - docling-streamlit.service
   # - deploy-systemd.sh
   ```

2. **Run the deployment script:**
   ```bash
   sudo ./deploy-systemd.sh
   ```

3. **Configure environment variables:**
   ```bash
   # Edit the created .env file with your actual credentials
   sudo nano /opt/docling-app/.env
   ```

4. **Start the service:**
   ```bash
   sudo systemctl start docling-streamlit
   sudo systemctl enable docling-streamlit
   ```

### Option 2: Manual Setup

1. **Copy the service file:**
   ```bash
   sudo cp docling-streamlit.service /etc/systemd/system/
   ```

2. **Reload systemd:**
   ```bash
   sudo systemctl daemon-reload
   ```

3. **Enable and start the service:**
   ```bash
   sudo systemctl enable docling-streamlit
   sudo systemctl start docling-streamlit
   ```

## Service Configuration Details

The systemd service is configured with:

- **User/Group:** `docling/docling` (created automatically by the script)
- **Working Directory:** `/opt/docling-app`
- **Python Environment:** Virtual environment at `/opt/docling-app/venv`
- **Port:** 8501 (accessible from all interfaces)
- **Auto-restart:** Service automatically restarts on failure
- **Security:** Hardened with security restrictions
- **Logging:** All output goes to systemd journal

## Environment Variables Required

Create `/opt/docling-app/.env` with your actual values:

```bash
# Required: Neon Database Connection String
NEON_CONNECTION_STRING=postgresql://username:password@host/database

# Required: At least one LLM provider API key
OPENAI_API_KEY=your-openai-api-key-here
# OR
MISTRAL_API_KEY=your-mistral-api-key-here
```

## Useful Commands

```bash
# Service management
sudo systemctl start docling-streamlit      # Start service
sudo systemctl stop docling-streamlit       # Stop service
sudo systemctl restart docling-streamlit    # Restart service
sudo systemctl status docling-streamlit     # Check status
sudo systemctl enable docling-streamlit     # Enable on boot
sudo systemctl disable docling-streamlit    # Disable on boot

# View logs
sudo journalctl -u docling-streamlit -f     # Follow logs
sudo journalctl -u docling-streamlit --since today  # Today's logs

# Check service health
curl http://localhost:8501/healthz  # If health endpoint exists
curl http://localhost:8501           # Check if app is responding
```

## Troubleshooting

### Service won't start
```bash
# Check detailed status
sudo systemctl status docling-streamlit --no-pager -l

# View recent logs
sudo journalctl -u docling-streamlit --since "1 hour ago"

# Check if port is in use
sudo netstat -tlnp | grep :8501
```

### Application errors
```bash
# Check application logs for errors
sudo journalctl -u docling-streamlit -f

# Test if Python environment works
sudo -u docling /opt/docling-app/venv/bin/python -c "import streamlit; print('OK')"

# Check if all dependencies are installed
sudo -u docling /opt/docling-app/venv/bin/pip list
```

### Permission issues
```bash
# Fix ownership if needed
sudo chown -R docling:docling /opt/docling-app

# Fix permissions
sudo chmod +x /opt/docling-app/*.py
sudo chmod +x /opt/docling-app/venv/bin/*
```

## Security Considerations

The service is configured with security best practices:

- **Non-privileged user:** Runs as `docling` user, not root
- **Restricted permissions:** Limited file system access
- **Resource limits:** Memory and file descriptor limits
- **Private temporary files:** Temporary files are private to the service

## Production Deployment Checklist

- [ ] Upload application files to server
- [ ] Run deployment script or set up manually
- [ ] Configure environment variables in `.env` file
- [ ] Test service startup: `sudo systemctl start docling-streamlit`
- [ ] Verify application is accessible: `curl http://localhost:8501`
- [ ] Check logs for errors: `sudo journalctl -u docling-streamlit -f`
- [ ] Enable service on boot: `sudo systemctl enable docling-streamlit`
- [ ] Set up firewall rules if needed
- [ ] Configure reverse proxy (nginx/apache) if needed
- [ ] Set up SSL/TLS certificate if needed
- [ ] Monitor service with systemd timers or external monitoring

## Application Access

Once deployed, your application will be available at:
- **Local:** http://localhost:8501
- **Network:** http://your-server-ip:8501
- **Domain:** https://yourdomain.com (if configured with reverse proxy)

## Updates and Maintenance

To update the application:

1. **Stop the service:**
   ```bash
   sudo systemctl stop docling-streamlit
   ```

2. **Update application files:**
   ```bash
   # Upload new files to /opt/docling-app/
   sudo cp new-files/* /opt/docling-app/
   sudo chown -R docling:docling /opt/docling-app
   ```

3. **Update dependencies if needed:**
   ```bash
   cd /opt/docling-app
   sudo -u docling ./venv/bin/pip install -r requirements.txt --upgrade
   ```

4. **Restart the service:**
   ```bash
   sudo systemctl start docling-streamlit
   ```

## Monitoring and Logs

- **Service status:** `sudo systemctl status docling-streamlit`
- **Application logs:** `sudo journalctl -u docling-streamlit -f`
- **System resource usage:** `sudo systemctl status docling-streamlit`
- **Error monitoring:** Check logs regularly for application errors

## Support

If you encounter issues:

1. Check the logs: `sudo journalctl -u docling-streamlit --since today`
2. Verify environment variables are set correctly
3. Ensure all dependencies are installed
4. Check file permissions and ownership
5. Verify database connectivity

The service is designed to be robust and will automatically restart if it crashes, making it suitable for production use.