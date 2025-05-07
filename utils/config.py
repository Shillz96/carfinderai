import os
import json
from dotenv import load_dotenv
from utils.logger import setup_logger

# Set up logger
logger = setup_logger('config')

def load_config():
    """
    Load configuration from .env file
    
    Returns:
        dict: Configuration dictionary
    """
    # Load .env file
    load_dotenv()
    
    # Required configuration keys
    required_keys = [
        'TWILIO_ACCOUNT_SID',
        'TWILIO_AUTH_TOKEN',
        'TWILIO_PHONE_NUMBER',
        'CLIENT_EMAIL',
        'CLIENT_PHONE_NUMBER',
        'MIN_VEHICLE_YEAR',
        'GOOGLE_SHEET_ID'
    ]
    
    # Create config dictionary
    config = {
        'twilio': {
            'account_sid': os.getenv('TWILIO_ACCOUNT_SID'),
            'auth_token': os.getenv('TWILIO_AUTH_TOKEN'),
            'phone_number': os.getenv('TWILIO_PHONE_NUMBER')
        },
        'client': {
            'email': os.getenv('CLIENT_EMAIL'),
            'phone_number': os.getenv('CLIENT_PHONE_NUMBER')
        },
        'scraper': {
            'craigslist_urls': json.loads(os.getenv('CRAIGSLIST_URLS')),
            'min_vehicle_year': int(os.getenv('MIN_VEHICLE_YEAR', 2018)),
            'scrape_interval_hours': int(os.getenv('SCRAPE_INTERVAL_HOURS', 4))
        },
        'google_sheets': {
            'sheet_id': os.getenv('GOOGLE_SHEET_ID')
        },
        'thryv': {
            'api_key': os.getenv('THRYV_API_KEY'),
            'account_id': os.getenv('THRYV_ACCOUNT_ID')
        },
        'web': {
            'username': os.getenv('WEB_USERNAME', 'admin'),
            'password': os.getenv('WEB_PASSWORD', 'password'),
            'port': int(os.getenv('WEB_PORT', 5000))
        }
    }
    
    # Validate required configuration
    missing_keys = []
    for key in required_keys:
        if not os.getenv(key):
            missing_keys.append(key)
    
    if missing_keys:
        logger.warning(f"Missing required configuration keys: {', '.join(missing_keys)}")
    
    return config 