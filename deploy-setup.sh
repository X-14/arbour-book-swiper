#!/bin/bash

# 🚀 Quick Deploy Setup Script for Render
# This script prepares your project for deployment

echo "🎯 Arbour Book Swiper - Deployment Setup"
echo "========================================="
echo ""

# Navigate to project directory
cd "/Users/xavierjudge/Desktop/Arbour Book Swiper/Anti Gravity Recomendation"

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📦 Initializing Git repository..."
    git init
    echo "✅ Git initialized"
else
    echo "✅ Git already initialized"
fi

# Add all files
echo ""
echo "📝 Adding files to Git..."
git add .

# Create initial commit
echo ""
echo "💾 Creating commit..."
git commit -m "Initial commit - Ready for Render deployment"

echo ""
echo "========================================="
echo "✨ Setup Complete! Next steps:"
echo ""
echo "1. Create a new repository on GitHub:"
echo "   👉 https://github.com/new"
echo ""
echo "2. Run these commands to push your code:"
echo "   git remote add origin https://github.com/YOUR_USERNAME/arbour-book-swiper.git"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""
echo "3. Go to Render.com and deploy:"
echo "   👉 https://render.com"
echo ""
echo "4. Follow the DEPLOYMENT_GUIDE.md for detailed instructions"
echo "========================================="
echo ""
echo "⚠️  IMPORTANT: Check that models/ folder is included (104MB)"
echo "   If it's too large for GitHub, you may need to:"
echo "   - Use Git LFS (Large File Storage)"
echo "   - Or regenerate models on Render using a build script"
echo ""
