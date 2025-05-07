# Environment Variables Configuration Guide

This document provides detailed instructions for setting up environment variables for the Used Car Lead Generation Agent. Proper configuration is essential for connecting to external services and ensuring the application functions correctly.

## Quick Start

1. Copy `.env.template` to a new file named `.env` in the project root.
2. Replace the placeholder values with your actual credentials for initial setup.
3. For development without real API credentials, you can use the `--mock` flag when running the agent (if applicable).
4. Once the application is running, many of these settings can be viewed and updated via the web interface under "Settings" > "Manage Environment Variables".

## Managing Settings: `.env` File vs. Web Interface

Environment variables are primarily managed in two ways:

1.  **Directly in the `.env` file:** This is necessary for the initial setup of the application, especially for variables required before the web server can even start (e.g., `FLASK_SECRET_KEY`, potentially database connection strings if they were used differently).
    All variables used by the application *can* be set here.

2.  **Via the Web Interface (`/env-settings` page):** A curated set of environment variables, defined in `managers.config_manager.CONFIGURABLE_SETTINGS`, can be viewed and modified through the application's web UI once it's running. This is the recommended way to adjust these specific settings post-deployment as it provides descriptions, type-specific inputs, and validation.
    *   Changes made in the UI will directly update the `.env` file.
    *   Variables not listed in `CONFIGURABLE_SETTINGS` must still be managed directly in the `.env` file.

## Required vs. Optional Variables

This distinction primarily applies to the initial setup via the `.env` file. The web interface will display all settings that have been made configurable through `managers.config_manager.py`.

### Required Variables
These variables are necessary for basic functionality:

- `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`: Required for SMS functionality
- `CLIENT_EMAIL`, `CLIENT_PHONE_NUMBER`: Required for client notifications
- `GOOGLE_SHEET_ID`: Required for data storage

### Optional Variables
These variables enable additional features but are not required for basic operation:

- Email configuration (`EMAIL_*`): For email notifications to clients
- Thryv CRM configuration (`THRYV_*`): For CRM integration
- Web interface configuration (`WEB_*`): For the optional web dashboard

## Detailed Configuration Guide

### Twilio Configuration (Required)

```
TWILIO_ACCOUNT_SID="your_twilio_sid"
TWILIO_AUTH_TOKEN="your_twilio_auth_token"
TWILIO_PHONE_NUMBER="your_twilio_phone_number"
```

**How to obtain:**
1. Sign up for a Twilio account at [twilio.com](https://www.twilio.com)
2. Navigate to your Dashboard to find your Account SID and Auth Token
3. Purchase a phone number or use a trial number (ensure it has SMS capabilities)

**Format:** 
- Account SID and Auth Token are alphanumeric strings
- Phone number must be in E.164 format (e.g., `+18085551234`)

### Client Contact Information (Required)

```
CLIENT_EMAIL="client_email@example.com"
CLIENT_PHONE_NUMBER="+18085551234"
```

**Format:**
- Email should be a valid email address
- Phone number must be in E.164 format (with country code)

### Email Configuration (Optional)

```
EMAIL_HOST="smtp.gmail.com"
EMAIL_PORT=587
EMAIL_USERNAME="your_email@example.com"
EMAIL_PASSWORD="your_email_password"
EMAIL_FROM="your_email@example.com"
```

**Notes:**
- For Gmail, you'll need to create an "App Password" if you have 2-factor authentication enabled
- Common SMTP settings:
  - Gmail: Host=`smtp.gmail.com`, Port=`587`
  - Outlook: Host=`smtp-mail.outlook.com`, Port=`587`
  - Yahoo: Host=`smtp.mail.yahoo.com`, Port=`587`

### Scraping Configuration (Required)

```
CRAIGSLIST_URLS=["https://honolulu.craigslist.org/search/cta", "https://hawaii.craigslist.org/search/cta"]
FACEBOOK_MARKETPLACE_URLS="https://www.facebook.com/marketplace/honolulu/vehicles/,https://www.facebook.com/marketplace/maui/vehicles/"
MIN_VEHICLE_YEAR=2018
SCRAPE_INTERVAL_HOURS=4
```

**Notes:**
- Craigslist URLs should be JSON-formatted array of search result pages
- Facebook Marketplace URLs should be comma-separated
- Minimum vehicle year filters out older vehicles
- Scrape interval determines how frequently the agent runs (in hours)

### Google Sheets Configuration (Required)

```
GOOGLE_SHEET_ID="your_google_sheet_id"
```

**How to obtain:**
1. Create a new Google Sheet or use an existing one
2. Get the Sheet ID from the URL: `https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit`
3. Create a service account:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project
   - Enable the Google Sheets API
   - Create a service account
   - Download the credentials JSON file
   - Save it as `credentials.json` in the project root

**Important:** Share your Google Sheet with the service account email address (which looks like `something@project-id.iam.gserviceaccount.com`)

### Thryv CRM Configuration (Optional)

```
THRYV_API_KEY="your_thryv_api_key"
THRYV_ACCOUNT_ID="your_thryv_account_id"
```

**How to obtain:**
1. Contact your Thryv account representative for API credentials
2. Request an API key and your account identifier

### Web Interface Configuration (Optional)

```
WEB_USERNAME="admin"
WEB_PASSWORD="secure_password"
WEB_PORT=5000
```

**Notes:**
- Choose a secure password for the web interface
- Default port is 5000, but can be changed if needed
- Web interface provides a dashboard for monitoring the agent's activity

## Development Without Real Credentials

For development and testing without actual API credentials:

1. Fill in placeholder values in your `.env` file for initial startup.
2. Run the agent with the `--mock` flag (if available in `main_agent.py`): `python main_agent.py --mock`.
3. Alternatively, use the web interface to set mock or placeholder values for the configurable settings if the application can start with minimal initial `.env` values.

This will use mock services instead of connecting to real APIs. You can also use `--dry-run` to preview what would happen without making any changes.

## Testing Your Configuration

To verify your configuration without running the full agent:

```bash
python deploy.py --skip-deps --skip-test
```

This will validate your environment variables and configurations without installing dependencies or running tests.

## Troubleshooting

- **"Authentication failed" errors:** Check your API credentials and ensure they are correctly entered in the `.env` file
- **"No such file or directory" errors:** Make sure you have the `credentials.json` file for Google Sheets in the correct location
- **Twilio errors:** Verify that your Twilio account is active and has sufficient credit

For more assistance, check the logs in the `logs/` directory or run with increased logging: `export LOG_LEVEL=DEBUG` before running the agent. 