# Deployment Quick Start

Quick reference for deploying we-mp-rss to your server.

## 5-Minute Setup Checklist

### Step 1: Prepare Server (5 min)

```bash
# SSH to your server
ssh user@your-server

# Install Docker (if not installed)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Create directories
sudo mkdir -p /opt/we-mp-rss/{config,data}
sudo chown -R $USER:$USER /opt/we-mp-rss

# Create minimal config
cat > /opt/we-mp-rss/config/config.yaml <<EOF
app_name: we-mp-rss
server:
  name: we-mp-rss
  web_name: WeRSS微信公众号订阅助手
  enable_job: True
  threads: 4

db: sqlite:///data/db.db
secret: $(openssl rand -hex 32)
port: 8001
debug: False

rss:
  base_url: "http://$(curl -s ifconfig.me):8001/"
  local: False
  full_context: True
  page_size: 30

safe:
  lic_key: "RACHELOS"

log:
  level: INFO
EOF

# Open firewall
sudo ufw allow 8001/tcp || true
```

### Step 2: Generate SSH Key (2 min)

```bash
# On your local machine
ssh-keygen -t ed25519 -C "github-deploy" -f ~/.ssh/github_deploy -N ""

# Copy to server (replace user@server)
ssh-copy-id -i ~/.ssh/github_deploy.pub user@your-server

# Get private key content for GitHub
cat ~/.ssh/github_deploy
# Copy this output for next step
```

### Step 3: Configure GitHub Secrets (3 min)

Go to: `GitHub Repo → Settings → Secrets and variables → Actions`

Click **New repository secret** for each:

| Secret Name | Value | Example |
|-------------|-------|---------|
| `VAR_REGISTRY_URL` | Your Docker registry | `registry.example.com` |
| `VAR_REGISTRY_USERNAME` | Registry username | `mason105` |
| `VAR_REGISTRY_PASSWORD` | Registry password | `your-token-here` |
| `SERVER_HOST` | Server IP/hostname | `192.168.1.100` |
| `SERVER_PORT` | SSH port | `22` |
| `SERVER_USER` | SSH username | `ubuntu` |
| `SERVER_SSH_KEY` | Private key content | Paste from Step 2 |

**Optional** (if using custom paths):
- `DEPLOY_CONFIG_PATH` → `/opt/we-mp-rss/config`
- `DEPLOY_DATA_PATH` → `/opt/we-mp-rss/data`
- `DEPLOY_PORT` → `8001`

### Step 4: Deploy (1 min)

1. Go to: `GitHub Repo → Actions → Deploy to Server`
2. Click **Run workflow**
3. Leave defaults (image_tag: `latest`)
4. Click **Run workflow** button
5. Wait ~2-3 minutes
6. Open: `http://your-server-ip:8001`

## Quick Commands

### Check Deployment Status
```bash
ssh user@server "docker ps | grep we-mp-rss"
```

### View Logs
```bash
ssh user@server "docker logs -f we-mp-rss"
```

### Restart Service
```bash
ssh user@server "docker restart we-mp-rss"
```

### Rollback to Previous Version
```bash
# In GitHub Actions
# Run workflow with image_tag: <previous-commit-sha>
```

## Troubleshooting

### Can't SSH
```bash
# Test connection
ssh -i ~/.ssh/github_deploy user@your-server

# If fails, check:
# - Is server IP correct?
# - Is SSH key copied? (ssh-copy-id)
# - Is firewall blocking port 22?
```

### Docker Login Fails
```bash
# Test on server
ssh user@server
docker login --username=<user> <registry>

# If fails, check:
# - Registry URL correct?
# - Username/password correct?
# - Token not expired?
```

### Container Won't Start
```bash
# Check logs
ssh user@server "docker logs we-mp-rss"

# Common issues:
# - Config file missing/invalid
# - Port 8001 already in use
# - Insufficient permissions
```

### Port Already in Use
```bash
# Find what's using it
ssh user@server "sudo lsof -i :8001"

# Kill old container
ssh user@server "docker rm -f we-mp-rss"

# Run deployment again
```

## Manual Deployment (Emergency)

If GitHub Actions fails, deploy manually:

```bash
# SSH to server
ssh user@your-server

# Login to registry
docker login --username=<user> <registry>

# Pull image
docker pull <registry>/mason105/we-mp-rss:latest

# Stop old container
docker rm -f we-mp-rss || true

# Run new container
docker run -d \
  --name=we-mp-rss \
  --restart=always \
  -p 8001:8001 \
  -v /opt/we-mp-rss/config/config.yaml:/app/config.yaml \
  -v /opt/we-mp-rss/data:/app/data \
  -e TZ=Asia/Shanghai \
  <registry>/mason105/we-mp-rss:latest

# Check status
docker ps | grep we-mp-rss
docker logs -f we-mp-rss
```

## Production Checklist

Before going to production:

- [ ] Change `secret` in config.yaml to random value
- [ ] Set up HTTPS with reverse proxy (nginx/Caddy)
- [ ] Configure proper domain name
- [ ] Set up database backups
- [ ] Configure monitoring/alerts
- [ ] Update `rss.base_url` to production domain
- [ ] Test health check endpoint
- [ ] Document rollback procedure
- [ ] Set up log rotation
- [ ] Review security settings

## Need Help?

1. Check deployment logs in GitHub Actions
2. Check server logs: `docker logs we-mp-rss`
3. Review [Full Deployment Guide](./DEPLOYMENT.md)
4. Check [Project Issues](https://github.com/yourusername/we-mp-rss/issues)

## Common Workflows

### Deploy Latest Version
```
Actions → Deploy to Server → Run workflow (defaults) → Run
```

### Deploy Specific Version
```
Actions → Deploy to Server → Run workflow
  → image_tag: a1b2c3d → Run
```

### Deploy After Build
```
# Automatically deploys after successful build on main branch
# (if configured in build workflow)
```

### Check Deployment
```
Actions → Deploy to Server → Latest run → View details
```

## Next Steps

After successful deployment:
1. Create admin account via web UI
2. Configure notification webhooks
3. Add RSS subscriptions
4. Set up regular backups
5. Configure monitoring

For detailed information, see [DEPLOYMENT.md](./DEPLOYMENT.md)
