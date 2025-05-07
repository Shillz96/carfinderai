"""
Manages UI-specific configurations for the Car Finder Agent.
Settings are stored in a JSON file (ui_settings.json) in the project root.
OAuth credentials are stored in user_google_creds.json.
"""
import json
import os
from .logger import setup_logger
from google.oauth2.credentials import Credentials

logger = setup_logger('ui_config_manager')

# Main UI settings file
SETTINGS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ui_settings.json')
# File to store user's Google OAuth credentials
USER_GOOGLE_CREDS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'user_google_creds.json')
# Path for the client secret file (downloaded from Google Cloud Console)
# This is needed for the OAuth flow initiation.
CLIENT_SECRET_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'client_secret.json')

# Define the scopes required by the application
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Name of the environment variable that will hold the JSON string of the user credentials
GOOGLE_CREDS_JSON_ENV_VAR = "GOOGLE_APPLICATION_CREDENTIALS_JSON"

DEFAULT_SETTINGS = {
    "enable_thryv_crm": True,
    # "google_credentials_configured": False # Removed
}

def get_ui_settings():
    """
    Loads UI settings from ui_settings.json.
    If the file doesn't exist or is invalid, creates it with default settings.

    Returns:
        dict: A dictionary containing UI settings.
    """
    if not os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(DEFAULT_SETTINGS, f, indent=2)
        logger.info(f"Created default UI settings file: {SETTINGS_FILE}")
        return DEFAULT_SETTINGS.copy()
    try:
        with open(SETTINGS_FILE, 'r') as f:
            settings = json.load(f)
            updated = False
            for key, value in DEFAULT_SETTINGS.items():
                if key not in settings:
                    settings[key] = value
                    updated = True
            # Remove obsolete keys
            if "google_credentials_configured" in settings:
                del settings["google_credentials_configured"]
                updated = True

            if updated:
                save_ui_settings(settings) # Save if changes were made (new defaults or removed keys)
            return settings
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding UI settings file {SETTINGS_FILE}: {e}. Creating with defaults.")
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(DEFAULT_SETTINGS, f, indent=2)
        return DEFAULT_SETTINGS.copy()
    except Exception as e:
        logger.error(f"Unexpected error reading UI settings file {SETTINGS_FILE}: {e}. Returning defaults.")
        return DEFAULT_SETTINGS.copy()

def save_ui_settings(settings_data: dict):
    """
    Saves the provided settings data to ui_settings.json.

    Args:
        settings_data (dict): The dictionary of settings to save.

    Returns:
        bool: True if saving was successful, False otherwise.
    """
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings_data, f, indent=2)
        logger.info(f"UI settings saved to {SETTINGS_FILE}")
        return True
    except Exception as e:
        logger.error(f"Error saving UI settings to {SETTINGS_FILE}: {e}")
        return False

def update_setting(key: str, value):
    """
    Updates a single setting in ui_settings.json and saves it.

    Args:
        key (str): The setting key to update.
        value: The new value for the setting.

    Returns:
        bool: True if successful, False otherwise.
    """
    settings = get_ui_settings()
    settings[key] = value
    return save_ui_settings(settings)

def is_crm_enabled():
    """
    Checks if Thryv CRM integration is enabled in the settings.

    Returns:
        bool: True if CRM is enabled, False otherwise.
    """
    return get_ui_settings().get("enable_thryv_crm", True)

# --- Google OAuth Credential Management ---

def save_google_oauth_credentials(credentials: Credentials) -> bool:
    """
    Saves Google OAuth credentials to user_google_creds.json.
    The input 'credentials' object should be from google.oauth2.credentials.
    """
    try:
        # credentials.to_json() creates a JSON string representation of the credentials object
        with open(USER_GOOGLE_CREDS_FILE, 'w') as f:
            f.write(credentials.to_json())
        logger.info(f"Google OAuth credentials saved to {USER_GOOGLE_CREDS_FILE}")
        return True
    except Exception as e:
        logger.error(f"Error saving Google OAuth credentials to {USER_GOOGLE_CREDS_FILE}: {e}")
        return False

