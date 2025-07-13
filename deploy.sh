#!/bin/bash

# Livekit Design Agent - Deployment Script
# This script helps prepare and deploy the application

set -e

echo "🚀 Livekit Design Agent Deployment Script"
echo "=========================================="

# Check if we're in the right directory
if [ ! -f "README.md" ] || [ ! -d "voice-assistant-frontend" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check dependencies
echo "🔍 Checking dependencies..."

if ! command_exists node; then
    echo "❌ Node.js is not installed. Please install Node.js first."
    exit 1
fi

if ! command_exists pnpm; then
    echo "❌ pnpm is not installed. Installing pnpm..."
    npm install -g pnpm
fi

if ! command_exists git; then
    echo "❌ Git is not installed. Please install Git first."
    exit 1
fi

echo "✅ All dependencies are available"

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ This is not a git repository. Please initialize git first."
    exit 1
fi

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo "⚠️  Warning: You have uncommitted changes."
    read -p "Do you want to commit them first? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "📝 Committing changes..."
        git add .
        git commit -m "feat: prepare for deployment"
        git push
    fi
fi

# Test frontend build
echo "🔧 Testing frontend build..."
cd voice-assistant-frontend

# Install dependencies
echo "📦 Installing frontend dependencies..."
pnpm install

# Run build test
echo "🏗️  Testing build..."
pnpm build

if [ $? -eq 0 ]; then
    echo "✅ Frontend build successful!"
else
    echo "❌ Frontend build failed. Please fix the errors before deploying."
    exit 1
fi

cd ..

# Check environment variables
echo "🔐 Checking environment variables..."
ENV_FILE="voice-assistant-frontend/.env.local"

if [ ! -f "$ENV_FILE" ]; then
    echo "⚠️  Warning: $ENV_FILE not found."
    echo "You'll need to set up environment variables in Vercel dashboard."
else
    echo "✅ Environment file found"
fi

# Display deployment instructions
echo ""
echo "🎉 Ready for deployment!"
echo "======================="
echo ""
echo "Next steps:"
echo "1. Go to https://vercel.com/dashboard"
echo "2. Click 'New Project'"
echo "3. Import your GitHub repository"
echo "4. Vercel will detect the Next.js project automatically"
echo "5. Add environment variables in Vercel dashboard:"
echo "   - LIVEKIT_URL"
echo "   - LIVEKIT_API_KEY"
echo "   - LIVEKIT_API_SECRET"
echo "   - NEXT_PUBLIC_SUPABASE_URL"
echo "   - NEXT_PUBLIC_SUPABASE_ANON_KEY"
echo "   - OPENAI_API_KEY"
echo "6. Deploy!"
echo ""
echo "📖 For detailed instructions, see DEPLOYMENT.md"
echo ""
echo "🐍 Don't forget to deploy your Python backend separately!"
echo "   - Railway: https://railway.app"
echo "   - Render: https://render.com"
echo "   - Or your own server"
echo ""
echo "✨ Good luck with your deployment!" 