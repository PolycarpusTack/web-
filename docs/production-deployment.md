# Production Deployment Guide

This guide covers deploying Web+ to production with PostgreSQL, Redis, and proper security configurations.

## Prerequisites

- Ubuntu 20.04+ or similar Linux distribution
- Docker and Docker Compose (optional but recommended)
- Python 3.9+
- Node.js 18+
- PostgreSQL 14+
- Redis 6+ (optional but recommended)
- Nginx or similar reverse proxy

## Database Setup

### Option 1: Using Docker Compose (Recommended)

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/web-plus.git
   cd web-plus
   ```

2. Create production environment file:
   ```bash
   cp apps/backend/.env.production.example apps/backend/.env
   # Edit .env with your production values
   ```

3. Start services:
   ```bash
   docker-compose up -d
   ```

This will start:
- PostgreSQL on port 5432
- Redis on port 6379
- Backend on port 8000
- Frontend on port 3000

### Option 2: Manual PostgreSQL Setup

1. Install PostgreSQL:
   ```bash
   sudo apt update
   sudo apt install postgresql postgresql-contrib
   ```

2. Create database and user:
   ```bash
   sudo -u postgres psql
   ```
   ```sql
   CREATE USER webplus_user WITH PASSWORD 'your_secure_password';
   CREATE DATABASE webplus OWNER webplus_user;
   GRANT ALL PRIVILEGES ON DATABASE webplus TO webplus_user;
   \q
   ```

3. Update PostgreSQL configuration for remote connections (if needed):
   ```bash
   sudo nano /etc/postgresql/14/main/postgresql.conf
   # Set: listen_addresses = '*'
   
   sudo nano /etc/postgresql/14/main/pg_hba.conf
   # Add: host all all 0.0.0.0/0 md5
   
   sudo systemctl restart postgresql
   ```

## Backend Deployment

### 1. Set Up Python Environment

```bash
cd apps/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment

Create `.env` file:
```bash
# Database
WEBPLUS_POSTGRES_SERVER=localhost
WEBPLUS_POSTGRES_USER=webplus_user
WEBPLUS_POSTGRES_PASSWORD=your_secure_password
WEBPLUS_POSTGRES_DB=webplus

# Security
WEBPLUS_SECRET_KEY=generate-a-secure-secret-key-minimum-32-chars
WEBPLUS_DEBUG=false

# Redis (if using)
WEBPLUS_REDIS_URL=redis://localhost:6379/0

# CORS
WEBPLUS_CORS_ORIGINS=["https://your-domain.com"]
```

### 3. Initialize Database

```bash
python scripts/init_production_db.py --seed
```

### 4. Run with Gunicorn

Install Gunicorn:
```bash
pip install gunicorn
```

Create systemd service:
```bash
sudo nano /etc/systemd/system/webplus.service
```

```ini
[Unit]
Description=Web+ Backend
After=network.target

[Service]
Type=notify
User=webplus
Group=webplus
WorkingDirectory=/path/to/web-plus/apps/backend
Environment="PATH=/path/to/web-plus/apps/backend/.venv/bin"
ExecStart=/path/to/web-plus/apps/backend/.venv/bin/gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start service:
```bash
sudo systemctl enable webplus
sudo systemctl start webplus
sudo systemctl status webplus
```

## Frontend Deployment

### 1. Build Frontend

```bash
cd apps/frontend
npm install
npm run build
```

### 2. Serve with Nginx

Install Nginx:
```bash
sudo apt install nginx
```

Configure Nginx:
```bash
sudo nano /etc/nginx/sites-available/webplus
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        root /path/to/web-plus/apps/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/webplus /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## SSL/TLS Setup

Use Certbot for Let's Encrypt SSL:

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## Security Hardening

### 1. Firewall Configuration

```bash
sudo ufw allow 22/tcp  # SSH
sudo ufw allow 80/tcp  # HTTP
sudo ufw allow 443/tcp # HTTPS
sudo ufw enable
```

### 2. Database Security

- Use strong passwords
- Limit database connections to localhost or specific IPs
- Regular backups
- Enable SSL for database connections

### 3. Application Security

- Set secure SECRET_KEY
- Disable DEBUG in production
- Use HTTPS only
- Implement rate limiting
- Regular security updates

## Monitoring

### 1. Application Logs

```bash
# View backend logs
sudo journalctl -u webplus -f

# View Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 2. Database Monitoring

```sql
-- Check active connections
SELECT COUNT(*) FROM pg_stat_activity;

-- Check database size
SELECT pg_database_size('webplus');
```

### 3. System Monitoring

Consider using:
- Prometheus + Grafana
- New Relic
- DataDog
- CloudWatch (AWS)

## Backup Strategy

### 1. Database Backups

Create backup script:
```bash
#!/bin/bash
BACKUP_DIR="/backups/postgres"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_NAME="webplus"
DB_USER="webplus_user"

mkdir -p $BACKUP_DIR
pg_dump -U $DB_USER -d $DB_NAME > $BACKUP_DIR/backup_$TIMESTAMP.sql

# Keep only last 7 days
find $BACKUP_DIR -name "backup_*.sql" -mtime +7 -delete
```

Add to crontab:
```bash
0 2 * * * /path/to/backup.sh
```

### 2. File Backups

Backup uploaded files:
```bash
rsync -av /path/to/uploads/ /backups/uploads/
```

## Scaling Considerations

### Horizontal Scaling

1. **Load Balancer**: Use HAProxy or Nginx for load balancing
2. **Multiple Backend Instances**: Run multiple Gunicorn workers
3. **Database Replication**: Set up PostgreSQL replication
4. **Redis Cluster**: For distributed caching

### Vertical Scaling

1. Increase server resources (CPU, RAM)
2. Optimize database queries
3. Use connection pooling
4. Enable query caching

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Check PostgreSQL is running
   - Verify credentials in .env
   - Check firewall rules

2. **502 Bad Gateway**
   - Check backend service is running
   - Verify Nginx proxy configuration
   - Check application logs

3. **Slow Performance**
   - Enable Redis caching
   - Optimize database indexes
   - Check for N+1 queries
   - Monitor resource usage

### Health Checks

Backend health endpoint:
```bash
curl http://localhost:8000/health
```

Database connection test:
```bash
cd apps/backend
python -c "from db.database import engine; print('DB OK')"
```

## Maintenance

### Regular Tasks

1. **Daily**
   - Monitor logs for errors
   - Check disk space
   - Verify backups

2. **Weekly**
   - Review performance metrics
   - Check for security updates
   - Test backup restoration

3. **Monthly**
   - Update dependencies
   - Review access logs
   - Performance optimization

### Update Procedure

1. Backup database
2. Pull latest code
3. Install dependencies
4. Run migrations
5. Restart services
6. Verify functionality

```bash
# Example update script
cd /path/to/web-plus
git pull
cd apps/backend
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
sudo systemctl restart webplus
cd ../frontend
npm install
npm run build
sudo systemctl restart nginx
```

## Support

For production support:
1. Check application logs
2. Review this documentation
3. Search issue tracker
4. Contact support team