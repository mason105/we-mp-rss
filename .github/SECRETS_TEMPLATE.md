# GitHub Secrets Configuration Template

Use this template to configure your GitHub repository secrets for automated deployment.

**Location**: `Repository → Settings → Secrets and variables → Actions → New repository secret`

## Required Secrets Checklist

Copy this checklist and fill in the values as you configure each secret:

```
[ ] VAR_REGISTRY_URL
[ ] VAR_REGISTRY_USERNAME
[ ] VAR_REGISTRY_PASSWORD
[ ] SERVER_HOST
[ ] SERVER_PORT
[ ] SERVER_USER
[ ] SERVER_SSH_KEY
```

## Secret Details

### 1. VAR_REGISTRY_URL
**Description**: Your Docker registry URL (without protocol)

**Example Values**:
```
registry.example.com
docker.mycompany.com
harbor.example.io
```

**How to find**:
- Check with your registry administrator
- Look at existing docker login commands
- Check your Docker registry dashboard

**Value**:
```
[Your registry URL here]
```

---

### 2. VAR_REGISTRY_USERNAME
**Description**: Username for Docker registry authentication

**Example Values**:
```
mason105
admin
deployuser
```

**How to find**:
- Your Docker registry account username
- Service account name provided by admin
- Registry access token username

**Value**:
```
[Your registry username here]
```

---

### 3. VAR_REGISTRY_PASSWORD
**Description**: Password or access token for Docker registry

**Example Values**:
```
mySecretPassword123!
ghp_xxxxxxxxxxxxxxxxxxxx (for GitHub)
dckr_pat_xxxxxxxxxxxx (for Docker Hub)
```

**How to find**:
- Your registry account password
- Generate an access token from registry settings
- Contact your registry administrator

**Security Note**: Use access tokens instead of passwords when possible

**Value**:
```
[Your registry password/token here]
```

---

### 4. SERVER_HOST
**Description**: IP address or hostname of your deployment server

**Example Values**:
```
192.168.1.100
server.example.com
deploy-prod-01.mycompany.com
```

**How to find**:
```bash
# From server:
hostname -I
curl ifconfig.me

# From local:
ssh user@your-server 'hostname -I'
```

**Value**:
```
[Your server IP/hostname here]
```

---

### 5. SERVER_PORT
**Description**: SSH port number (default is 22)

**Example Values**:
```
22
2222
22022
```

**Default**: `22`

**How to find**:
```bash
# Check SSH config on server:
grep Port /etc/ssh/sshd_config

# Or check your usual SSH connection:
# If you use: ssh -p 2222 user@server
# Then SERVER_PORT = 2222
```

**Value**:
```
[Your SSH port, usually 22]
```

---

### 6. SERVER_USER
**Description**: SSH username for server access

**Example Values**:
```
ubuntu
deploy
root (not recommended)
admin
```

**How to find**:
- The username you use to SSH into the server
- Check with your system administrator
- Look at existing SSH commands you use

**Value**:
```
[Your SSH username here]
```

---

### 7. SERVER_SSH_KEY
**Description**: Private SSH key for authentication (entire key including header/footer)

**How to generate**:
```bash
# Generate new SSH key pair
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/github_deploy -N ""

# Copy public key to server
ssh-copy-id -i ~/.ssh/github_deploy.pub user@your-server

# Get private key for GitHub Secret
cat ~/.ssh/github_deploy
```

**Format** (entire output including headers):
```
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
QyNTUxOQAAACBK... (many lines)
...xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx=
-----END OPENSSH PRIVATE KEY-----
```