def load_google_oauth_credentials() -> Credentials:
    """
    Loads Google OAuth credentials.
    Tries from an environment variable first (for platforms like Vercel),
    then falls back to user_google_creds.json file (for local development).
    """
    creds_json_str = os.getenv(GOOGLE_CREDS_JSON_ENV_VAR)
    if creds_json_str:
        try:
            creds_info = json.loads(creds_json_str)
            # from_authorized_user_info is suitable if creds_info is a dict from the JSON
            # It requires client_id, client_secret, refresh_token typically.
            # Scopes might be needed if not embedded in creds_info.
            # If creds_info already has scopes, they will be used.
            creds = Credentials.from_authorized_user_info(creds_info, scopes=SCOPES if 'scopes' not in creds_info else None)
            logger.info("Google OAuth credentials loaded from environment variable.")
            
            if not creds.valid and creds.refresh_token:
                try:
                    from google.auth.transport.requests import Request
                    logger.info("Attempting to refresh token loaded from env var.")
                    creds.refresh(Request())
                    logger.info("Token from env var refreshed successfully.")
                    # Note: Persisting this refreshed token in an env var context is complex.
                    # The current creds object is refreshed for the instance's lifetime.
                except Exception as refresh_e:
                    logger.error(f"Failed to refresh token from env var: {refresh_e}")
            return creds
        except Exception as e:
            logger.error(f"Error loading Google OAuth credentials from env var '{GOOGLE_CREDS_JSON_ENV_VAR}': {e}")
            # Fall through to try file if env var loading fails

    if os.path.exists(USER_GOOGLE_CREDS_FILE):
        try:
            # from_authorized_user_file is designed to load files saved by credentials.to_json()
            # It will use the scopes embedded in the file if present, or the ones passed.
            creds = Credentials.from_authorized_user_file(USER_GOOGLE_CREDS_FILE, SCOPES)
            logger.info(f"Google OAuth credentials loaded from file: {USER_GOOGLE_CREDS_FILE}")
            
            if not creds.valid and creds.refresh_token:
                 try:
                    from google.auth.transport.requests import Request
                    logger.info("Attempting to refresh token loaded from file.")
                    creds.refresh(Request())
                    save_google_oauth_credentials(creds) # Save refreshed token back to file for local dev
                    logger.info("Token from file refreshed and saved successfully.")
                 except Exception as refresh_e:
                    logger.error(f"Failed to refresh token from file: {refresh_e}")
            return creds
        except Exception as e:
            logger.error(f"Error loading Google OAuth credentials from file {USER_GOOGLE_CREDS_FILE}: {e}")
            # Optionally, remove corrupted file
            # try:
            #     os.remove(USER_GOOGLE_CREDS_FILE)
            #     logger.info(f"Removed invalid/corrupted credentials file: {USER_GOOGLE_CREDS_FILE}")
            # except OSError as oe:
            #     logger.error(f"Error removing invalid credentials file {USER_GOOGLE_CREDS_FILE}: {oe}")
            return None
            
    logger.info("User Google OAuth credentials not found in environment variable or local file.")
    return None

def delete_google_oauth_credentials():
    """Deletes the user_google_creds.json file."""
    try:
        if os.path.exists(USER_GOOGLE_CREDS_FILE):
            os.remove(USER_GOOGLE_CREDS_FILE)
            logger.info(f"Deleted Google OAuth credentials file: {USER_GOOGLE_CREDS_FILE}")
            return True
        return False # File didn't exist
    except Exception as e:
        logger.error(f"Error deleting Google OAuth credentials file {USER_GOOGLE_CREDS_FILE}: {e}")
        return False

def are_google_oauth_credentials_present():
    """
    Checks if Google OAuth credentials might be available (either via env var or file).
    This is a basic check; actual loading and validation happen in load_google_oauth_credentials.
    """
    if os.getenv(GOOGLE_CREDS_JSON_ENV_VAR):
        return True 
    if os.path.exists(USER_GOOGLE_CREDS_FILE):
        return True
    return False

def is_client_secret_configured() -> bool:
    """Checks if the client_secret.json file exists."""
    return os.path.exists(CLIENT_SECRET_FILE)

# Ensure __init__.py exists in utils, if not already handled by project rules
# This is more of a conceptual note for package structure. 