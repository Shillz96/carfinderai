import os
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv, find_dotenv, get_key, set_key

# Define the path to the .env file
# This assumes config_manager.py is in a 'managers' subdirectory of the project root.
DOTENV_PATH = None
try:
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # Attempt to find .env in the project root or current working directory.
    # Do not raise an error if not found, and do not create it.
    found_dotenv_path = find_dotenv(filename='.env', usecwd=True, raise_error_if_not_found=False)

    if found_dotenv_path and os.path.exists(found_dotenv_path):
        DOTENV_PATH = found_dotenv_path
        load_dotenv(DOTENV_PATH, override=True) # Load existing .env file
        print(f"Loaded .env file from: {DOTENV_PATH}") # For debugging
    else:
        # If .env is not found, DOTENV_PATH remains None.
        # The application will rely on environment variables set externally (e.g., by Vercel).
        print(".env file not found. Relying on system-set environment variables.")
        # Attempt to load from process environment anyway, in case they are already set
        load_dotenv(override=True)


except Exception as e:
    # Fallback if path resolution or loading fails (e.g., in some execution contexts)
    print(f"Error during .env file processing: {e}. Relying on system-set environment variables.")
    # Attempt to load from process environment as a last resort
    load_dotenv(override=True)


# Define configurations that can be managed via UI
# Structure: 'ENV_VAR_NAME': {'description': 'Helpful note', 'type': 'string'/'int'/'bool'/'list', 'sensitive': True/False, 'options': [] (for type='select')}
CONFIGURABLE_SETTINGS: Dict[str, Dict[str, Any]] = {
    'GOOGLE_SHEET_ID': {
        'description': "The ID of the Google Sheet used to store leads. If left blank or set to 'your_google_sheet_id', the system may attempt to create a new sheet when DataManager initializes. Update this with the ID of an existing sheet if you have one.",
        'type': 'string',
        'sensitive': False
    },
    'MIN_VEHICLE_YEAR': {
        'description': "The minimum year for vehicles to be considered a lead (e.g., 2018). Leads for vehicles older than this year will be skipped.",
        'type': 'int',
        'sensitive': False
    },
    'LOG_LEVEL': {
        'description': "Set the application-wide logging verbosity. 'DEBUG' is most verbose, 'ERROR' is least.",
        'type': 'select',
        'options': ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        'sensitive': False
    },
    'SCRAPER_REQUEST_TIMEOUT_SECONDS': {
        'description': "Maximum time (in seconds) to wait for a response when scraping websites.",
        'type': 'int',
        'sensitive': False
    },
    'SCRAPER_DELAY_MIN_SECONDS': {
        'description': "Minimum random delay (in seconds) between scraping requests to avoid overloading target websites.",
        'type': 'float', # Using float for potentially sub-second precision
        'sensitive': False
    },
    'SCRAPER_DELAY_MAX_SECONDS': {
        'description': "Maximum random delay (in seconds) between scraping requests.",
        'type': 'float',
        'sensitive': False
    },
    'THRYV_API_KEY': {
        'description': "Your API Key for Thryv integration. Used to send leads to Thryv. (Sensitive)",
        'type': 'string',
        'sensitive': True
    },
    'THRYV_BUSINESS_ID': {
        'description': "Your Business ID for Thryv. Necessary for API interactions.",
        'type': 'string',
        'sensitive': False
    },
    'TWILIO_ACCOUNT_SID': {
        'description': "Your Twilio Account SID, used for sending SMS notifications about new leads. (Sensitive)",
        'type': 'string',
        'sensitive': True
    },
    'TWILIO_AUTH_TOKEN': {
        'description': "Your Twilio Auth Token. Kept highly confidential. (Sensitive)",
        'type': 'string',
        'sensitive': True
    },
    'TWILIO_PHONE_NUMBER': {
        'description': "The Twilio phone number (in E.164 format, e.g., +12345678900) from which SMS notifications will be sent.",
        'type': 'string',
        'sensitive': False
    },
    'USER_EMAIL_ADDRESS': {
        'description': "Primary email address for notifications or user identification within the system.",
        'type': 'string',
        'sensitive': False
    }
    # Add more settings here based on your application's .env variables
}

