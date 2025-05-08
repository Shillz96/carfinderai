# Car Finder AI - Vercel Deployment Guide

This guide provides instructions and key considerations for deploying the Car Finder AI Flask application to Vercel.

## 1. Project Overview for Deployment

-   **Main Application File (Flask Entry Point):** `web_interface/app.py`
    -   This file contains the Flask `app` object and all web routes.
-   **Vercel Configuration:** `vercel.json` (in the project root)
    -   Defines how Vercel builds and routes the application.
-   **Static Files:** Served from `web_interface/static/` (CSS, JavaScript, images).
    -   Routed via `vercel.json`.
-   **Templates:** HTML templates are located in `web_interface/templates/`.
-   **Python Package Structure:**
    -   Ensure `utils/`, `managers/`, and any other custom module directories contain an `__init__.py` file to be recognized as Python packages.

## 2. Vercel Configuration (`vercel.json`)

The `vercel.json` file is crucial for telling Vercel how to deploy this Python Flask application.

Key sections:

-   **`"builds"`**:
    -   Specifies the source file (`"src": "web_interface/app.py"`) and the builder (`"use": "@vercel/python"`).
    -   Sets Python runtime (e.g., `"runtime": "python3.9"`).
-   **`"routes"`**:
    -   A specific route for static files: `{"src": "/static/(.*)", "dest": "/web_interface/static/$1"}`.
    -   A catch-all route for the Flask app: `{"src": "/(.*)", "dest": "web_interface/app.py"}`.
-   **`"env"`**:
    -   `"FLASK_APP": "web_interface.app:app"`: Tells Flask where the `app` object is.
    -   `"PYTHONPATH": "$PYTHONPATH:."`: Adds the project root to the Python path, allowing imports like `from managers. ...` from within `web_interface/app.py`.
    -   `"FLASK_ENV": "production"`: Sets Flask to run in production mode.

## 3. Environment Variables on Vercel (CRITICAL)

Environment variables are used for all configuration and secrets. **Do NOT hardcode secrets in the code.**

-   **How to Set:** Vercel Dashboard -> Your Project (`clean-carfinderai`) -> Settings -> Environment Variables.
-   Changes to environment variables usually require a redeploy to take effect.

### Required Environment Variables:

-   `FLASK_SECRET_KEY`: A long, random, unique string used by Flask for session security.
    -   Generate one using: `python -c "import secrets; print(secrets.token_hex(32))"`
-   `WEB_UI_USERNAME`: Username for accessing the web interface.
-   `WEB_UI_PASSWORD`: Password for the web interface.
    -   *Defaults in code are `admin`/`vercel123` if these are not set, but setting them is highly recommended for security.*

### Service-Specific / Optional Environment Variables:

These depend on the features you are using. The application should ideally handle their absence gracefully.

-   **Google Sheets / OAuth:**
    -   `GOOGLE_CLIENT_SECRET_JSON`: **The entire JSON content** of your `client_secret.json` file (obtained from Google Cloud Console for OAuth 2.0) should be pasted as the value for this variable. This is used for the Google OAuth flow.
    -   `GOOGLE_APPLICATION_CREDENTIALS_JSON`: (Optional, alternative to file-based `user_google_creds.json`) If you store the *user's* OAuth tokens (after they authorize) as an environment variable, this is a common name. Your `ui_config_manager.py` tries to load from this.
    -   `GOOGLE_SHEET_ID`: The ID of the Google Sheet to use.
-   **Twilio (for SMS):**
    -   `TWILIO_ACCOUNT_SID`
    -   `TWILIO_AUTH_TOKEN`
    -   `TWILIO_PHONE_NUMBER`
-   **Thryv CRM:**
    -   `THRYV_API_KEY`
    -   `THRYV_BUSINESS_ID` (or `THRYV_ACCOUNT_ID` as per `utils/config.py`)
