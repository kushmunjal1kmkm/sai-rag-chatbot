# GitHub Workflows Setup Guide

## 🚀 Available Workflows

### 1. **Test Workflow** (`.github/workflows/test-app.yml`)
- **Purpose**: Automated testing on every push/PR
- **Runtime**: ~5 minutes
- **What it does**: 
  - Tests Python imports
  - Verifies Flask app startup
  - Checks health endpoints
  - Validates configuration

### 2. **Deploy Workflow** (`.github/workflows/deploy-flask-app.yml`)
- **Purpose**: Temporarily run your app with public URL
- **Runtime**: 1-6 hours (configurable)
- **What it does**:
  - Starts Flask server on GitHub Actions
  - Creates public URL via ngrok
  - Runs for specified duration
  - ⚠️ **Limited runtime** - not for production

### 3. **GitHub Codespaces** (`.devcontainer/devcontainer.json`)
- **Purpose**: Full development environment
- **Runtime**: Unlimited (while active)
- **What it does**:
  - Complete Python environment
  - Auto-installs dependencies
  - Port forwarding for testing
  - ✅ **Best for development**

## 🛠️ Setup Instructions

### Step 1: Required Secrets
Add these to your GitHub repository secrets:

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Add secrets:
   ```
   GEMINI_API_KEY = your_actual_gemini_api_key
   NGROK_AUTH_TOKEN = your_ngrok_token (optional, for deploy workflow)
   ```

### Step 2: Enable Workflows
1. Push these files to your repository
2. Go to **Actions** tab
3. Workflows will appear automatically

### Step 3: Using the Deploy Workflow
1. Go to **Actions** → **Deploy SAI RAG Chatbot**
2. Click **Run workflow**
3. Set duration (max 360 minutes)
4. Get public URL from logs

## 🎯 Recommended Approach

### For Development:
```bash
# Use GitHub Codespaces
1. Click "Code" → "Codespaces" → "Create codespace"
2. Wait for environment setup
3. Run: python main_app.py
4. Access via forwarded port
```

### For Production:
```bash
# Use Render (most reliable)
1. Connect GitHub repo to Render
2. Deploy automatically
3. Get permanent public URL
```

### For Testing:
```bash
# GitHub Actions automatically test on every push
git push origin main
# Check Actions tab for results
```

## 📊 Workflow Comparison

| Method | Runtime | Public URL | Cost | Best For |
|--------|---------|------------|------|----------|
| **Render** | ∞ | ✅ Permanent | Free tier | **Production** |
| **Codespaces** | While active | ✅ Temporary | Free hours | **Development** |
| **Actions Deploy** | 6h max | ✅ Temporary | Free minutes | **Demo/Testing** |
| **Actions Test** | 5min | ❌ | Free minutes | **CI/CD** |

## 🔗 Next Steps

1. **Immediate**: Use test workflow to verify everything works
2. **Development**: Set up Codespaces for coding
3. **Production**: Deploy to Render for permanent hosting
4. **Demo**: Use deploy workflow for temporary public access

## 🚨 Important Notes

- **GitHub Actions**: Limited runtime, not for production
- **Codespaces**: Great for development, has usage limits
- **Render**: Best for production deployment
- **Always protect API keys** in repository secrets