**Important Notes**:
- Copy the ENTIRE key including `-----BEGIN` and `-----END` lines
- Include all newlines (don't make it a single line)
- Do NOT share this key publicly
- Do NOT commit this key to git
- Keep the private key secure

**How to test**:
```bash
# Test SSH connection with the key
ssh -i ~/.ssh/github_deploy user@your-server

# Should connect without password prompt
```

**Value**:
```
[Paste entire private key here]
```

---

## Optional Secrets (Advanced Configuration)

### 8. DEPLOY_CONFIG_PATH (Optional)
**Description**: Custom path for config file on server

**Default**: `/opt/we-mp-rss/config`

**When to use**: Only if you want to store config in a different location

**Example Values**:
```
/home/deploy/app/config
/var/app/we-mp-rss/config
/data/applications/we-mp-rss/config
```

**Value**:
```
[Custom config path, or leave empty to use default]
```

---

### 9. DEPLOY_DATA_PATH (Optional)
**Description**: Custom path for data directory on server

**Default**: `/opt/we-mp-rss/data`

**When to use**: Only if you want to store data in a different location

**Example Values**:
```
/home/deploy/app/data
/var/app/we-mp-rss/data
/mnt/storage/we-mp-rss/data
```

**Value**:
```
[Custom data path, or leave empty to use default]
```

---

### 10. DEPLOY_PORT (Optional)
**Description**: Custom host port for the application

**Default**: `8001`

**When to use**: Only if port 8001 is already in use or you prefer different port

**Example Values**:
```
8001
8080
3000
```

**Value**:
```
[Custom port number, or leave empty to use default 8001]
```

---

## Configuration Validation

Before running deployment, verify your configuration:

### Test 1: SSH Connection
```bash
ssh -i ~/.ssh/github_deploy [SERVER_USER]@[SERVER_HOST] -p [SERVER_PORT]
```

Expected: Should connect without password prompt

### Test 2: Docker Registry Login
```bash
ssh [SERVER_USER]@[SERVER_HOST] "docker login --username=[VAR_REGISTRY_USERNAME] [VAR_REGISTRY_URL]"
# Enter VAR_REGISTRY_PASSWORD when prompted
```

Expected: "Login Succeeded"

### Test 3: Server Preparation
```bash
ssh [SERVER_USER]@[SERVER_HOST] "
  mkdir -p /opt/we-mp-rss/{config,data}
  ls -la /opt/we-mp-rss/
"
```

Expected: Directories created successfully

### Test 4: Docker Access
```bash
ssh [SERVER_USER]@[SERVER_HOST] "docker ps"
```

Expected: List of running containers (or empty list)

## Quick Configuration Script

Copy and fill in this script to configure all secrets at once using GitHub CLI:

```bash
#!/bin/bash
# Fill in these values:
export VAR_REGISTRY_URL=""
export VAR_REGISTRY_USERNAME=""
export VAR_REGISTRY_PASSWORD=""
export SERVER_HOST=""
export SERVER_PORT="22"
export SERVER_USER=""
export SERVER_SSH_KEY_FILE="~/.ssh/github_deploy"

# Optional:
# export DEPLOY_CONFIG_PATH="/opt/we-mp-rss/config"
# export DEPLOY_DATA_PATH="/opt/we-mp-rss/data"
# export DEPLOY_PORT="8001"

# Configure secrets using GitHub CLI
gh secret set VAR_REGISTRY_URL -b"$VAR_REGISTRY_URL"
gh secret set VAR_REGISTRY_USERNAME -b"$VAR_REGISTRY_USERNAME"
gh secret set VAR_REGISTRY_PASSWORD -b"$VAR_REGISTRY_PASSWORD"
gh secret set SERVER_HOST -b"$SERVER_HOST"
gh secret set SERVER_PORT -b"$SERVER_PORT"
gh secret set SERVER_USER -b"$SERVER_USER"
gh secret set SERVER_SSH_KEY < "$SERVER_SSH_KEY_FILE"

# Optional secrets (uncomment if needed):
# gh secret set DEPLOY_CONFIG_PATH -b"$DEPLOY_CONFIG_PATH"
# gh secret set DEPLOY_DATA_PATH -b"$DEPLOY_DATA_PATH"
# gh secret set DEPLOY_PORT -b"$DEPLOY_PORT"

echo "All secrets configured successfully!"
gh secret list
```

## Security Best Practices

1. **Never commit secrets to git**
   - Always use GitHub Secrets for sensitive data
   - Add sensitive files to `.gitignore`

2. **Rotate credentials regularly**
   - Update passwords/tokens every 90 days
   - Regenerate SSH keys periodically

3. **Use least privilege principle**
   - Create dedicated deployment user on server
   - Grant only necessary permissions
   - Avoid using root account

4. **Protect SSH keys**
   - Set proper permissions: `chmod 600 ~/.ssh/github_deploy`
   - Never share private keys
   - Use different keys for different purposes

5. **Monitor access**
   - Review GitHub Actions logs regularly
   - Monitor server access logs
   - Set up alerts for failed deployments

## Troubleshooting

### "Secret not found" error
- Verify secret name is exactly as shown (case-sensitive)
- Check you're in the correct repository
- Ensure secret is in "Actions" section, not "Codespaces" or "Dependabot"

### "Permission denied (publickey)" error
- Verify public key is copied to server: `cat ~/.ssh/authorized_keys`
- Check private key is complete in GitHub Secret
- Test SSH connection manually first

### "Could not resolve hostname" error
- Verify SERVER_HOST is correct
- Check DNS resolution: `nslookup [SERVER_HOST]`
- Try using IP address instead of hostname

### "Connection refused" error
- Verify SERVER_PORT is correct
- Check SSH service is running on server: `sudo systemctl status ssh`
- Verify firewall allows SSH: `sudo ufw status`

## Next Steps

After configuring all secrets:

1. Verify all secrets are set:
   ```bash
   gh secret list
   ```

2. Review deployment documentation:
   - Quick Start: `.github/DEPLOYMENT_QUICKSTART.md`
   - Full Guide: `.github/DEPLOYMENT.md`

3. Prepare server environment (see DEPLOYMENT_QUICKSTART.md)

4. Run your first deployment!

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review workflow logs in GitHub Actions
3. Test each component (SSH, Docker login, etc.) individually
4. Consult full deployment guide: `.github/DEPLOYMENT.md`