def get_config_value(key_name: str) -> Optional[str]:
    """
    Retrieves a configuration value from the .env file.
    This function reloads from .env each time to ensure freshness if .env is edited externally,
    though set_key also reloads internally.

    Args:
        key_name (str): The name of the environment variable.
        
    Returns:
        Optional[str]: The value of the environment variable, or None if not found.
    """
    # Ensure DOTENV_PATH is valid and load_dotenv has been called
    if not DOTENV_PATH or not os.path.exists(DOTENV_PATH):
        # This case should ideally be handled by the initial load, but as a safeguard:
        # print(f"Warning: .env file path '{DOTENV_PATH}' not found when getting key '{key_name}'.")
        return os.getenv(key_name) # Fallback to process environment

    # python-dotenv's get_key reads directly from the file.
    # os.getenv would read from the loaded environment variables.
    # For UI display, direct file read is fine. For application logic, os.getenv is usually used after initial load.
    return get_key(DOTENV_PATH, key_name)

def get_all_configurable_settings_with_values() -> Dict[str, Dict[str, Any]]:
    """
    Retrieves all defined configurable settings with their current values and descriptions.
    Sensitive values are masked.
    
    Returns:
        Dict[str, Dict[str, Any]]: A dictionary where keys are setting names,
                                   and values are dicts containing 'description', 'current_value', 
                                   'type', 'sensitive', 'options', and 'actual_value_present'.
    """
    settings_with_values = {}
    for key, details in CONFIGURABLE_SETTINGS.items():
        current_value = get_config_value(key) # Get current value from .env
        
        display_value = current_value
        actual_value_present = current_value is not None and current_value != ""

        if details['sensitive'] and actual_value_present:
            display_value = "********" 
            
        settings_with_values[key] = {
            'description': details['description'],
            'current_value': display_value,
            'type': details['type'],
            'sensitive': details['sensitive'],
            'options': details.get('options', []), # Include options for select type
            'actual_value_present': actual_value_present # Helps UI decide placeholder text for sensitive fields
        }
    return settings_with_values

def _validate_value(key: str, value: str, details: Dict[str, Any]) -> bool:
    """Helper to validate value based on type."""
    setting_type = details['type']
    if value is None or value == "": # Allow clearing a value
        return True

    if setting_type == 'int':
        try:
            int(value)
        except ValueError:
            print(f"Validation Error: '{key}' value '{value}' is not a valid integer.")
            return False
    elif setting_type == 'float':
        try:
            float(value)
        except ValueError:
            print(f"Validation Error: '{key}' value '{value}' is not a valid float.")
            return False
    elif setting_type == 'bool':
        if value.lower() not in ['true', 'false', 'yes', 'no', '1', '0', 'on', 'off', '']:
            print(f"Validation Error: '{key}' value '{value}' is not a valid boolean representation.")
            return False
    elif setting_type == 'select':
        if value not in details.get('options', []):
            print(f"Validation Error: '{key}' value '{value}' is not in the allowed options {details.get('options', [])}.")
            return False
    # Add more type checks if needed (e.g., for email format, URL)
    return True


