"""
Flask web interface for the Used Car Lead Generation Agent.
This application provides a private UI for the client to view and manage car leads.
"""
import os
import sys
import datetime
import json # For loading client_secret.json
from flask import Flask, render_template, request, redirect, url_for, flash, session, current_app
# from flask_httpauth import HTTPBasicAuth # Using custom login for now
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
# from werkzeug.utils import secure_filename # No longer uploading credentials file
# import shutil # No longer uploading credentials file
import time

# Google OAuth specific imports
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# Add the parent directory to the path to import from the rest of the application
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the data manager and config loader
try:
    from managers.data_manager import DataManager
    from utils.config import load_config
    from utils.ui_config_manager import (
        get_ui_settings, save_ui_settings, update_setting, 
        save_google_oauth_credentials, load_google_oauth_credentials,
        delete_google_oauth_credentials, are_google_oauth_credentials_present,
        USER_GOOGLE_CREDS_FILE # For checking existence
    )
    # Import new config manager functions
    from managers.config_manager import get_all_configurable_settings_with_values, update_multiple_config_values, get_config_value
except ImportError as e:
    # Mock DataManager for development if the actual module is not ready
    # This mock should be updated if its interface changes significantly
    print(f"ImportError in app.py: {e}. Using Mocks or will fail if essential.")
    class DataManager:
        def __init__(self, config):
            print("Using Mock DataManager")
            self.config = config
        def get_all_leads(self): return []
        def update_lead_status(self, *args, **kwargs): return False
        def refresh_google_connection(self): return False # Mock refresh
        def get_created_sheet_info(self): return None # Added this method
        def get_sheet_error_info(self): return None # Added this method

    class load_config:
        def __call__(self):
            print("Using Mock load_config")
            return {}
    # Mock ui_config_manager functions if needed for basic startup
    def get_ui_settings(): return {}
    def are_google_oauth_credentials_present(): return False
    def save_google_oauth_credentials(c): pass
    def delete_google_oauth_credentials(): pass

    # Mock for new config manager functions
    def get_all_configurable_settings_with_values(): return {}
    def update_multiple_config_values(s): return {k: {'success': False, 'message': 'Mock update failed'} for k in s}
    def get_config_value(k): return None

# --- Flask App Initialization and Basic Config ---
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'vercel_deployment_secret_key_123')
# app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024  # No longer uploading large files directly

# Define client_secret.json path (should be in project root)
CLIENT_SECRET_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'client_secret.json')
# Environment variable for client secret JSON content
GOOGLE_CLIENT_SECRET_JSON_ENV_VAR = "GOOGLE_CLIENT_SECRET_JSON"

# Define the scopes for Google Sheets API
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Basic User Authentication (replace with a more robust system for production)
users = {
    os.environ.get('FLASK_SECRET_KEYWEB_UI_USERNAME', 'admin'): generate_password_hash(os.environ.get('WEB_UI_PASSWORD', 'vercel123'))
}

# Check if we're running on Vercel
IS_VERCEL = os.environ.get('VERCEL', '') == '1'

# Load main application configuration
try:
    config = load_config()
except Exception as e:
    print(f"Error loading config: {e}. Using empty config.")
    config = {}

# Initialize DataManager (will attempt to load OAuth creds if present)
try:
    data_manager = DataManager(config)
    # Store sheet info messages to be displayed in routes instead of using flash directly here
    # These will be used inside request contexts later
    new_sheet_info = data_manager.get_created_sheet_info()
    sheet_error_info = data_manager.get_sheet_error_info()
except Exception as e:
    print(f"Error initializing DataManager: {e}. Using mock.")
    class MockDataManager:
        def __init__(self):
            pass
        def get_all_leads(self): return []
        def update_lead_status(self, *args, **kwargs): return False
        def refresh_google_connection(self): return False
        def get_created_sheet_info(self): return None
        def get_sheet_error_info(self): return None
    
    data_manager = MockDataManager()
    new_sheet_info = None
    sheet_error_info = None