-   **Other Application Settings (from `utils/config.py` and `managers/config_manager.py`):**
    -   `CLIENT_EMAIL`
    -   `CLIENT_PHONE_NUMBER`
    -   `MIN_VEHICLE_YEAR`
    -   `CRAIGSLIST_URLS` (as a JSON string, e.g., `["url1", "url2"]`)
    -   `SCRAPE_INTERVAL_HOURS`
    -   `LOG_LEVEL` (e.g., `INFO`, `DEBUG`)
    -   `SCRAPER_REQUEST_TIMEOUT_SECONDS`
    -   `SCRAPER_DELAY_MIN_SECONDS`
    -   `SCRAPER_DELAY_MAX_SECONDS`
    -   `USER_EMAIL_ADDRESS`

## 4. Local Development vs. Vercel Deployment

-   **`.env` File:**
    -   Used for local development to store environment variables. `python-dotenv` loads this.
    -   **NOT used by Vercel at runtime.** Vercel uses the environment variables set in its dashboard.
-   **Read-Only Filesystem on Vercel:**
    -   The `/var/task/` directory where your code is deployed is read-only.
    -   **Your application cannot write or modify files in the project directory at runtime.**
    -   This impacts:
        -   `managers/config_manager.py`: It was modified to not attempt to write to `.env` at import time. The UI for editing these "environment settings" via the web app will not persistently change them on Vercel; use the Vercel dashboard instead.
        -   `utils/ui_config_manager.py`:
            -   `get_ui_settings()` was modified to be read-only. It will load from `ui_settings.json` if that file is part of your deployment. If not, it uses hardcoded defaults.
            -   `save_ui_settings()` and `update_setting()` will fail on Vercel because they try to write to `ui_settings.json`. Dynamic UI settings on Vercel would require using environment variables or a database.
            -   `save_google_oauth_credentials()` and `delete_google_oauth_credentials()` (which manage `user_google_creds.json`) will also fail. User OAuth tokens on Vercel should be managed via the `GOOGLE_APPLICATION_CREDENTIALS_JSON` environment variable or a database.

## 5. Standard Deployment Workflow

1.  Make your code changes locally.
2.  Ensure all necessary `__init__.py` files exist in your module directories (e.g., `utils/`, `managers/`).
3.  Stage your changes: `git add .`
4.  Commit your changes: `git commit -m "Your descriptive commit message"`
5.  Push to your main deployment branch on GitHub/GitLab: `git push origin master` (or your primary branch name).
6.  Vercel will automatically pick up the push and start a new deployment.
7.  Monitor the deployment in the Vercel dashboard.
8.  Test the preview URL provided by Vercel.
9.  If the preview is successful and you want to make it live, promote it to production:
    -   Either via the Vercel dashboard.
    -   Or from your terminal (in the project root): `vercel --prod`

## 6. Troubleshooting Common Issues on Vercel

-   **404 Errors (Not Found):**
    -   Could mean the Flask application failed to start.
    -   Check **Build Logs** on Vercel for `ImportError` or other Python errors during the build phase.
    -   Check **Function (Runtime) Logs** for your `web_interface/app.py` function for any startup crashes (e.g., due to missing environment variables or errors in initialization code).
    -   Ensure `vercel.json` routing is correct.
-   **500 Errors (Internal Server Error):**
    -   The Flask application started but crashed while handling a request.
    -   **Check the Vercel Function (Runtime) Logs.** Look for the full Python `Traceback (most recent call last): ...` which will show the exact error, file, and line number.
-   **`OSError: [Errno 30] Read-only file system`:**
    -   The code attempted to write a file to the project directory at runtime (e.g., `.env`, `ui_settings.json`, `user_google_creds.json`). This is not allowed on Vercel. Adapt code to be read-only or use `/tmp` for temporary files (which don't persist).
-   **Missing Environment Variables:**
    -   Double-check variable names and values in the Vercel dashboard (Settings -> Environment Variables).
    -   Ensure all *required* variables are set. The app might crash or misbehave if they are not.
-   **Module Not Found / `ImportError`:**
    -   Ensure the module is listed in `requirements.txt`.
    -   Ensure `PYTHONPATH` is correctly set in `vercel.json` if needed for your project structure.
    -   Ensure directories that should be packages have an `__init__.py` file.

## 7. Python Dependencies

-   All Python dependencies required by your project must be listed in `requirements.txt` in the project root.
-   Vercel uses this file to install dependencies during the build step.
-   Keep it accurate and commit any changes to it.

---

This guide should serve as a good starting point. You can expand it with more project-specific details as needed. 