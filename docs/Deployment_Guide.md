# Deployment Guide: Used Car Lead Generation Agent

This guide provides detailed instructions for deploying the Used Car Lead Generation Agent, both for development/testing and production environments.

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git (for cloning the repository)
- Operating System: Windows, macOS, or Linux
- Access to required API services:
  - Twilio account (for SMS)
  - Google account with Sheets API enabled
  - Thryv CRM account (optional)
  - Email account with SMTP access (for notifications)

## Development Environment Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd carfinderai
```

### 2. Create a Virtual Environment

#### Windows:
```powershell
python -m venv venv
venv\Scripts\activate
```

#### macOS/Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy the template file and edit it with your configuration:

```bash
cp .env.template .env
```

Edit `.env` with your preferred text editor. For development, you can use mock values:

```
# Twilio Configuration (mock for development)
TWILIO_ACCOUNT_SID="ACmockaccount123456789"
TWILIO_AUTH_TOKEN="mockauthtoken123456789"
TWILIO_PHONE_NUMBER="+12345678901"

# Client Contact Information
CLIENT_EMAIL="your-email@example.com"
CLIENT_PHONE_NUMBER="+19876543210"

# Other settings...
```

### 5. Run in Development Mode

The agent can be run in development mode using mock services, which simulate external APIs without making actual calls:

```bash
python main_agent.py --mock
```

To only log actions without executing them (dry run):

```bash
python main_agent.py --mock --dry-run
```

### 6. Run Tests

Execute the tests to verify functionality:

```bash
python -m unittest discover tests
```

Or run a specific test:

```bash
python -m unittest tests.test_main_agent
```

## Production Deployment

For production deployment, you'll need actual API credentials and a server or cloud environment. The included `deploy.py` script helps automate the deployment process.

### 1. Prepare Production Configuration

Edit the `.env` file with real production credentials:

```
# Twilio Configuration
TWILIO_ACCOUNT_SID="your_actual_sid"
TWILIO_AUTH_TOKEN="your_actual_token"
TWILIO_PHONE_NUMBER="your_actual_phone_number"

# Google Sheets Configuration
GOOGLE_SHEET_ID="your_actual_sheet_id"

# Other settings...
```

Make sure to place your Google Sheets API `credentials.json` file in the root directory.

**Note on Post-Deployment Configuration:** Once the application is deployed and running with this initial `.env` configuration, many of the application's operational parameters (e.g., `MIN_VEHICLE_YEAR`, `LOG_LEVEL`, API keys if made configurable) can be viewed and updated via the web interface. Navigate to "Settings" and then "Manage Environment Variables". This allows for easier adjustments without directly editing the `.env` file on the server for these specific, pre-defined settings.

### 2. Run the Deployment Script

```bash
python deploy.py
```

This script will:
- Check your environment
- Install dependencies
- Validate configuration
- Set up a scheduler configuration
- Create startup scripts
- Run a test execution

If you want to skip certain steps:

```bash
python deploy.py --skip-deps --skip-test
```

### 3. Schedule Periodic Execution

#### Windows (Task Scheduler):

1. Open Task Scheduler
2. Create a Basic Task
3. Name it "Car Finder Agent"
4. Set the trigger to run daily
5. Set the action to start a program
6. Program/script: `path\to\run_agent.bat`
7. Start in: `path\to\project\directory`

#### Linux/macOS (Cron):

Edit your crontab:

```bash
crontab -e
```

Add the line (to run every 4 hours, for example):

```
0 */4 * * * cd /path/to/carfinderai && ./run_agent.sh
```

### 4. Server Deployment Options

#### Option 1: Simple VPS/Server

- Rent a VPS (DigitalOcean, Linode, AWS EC2, etc.)
- Install Python and required packages
- Clone the repository and follow the production deployment steps above
- Set up cron or systemd to run the agent periodically

#### Option 2: PythonAnywhere

- Sign up for a PythonAnywhere account
- Upload the code via their web interface or Git
- Configure the `.env` file
- Use the PythonAnywhere task scheduler to run the agent periodically

#### Option 3: Heroku

- Install the Heroku CLI
- Create a new Heroku app
- Add the environment variables in Heroku's config
- Create a Procfile for the web interface
- Use Heroku Scheduler add-on to run the agent periodically

## Monitoring and Maintenance

### Logging

Logs are stored in the `logs/` directory. For production, consider:

- Setting up log rotation
- Configuring alerts for critical errors
- Using a monitoring service like Sentry

### Updates and Maintenance

- Regularly check for new versions of dependencies
- Monitor scraper performance as websites may change
- Update API credentials as needed, either directly in the `.env` file or via the web interface for configurable settings.

## Troubleshooting

### Common Issues

1. **API Authentication Failures**
   - Check that credentials in `.env` are correct
   - Verify API keys haven't expired

2. **Scraper Not Finding Listings**
   - Website structure may have changed
   - Run with `--mock` flag to test other components

3. **Scheduler Not Running**
   - Check system logs for cron or Task Scheduler
   - Ensure correct paths in scheduler configuration

For detailed debugging, run with higher log levels:

```bash
python main_agent.py --mock --debug
```

## Security Considerations

- Never commit `.env` or `credentials.json` to version control
- Use environment variables for sensitive information
- Consider using a secrets manager for production
- Regularly rotate API keys and credentials
- Implement IP restrictions if supported by your APIs

## Support and Resources

- Project Documentation: `docs/` directory
- Issue Tracker: [GitHub Issues](https://github.com/your-repo/issues)
- Twilio API: [Twilio Docs](https://www.twilio.com/docs)
- Google Sheets API: [Google Sheets API Docs](https://developers.google.com/sheets/api) 