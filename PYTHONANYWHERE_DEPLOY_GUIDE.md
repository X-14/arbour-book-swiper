# 🚀 Deploy to PythonAnywhere - NO GITHUB NEEDED!

## Why PythonAnywhere?
- ✅ **100% FREE** - No credit card required
- ✅ **Upload files directly** - No GitHub needed
- ✅ **Always running** - Never sleeps (24/7 uptime!)
- ✅ **Python/Flask native** - Perfect for your app
- ✅ **Free subdomain** - yourname.pythonanywhere.com
- ✅ **Easy to use** - Web-based interface

---

## 📋 Complete Step-by-Step Guide

### STEP 1: Create PythonAnywhere Account (2 minutes)

1. **Go to:** https://www.pythonanywhere.com
2. **Click:** "Pricing & signup" → "Create a Beginner account"
3. **Fill in:**
   - Username (this will be your URL: `username.pythonanywhere.com`)
   - Email
   - Password
4. **Click:** "Register"
5. **Confirm your email** (check inbox)
6. **Log in** to your new account

---

### STEP 2: Upload Your Files (5 minutes)

#### Option A: Upload via Web Interface (Easier)

1. **In PythonAnywhere Dashboard**, click **"Files"** tab
2. **Navigate to:** `/home/yourusername/`
3. **Create a new directory:**
   - Click "New directory"
   - Name it: `arbour_book_swiper`
   - Click "Create"
4. **Enter the directory:** Click on `arbour_book_swiper`
5. **Upload your files:**
   - Click "Upload a file"
   - Upload these files/folders one by one:
     - `app.py`
     - `firebase_dal.py`
     - `train_model.py`
     - `requirements.txt`
     - `serviceAccountKey.json`
     - `models/` folder (both .joblib files)
     - `templates/` folder (all HTML files)
     - `static/` folder (CSS, JS, images)

#### Option B: Upload via ZIP (Faster for many files)

1. **On your Mac:** Create a ZIP of your project:
   ```bash
   cd "/Users/xavierjudge/Desktop/Arbour Book Swiper/Anti Gravity Recomendation"
   zip -r arbour_book_swiper.zip . -x "*.git*" "venv/*" "sklearn-env/*" "__pycache__/*" ".DS_Store" "*.pyc"
   ```

2. **In PythonAnywhere:**
   - Go to "Files" tab
   - Navigate to `/home/yourusername/`
   - Click "Upload a file"
   - Upload `arbour_book_swiper.zip`
   - After upload, click on the file and select "Extract"
   - Or use the console: `unzip arbour_book_swiper.zip -d arbour_book_swiper`

---

### STEP 3: Install Dependencies (3 minutes)

1. **Click on "Consoles" tab** in PythonAnywhere
2. **Click:** "Bash" to start a new Bash console
3. **Run these commands:**

```bash
# Navigate to your project
cd ~/arbour_book_swiper

# Create a virtual environment
python3.10 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install flask firebase-admin pandas numpy joblib scikit-learn

# Verify installation
pip list
```

4. **Keep this console open** - you'll need it later

---

### STEP 4: Create Web App (3 minutes)

1. **Click on "Web" tab** in PythonAnywhere
2. **Click:** "Add a new web app"
3. **Click:** "Next" (for the free domain)
4. **Select Python version:** "Python 3.10"
5. **Select framework:** "Flask"
6. **For Python file path:** Enter `/home/yourusername/arbour_book_swiper/app.py`
7. **Click:** "Next" until finished

---

### STEP 5: Configure WSGI File (5 minutes)

1. **Still in "Web" tab**, scroll to **"Code"** section
2. **Click on the "WSGI configuration file"** link (it looks like `/var/www/yourusername_pythonanywhere_com_wsgi.py`)
3. **Delete all the content** in the file
4. **Replace with this code:**

```python
import sys
import os

# Add your project directory to the sys.path
project_home = '/home/yourusername/arbour_book_swiper'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# Set environment variables if needed
os.environ['PYTHONPATH'] = project_home

# Activate virtual environment
activate_this = '/home/yourusername/arbour_book_swiper/venv/bin/activate_this.py'
if os.path.exists(activate_this):
    exec(open(activate_this).read(), {'__file__': activate_this})

# Import your Flask app
from app import app as application
```

5. **⚠️ IMPORTANT:** Replace `yourusername` with your actual PythonAnywhere username (4 places)
6. **Click:** "Save" (top right)

---

### STEP 6: Configure Virtual Environment (2 minutes)

1. **Still in "Web" tab**, scroll to **"Virtualenv"** section
2. **Click:** "Enter path to a virtualenv"
3. **Enter:** `/home/yourusername/arbour_book_swiper/venv`
4. **Click:** the checkmark to save

---

### STEP 7: Configure Static Files (2 minutes)

1. **Still in "Web" tab**, scroll to **"Static files"** section
2. **Click:** "Enter URL" and "Enter path"
3. **Add these mappings:**