# --- Authentication Decorator and Routes ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username in users and check_password_hash(users.get(username), password):
            session['logged_in'] = True
            session['username'] = username
            flash('Successfully logged in.', 'success')
            # Attempt to refresh Google connection on login if creds are present
            if are_google_oauth_credentials_present():
                if data_manager.refresh_google_connection():
                    flash('Google connection is active.', 'info')
                else:
                    flash('Could not activate Google connection. Please check settings.', 'warning')
            
            # Show sheet info messages if present
            if new_sheet_info:
                flash(new_sheet_info, 'success')
            if sheet_error_info:
                flash(sheet_error_info, 'danger')
                
            return redirect(url_for('leads'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# --- Google OAuth Routes ---
@app.route('/authorize_google')
@login_required
def authorize_google():
    """Initiates the Google OAuth 2.0 flow."""
    client_secret_json_str = os.getenv(GOOGLE_CLIENT_SECRET_JSON_ENV_VAR)
    flow = None

    try:
        if client_secret_json_str:
            try:
                client_config = json.loads(client_secret_json_str)
                flow = Flow.from_client_config(
                    client_config,
                    scopes=SCOPES,
                    redirect_uri=url_for('oauth2callback', _external=True)
                )
                current_app.logger.info("Google OAuth flow initiated using client secret from environment variable.")
            except json.JSONDecodeError as e:
                flash(f'Error decoding Google client secret from environment variable: {str(e)}. Falling back to file.', 'warning')
                current_app.logger.error(f"JSONDecodeError for GOOGLE_CLIENT_SECRET_JSON: {e}")
                # Fall through to try file if env var parsing fails
            except Exception as e: # Catch other potential errors from from_client_config
                flash(f'Error initiating OAuth with client secret from env var: {str(e)}. Falling back to file.', 'warning')
                current_app.logger.error(f"Error from_client_config with env var: {e}")
                # Fall through

        if not flow: # If env var wasn't there, or failed to load
            if not os.path.exists(CLIENT_SECRET_FILE):
                flash('Google Client Secret not found (neither as file nor environment variable). Please configure the application.', 'danger')
                return redirect(url_for('settings'))
            flow = Flow.from_client_secrets_file(
                CLIENT_SECRET_FILE,
                scopes=SCOPES,
                redirect_uri=url_for('oauth2callback', _external=True)
            )
            current_app.logger.info("Google OAuth flow initiated using client_secret.json file.")

        authorization_url, state = flow.authorization_url(
            access_type='offline',
            prompt='consent' # Force consent screen for refresh token
        )
        session['oauth_state'] = state
        return redirect(authorization_url)
    except Exception as e:
        flash(f'Error starting Google authorization: {str(e)}', 'danger')
        current_app.logger.error(f"OAuth Start Error: {e}")
        return redirect(url_for('settings'))

@app.route('/oauth2callback')
@login_required
def oauth2callback():
    """Callback route for Google OAuth 2.0."""
    state = session.get('oauth_state')
    
    if not state or state != request.args.get('state'):
        flash('OAuth state mismatch. Please try connecting again.', 'danger')
        current_app.logger.error("OAuth state mismatch.")
        return redirect(url_for('settings'))

    client_secret_json_str = os.getenv(GOOGLE_CLIENT_SECRET_JSON_ENV_VAR)
    flow = None

    try:
        if client_secret_json_str:
            try:
                client_config = json.loads(client_secret_json_str)
                flow = Flow.from_client_config(
                    client_config,
                    scopes=SCOPES,
                    state=state,
                    redirect_uri=url_for('oauth2callback', _external=True)
                )
                current_app.logger.info("Google OAuth callback using client secret from environment variable.")
            except json.JSONDecodeError as e:
                flash(f'Error decoding Google client secret from environment variable during callback: {str(e)}. Falling back to file.', 'warning')
                current_app.logger.error(f"JSONDecodeError for GOOGLE_CLIENT_SECRET_JSON during callback: {e}")
            except Exception as e: # Catch other potential errors from from_client_config
                flash(f'Error initiating OAuth callback with client secret from env var: {str(e)}. Falling back to file.', 'warning')
                current_app.logger.error(f"Error from_client_config with env var during callback: {e}")
        
        if not flow: # If env var wasn't there, or failed to load
            if not os.path.exists(CLIENT_SECRET_FILE):
                flash('Google Client Secret not found during callback (neither as file nor environment variable). Please configure.', 'danger')
                current_app.logger.error("Client secret not found (file or env var) during OAuth callback.")
                return redirect(url_for('settings'))
            flow = Flow.from_client_secrets_file(
                CLIENT_SECRET_FILE,
                scopes=SCOPES,
                state=state,
                redirect_uri=url_for('oauth2callback', _external=True)
            )
            current_app.logger.info("Google OAuth callback using client_secret.json file.")

        flow.fetch_token(authorization_response=request.url)
        
        credentials = flow.credentials
        save_google_oauth_credentials(credentials) # Save credentials using ui_config_manager
        
        # Re-initialize data_manager with new credentials
        if data_manager.refresh_google_connection():
            flash('Successfully connected to Google Sheets!', 'success')
        else:
            flash('Connected to Google, but could not initialize Sheets service. Check logs.', 'warning')
            
    except Exception as e:
        flash(f'Error during Google authentication callback: {str(e)}', 'danger')
        current_app.logger.error(f"OAuth Callback Error: {e}")

    return redirect(url_for('settings'))

@app.route('/disconnect_google')
@login_required
def disconnect_google():
    """Deletes stored Google OAuth credentials."""
    if delete_google_oauth_credentials():
        data_manager.sheet_service = None # Clear the service in data_manager
        data_manager.user_credentials = None
        flash('Successfully disconnected from Google Sheets.', 'info')
    else:
        flash('Could not delete Google credentials. They might not exist.', 'warning')
    return redirect(url_for('settings'))

# --- Main Application Routes ---
@app.route('/')
@app.route('/leads')
@login_required
def leads():
    """Display all leads from Google Sheets or local backup."""
    try:
        # Show sheet info messages if present (first time user accesses the app)
        # These are general messages about sheet creation/errors during DataManager init
        global new_sheet_info, sheet_error_info # Ensure we can clear them
        if new_sheet_info:
            flash(new_sheet_info, 'success')
            new_sheet_info = None # Clear after showing
        if sheet_error_info:
            flash(sheet_error_info, 'danger')
            sheet_error_info = None # Clear after showing
            
        leads_data = data_manager.get_all_leads() # This now handles local fallback
        
        data_source_is_local = False
        specific_leads_page_message = None

        if not data_manager.sheet_service: # Primary indicator of using local backup
            data_source_is_local = True
            if are_google_oauth_credentials_present():
                # Credentials exist, but service isn't up - implies connection issue
                specific_leads_page_message = ('Could not connect to Google Sheets. Displaying local data. Please try reconnecting in Settings.', 'warning')
            else:
                # No credentials configured
                specific_leads_page_message = ('Google Sheets not connected. Displaying local data. Connect in Settings to sync.', 'info')
        
        # Pass the specific message to flash if it was set
        if specific_leads_page_message:
            flash(specific_leads_page_message[0], specific_leads_page_message[1])

        return render_template('leads.html', leads=leads_data, data_source_is_local=data_source_is_local)
    except Exception as e:
        flash(f"Error retrieving leads: {str(e)}", 'danger')
        current_app.logger.error(f"Error in /leads route: {e}")
        # Still pass data_source_is_local, assume local if error
        return render_template('leads.html', leads=[], data_source_is_local=True)

@app.route('/settings')
@login_required
def settings():
    current_ui_settings = get_ui_settings()
    google_connected = are_google_oauth_credentials_present()
    current_sheet_id = data_manager.sheet_id
    sheet_id_display = "Not Set"

    if current_sheet_id and current_sheet_id != data_manager.placeholder_sheet_id:
        sheet_id_display = current_sheet_id
    elif data_manager.sheet_service: # If service is up, it implies it might auto-create or tried to
        sheet_id_display = "Not Set (will attempt auto-creation on next run/refresh if needed)"
    else: # No service, no valid ID
        sheet_id_display = "Not Set (Google connection inactive or failed)"

    settings_data = {
        'client_email': os.environ.get('CLIENT_EMAIL', 'N/A'),
        'client_phone': os.environ.get('CLIENT_PHONE', 'N/A'),
        'scrape_frequency': os.environ.get('SCRAPE_FREQUENCY', 'N/A'),
        'last_run': 'Not Implemented', # Placeholder
        'enable_thryv_crm': current_ui_settings.get('enable_thryv_crm', True),
        'google_oauth_connected': google_connected,
        'twilio_configured': bool(config.get('TWILIO_ACCOUNT_SID') and config.get('TWILIO_AUTH_TOKEN')),
        'google_sheet_id': sheet_id_display
    }
    # Check if client_secret.json exists or GOOGLE_CLIENT_SECRET_JSON_ENV_VAR is set for enabling connection button
    client_secret_env_var_exists = bool(os.getenv(GOOGLE_CLIENT_SECRET_JSON_ENV_VAR))
    client_secret_file_exists = os.path.exists(CLIENT_SECRET_FILE)
    settings_data['client_secret_configured'] = client_secret_file_exists or client_secret_env_var_exists
    
    if not settings_data['client_secret_configured']:
        flash_message = "CRITICAL: Google Client Secret is not configured. "
        if not client_secret_file_exists and not client_secret_env_var_exists:
            flash_message += "Neither `client_secret.json` found in project root nor `GOOGLE_CLIENT_SECRET_JSON` environment variable is set. "
        elif not client_secret_file_exists:
            flash_message += "`client_secret.json` not found in project root (checking env var). "
        elif not client_secret_env_var_exists:
            flash_message += "`GOOGLE_CLIENT_SECRET_JSON` environment variable not set (checking file). "
        flash_message += "Google OAuth connection will fail."
        flash(flash_message, "danger")
    # Old logic for client_secret_exists, to be replaced by client_secret_configured check in template if needed
    # settings_data['client_secret_exists'] = os.path.exists(CLIENT_SECRET_FILE) 
    # if not settings_data['client_secret_exists']:
    #     flash("CRITICAL: `client_secret.json` not found in project root. Google OAuth connection will fail.", "danger")

    return render_template('settings.html', settings=settings_data)

@app.route('/update_settings', methods=['POST'])
@login_required
def update_settings_route():
    """Handle updates to UI settings like CRM toggle."""
    if request.method == 'POST':
        enable_crm = request.form.get('enable_thryv_crm') == 'on'
        if update_setting('enable_thryv_crm', enable_crm):
            flash('CRM settings updated successfully!', 'success')
        else:
            flash('Failed to update CRM settings.', 'danger')
    return redirect(url_for('settings'))

# Removed old /upload_credentials and /reset_credentials routes

@app.route('/leads/manage/<int:lead_index>', methods=['GET', 'POST'])
@login_required
def manage_lead(lead_index):
    """Route for manually managing a lead's status (primarily local backup)."""
    all_leads = data_manager.get_all_leads() # Get current leads (could be from GSheet or local)
    
    if not (0 < lead_index <= len(all_leads)):
        flash('Invalid lead index.', 'danger')
        return redirect(url_for('leads'))

    # Adjust for zero-based indexing for list access
    actual_lead_index_in_list = lead_index -1 
    lead_to_manage = all_leads[actual_lead_index_in_list]
    lead_id = lead_to_manage.get('_local_id') # Expecting _local_id from data_manager

    if not lead_id:
        # This case should be rare if data_manager._save_to_local_backup ensures _local_id
        flash('Lead does not have a local ID for management. Cannot update.', 'warning')
        return redirect(url_for('leads'))

    if request.method == 'POST':
        lead_status = request.form.get('lead_status')
        lead_notes = request.form.get('lead_notes', '')
        
        if data_manager.update_lead_status(lead_id, lead_status, lead_notes):
            flash(f'Lead \'{lead_to_manage.get("title", lead_id)}\' status updated to: {lead_status}', 'success')
        else:
            flash(f'Failed to update status for lead \'{lead_to_manage.get("title", lead_id)}\'.', 'danger')
        return redirect(url_for('leads'))
    
    # GET request should ideally show a manage page, but for now, modal is in leads.html
    # If you want a dedicated page, you would render_template here with lead_to_manage
    flash('Manual lead management is done via the modal on the Leads page.', 'info')
    return redirect(url_for('leads'))


@app.route('/documentation')
@login_required
def documentation():
    docs = [
        {
            'title': 'Project Specification',
            'description': 'Detailed requirements for the Used Car Lead Generation Agent.',
            'path': '/docs/Project Specification.md' # These paths might need to be served via Flask if static serving isn't set up for /docs
        },
        {
            'title': 'Technical Design Document',
            'description': 'Architecture and technical details of the system.',
            'path': '/docs/Technical Design Document.md'
        },
        {
            'title': 'User Guide',
            'description': 'How to use the web interface and understand the lead data.',
            'path': '/docs/User Guide.md'
        }
    ]
    return render_template('documentation.html', docs=docs)

# --- Environment Settings Route ---
@app.route('/env-settings', methods=['GET', 'POST'])
@login_required
def env_settings():
    """Manage environment variables stored in .env file."""
    if request.method == 'POST':
        form_data = request.form.to_dict()
        # print(f"Form data received: {form_data}") # Debugging line
        results = update_multiple_config_values(form_data)
        # print(f"Update results: {results}") # Debugging line
        
        all_successful = True
        for key, result in results.items():
            if result['success']:
                flash(f"{key}: {result['message']}", 'success')
            else:
                flash(f"{key}: {result['message']}", 'danger')
                all_successful = False
        
        if all_successful and any(r['success'] and 'unchanged' not in r['message'].lower() for r in results.values()):
            flash('All applicable settings updated successfully. Some changes may require an application restart.', 'info')
        elif not all_successful:
            flash('Some settings could not be updated. Please check the messages.', 'warning')
        else: # All were successful but no actual changes (e.g. all were 'unchanged' or no data submitted)
            flash('No changes were applied to the settings.', 'info')

        return redirect(url_for('env_settings'))

    # GET request
    current_env_settings = get_all_configurable_settings_with_values()
    
    # This helper is needed for the template if a sensitive select field needs to show its actual current value
    # The main get_all_configurable_settings_with_values masks sensitive values.
    def get_actual_value_for_select_field(key_name):
        return get_config_value(key_name)
        
    return render_template('env_settings.html', 
                           settings=current_env_settings, 
                           get_actual_value_for_select=get_actual_value_for_select_field,
                           form_csrf_token=lambda: "") # Basic CSRF placeholder, replace if using Flask-WTF

@app.context_processor
def inject_current_year():
    return {'current_year': datetime.datetime.now().year}

# --- Default Route for Vercel ---
@app.route('/api/health')
def health_check():
    """Health check endpoint for Vercel."""
    return {"status": "ok", "timestamp": datetime.datetime.now().isoformat()}

# --- Handle FUNCTION_INVOCATION_FAILED Error ---
@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors and provide a helpful message."""
    # Check if running on Vercel
    if IS_VERCEL:
        return {
            "error": "Internal Server Error",
            "message": "The application encountered an error. Please make sure all environment variables are set correctly.",
            "documentation": "See the project README for required environment variables and configuration steps.",
            "status": 500
        }, 500
    return "Internal Server Error", 500

if __name__ == '__main__':
    # Ensure the FLASK_ENV is set to development for debugging, or use app.debug = True
    # For production, use a WSGI server like Gunicorn or Waitress.
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1' # Allow HTTP for local OAuth testing - SET THIS IF NOT USING HTTPS LOCALLY
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000))) 