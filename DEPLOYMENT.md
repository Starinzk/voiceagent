# Vercel Deployment Guide

## 🚀 Deploying Livekit Design Agent to Vercel

This guide covers deploying the Next.js frontend to Vercel while keeping the Python backend separate.

### Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Vercel        │    │   Python        │    │   LiveKit       │
│   (Frontend)    │◄──►│   Backend       │◄──►│   Cloud         │
│   Next.js App   │    │   (Separate)    │    │   (Agents)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📋 Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **GitHub Repository**: Your code should be pushed to GitHub
3. **Environment Variables**: All API keys and credentials ready
4. **Python Backend**: Deployed separately (Railway, Render, or your own server)

## 🔧 Step 1: Prepare Your Repository

### 1.1 Ensure vercel.json is configured
The `vercel.json` file has been created with the proper configuration for your project structure.

### 1.2 Update Backend URL (if needed)
If your Python backend will be deployed separately, you may need to update API endpoints in your frontend code.

## 🌐 Step 2: Deploy to Vercel

### 2.1 Connect Repository
1. Go to [vercel.com/dashboard](https://vercel.com/dashboard)
2. Click "New Project"
3. Import your GitHub repository
4. Vercel will automatically detect it's a Next.js project

### 2.2 Configure Build Settings
Vercel should automatically detect the configuration from `vercel.json`:
- **Framework Preset**: Next.js
- **Root Directory**: `voice-assistant-frontend`
- **Build Command**: `pnpm install && pnpm build`
- **Output Directory**: `.next`

### 2.3 Environment Variables
Add these environment variables in Vercel dashboard:

#### Required Variables:
```env
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
OPENAI_API_KEY=your_openai_api_key
```

#### Optional Variables:
```env
NEXT_PUBLIC_CONN_DETAILS_ENDPOINT=/api/connection-details
```

### 2.4 Deploy
1. Click "Deploy"
2. Vercel will build and deploy your application
3. You'll get a URL like `https://your-app.vercel.app`

## 🐍 Step 3: Deploy Python Backend Separately

### Option A: Railway
1. Go to [railway.app](https://railway.app)
2. New Project → Deploy from GitHub → select this repo
3. Service root: `design_assistant`
4. If using Docker: add service from `design_assistant/Dockerfile` (recommended)
5. Otherwise, set Build/Start:
   - Build: `pip install -r requirements.txt`
   - Start: `python -m design_assistant.main`
6. Add environment variables (same as local `.env`):
   - `OPENAI_API_KEY`
   - `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`
   - `SUPABASE_URL`, `SUPABASE_KEY` (service role)
   - `DEEPGRAM_API_KEY`, `CARTESIA_API_KEY`
7. Deploy

### Option B: Render
1. Go to [render.com](https://render.com)
2. Create a new Web Service → connect repository
3. Root directory: `design_assistant`
4. If using Docker: Auto-detect `design_assistant/Dockerfile`
5. Otherwise:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python -m design_assistant.main`
6. Environment: same keys as Railway section

### Option C: Your Own Server
Deploy using Docker, PM2, or your preferred method.

## 🔗 Step 4: Connect Frontend to Backend

### 4.1 Update API Endpoints
If your backend is deployed separately, update any API calls in your frontend to point to the backend URL.

For this project: the frontend only calls LiveKit JobService and uses LiveKit Cloud; the Python worker connects to LiveKit directly. No backend HTTP endpoint is required for the UI.

### 4.2 CORS Configuration
Ensure your Python backend allows requests from your Vercel domain:
```python
# In your backend
ALLOWED_ORIGINS = [
    "https://your-app.vercel.app",
    "http://localhost:3000",  # for development
]
```

## 🧪 Step 5: Test Deployment

### 5.1 Frontend Testing
1. Visit your Vercel URL
2. Test the UI components
3. Check browser console for errors

### 5.2 Backend Integration
1. Verify worker registers with LiveKit (Railway/Render logs)
2. Test voice functionality via frontend session
3. Check Supabase connections

### 5.3 LiveKit Integration
1. Test room creation
2. Verify agent dispatch
3. Check audio/video functionality

## 🔧 Troubleshooting

### Common Issues:

#### Build Errors
- **Missing dependencies**: Check `package.json` in `voice-assistant-frontend`
- **TypeScript errors**: Fix any type issues before deployment
- **Environment variables**: Ensure all required vars are set

#### Runtime Errors
- **API routes failing**: Check Vercel function logs
- **CORS issues**: Verify backend CORS configuration
- **LiveKit connection**: Verify LiveKit credentials and URL

#### Performance Issues
- **Cold starts**: Vercel functions may have cold start delays
- **Timeouts**: Increase function timeout in `vercel.json`
- **Memory limits**: Check function memory usage

### Debugging Tools:
- **Vercel Dashboard**: Check deployment logs
- **Browser DevTools**: Check network requests and console
- **Vercel CLI**: `vercel logs` for real-time logs

## 📊 Monitoring

### Vercel Analytics
Enable Vercel Analytics for performance monitoring:
1. Go to your project dashboard
2. Click "Analytics" tab
3. Enable Web Analytics

### Error Tracking
Consider adding error tracking:
- Sentry
- LogRocket
- Vercel's built-in error tracking

## 🚀 Production Optimizations

### Performance
- Enable Vercel Edge Functions for faster response times
- Use Vercel's Image Optimization for any images
- Enable compression and caching

### Security
- Review Content Security Policy in `next.config.js`
- Ensure all API keys are properly secured
- Enable HTTPS only

### Scalability
- Monitor function execution times
- Consider upgrading Vercel plan if needed
- Implement proper error handling and retries

## 📝 Post-Deployment Checklist

- [ ] Frontend deployed successfully
- [ ] Backend deployed and accessible
- [ ] All environment variables configured
- [ ] Voice functionality working
- [ ] Agent responses functioning
- [ ] Database connections established
- [ ] LiveKit integration working
- [ ] Error monitoring set up
- [ ] Performance monitoring enabled
- [ ] Domain configured (if custom domain needed)

## 🆘 Need Help?

- **Vercel Docs**: [vercel.com/docs](https://vercel.com/docs)
- **Next.js Deployment**: [nextjs.org/docs/deployment](https://nextjs.org/docs/deployment)
- **LiveKit Docs**: [docs.livekit.io](https://docs.livekit.io)

---

**Note**: This deployment separates the frontend (Vercel) from the backend (separate service). For a fully integrated deployment, consider using Vercel's Python runtime or converting backend logic to serverless functions. 