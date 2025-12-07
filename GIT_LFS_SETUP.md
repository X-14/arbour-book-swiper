# Git LFS Setup for Large Model Files

## Problem
Your `similarity_matrix.joblib` file is 104MB, but GitHub's limit is 100MB per file.

## Solution: Git Large File Storage (LFS)

### Option 1: Install and Configure Git LFS

```bash
# Install Git LFS (macOS)
brew install git-lfs

# Initialize Git LFS in your repository
cd "/Users/xavierjudge/Desktop/Arbour Book Swiper/Anti Gravity Recomendation"
git lfs install

# Track large joblib files
git lfs track "models/*.joblib"

# Add the .gitattributes file that tracks LFS files
git add .gitattributes

# Add your models
git add models/

# Commit
git commit -m "Add models with Git LFS"

# Push (LFS will handle large files)
git push origin main
```

### Option 2: Regenerate Models on Deployment

Instead of including the models in Git, regenerate them during the build process on Render.

**Create a build script:**

1. Update `render.yaml`:
```yaml
services:
  - type: web
    name: arbour-book-swiper
    env: python
    buildCommand: pip install -r requirements.txt && python train_model.py
    startCommand: gunicorn app:app
```

2. Make sure `train_model.py` and your data files are in the repository

**Pros:** No large file issues
**Cons:** Longer build time (but only on first deploy)

### Option 3: Use External Storage

Store models in:
- Google Cloud Storage
- AWS S3
- Dropbox/Google Drive (with public URLs)

Download them at app startup.

## Recommendation

**Use Option 1 (Git LFS)** if you want the simplest solution.  
**Use Option 2** if builds are fast and you have the training data.  
**Use Option 3** if you want more control.

## Quick Commands

### Check file sizes:
```bash
ls -lh models/
```

### See which files are large:
```bash
find . -type f -size +50M
```

### Install Git LFS (macOS):
```bash
brew install git-lfs
```

### Configure LFS:
```bash
git lfs install
git lfs track "models/*.joblib"
git add .gitattributes models/
git commit -m "Track large files with LFS"
```

---

**After setting up LFS, continue with the deployment steps in QUICKSTART.md!**