def update_multiple_config_values(settings_to_update: Dict[str, str]) -> Dict[str, Dict[str, Any]]:
    """
    Updates multiple configuration values in the .env file.
    
    Args:
        settings_to_update (Dict[str, str]): A dictionary where keys are setting names
                                             and values are the new values.
                                             
    Returns:
        Dict[str, Dict[str, Any]]: Results 도로
                                    {'key': {'success': bool, 'message': str}}
    """
    results: Dict[str, Dict[str, Any]] = {}
    something_changed_successfully = False

    if not DOTENV_PATH or not os.path.exists(DOTENV_PATH):
        # This should not happen if initial setup worked.
        for key_to_update in settings_to_update:
            results[key_to_update] = {'success': False, 'message': f"Configuration file (.env) not found at {DOTENV_PATH}."}
        return results

    for key, new_value in settings_to_update.items():
        if key not in CONFIGURABLE_SETTINGS:
            results[key] = {'success': False, 'message': 'This setting is not defined as configurable.'}
            continue

        details = CONFIGURABLE_SETTINGS[key]

        # For sensitive fields, if the submitted value is the mask "********", it means "do not change".
        # This check should happen BEFORE validation.
        if details['sensitive']:
            # Check if a value was actually set for this sensitive key before
            # If user submits "********" for a field that was already set and masked, don't change it.
            # If user submits "********" for a field that was blank, it still means "don't set it / leave blank".
            # The crucial part is not to literally save "********" as the value.
            current_actual_value = get_key(DOTENV_PATH, key) # Get actual value, not from os.getenv
            if new_value == "********" and current_actual_value is not None and current_actual_value != "":
                results[key] = {'success': True, 'message': 'Sensitive value unchanged.'}
                continue # Skip update for this key

        # Type Validation
        if not _validate_value(key, new_value, details):
            results[key] = {'success': False, 'message': f"Invalid value format for type '{details['type']}'."}
            continue
        
        # Normalize boolean values before saving
        if details['type'] == 'bool':
            if new_value.lower() in ['true', 'yes', '1', 'on']:
                new_value = 'true'
            elif new_value.lower() in ['false', 'no', '0', 'off', '']: # Treat empty string as false for bool
                new_value = 'false'
        
        # If new_value for a sensitive field is now blank, it means "clear this sensitive value".
        # `set_key` handles empty string correctly (sets `KEY=` or removes if it was `KEY=value`).

        try:
            success = set_key(DOTENV_PATH, key, new_value, quote_mode='always')
            if success:
                results[key] = {'success': True, 'message': 'Updated successfully.'}
                something_changed_successfully = True
            else:
                # This part of set_key from python-dotenv usually returns True if file write was okay,
                # but good to have a branch.
                results[key] = {'success': False, 'message': 'Failed to update due to an unexpected issue with set_key.'}
        except Exception as e:
            results[key] = {'success': False, 'message': f"Error writing to .env file: {e}"}
            
    if something_changed_successfully:
        # Reload environment variables in the current process if any key was successfully updated.
        # This makes changes available to os.getenv() immediately for the current process.
        load_dotenv(DOTENV_PATH, override=True)
        # Note: Some application components might need to be re-initialized or the app restarted
        # to pick up certain changes (e.g., database connections, external service clients).
        
    return results

def ensure_init_py_exists():
    """
    Ensures that __init__.py exists in the managers directory, making it a package.
    This is a utility function and might be better placed in a setup script.
    On read-only filesystems, this will log an error if it needs to create the file.
    """
    managers_dir = os.path.dirname(os.path.abspath(__file__))
    init_py_path = os.path.join(managers_dir, "__init__.py")
    if not os.path.exists(init_py_path):
        try:
            # In a read-only environment, this write will fail.
            # This function should ideally not be called at import time in such environments
            # or should be designed to be a no-op if writing is not possible.
            with open(init_py_path, 'w') as f:
                f.write("# Initializes the managers package\n")
            print(f"Created {init_py_path}")
        except IOError as e:
            print(f"Could not create {init_py_path} (expected in read-only environments): {e}")

# Call it once to ensure the __init__.py exists for the 'managers' package
if __name__ != "__main__": # Avoid running on direct script execution if any
    # Consider removing this call if it causes issues in Vercel due to attempting file write,
    # or ensure your deployment package includes this __init__.py.
    # For Vercel, it's best if all necessary files, including __init__.py, are part of the deployment.
    # ensure_init_py_exists() # Commenting out for Vercel to prevent write attempts
    pass # __init__.py should be part of the codebase

