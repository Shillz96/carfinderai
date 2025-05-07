import os
from functools import wraps
from flask import request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash

# Basic User Authentication
# Load from environment variables for security and flexibility
# Default values are provided for local development if environment variables are not set.
users = {
    os.environ.get('WEB_UI_USERNAME', 'admin'): generate_password_hash(os.environ.get('WEB_UI_PASSWORD', 'change_this_password'))
}

# Initialize a variable to store data_manager. This will be set from app.py
# to avoid circular imports and allow auth functions to access it.
_data_manager = None

def init_auth_data_manager(data_manager_instance):
    \"\"\"
    Initializes the data_manager instance for the auth module.
    This function should be called from app.py after DataManager is initialized.

    Args:
        data_manager_instance: The initialized DataManager instance.
    \"\"\"
    global _data_manager
    _data_manager = data_manager_instance

def login_required(f):
    \"\"\"
    Decorator to ensure a user is logged in before accessing a route.
    If not logged in, redirects to the login page.
    \"\"\"
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash('Please log in to access this page.', 'info')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def configure_auth_routes(bp, new_sheet_info_ref, sheet_error_info_ref):
    \"\"\"
    Configures and registers authentication routes (login, logout) on a Blueprint.

    Args:
        bp: The Flask Blueprint to register routes on.
        new_sheet_info_ref (dict): A mutable dictionary-like object (e.g. {'value': new_sheet_info}) 
                                   to access and potentially clear the new_sheet_info message.
        sheet_error_info_ref (dict): A mutable dictionary-like object for sheet_error_info.
    \"\"\"

    @bp.route('/login', methods=['GET', 'POST'])
    def login():
        \"\"\"Handles user login attempts.\"\"\"
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            # Ensure users dictionary is populated
            if not users or not any(users.values()): # Check if users is empty or has no actual password hashes
                 # Regenerate users if empty - this can happen if env vars changed or weren't set at module load
                current_username = os.environ.get('WEB_UI_USERNAME', 'admin')
                current_password_hash = generate_password_hash(os.environ.get('WEB_UI_PASSWORD', 'change_this_password'))
                users.clear() # Clear any potentially stale entries
                users[current_username] = current_password_hash


            user_password_hash = users.get(username)

            if user_password_hash and check_password_hash(user_password_hash, password):
                session['logged_in'] = True
                session['username'] = username
                flash('Successfully logged in.', 'success')

                # Attempt to refresh Google connection on login if creds are present
                # Ensure _data_manager is initialized before calling its methods
                if _data_manager and _data_manager.are_google_oauth_credentials_present_in_manager(): # Changed to a method on data_manager
                    if _data_manager.refresh_google_connection():
                        flash('Google connection is active.', 'info')
                    else:
                        flash('Could not activate Google connection. Please check OAuth settings and ensure client_secret is configured.', 'warning')
                
                # Show sheet info messages if present, using the passed references
                if new_sheet_info_ref and new_sheet_info_ref.get('value'):
                    flash(new_sheet_info_ref['value'], 'success')
                    new_sheet_info_ref['value'] = None # Clear after showing
                if sheet_error_info_ref and sheet_error_info_ref.get('value'):
                    flash(sheet_error_info_ref['value'], 'danger')
                    sheet_error_info_ref['value'] = None # Clear after showing
                    
                next_url = request.args.get('next')
                return redirect(next_url or url_for('main.leads')) # Assuming main blueprint for leads
            else:
                flash('Invalid username or password. Please try again.', 'danger')
        return render_template('login.html')

    @bp.route('/logout')
    @login_required # Ensures user is logged in to log out
    def logout():
        \"\"\"Handles user logout.\"\"\"
        session.pop('logged_in', None)
        session.pop('username', None)
        flash('You have been successfully logged out.', 'info')
        return redirect(url_for('auth.login'))

    return bp 