# Car Finder AI Web Interface

This is the private web interface for the Used Car Lead Generation Agent. It provides a secure dashboard for viewing and managing car leads scraped from Craigslist and Facebook Marketplace.

## Features

- **Secure Authentication**: Password-protected access to the dashboard.
- **Leads Dashboard**: View all scraped car leads with sorting and filtering capabilities.
- **Settings Page**: View current configuration settings.
- **Documentation**: Access project documentation and help resources.

## Setup and Installation

### Prerequisites

- Python 3.9 or higher
- All dependencies from the main `requirements.txt` file in the project root

### Configuration

The web interface uses environment variables for configuration. You can set these in your `.env` file:

```
# Web UI Authentication
FLASK_SECRET_KEY=your_secure_random_key
WEB_UI_USERNAME=your_username
WEB_UI_PASSWORD=your_password

# Web Server Configuration
FLASK_DEBUG=False  # Set to True for development
PORT=5000  # Web server port
```

### Running the Web Interface

1. From the project root directory, activate your virtual environment:
   ```
   venv\Scripts\activate  # Windows
   source venv/bin/activate  # Linux/macOS
   ```

2. Run the Flask application:
   ```
   python -m web_interface.app
   ```
   
   Or directly:
   ```
   python web_interface/app.py
   ```

3. Access the web interface in your browser at:
   ```
   http://localhost:5000
   ```

4. Log in using the credentials defined in your `.env` file (or the defaults if not set).

## Usage Guide

### Leads Dashboard

- **View Leads**: The main dashboard displays all vehicle leads.
- **Sort**: Click on any column header to sort by that field.
- **Filter**: Use the search box to filter leads by any keyword.
- **Details**: Click the "Details" button to view complete information about a lead.
- **View Listing**: Click "View" to open the original listing in a new tab.

### Settings Page

The Settings page provides a read-only view of the current configuration, including:
- Client notification contact details
- Scraping frequency
- API integration statuses

### Documentation Page

Access helpful documentation resources, including:
- Project specification
- Technical design document
- User guide
- Quick reference for terms and status indicators

## Development

To modify the web interface:
1. Templates are located in `web_interface/templates/`
2. Custom styles are in `web_interface/static/css/style.css`
3. The main application logic is in `web_interface/app.py`

## Security Notes

- Always use HTTPS in production
- Regularly change the admin password
- The web interface is intended for private use only, not public access 