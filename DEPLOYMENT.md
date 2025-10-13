# Deployment Guide

This guide covers different deployment options for Docling v2.

## Local Development

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL
- Git

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/docling_v2.git
   cd docling_v2
   ```

2. **Install dependencies**
   ```bash
   npm run install-all
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Start development servers**
   ```bash
   npm run dev
   ```

## Docker Deployment

### Using Docker Compose

1. **Create docker-compose.yml**
   ```yaml
   version: '3.8'
   
   services:
     postgres:
       image: postgres:15
       environment:
         POSTGRES_DB: docling
         POSTGRES_USER: docling_user
         POSTGRES_PASSWORD: docling_password
       volumes:
         - postgres_data:/var/lib/postgresql/data
       ports:
         - "5432:5432"
   
     backend:
       build: ./backend
       ports:
         - "8000:8000"
       environment:
         - DATABASE_URL=postgresql://docling_user:docling_password@postgres:5432/docling
         - SECRET_KEY=your-secret-key
         - OPENAI_API_KEY=your-openai-key
       depends_on:
         - postgres
   
     frontend:
       build: ./frontend
       ports:
         - "3000:3000"
       environment:
         - NEXT_PUBLIC_API_URL=http://localhost:8000
       depends_on:
         - backend
   
   volumes:
     postgres_data:
   ```

2. **Build and start**
   ```bash
   docker-compose up -d
   ```

### Individual Docker Containers

#### Backend Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Frontend Dockerfile
```dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]
```

## Production Deployment

### Environment Setup

1. **Set up PostgreSQL**
   ```bash
   # Install PostgreSQL
   sudo apt update
   sudo apt install postgresql postgresql-contrib
   
   # Create database and user
   sudo -u postgres psql
   CREATE DATABASE docling;
   CREATE USER docling_user WITH PASSWORD 'secure_password';
   GRANT ALL PRIVILEGES ON DATABASE docling TO docling_user;
   ```

2. **Configure environment variables**
   ```bash
   # Production .env
   DEBUG=false
   SECRET_KEY=your-production-secret-key
   DATABASE_URL=postgresql://docling_user:password@localhost:5432/docling
   ```

### Backend Deployment

1. **Install system dependencies**
   ```bash
   sudo apt update
   sudo apt install python3.11 python3.11-venv nginx
   ```

2. **Set up virtual environment**
   ```bash
   cd backend
   python3.11 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

4. **Configure systemd service**
   ```bash
   sudo nano /etc/systemd/system/docling-backend.service
   ```
   
   ```ini
   [Unit]
   Description=Docling Backend
   After=network.target
   
   [Service]
   Type=simple
   User=www-data
   WorkingDirectory=/path/to/docling_v2/backend
   Environment=PATH=/path/to/docling_v2/backend/.venv/bin
   ExecStart=/path/to/docling_v2/backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
   Restart=always
   
   [Install]
   WantedBy=multi-user.target
   ```

5. **Start the service**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable docling-backend
   sudo systemctl start docling-backend
   ```

### Frontend Deployment

1. **Build the application**
   ```bash
   cd frontend
   npm install
   npm run build
   ```

2. **Configure nginx**
   ```bash
   sudo nano /etc/nginx/sites-available/docling
   ```
   
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
   
       location / {
           proxy_pass http://localhost:3000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection 'upgrade';
           proxy_set_header Host $host;
           proxy_cache_bypass $http_upgrade;
       }
   
       location /api {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

3. **Enable the site**
   ```bash
   sudo ln -s /etc/nginx/sites-available/docling /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl reload nginx
   ```

## Cloud Deployment

### Vercel (Frontend)

1. **Install Vercel CLI**
   ```bash
   npm i -g vercel
   ```

2. **Deploy**
   ```bash
   cd frontend
   vercel
   ```

### Railway (Backend)

1. **Connect GitHub repository**
2. **Set environment variables**
3. **Deploy automatically**

### Render

1. **Create new web service**
2. **Connect repository**
3. **Configure build settings**
4. **Set environment variables**

## SSL/HTTPS Setup

### Using Let's Encrypt

1. **Install Certbot**
   ```bash
   sudo apt install certbot python3-certbot-nginx
   ```

2. **Get certificate**
   ```bash
   sudo certbot --nginx -d your-domain.com
   ```

3. **Auto-renewal**
   ```bash
   sudo crontab -e
   # Add: 0 12 * * * /usr/bin/certbot renew --quiet
   ```

## Monitoring and Logging

### Backend Logs
```bash
sudo journalctl -u docling-backend -f
```

### Nginx Logs
```bash
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Database Monitoring
```bash
# Check database connections
psql -U docling_user -d docling -c "SELECT count(*) FROM pg_stat_activity;"
```

## Backup and Recovery

### Database Backup
```bash
# Daily backup
pg_dump -U docling_user docling > backup_$(date +%Y%m%d).sql

# Restore
psql -U docling_user docling < backup_file.sql
```

### File Uploads Backup
```bash
# Backup uploads directory
tar -czf uploads_backup_$(date +%Y%m%d).tar.gz backend/data/uploads/
```

## Troubleshooting

### Common Issues

1. **Database connection errors**
   - Check PostgreSQL is running
   - Verify connection string in .env
   - Check firewall settings

2. **API not responding**
   - Check backend service status
   - Verify port 8000 is accessible
   - Check logs for errors

3. **Frontend build failures**
   - Clear node_modules and reinstall
   - Check Node.js version compatibility
   - Verify environment variables

### Performance Optimization

1. **Database optimization**
   ```sql
   -- Create indexes for common queries
   CREATE INDEX idx_documents_user_id ON documents(user_id);
   CREATE INDEX idx_chunks_document_id ON chunks(document_id);
   ```

2. **Caching setup**
   - Consider adding Redis for session storage
   - Implement response caching for static content

## Security Checklist

- [ ] Change default passwords
- [ ] Enable HTTPS
- [ ] Configure firewall
- [ ] Regular security updates
- [ ] Database backup strategy
- [ ] Monitor logs for suspicious activity
- [ ] Use environment variables for secrets
- [ ] Implement rate limiting
- [ ] Regular security audits