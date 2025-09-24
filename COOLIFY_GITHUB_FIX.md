# 🔧 Coolify GitHub Authentication Fix

## Problem
Coolify is failing to clone your GitHub repository with error:
```
fatal: could not read Username for 'https://github.com': No such device or address
```

## Solution Options

### Option 1: Use GitHub App Integration (Recommended)

1. **Go to Coolify Dashboard** → Settings → Source Control
2. **Connect GitHub** using OAuth/GitHub App
3. **Authorize Coolify** to access your repositories
4. **Reconfigure your project** to use the authenticated connection

### Option 2: Use Personal Access Token (PAT)

1. **Create a GitHub Personal Access Token**:
   - Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
   - Generate new token with these permissions:
     - `repo` (full control of private repositories)
     - `read:org` (optional, for organization repos)

2. **Configure in Coolify**:
   - In Coolify dashboard, go to your project settings
   - Update the Git URL to include the token:
     ```
     https://[TOKEN]@github.com/aligator81/docling.git
     ```
   - Or configure in Coolify's source control settings

### Option 3: Use SSH Key Authentication

1. **Generate SSH Key** on your Coolify server:
   ```bash
   ssh-keygen -t ed25519 -C "coolify@your-server"
   ```

2. **Add SSH Key to GitHub**:
   - Copy the public key: `cat ~/.ssh/id_ed25519.pub`
   - Go to GitHub → Settings → SSH and GPG keys → New SSH key

3. **Update Coolify Configuration**:
   - Use SSH URL: `git@github.com:aligator81/docling.git`
   - Ensure Coolify has access to the SSH key

## Quick Fix Steps

### Immediate Action:
1. **Check Coolify GitHub Integration**:
   - Go to Coolify Settings → Source Control
   - Ensure GitHub is properly connected
   - Re-authenticate if necessary

2. **Verify Repository URL** in Coolify project settings:
   - Should be: `https://github.com/aligator81/docling.git`
   - Or SSH: `git@github.com:aligator81/docling.git`

3. **Test Manual Clone** on your Coolify server:
   ```bash
   git clone https://github.com/aligator81/docling.git
   ```
   If this fails, the server needs GitHub authentication setup.

### Alternative: Deploy via Docker Image

If GitHub authentication continues to be problematic, you can deploy via Docker Hub:

1. **Build and push to Docker Hub**:
   ```bash
   docker build -t aligator81/docling-app .
   docker push aligator81/docling-app
   ```

2. **Configure Coolify to use Docker image** instead of Git repository

## Verification Steps

After applying the fix:

1. **Test the connection** in Coolify
2. **Redeploy** your application
3. **Monitor build logs** for authentication success

## Common Causes

- GitHub rate limiting
- Expired authentication tokens
- Repository privacy settings (if private)
- Network/firewall issues on Coolify server
- Incorrect repository URL format

## Support Resources

- Coolify GitHub Integration Docs: https://coolify.io/docs/source-control/github
- GitHub Personal Access Tokens: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens

Try Option 1 (GitHub App integration) first as it's the most reliable method.