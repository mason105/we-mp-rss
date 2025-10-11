# Deployment Guide

This document describes how to deploy the we-mp-rss application to a remote server using GitHub Actions.

## Overview

The deployment workflow automates the entire deployment process:
1. Logs into your Docker registry
2. Pulls the specified image version
3. Stops and removes old container (if exists)
4. Starts a new container with proper configuration
5. Performs health check
6. Cleans up unused images

## Prerequisites

### Server Requirements

1. **Linux server** with Docker installed (Ubuntu 20.04+ recommended)
2. **SSH access** configured with key-based authentication
3. **Sufficient resources**:
   - Minimum: 1 CPU, 1GB RAM, 10GB disk
   - Recommended: 2 CPU, 2GB RAM, 20GB disk

### Docker Installation on Server

If Docker is not installed on your server:

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

### SSH Key Setup

Generate an SSH key pair for GitHub Actions (if you don't have one):

```bash
# On your local machine
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/github_actions_deploy

# Copy the public key to your server
ssh-copy-id -i ~/.ssh/github_actions_deploy.pub user@your-server
```

## GitHub Secrets Configuration

Before running the deployment workflow, configure the following secrets in your GitHub repository:

**Settings → Secrets and variables → Actions → New repository secret**

### Required Secrets

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `VAR_REGISTRY_URL` | Docker registry URL | `registry.example.com` |
| `VAR_REGISTRY_USERNAME` | Registry username | `mason105` |
| `VAR_REGISTRY_PASSWORD` | Registry password/token | `your-password-or-token` |
| `SERVER_HOST` | Server IP or hostname | `192.168.1.100` or `deploy.example.com` |
| `SERVER_PORT` | SSH port (default: 22) | `22` |
| `SERVER_USER` | SSH username | `ubuntu` or `deploy` |
| `SERVER_SSH_KEY` | SSH private key content | Contents of `~/.ssh/github_actions_deploy` |

### Optional Secrets (Custom Configuration)

| Secret Name | Description | Default Value |
|-------------|-------------|---------------|
| `DEPLOY_CONFIG_PATH` | Server path for config file | `/opt/we-mp-rss/config` |
| `DEPLOY_DATA_PATH` | Server path for data directory | `/opt/we-mp-rss/data` |
| `DEPLOY_PORT` | Host port mapping | `8001` |

### How to Add SSH Private Key

1. Copy your private key content:
   ```bash
   cat ~/.ssh/github_actions_deploy
   ```

2. In GitHub:
   - Go to **Settings → Secrets → New repository secret**
   - Name: `SERVER_SSH_KEY`
   - Value: Paste the entire private key content (including `-----BEGIN` and `-----END` lines)

## Server Preparation

### 1. Create Deployment Directory Structure

SSH into your server and create the necessary directories:

```bash
# Connect to server
ssh user@your-server

# Create directory structure
sudo mkdir -p /opt/we-mp-rss/config
sudo mkdir -p /opt/we-mp-rss/data/{cache,pdf,markdown}

# Set ownership (replace 'deploy' with your SSH user)
sudo chown -R deploy:deploy /opt/we-mp-rss
```

### 2. Create Configuration File

Create the configuration file on the server:

```bash
# Create config.yaml
nano /opt/we-mp-rss/config/config.yaml
```

Example minimal configuration:

```yaml
app_name: we-mp-rss
server:
  name: we-mp-rss
  web_name: WeRSS微信公众号订阅助手
  enable_job: True
  auto_reload: False
  threads: 4

db: sqlite:///data/db.db

secret: YOUR_SECRET_KEY_HERE
user_agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36

port: 8001
debug: False

max_page: 5

rss:
  base_url: "https://your-domain.com/"
  local: False
  full_context: True
  add_cover: True
  page_size: 30

token_expire_minutes: 4320

cache:
  dir: ./data/cache

article:
  true_delete: False

gather:
  content: True
  model: app
  content_auto_check: False
  content_auto_interval: 59
  content_mode: web

safe:
  hide_config: "db,secret,token,notice.wechat,notice.feishu,notice.dingding"
  lic_key: "YOUR_LIC_KEY_HERE"

log:
  file: ""
  level: INFO

export:
  pdf:
    enable: False
    dir: ./data/pdf
  markdown:
    enable: False
    dir: ./data/markdown
```

**Important**: Update these values:
- `secret`: Change to a random secure string
- `rss.base_url`: Your domain or server IP with port
- `safe.lic_key`: Your license key

### 3. Configure Firewall (if applicable)

If using UFW or iptables, allow the application port:

```bash
# UFW
sudo ufw allow 8001/tcp

# Or iptables
sudo iptables -A INPUT -p tcp --dport 8001 -j ACCEPT
```

## How to Deploy

### Method 1: Manual Deployment (Recommended for First Deploy)

1. Go to your GitHub repository
2. Click **Actions** tab
3. Select **Deploy to Server** workflow
4. Click **Run workflow** button
5. Choose options:
   - **Image tag**: `latest` (or specific version like `a1b2c3d`)
   - **Force recreate**: Check if you want to force container recreation
6. Click **Run workflow**

### Method 2: Automated Deployment

You can trigger deployment automatically by adding to your build workflow:

```yaml
# In .github/workflows/test-docker-build.yaml
jobs:
  build-and-push:
    # ... existing build job ...

  deploy:
    name: Deploy to Production
    needs: build-and-push
    if: github.ref == 'refs/heads/main'  # Only deploy from main branch
    uses: ./.github/workflows/deploy.yaml
    secrets: inherit
    with:
      image_tag: latest
```

### Method 3: Deploy via GitHub CLI

```bash
# Deploy latest version
gh workflow run deploy.yaml

# Deploy specific version
gh workflow run deploy.yaml -f image_tag=a1b2c3d
```

## Monitoring Deployment

### Watch Workflow Progress

1. In GitHub Actions, click on the running workflow
2. Expand the deployment job steps to see real-time logs
3. Check the summary at the end for deployment status

### Verify on Server

SSH into your server and check:

```bash
# Check container status
docker ps | grep we-mp-rss

# View container logs
docker logs -f we-mp-rss

# Check if service is responding
curl http://localhost:8001/health
```

### Access Application

Open in browser: `http://your-server-ip:8001`

## Troubleshooting

### Deployment Failed: SSH Connection Error

**Symptoms**: "Connection refused" or "Permission denied"

**Solutions**:
1. Verify SSH key is correct in GitHub Secrets
2. Test SSH connection manually:
   ```bash
   ssh -i ~/.ssh/github_actions_deploy user@server
   ```
3. Check `SERVER_HOST`, `SERVER_PORT`, and `SERVER_USER` secrets
4. Ensure firewall allows SSH (port 22)

### Deployment Failed: Docker Login Error

**Symptoms**: "unauthorized" or "authentication required"

**Solutions**:
1. Verify `VAR_REGISTRY_URL`, `VAR_REGISTRY_USERNAME`, `VAR_REGISTRY_PASSWORD`
2. Test Docker login manually on server:
   ```bash
   docker login --username=<user> <registry>
   ```
3. Check if password/token has expired or been revoked

### Container Fails to Start

**Symptoms**: Container exits immediately after starting

**Solutions**:
1. Check container logs:
   ```bash
   docker logs we-mp-rss
   ```
2. Verify `config.yaml` exists and is valid:
   ```bash
   cat /opt/we-mp-rss/config/config.yaml
   ```
3. Check file permissions:
   ```bash
   ls -la /opt/we-mp-rss/
   ```
4. Verify all required directories exist

### Port Already in Use

**Symptoms**: "port is already allocated"

**Solutions**:
1. Check what's using the port:
   ```bash
   sudo lsof -i :8001
   ```
2. Stop the conflicting service or change `DEPLOY_PORT` secret
3. Remove old container if it's still running:
   ```bash
   docker rm -f we-mp-rss
   ```

### Health Check Timeout

**Symptoms**: Health check step shows timeout warning

**Solutions**:
1. This is often normal for first deployment (service needs time to initialize)
2. Check container is running: `docker ps | grep we-mp-rss`
3. Check logs for errors: `docker logs we-mp-rss`
4. Try accessing manually: `curl http://localhost:8001`

### Disk Space Issues

**Symptoms**: "no space left on device"

**Solutions**:
1. Check disk space: `df -h`
2. Clean up Docker resources:
   ```bash
   docker system prune -a --volumes
   ```
3. Remove old images manually:
   ```bash
   docker images
   docker rmi <image-id>
   ```

## Rollback Procedure

If a deployment causes issues, you can quickly rollback:

### Option 1: Redeploy Previous Version

1. Find the previous working commit SHA (short form)
2. Go to Actions → Deploy to Server → Run workflow
3. Set **image_tag** to the previous SHA (e.g., `b3e8f92`)
4. Run workflow

### Option 2: Manual Rollback on Server

```bash
# SSH to server
ssh user@your-server

# Find previous image
docker images | grep we-mp-rss

# Stop current container
docker stop we-mp-rss
docker rm we-mp-rss

# Run previous version
docker run -d \
  --name=we-mp-rss \
  --restart=always \
  -p 8001:8001 \
  -v /opt/we-mp-rss/config/config.yaml:/app/config.yaml \
  -v /opt/we-mp-rss/data:/app/data \
  -e TZ=Asia/Shanghai \
  registry.example.com/mason105/we-mp-rss:<previous-tag>
```

## Maintenance

### Viewing Logs

```bash
# Real-time logs
docker logs -f we-mp-rss

# Last 100 lines
docker logs --tail 100 we-mp-rss

# Logs with timestamps
docker logs -f --timestamps we-mp-rss
```

### Restarting Container

```bash
docker restart we-mp-rss
```

### Updating Configuration

1. Edit config file on server:
   ```bash
   nano /opt/we-mp-rss/config/config.yaml
   ```
2. Restart container:
   ```bash
   docker restart we-mp-rss
   ```

### Backup Data

```bash
# Backup database and data
cd /opt/we-mp-rss
tar -czf backup-$(date +%Y%m%d-%H%M%S).tar.gz data/

# Copy to safe location
scp backup-*.tar.gz user@backup-server:/backups/
```

### Database Migration

If switching from SQLite to MySQL/PostgreSQL:

1. Update `config.yaml` with new database connection
2. Export data from SQLite
3. Import into new database
4. Deploy with updated config
5. Restart container

## Security Best Practices

1. **Use Strong Secrets**
   - Generate random secret keys
   - Rotate credentials periodically
   - Never commit secrets to repository

2. **SSH Security**
   - Use key-based authentication only
   - Consider using a dedicated deployment user
   - Restrict SSH key permissions: `chmod 600 ~/.ssh/github_actions_deploy`

3. **Network Security**
   - Use HTTPS/reverse proxy (nginx, Caddy) in production
   - Implement rate limiting
   - Consider using VPN or IP whitelisting

4. **Container Security**
   - Keep base images updated
   - Run container as non-root user when possible
   - Limit container resources if needed

5. **Monitoring**
   - Set up log aggregation
   - Monitor container resource usage
   - Set up alerts for failures

## Advanced Configuration

### Using Reverse Proxy (Nginx)

Example nginx configuration:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Using Docker Compose

For easier local management, create `docker-compose.yml` on server:

```yaml
version: '3.8'

services:
  we-mp-rss:
    image: registry.example.com/mason105/we-mp-rss:latest
    container_name: we-mp-rss
    restart: always
    ports:
      - "8001:8001"
    volumes:
      - /opt/we-mp-rss/config/config.yaml:/app/config.yaml
      - /opt/we-mp-rss/data:/app/data
    environment:
      - TZ=Asia/Shanghai
```

Then deploy with:
```bash
docker-compose pull
docker-compose up -d
```

### Multi-Environment Deployment

Create separate secrets for different environments:

- `PROD_SERVER_HOST`, `PROD_SERVER_USER`, etc. for production
- `STAGE_SERVER_HOST`, `STAGE_SERVER_USER`, etc. for staging

Modify workflow to use environment-specific secrets based on branch or input.

## Support

For issues or questions:
- Check [GitHub Issues](https://github.com/yourusername/we-mp-rss/issues)
- Review workflow logs in GitHub Actions
- Check server logs with `docker logs we-mp-rss`

## Related Documentation

- [Docker Documentation](https://docs.docker.com/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [SSH Action Documentation](https://github.com/appleboy/ssh-action)
