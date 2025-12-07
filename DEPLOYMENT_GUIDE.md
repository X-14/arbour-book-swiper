# 🚀 Deployment Guide - Arbour Book Swiper

## ✨ Option 1: Render.com (RECOMMENDED - Easiest)

### Why Render?
- ✅ **100% Free** - No credit card required
- ✅ **Auto-deploy** from GitHub
- ✅ **Python native** support
- ✅ **SSL/HTTPS** included
- ✅ **Easy setup** - Works in minutes

### Steps:

1. **Push to GitHub** 
   ```bash
   cd "/Users/xavierjudge/Desktop/Arbour Book Swiper/Anti Gravity Recomendation"
   git init
   git add .
   git commit -m "Initial commit for Render deployment"
   # Create a new repo on GitHub, then:
   git remote add origin https://github.com/YOUR_USERNAME/arbour-book-swiper.git
   git push -u origin main
   ```

2. **Sign up on Render**
   - Go to [https://render.com](https://render.com)
   - Sign up with GitHub (recommended)

3. **Create New Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select "arbour-book-swiper" repo

4. **Configure Deployment**
   - **Name:** arbour-book-swiper
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Plan:** Free

5. **Add Environment Variables** (Important!)
   - Go to "Environment" tab
   - Add your Firebase credentials if needed
   - Upload `serviceAccountKey.json` as a secret file

6. **Deploy!**
   - Click "Create Web Service"
   - Wait 5-10 minutes for first deployment
   - Your site will be live at: `https://arbour-book-swiper.onrender.com`

### ⚠️ Important Notes:
- Free tier sleeps after 15 minutes of inactivity (first load takes ~30 seconds)
- Auto-deploys on every git push
- You get 750 hours/month free (enough for most projects)

---

## 🔷 Option 2: Railway.app (Great Alternative)

### Steps:

1. **Sign up at [Railway.app](https://railway.app)**
2. **New Project** → **Deploy from GitHub**
3. **Select your repo**
4. Railway auto-detects Python and requirements.txt
5. **Add Start Command:** `gunicorn app:app`
6. **Deploy!**

**Free Tier:** $5 credit/month (usually enough for small projects)

---

## 🌐 Option 3: PythonAnywhere (Good for Learning)

### Steps:

1. **Sign up at [PythonAnywhere.com](https://www.pythonanywhere.com)**
2. **Go to "Web" tab** → "Add a new web app"
3. **Choose Flask** and Python 3.10
4. **Upload your files** via Files tab or Git
5. **Configure WSGI file** to point to your app
6. **Reload web app**

**Free Tier:** 
- 1 web app
- Custom subdomain: `yourusername.pythonanywhere.com`
- Runs 24/7 (no sleep!)

---

## 🔧 Option 4: Google Cloud Run (Advanced but Powerful)

If you want to stay in the Google ecosystem:

1. **Create Dockerfile**
2. **Build container**
3. **Deploy to Cloud Run**

**Free Tier:** 2 million requests/month (very generous!)

---

## 📊 Quick Comparison

| Platform | Free Tier | Uptime | Setup Difficulty | Best For |
|----------|-----------|---------|------------------|----------|
| **Render** | ✅ 750h/month | Sleeps after 15min | ⭐️ Easy | **Recommended** |
| **Railway** | ✅ $5/month credit | Always on | ⭐️ Easy | Good alternative |
| **PythonAnywhere** | ✅ 1 app | Always on | ⭐️⭐️ Medium | 24/7 uptime |
| **Cloud Run** | ✅ 2M requests | Pay-per-use | ⭐️⭐️⭐️ Hard | Scale & control |

---

## 🎯 My Recommendation

**Start with Render.com** - It's the easiest and most straightforward for Flask apps. The free tier is perfect for this project!

---

## 🆘 Need Help?

If you encounter issues:
1. Check Render/Railway logs for errors
2. Ensure all files are committed to Git
3. Verify `serviceAccountKey.json` is properly configured
4. Make sure models folder is included in the repo

---

## 📝 Files Added for Deployment

- ✅ `requirements.txt` - Updated with gunicorn
- ✅ `render.yaml` - Auto-config for Render
- 📄 This guide!

**You're all set! Choose a platform and deploy! 🚀**
