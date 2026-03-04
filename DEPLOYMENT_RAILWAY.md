# BATTLEZONE RAILWAY DEPLOYMENT GUIDE

## Overview

This guide covers deploying the Battlezone Flask application to Railway.

## Application Status

✅ **Application is working correctly** on Windows and will work on Railway (Linux)

- Flask development server: ✅ Working
- Database connectivity: ✅ Configured (SQLite local, PostgreSQL on Railway)  
- All modules: ✅ Loading successfully
- Gunicorn compatibility: ⚠️ Works on Linux only (Railway), not on Windows

## Local Development

### Running the Application Locally

```bash
# Navigate to project directory
cd d:\Backup_Sistema\Flask\battlezone_flask

# Activate virtual environment
.venv\Scripts\activate

# Install dependencies (if not already installed)
pip install -r requirements.txt

# Start the development server
python start.py
```

The app will start on `http://localhost:5000`

### Troubleshooting Local Development

If you don't see startup output immediately:
- This is normal - Flask in debug mode takes 2-3 seconds to start
- Once started, you should see: "Running on http://127.0.0.1:5000"
- Access the app in your browser

## Railway Deployment

### Prerequisites

1. Railway account (https://railway.app)
2. Git repository connected to Railway
3. PostgreSQL add-on enabled in Railway

### Step 1: Configure Environment Variables on Railway

Go to your Railway project settings and add:

```
SECRET_KEY=<your-secret-key>
FLASK_ENV=production
DATABASE_URL=<automatically set by Railway when PostgreSQL is added>
```

### Step 2: Verify Procfile

The root `Procfile` should contain:

```
web: gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 60 --access-logfile - --error-logfile - wsgi:application
```

This file tells Railway how to start the application using Gunicorn (WSGI server for Linux).

### Step 3: Verify WSGI Entry Point

The `wsgi.py` file should be a simple entry point:

```python
from app import app
application = app
```

This is required for Gunicorn to find the Flask application.

### Step 4: Python Version

Railway will use the Python version specified in:
- `runtime.txt` (should contain `python-3.11.7` or similar)
- `Dockerfile` (if using custom build)

### Step 5: Deploy

Push to your connected Git repository:

```bash
git add -A
git commit -m "Deploy to Railway"
git push origin main
```

Railway will automatically:
1. Pull the code
2. Install dependencies from `requirements.txt`
3. Run the command in `Procfile`
4. Start the application with Gunicorn

### Step 6: Monitor Deployment

In Railway dashboard:
1. Go to Deployments tab
2. Watch the build log
3. Once deployed, you'll see "Deployment Successful"
4. Click on the deployment URL to access your app

## Common Issues & Solutions

### Issue: 502 Bad Gateway

**Possible causes:**
1. App not starting - check logs
2. DATABASE_URL not set - add PostgreSQL add-on
3. SECRET_KEY not configured - add to environment variables

**Solution:**
1. Check Railway logs: `railway logs`
2. Verify environment variables are set
3. Ensure `wsgi.py` exists and is correct
4. Ensure `Procfile` exists in root directory

### Issue: Database Connection Errors

**Solution:**
1. Add PostgreSQL add-on to Railway project
2. Wait for DATABASE_URL to appear in environment
3. Redeploy the application
4. Check database connection in app logs

### Issue: Module Not Found (gunicorn, etc.)

**Solution:**
1. Ensure all dependencies are in `requirements.txt`
2. Verify `requirements.txt` doesn't have platform-specific packages
3. Gunicorn works on Linux only - Railway uses Linux containers

### Issue: Port Binding Error

**Solution:**
1. Railway sets `$PORT` environment variable automatically
2. Procfile must use `--bind 0.0.0.0:$PORT`
3. Don't hardcode port 5000 in Procfile

## File Structure for Deployment

```
battlezone_flask/
├── app.py                 # Main Flask application
├── wsgi.py               # WSGI entry point for Gunicorn (REQUIRED)
├── Procfile              # Railway-specific startup command (REQUIRED)
├── runtime.txt           # Python version (REQUIRED)
├── requirements.txt      # Python dependencies (REQUIRED)
├── config.py             # Configuration with DATABASE_URL support
├── start.py              # Development server starter
├── seguranca.env         # Environment variables (DON'T commit)
├── seguranca.env.example # Example environment file
├── backend/              # Backend modules
├── frontend/             # Frontend templates and static files
└── instance/             # Database and instance files
```

## Database Initialization on Railway

The first time the app starts on Railway:

1. SQLAlchemy will attempt to create tables
2. If tables don't exist, they'll be created automatically
3. First admin user should be created via admin route or command

To manually create database:
```bash
railway run python -c "from app import app, db; app.app_context().push(); db.create_all(); print('Tables created')"
```

## Performance Optimization

The current Procfile configuration:
- **Workers: 2** - Good balance for small apps
- **Timeout: 60s** - Sufficient for most operations
- **Access log** - Logs all requests (debug purposes)
- **Error log** - Logs all errors

For production optimization:
```
web: gunicorn --bind 0.0.0.0:$PORT --workers 4 --threads 2 --timeout 120 wsgi:application
```

Adjust based on traffic and needs.

## Health Checks

The application includes a Database Health Check module that:
- Verifies database connection every 30 seconds
- Automatically reconnects if connection fails
- Maintains connection pool (10 connections)

No additional configuration needed - this runs automatically.

## Support

For issues:
1. Check Railway dashboard logs
2. Review app.py for initialization errors
3. Verify all environment variables are set
4. Ensure PostgreSQL add-on is enabled
5. Check `seguranca.env` has all required values

## Next Steps

After deploying:
1. Test login functionality
2. Verify database operations
3. Check file uploads work
4. Monitor performance in Railway dashboard
5. Set up error tracking (optional: Sentry)
