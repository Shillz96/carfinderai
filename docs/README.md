# Used Car Lead Generation Agent

A Python-based agent to help a car dealership find leads from used car listings on websites like Craigslist. The agent automatically scrapes listings, contacts sellers, and tracks responses.

## Project Structure

- `scrapers/`: Contains website scrapers for various listing sites
- `managers/`: Contains business logic for messaging, data management, etc.
- `utils/`: Utility functions like logging and configuration
- `tests/`: Unit tests for the application
- `web_interface/`: A web interface for viewing and managing leads (Phase 2)

## Setup Instructions

1. Clone the repository
2. Create a Python virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `.\venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Copy `.env.template` to `.env` and fill in your configuration values
6. Run the application: `python main.py`

## Configuration

The application uses a `.env` file for configuration. Copy the `.env.template` file to `.env` and update the values:

```
# Twilio Configuration
TWILIO_ACCOUNT_SID="your_twilio_sid"
TWILIO_AUTH_TOKEN="your_twilio_auth_token"
TWILIO_PHONE_NUMBER="your_twilio_phone_number"

# Client Contact Information
CLIENT_EMAIL="client_email@example.com"
CLIENT_PHONE_NUMBER="+18085551234"

# Other settings...
```

## Features

### Phase 1 (Current)
- Craigslist listing scraper
- Basic text messaging via Twilio
- Automatic filtering of listings based on year and other criteria

### Phase 2 (Upcoming)
- Web interface for viewing and managing leads
- Integration with Google Sheets for data storage
- Scheduling of automatic scraping runs

### Phase 3 (Future)
- Multiple listing site support
- CRM integration
- Advanced filtering and analysis

## Running Tests

Run the test suite with:

```
cd tests
python -m unittest discover
```

## Development

Please follow these guidelines when contributing:
- Write tests for new features
- Follow PEP 8 style guidelines
- Document new functions and classes
- Update the README with any new dependencies or features

## License

This project is for internal use only. Unauthorized distribution is prohibited. 