| URL | Directory |
|-----|-----------|
| `/static/` | `/home/yourusername/arbour_book_swiper/static/` |
| `/models/` | `/home/yourusername/arbour_book_swiper/models/` |

4. **Click checkmarks** to save each one

---

### STEP 8: Reload and Test! (1 minute)

1. **Scroll to the top** of the "Web" tab
2. **Click the big green "Reload" button**
3. **Wait 10-20 seconds**
4. **Click on your URL:** `yourusername.pythonanywhere.com`

**🎉 Your app should now be LIVE!**

---

## 🔧 Troubleshooting

### Issue: "ImportError" or "ModuleNotFoundError"

**Solution:**
1. Go to "Consoles" → Open your Bash console
2. Run:
```bash
cd ~/arbour_book_swiper
source venv/bin/activate
pip install flask firebase-admin pandas numpy joblib scikit-learn
```
3. Check installed packages: `pip list`
4. Reload the web app

---

### Issue: "Error loading model files"

**Solution:**
1. Make sure `models/` folder was uploaded with both files:
   - `book_data_processed.joblib`
   - `similarity_matrix.joblib`
2. Go to "Files" tab and verify they exist
3. Check file permissions in Bash console:
```bash
cd ~/arbour_book_swiper
ls -lh models/
```

---

### Issue: "Application Error" or 500 Error

**Solution:**
1. Click "Web" tab
2. Scroll to "Log files"
3. Click on "Error log" to see what went wrong
4. Common fixes:
   - Wrong username in WSGI file
   - Virtual environment path incorrect
   - Missing dependencies
   - Wrong file paths

---

### Issue: Firebase Authentication Not Working

**Solution:**
1. Make sure `serviceAccountKey.json` was uploaded
2. Check file path in `firebase_dal.py`:
```bash
cd ~/arbour_book_swiper
cat firebase_dal.py | grep serviceAccountKey
```

---

## 📊 Checking Logs

**Error Log:**
- Web tab → Log files → Error log
- Shows Python errors and stack traces

**Server Log:**
- Web tab → Log files → Server log
- Shows all requests to your app

**Access Log:**
- Web tab → Log files → Access log
- Shows who visited your site

---

## 🔄 Updating Your App

Whenever you make changes:

1. **Upload changed files** via "Files" tab
2. **Go to "Web" tab**
3. **Click "Reload"** button
4. **Test your changes**

---

## 📂 Your File Structure Should Look Like:

```
/home/yourusername/
└── arbour_book_swiper/
    ├── app.py
    ├── firebase_dal.py
    ├── train_model.py
    ├── requirements.txt
    ├── serviceAccountKey.json
    ├── models/
    │   ├── book_data_processed.joblib
    │   └── similarity_matrix.joblib
    ├── templates/
    │   ├── index.html
    │   ├── homepage.html
    │   ├── preferences.html
    │   ├── recommendation.html
    │   ├── liked.html
    │   ├── search.html
    │   └── ... (all other HTML files)
    ├── static/
    │   ├── css/
    │   ├── js/
    │   └── images/
    └── venv/
        └── ... (virtual environment files)
```

---

## 💡 Pro Tips

1. **Bookmark your error log** - you'll check it often while debugging
2. **Use the Bash console** to test Python code before uploading
3. **Always click "Reload"** after making changes
4. **Free tier limitations:**
   - 512 MB disk space
   - 1 web app
   - Always-on (no sleep!)
   - No custom domain (use username.pythonanywhere.com)

---

## 🎯 Quick Command Reference

```bash
# Navigate to project
cd ~/arbour_book_swiper

# Activate virtual environment
source venv/bin/activate

# Install new package
pip install package_name

# Check Python version
python --version

# List files
ls -lh

# Check disk usage
du -sh *

# View file contents
cat filename.py

# Edit file (simple editor)
nano filename.py
```

---

## ✅ Checklist

Before going live, verify:

- [ ] All files uploaded to `/home/yourusername/arbour_book_swiper/`
- [ ] Virtual environment created and activated
- [ ] All dependencies installed (`pip list` shows them)
- [ ] WSGI file configured with correct paths
- [ ] Virtual environment path set in Web tab
- [ ] Static files configured
- [ ] Web app reloaded
- [ ] Error log shows no errors
- [ ] Can access site at `yourusername.pythonanywhere.com`

---

## 🆘 Still Having Issues?

1. **Check the error log** (Web tab → Log files → Error log)
2. **Verify all paths** in WSGI file match your username
3. **Test locally first:** Your app runs fine on your Mac, right?
4. **PythonAnywhere Help:** https://help.pythonanywhere.com
5. **Forums:** https://www.pythonanywhere.com/forums/

---

## 🎉 Success!

Once deployed, your site will be at:
**`https://yourusername.pythonanywhere.com`**

Share it with friends! It's live 24/7 with no sleep!

**Free tier is perfect for:**
- Personal projects
- Demos
- Learning
- Portfolio sites
- Small applications

---

**Ready to deploy? Follow the steps above! 🚀**