# Example usage (for testing this module directly):
if __name__ == "__main__":
    print("Configurable Settings Test:")
    settings = get_all_configurable_settings_with_values()
    for k, v in settings.items():
        print(f"- {k}: Current Value='{v['current_value']}' (Type: {v['type']}, Sensitive: {v['sensitive']}, Options: {v.get('options', 'N/A')}) Desc: {v['description']}")

    print("\nTesting update (example - MIN_VEHICLE_YEAR to 2020):")
    # Ensure MIN_VEHICLE_YEAR is in CONFIGURABLE_SETTINGS for this test to run
    if 'MIN_VEHICLE_YEAR' in CONFIGURABLE_SETTINGS:
        update_results = update_multiple_config_values({'MIN_VEHICLE_YEAR': '2020', 'LOG_LEVEL': 'DEBUG', 'MADE_UP_KEY': 'test'})
        print("Update Results:", update_results)
        
        print("\nFetching MIN_VEHICLE_YEAR and LOG_LEVEL again:")
        print(f"MIN_VEHICLE_YEAR: {get_config_value('MIN_VEHICLE_YEAR')}")
        print(f"LOG_LEVEL: {get_config_value('LOG_LEVEL')}")
    else:
        print("MIN_VEHICLE_YEAR not in CONFIGURABLE_SETTINGS, skipping update test.")

    # Test creating/updating a sensitive key
    if 'TEST_SENSITIVE_KEY' not in CONFIGURABLE_SETTINGS:
        CONFIGURABLE_SETTINGS['TEST_SENSITIVE_KEY'] = {
            'description': "A test sensitive key.",
            'type': 'string',
            'sensitive': True
        }
        print("Added TEST_SENSITIVE_KEY to CONFIGURABLE_SETTINGS for this test run.")

    print("\nTesting update for TEST_SENSITIVE_KEY:")
    update_results_sensitive = update_multiple_config_values({'TEST_SENSITIVE_KEY': 'mysecretvalue'})
    print("Sensitive Update Results:", update_results_sensitive)
    print(f"TEST_SENSITIVE_KEY (from get_config_value): {get_config_value('TEST_SENSITIVE_KEY')}")
    
    settings_after_sensitive_update = get_all_configurable_settings_with_values()
    print(f"TEST_SENSITIVE_KEY (displayed): {settings_after_sensitive_update.get('TEST_SENSITIVE_KEY', {}).get('current_value')}")

    print("\nTesting 'no change' for TEST_SENSITIVE_KEY by passing '********':")
    update_results_nochange = update_multiple_config_values({'TEST_SENSITIVE_KEY': '********'})
    print("No Change Sensitive Update Results:", update_results_nochange)
    print(f"TEST_SENSITIVE_KEY (should be 'mysecretvalue'): {get_config_value('TEST_SENSITIVE_KEY')}")


    print("\nTesting clearing TEST_SENSITIVE_KEY by passing empty string:")
    update_results_clear = update_multiple_config_values({'TEST_SENSITIVE_KEY': ''})
    print("Clear Sensitive Update Results:", update_results_clear)
    print(f"TEST_SENSITIVE_KEY (should be None or empty): {get_config_value('TEST_SENSITIVE_KEY')}")
    
    # Clean up the test key from .env if it was added
    # Note: python-dotenv's set_key with an empty value might result in `KEY=` or removing the line.
    # unset_key would be more explicit for removal if that's the desired behavior.
    # For now, setting to empty string is fine.
    # from dotenv import unset_key
    # unset_key(DOTENV_PATH, 'TEST_SENSITIVE_KEY')
    # print("Cleaned up TEST_SENSITIVE_KEY from .env")
    set_key(DOTENV_PATH, 'TEST_SENSITIVE_KEY', '') # Effectively clears or sets to KEY=
    load_dotenv(DOTENV_PATH, override=True)
    print("Attempted to clear TEST_SENSITIVE_KEY in .env") 