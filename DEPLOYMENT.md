# 🚀 Spendly - Deployment Guide (Render)

## Prerequisites
- GitHub account (to push your code)
- Render account (free tier available at https://render.com)

---

## Step 1: Prepare Your Project

✅ **Already Done:**
- Updated `config.py` to support PostgreSQL
- Updated `requirements.txt` with `psycopg2-binary` and `gunicorn`
- Created `Procfile` for Render
- Updated `run.py` for production environment

---

## Step 2: Push to GitHub

1. **Initialize Git** (if not already done):
   ```bash
   git init
   git add .
   git commit -m "Initial commit - ready for Spendly deployment"
   ```

2. **Create GitHub Repository:**
   - Go to https://github.com/new
   - Create a new repository named `Spendly`
   - Follow GitHub's instructions to push your code:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/Spendly.git
   git branch -M main
   git push -u origin main
   ```

---

## Step 3: Deploy to Render

### Option A: Using `render.yaml` (Recommended - Auto-setup)

1. **Go to Render Dashboard:**
   - Visit https://dashboard.render.com

2. **Click "New +"** → **Blueprint**

3. **Connect GitHub:**
   - Authorize Render to access your GitHub account
   - Select the `Spendly` repository

4. **Select Branch:** `main`

5. **Render will automatically:**
   - Read `render.yaml`
   - Create a PostgreSQL database
   - Deploy the Flask app
   - Set environment variables
   - Assign a free `.onrender.com` domain

6. **Wait for Deployment** (2-5 minutes)

### Option B: Manual Setup (If `render.yaml` doesn't work)

1. **Go to Render Dashboard:** https://dashboard.render.com

2. **Create PostgreSQL Database:**
   - Click "New +" → "PostgreSQL"
   - Name: `spendly-db`
   - Select Free tier
   - Create → Copy the **Internal Database URL**

3. **Deploy Web Service:**
   - Click "New +" → "Web Service"
   - Connect your GitHub `Spendly` repository
   - Configure:
     - **Name:** `spendly-app`
     - **Runtime:** Python 3
     - **Build Command:** `pip install -r backend/requirements.txt`
     - **Start Command:** `cd backend && gunicorn app:app`
     - **Plan:** Free

4. **Add Environment Variables:**
   - Go to "Environment" tab
   - Add:
     ```
     FLASK_ENV = production
     SECRET_KEY = (auto-generate strong key)
     DATABASE_URL = (paste PostgreSQL internal URL from step 2)
     ```

5. **Deploy** → Wait for success

---

## Step 4: Initialize the Database

After deployment, the app will start but the database needs to be initialized:

1. **Access Render Shell:**
   - Go to your Render service
   - Click "Shell" tab

2. **Create tables:**
   ```bash
   cd backend
   python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all(); print('Database initialized!')"
   ```

3. **Your app is now live!** ✅

---

## Step 5: Post-Deployment

### Access Your App
- Your app will be available at: `https://spendly-app.onrender.com`
- Login with your Render-deployed credentials

### Monitor Logs
- Go to Render dashboard → Your service
- View "Logs" tab for any errors

### Update Code
- Push changes to GitHub
- Render automatically redeploys on push

---

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| `Module not found` errors | Check `requirements.txt` includes all packages |
| Database connection error | Verify `DATABASE_URL` env var is set correctly |
| Port binding error | Ensure app listens on port from `os.environ.get('PORT')` |
| Static files not loading | Check `app/static/` is in correct location |

---

## ✅ Deployment Checklist

- [ ] Pushed code to GitHub
- [ ] Created Render account
- [ ] Deployed using `render.yaml` OR manually created PostgreSQL + Web Service
- [ ] Added environment variables (SECRET_KEY, DATABASE_URL)
- [ ] Ran `db.create_all()` in Render Shell
- [ ] Verified app loads at `.onrender.com` URL
- [ ] Tested login/registration functionality
- [ ] Checked logs for errors

---

## 📊 Free Tier Limits (Render)

- **Web Service:** 750 hours/month (unlimited for 1 active service)
- **PostgreSQL:** 100MB storage, 25 connections max
- **Auto-sleep:** Services spin down after 15 min of inactivity (restart on request)

---

## 💡 Next Steps

1. **Custom Domain:** Add your domain in Render settings (paid feature)
2. **Email Notifications:** Configure SMTP for password resets
3. **Backups:** Enable PostgreSQL automated backups
4. **Monitoring:** Set up alerts for deployment failures

---

## 📞 Support

- **Render Docs:** https://render.com/docs
- **Flask Deployment:** https://flask.palletsprojects.com/deployment/
- **PostgreSQL:** https://www.postgresql.org/docs/

