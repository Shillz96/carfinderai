# Project Structure and Dependencies

## Directory Structure

```
carfinderai/
├── docs/                   # Documentation
├── managers/               # Business logic managers
│   ├── messaging_manager.py    # Handles SMS communication
│   ├── data_manager.py         # Handles Google Sheets and data processing (Assumed from other docs)
│   ├── notification_manager.py # Handles client notifications (Assumed from other docs)
│   ├── thryv_integrator.py     # Handles Thryv CRM integration (Assumed from other docs)
│   └── config_manager.py       # Manages application configuration from .env file via UI
├── scrapers/               # Web scrapers
│   └── craigslist_scraper.py   # Scrapes Craigslist listings
├── tests/                  # Unit tests
│   ├── test_craigslist_scraper.py
│   └── test_messaging_manager.py
├── utils/                  # Utility functions
│   ├── config.py           # Configuration loading
│   └── logger.py           # Logging setup
├── web_interface/          # Web UI (Phase 2)
│   ├── app.py              # Main Flask application for the web interface
│   ├── templates/
│   │   ├── base.html       # Base template for all UI pages
│   │   ├── leads.html      # Page to display leads
│   │   ├── settings.html   # General settings page, links to env settings
│   │   ├── env_settings.html # Page for managing .env configuration variables
│   │   └── documentation.html # Page for documentation links
│   └── static/
│       └── css/
│           └── style.css   # Custom CSS styles
├── .env                    # Environment variables (not in version control)
├── .env.template           # Template for environment variables
├── .gitignore              # Git ignore file
├── main.py                 # Main application entry point
└── requirements.txt        # Python dependencies
```

## Core Components

### Scrapers

The `scrapers/` directory contains specialized scrapers for different websites:

- `craigslist_scraper.py`: Scrapes used car listings from Craigslist

Scrapers handle:
- Fetching web pages
- Parsing HTML content
- Extracting relevant vehicle information
- Filtering listings based on criteria

### Managers

The `managers/` directory contains business logic:

- `messaging_manager.py`: Manages SMS communication with sellers
  - Uses Twilio for sending SMS
  - Parses phone numbers from listings
  - Creates templated messages
- `data_manager.py` (Assumed): Manages data storage in Google Sheets, data cleaning, and duplicate checks.
- `notification_manager.py` (Assumed): Manages sending email and SMS notifications to the client.
- `thryv_integrator.py` (Assumed): Manages integration with Thryv CRM.
- `config_manager.py`: Manages application settings from the `.env` file, providing an interface for these settings to be updated via the web UI. It defines which settings are configurable, their types, and descriptions, and handles reading/writing to the `.env` file.

### Utilities

The `utils/` directory contains shared functionality:

- `config.py`: Loads and validates configuration from `.env` files
- `logger.py`: Sets up logging to files and console

## Dependencies

### Core Dependencies

- `requests`: For making HTTP requests to websites
- `beautifulsoup4`: For parsing HTML and extracting data
- `python-dotenv`: For loading environment variables
- `twilio`: For sending SMS messages to sellers
- `APScheduler`: For scheduling recurring scraper runs

### Development Dependencies

- `unittest`: For unit testing
- `mock`: For mocking external services in tests

## Configuration

The application is configured through environment variables, loaded from a `.env` file:

- Twilio credentials for SMS
- Target websites for scraping
- Filtering criteria for vehicles
- Scheduling intervals

## Extending the Project

### Adding a New Scraper

1. Create a new file in the `scrapers/` directory
2. Implement the scraper class following the pattern of `CraigslistScraper`
3. Add configuration options to `.env.template`
4. Update `main.py` to use the new scraper
5. Create unit tests for the new scraper

### Adding New Functionality

1. Determine if the functionality belongs in an existing component or needs a new one
2. Add appropriate methods/classes
3. Update `main.py` to use the new functionality
4. Add unit tests for the new functionality
5. Update documentation 