# Oracle Cloud Always Free Deployment Guide

## Overview

Oracle Cloud's Always Free tier provides:
- ✅ **2 Compute Instances** (2GB RAM each)
- ✅ **20GB Storage**
- ✅ **Always Free** (never expires, no credit card after trial)
- ✅ **Full Docker support**

This is perfect for deploying CareerLens without memory constraints!

---

## Step 1: Create Oracle Cloud Account

1. Go to: https://www.oracle.com/cloud/free/
2. Click **"Start for free"**
3. Create account and verify email
4. **Important**: Choose region closest to you (e.g., `us-phoenix-1` for Americas)
5. Skip the "free trial credits" to go directly to Always Free tier

---

## Step 2: Create a Compute Instance (Always Free VM)

1. **Go to**: Oracle Cloud Console → **Compute** → **Instances**
2. Click **"Create Instance"**
3. **Configure**:
   - **Name**: `careerlens-app`
   - **Image**: Ubuntu 22.04 (Always Free eligible)
   - **Shape**: `VM.Standard.E2.1.Micro` (Always Free - 1 OCPU, 1GB RAM)
     - ⚠️ **Important**: Expand "Flexible Shape" and set to:
       - **OCPUs**: 2
       - **Memory**: 2GB (within Always Free limit)
   - **VCN**: Create new or use default
   - **Public IP**: Assign (needed for internet access)

4. **SSH Key**: Download and save the key (e.g., `ssh-key-2026-06-06.key`)
5. Click **"Create"** (takes 1-2 minutes)

---

## Step 3: Configure Security Rules

1. **Go to**: Networking → **Virtual Cloud Networks**
2. Click your VCN → **Security Lists** → **Default Security List**
3. Click **"Add Ingress Rules"**:
   ```
   Protocol: TCP
   Source: 0.0.0.0/0 (anywhere)
   Destination Port: 80
   Action: Allow
   ```
4. **Repeat** for port `443` (HTTPS) and `5000` (if testing)
5. Click **"Add Ingress Rule"**

---

## Step 4: SSH into Your Instance

### On Windows (PowerShell):
```powershell
# Set correct permissions for key
icacls "C:\path\to\ssh-key-2026-06-06.key" /inheritance:r /grant:r "$env:username`:F"

# SSH into instance (replace IP with your instance's public IP)
ssh -i "C:\path\to\ssh-key-2026-06-06.key" ubuntu@YOUR_INSTANCE_IP
```

### On Mac/Linux:
```bash
chmod 600 ssh-key-2026-06-06.key
ssh -i ssh-key-2026-06-06.key ubuntu@YOUR_INSTANCE_IP
```

---

## Step 5: Install Docker & Deploy

Once SSH'd into the instance:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Exit and reconnect SSH (to apply docker group)
exit
ssh -i ssh-key-2026-06-06.key ubuntu@YOUR_INSTANCE_IP

# Clone your repository
git clone https://github.com/aaushx/CareerLens-v1.git
cd CareerLens-v1

# Create .env file with your configuration
cat > .env << 'EOF'
FLASK_ENV=production
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
DATABASE_PATH=/app/data/careerlens.db
PORT=5000
EOF

# Build and run with Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Pull image and start
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs -f
```

---

## Step 6: Access Your App

1. **Get your instance's public IP** from Oracle Cloud Console
2. **Open browser**: `http://YOUR_INSTANCE_IP:5000`
3. ✅ Your app should be running!

---

## Step 7: Set Up Domain (Optional)

### Using a Free Domain with CloudFlare:

1. Register free domain at **Freenom**: https://freenom.com (or use existing)
2. Go to **CloudFlare**: https://www.cloudflare.com (free tier)
3. Add your domain and point to your instance IP
4. Enjoy: `https://yourdomain.com` 🎉

---

## Useful Commands

```bash
# View logs
docker-compose logs -f

# Restart app
docker-compose restart

# Stop app
docker-compose down

# Update from GitHub
git pull origin main
docker-compose up -d --build

# Check disk usage
df -h

# Check memory
free -h

# SSH back in (from your local machine)
ssh -i ssh-key-2026-06-06.key ubuntu@YOUR_INSTANCE_IP
```

---

## Troubleshooting

### Issue: Docker image build fails
**Solution**: The instance may not have enough memory during build. SSH in and:
```bash
# Check memory
free -h

# If low, wait a bit or reduce parallel build jobs
docker build --build-arg BUILDKIT_INLINE_CACHE=1 .
```

### Issue: App crashes with OOM
**Solution**: You can swap additional space:
```bash
# Create 2GB swap
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Issue: Can't SSH in
**Solution**: 
- Check instance is running in Oracle Console
- Verify Security List rules allow port 22 (SSH)
- Try: `ssh -v` for verbose output

### Issue: Database errors
**Solution**: Ensure `/app/data` directory exists and is writable:
```bash
docker exec careerlens-app mkdir -p /app/data
docker exec careerlens-app chmod 777 /app/data
```

---

## Cost

✅ **$0/month** - Everything is covered by Always Free tier

---

## Next Steps

1. ✅ Create Oracle account
2. ✅ Launch Compute Instance (always free)
3. ✅ Follow Step 4-5 above to deploy
4. ✅ Enjoy your free, high-memory app! 🚀

---

**Questions?** Check Oracle Cloud docs: https://docs.oracle.com/en-us/iaas/Content/home.htm
