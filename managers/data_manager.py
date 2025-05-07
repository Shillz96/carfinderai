"""
Data Manager module for handling data storage and retrieval operations.
Primarily manages interactions with Google Sheets for storing car leads.
"""

import os
from typing import List, Dict, Any, Optional
import json
from datetime import datetime
import socket
import time

# from google.oauth2 import service_account # No longer using service account directly here
from google.oauth2.credentials import Credentials as UserCredentials # For type hinting
# Removing complex httplib2 and AuthorizedHttp imports that may be causing issues
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from utils.logger import setup_logger
# from utils.ui_config_manager import are_google_credentials_configured # Old
from utils.ui_config_manager import load_google_oauth_credentials, are_google_oauth_credentials_present
# Import Flask's flash if we want to flash messages directly from here (alternative: return status to app.py)
# from flask import flash # Consider if this is the best place for UI messages

# Set up logger
logger = setup_logger('data_manager')

# Define path for local backup file
LOCAL_DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'local_leads.json')

# Set a default socket timeout for all HTTP requests
# socket.setdefaulttimeout(60)  # This line should be commented out or removed.
                                # Libraries should manage their own timeouts.

class DataManager:
    """
    Manages data operations for car listings, including storage to Google Sheets
    and duplicate detection.
    
    Args:
        config (dict): Configuration dictionary containing Google Sheets credentials
                      and other configuration parameters.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the DataManager with the provided configuration.
        
        Args:
            config (dict): Configuration dictionary.
        """
        self.config = config
        self.sheet_id = config.get('google_sheets', {}).get('sheet_id')
        self.placeholder_sheet_id = "your_google_sheet_id" # Define placeholder
        
        # Define sheets and ranges
        self.leads_sheet_range = 'Leads!A:M'  # Extended to M for Thryv_Lead_ID
        
        # Check internet connectivity first
        if not self._check_internet_connection():
            logger.error("No internet connection detected. Google Sheets functionality will not be available.")
            self.sheet_service = None
            config['GOOGLE_SHEET_ERROR_INFO'] = "No internet connection. Google Sheets functionality is unavailable."
            return
        
        # Load user OAuth credentials
        self.user_credentials: Optional[UserCredentials] = load_google_oauth_credentials()
        
        # Initialize sheets service if credentials loaded successfully
        if self.user_credentials and self.user_credentials.valid:
            self.sheet_service = self._get_sheet_service_with_oauth(self.user_credentials)
            sheet_creation_triggered = False
            
            if not self.sheet_service: # Should not happen if creds are valid, but as a safeguard
                logger.error("Sheet service could not be initialized even with supposedly valid credentials.")
                # No point in trying to create or access sheets

            # Scenario 1: Sheet ID is not configured or is the placeholder
            elif not self.sheet_id or self.sheet_id == self.placeholder_sheet_id:
                logger.info(f"Google Sheet ID is not configured or is a placeholder ('{self.sheet_id}'). Attempting to create a new sheet.")
                new_sheet_id = self._create_new_sheet()
                if new_sheet_id:
                    self.sheet_id = new_sheet_id
                    config['GOOGLE_SHEET_ID_CREATED_INFO'] = f"NEW sheet automatically created (ID: {self.sheet_id}). Update .env to use permanently."
                    sheet_creation_triggered = True
                else:
                    config['GOOGLE_SHEET_ERROR_INFO'] = "Auto-creation of new Google Sheet failed. Check logs. Please configure GOOGLE_SHEET_ID manually."
                    logger.error("Failed to create a new Google Sheet automatically.")
            
            # Scenario 2: Sheet ID is configured, check if it's accessible
            elif self.sheet_id and self.sheet_id != self.placeholder_sheet_id:
                try:
                    # Access the spreadsheet with retries
                    request = self.sheet_service.spreadsheets().get(spreadsheetId=self.sheet_id)
                    try:
                        self._execute_with_retry(request)
                        logger.info(f"Successfully accessed configured Google Sheet ID: {self.sheet_id}")
                    except HttpError as e:
                        if e.resp.status == 404:
                            logger.error(f"Configured Google Sheet ID '{self.sheet_id}' not found (404). Attempting to create a new sheet as fallback.")
                            new_sheet_id = self._create_new_sheet()
                            if new_sheet_id:
                                self.sheet_id = new_sheet_id # Use the new sheet
                                config['GOOGLE_SHEET_ID_CREATED_INFO'] = f"Configured Sheet ID '{self.config.get('GOOGLE_SHEET_ID')}' was NOT FOUND. NEW sheet created (ID: {self.sheet_id}). Update .env."
                                sheet_creation_triggered = True
                            else:
                                config['GOOGLE_SHEET_ERROR_INFO'] = f"Configured Sheet ID '{self.config.get('GOOGLE_SHEET_ID')}' not found, AND auto-creation of a new sheet failed. Check logs."
                                logger.error(f"Configured Sheet ID '{self.config.get('GOOGLE_SHEET_ID')}' not found, and failed to create a new sheet.")
                        else:
                            config['GOOGLE_SHEET_ERROR_INFO'] = f"Error accessing configured Google Sheet ID '{self.sheet_id}': {e}. Check ID and permissions."
                            logger.error(f"Error accessing configured Google Sheet ID '{self.sheet_id}': {e}")
                    except TimeoutError as e:
                        logger.error(f"Timeout while accessing Google Sheet ID '{self.sheet_id}': {e}. Check your network connection.")
                        config['GOOGLE_SHEET_ERROR_INFO'] = f"Timeout accessing Google Sheet: {e}. Check your network connection or try again later."
                except Exception as e:
                    logger.error(f"Unexpected error accessing Google Sheet ID '{self.sheet_id}': {e}")
                    config['GOOGLE_SHEET_ERROR_INFO'] = f"Error accessing Google Sheet: {e}. Check logs for details."
            
            if sheet_creation_triggered:
                 logger.info(f"Using newly created Google Sheet with ID: {self.sheet_id}. Original configured ID was '{self.config.get('GOOGLE_SHEET_ID')}'.")

        else:
            self.sheet_service = None
            if not self.user_credentials:
                logger.warning("User Google OAuth credentials not found or failed to load.")
            elif not self.user_credentials.valid:
                logger.warning("User Google OAuth credentials are not valid (e.g., expired and no refresh token).")
                # Attempt to refresh might happen within googleapiclient, or we might need explicit refresh logic

    def _check_internet_connection(self, host="8.8.8.8", port=53, timeout=5, max_retries=3):
        """
        Check if there is an internet connection by trying to connect to Google's DNS.
        
        Args:
            host (str): The host to try connecting to (default is Google's DNS)
            port (int): The port to connect on (default is 53, DNS port)
            timeout (int): Connection timeout in seconds
            max_retries (int): Maximum number of connection attempts
            
        Returns:
            bool: True if connection successful, False otherwise
        """
        for attempt in range(max_retries):
            s = None  # Initialize s to None
            try:
                # socket.setdefaulttimeout(timeout) # Avoid using global default timeout
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(timeout) # Set timeout only for this socket instance
                s.connect((host, port))
                logger.info("Internet connection test successful")
                return True
            except socket.error as ex:
                logger.warning(f"Internet connection test attempt {attempt+1}/{max_retries} failed: {ex}")
                if attempt < max_retries - 1:
                    # Wait a bit before retrying
                    time.sleep(2) # Consider making this delay configurable or exponential
                else:
                    logger.error(f"Internet connection test failed after {max_retries} attempts")
            except Exception as e: # Catching broader exceptions during socket operations
                logger.error(f"Unexpected error during internet connection test: {e}")
                # Depending on the error, you might not want to immediately return False or retry.
                # For simplicity here, we'll let it fall through to the retry or final False.
                if attempt == max_retries - 1: # If it's the last attempt on an unexpected error
                    return False
            finally:
                if s:
                    s.close() # Ensure the socket is closed
        
        return False

    def _get_sheet_service_with_oauth(self, credentials: UserCredentials):
        """
        Initialize and return the Google Sheets service object using OAuth credentials.
        
        Args:
            credentials (google.oauth2.credentials.Credentials): User OAuth credentials.
            
        Returns:
            The Google Sheets service object or None if initialization fails.
        """
        if not credentials or not credentials.valid:
            logger.error("Cannot initialize Google Sheets service: OAuth credentials invalid or missing.")
            return None
        try:
            # Don't create custom HTTP object, as it's mutually exclusive with credentials
            # Just build service with credentials
            service = build('sheets', 'v4', credentials=credentials)
            logger.info("Google Sheets service initialized successfully using OAuth credentials.")
            return service
        except Exception as e:
            logger.error(f"Error initializing Google Sheets service with OAuth: {e}")
            return None

    # Remove or comment out the old _get_sheet_service that used service account file
    # def _get_sheet_service(self):
    #     """
    #     Initialize and return the Google Sheets service object.
    #     
    #     Returns:
    #         The Google Sheets service object or None if initialization fails.
    #     """
    #     # if not are_google_credentials_configured(): # Old check
    #     #     logger.warning("Google credentials are not configured in UI settings.")
    #     #     return None
            
    #     # Try service account first (legacy or fallback - decide on strategy)
    #     service_account_creds_path = 'credentials.json' # Path to service account file
    #     if os.path.exists(service_account_creds_path):
    #         try:
    #             from google.oauth2 import service_account
    #             credentials = service_account.Credentials.from_service_account_file(
    #                 service_account_creds_path, 
    #                 scopes=['https://www.googleapis.com/auth/spreadsheets']
    #             )
    #             service = build('sheets', 'v4', credentials=credentials)
    #             logger.info("Google Sheets service initialized successfully using Service Account.")
    #             return service
    #         except Exception as e:
    #             logger.error(f"Error initializing Google Sheets service with Service Account: {e}")
    #             # Fall through to try user OAuth or fail
    #     else:
    #         logger.info("Service account credentials.json not found.")
        
    #     # If service account failed or not present, rely on instance's self.user_credentials
    #     if self.user_credentials and self.user_credentials.valid:
    #        return self._get_sheet_service_with_oauth(self.user_credentials)

    #     logger.warning("Could not initialize Google Sheets service. No valid credentials found.")
    #     return None

    def refresh_google_connection(self) -> bool:
        """
        Attempts to reload OAuth credentials and re-initialize the Google Sheets service.
        Returns True if the service is successfully initialized, False otherwise.
        """
        logger.info("Attempting to refresh Google connection...")
        
        # Check internet connectivity first
        if not self._check_internet_connection():
            logger.error("Cannot refresh Google connection: No internet connection available.")
            return False
        
        self.user_credentials = load_google_oauth_credentials()
        if self.user_credentials and self.user_credentials.valid:
            self.sheet_service = self._get_sheet_service_with_oauth(self.user_credentials)
            if self.sheet_service:
                logger.info("Google connection refreshed and service re-initialized.")
                return True
            else:
                logger.error("Failed to re-initialize Google Sheets service after credential reload.")
                return False
        elif self.user_credentials and not self.user_credentials.valid and self.user_credentials.refresh_token:
            logger.info("Credentials loaded but are invalid/expired. Attempting refresh...")
            try:
                from google.auth.transport.requests import Request
                # Use the Request class without setting timeout since we have a global socket timeout
                self.user_credentials.refresh(Request())
                from utils.ui_config_manager import save_google_oauth_credentials # To save refreshed token
                save_google_oauth_credentials(self.user_credentials) # Save the updated credentials
                self.sheet_service = self._get_sheet_service_with_oauth(self.user_credentials)
                if self.sheet_service:
                    logger.info("Successfully refreshed Google OAuth token and re-initialized service.")
                    return True
                else:
                    logger.error("Failed to re-initialize Google Sheets service after token refresh.")
                    return False
            except TimeoutError as e:
                logger.error(f"Timeout refreshing Google OAuth token: {e}")
                self.sheet_service = None
                return False
            except Exception as e:
                logger.error(f"Error refreshing Google OAuth token: {e}")
                self.sheet_service = None
                return False
        else:
            logger.warning("Failed to refresh Google connection: No valid credentials loaded.")
            self.sheet_service = None
            return False

    def append_leads_to_sheet(self, leads_data: List[Dict[str, Any]]) -> bool:
        """
        Append new leads to the Google Sheet.
        
        Args:
            leads_data (list): List of lead dictionaries to append.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        if not leads_data:
            logger.warning("No leads data to append.")
            return False
        
        # Clean and filter leads
        cleaned_leads = self._clean_leads_data(leads_data)
        unique_leads = self.filter_duplicates(cleaned_leads)
        
        if not unique_leads:
            logger.info("No new unique leads to add.")
            return True
        
        # Save to local backup first
        self._save_to_local_backup(unique_leads)
        
        # If Google Sheets service is not available, return True since we saved locally
        if not self.sheet_service:
            if are_google_oauth_credentials_present():
                logger.warning("Sheets service not initialized, but OAuth credentials seem present. Attempting to refresh connection.")
                if not self.refresh_google_connection(): # Try to refresh/reconnect
                    logger.error("Failed to refresh Google connection. Leads saved locally only.")
                    return True # Saved locally, so consider it a success for this part
            else:
                logger.warning("Sheets service not initialized and no OAuth credentials. Leads saved locally only.")
                return True # Saved locally

        # If service became available after refresh
        if not self.sheet_service:
             logger.error("Google Sheets service still unavailable after refresh attempt. Leads saved locally only.")
             return True
        
        # Convert leads to row format
        value_range_body = {
            'values': [self._lead_to_row(lead) for lead in unique_leads]
        }
        
        try:
            request = self.sheet_service.spreadsheets().values().append(
                spreadsheetId=self.sheet_id,
                range=self.leads_sheet_range,
                valueInputOption='USER_ENTERED',
                insertDataOption='INSERT_ROWS',
                body=value_range_body
            )
            response = request.execute()
            logger.info(f"Successfully added {len(unique_leads)} leads to Google Sheet.")
            return True
        except HttpError as error:
            logger.error(f"Error appending to Google Sheet: {error}")
            # If a 401 or 403 error, token might be stale, try to refresh
            if error.resp.status in [401, 403]:
                logger.info(f"Google API returned {error.resp.status}. Attempting token refresh.")
                if self.refresh_google_connection():
                    logger.info("Token refreshed. Retrying append operation.")
                    # Retry the append operation
                    try:
                        request = self.sheet_service.spreadsheets().values().append(
                            spreadsheetId=self.sheet_id,
                            range=self.leads_sheet_range,
                            valueInputOption='USER_ENTERED',
                            insertDataOption='INSERT_ROWS',
                            body=value_range_body
                        )
                        response = request.execute()
                        logger.info(f"Successfully added {len(unique_leads)} leads to Google Sheet after refresh.")
                        return True
                    except HttpError as retry_error:
                        logger.error(f"Error appending to Google Sheet after refresh: {retry_error}")
                        return False # Failed even after refresh
                else:
                    logger.error("Token refresh failed. Cannot append to Google Sheet.")
                    return False
            return False # Other HttpError
        except TimeoutError as error:
            logger.error(f"Timeout appending to Google Sheet: {error}. Check your network connection.")
            return False
        except Exception as error:
            logger.error(f"Unexpected error appending to Google Sheet: {error}")
            return False
    
    def _lead_to_row(self, lead: Dict[str, Any]) -> List[Any]:
        """
        Convert a lead dictionary to a row format for Google Sheets.
        
        Args:
            lead (dict): Lead dictionary.
        
        Returns:
            list: Lead data as a list for a sheet row.
        """
        # Define a fixed order of columns for the sheet
        # Adjust these fields to match your schema in the sheet
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return [
            timestamp,  # Timestamp
            lead.get('title', ''),  # Title
            lead.get('year', ''),  # Year
            lead.get('make', ''),  # Make
            lead.get('model', ''),  # Model
            lead.get('price', ''),  # Price
            lead.get('source', ''),  # Source (e.g., "Craigslist", "Facebook")
            lead.get('listing_url', ''),  # Listing URL
            lead.get('description', ''),  # Description
            lead.get('phone_number', ''),  # Seller Phone (may be empty for many)
            lead.get('date_posted', ''),  # Date Posted
            lead.get('Thryv_Status', ''),  # Thryv_Status
            lead.get('Thryv_Lead_ID', '')  # Thryv_Lead_ID
        ]
    
    def _clean_leads_data(self, leads_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Clean and normalize lead data.
        
        Args:
            leads_data (list): List of lead dictionaries.
        
        Returns:
            list: Cleaned lead dictionaries.
        """
        cleaned_leads = []
        
        for lead in leads_data:
            cleaned_lead = lead.copy()
            
            # Handle price (remove $ and commas, convert to number)
            if 'price' in cleaned_lead and cleaned_lead['price']:
                try:
                    price_str = str(cleaned_lead['price'])
                    # Remove $ and commas
                    price_str = price_str.replace('$', '').replace(',', '')
                    cleaned_lead['price'] = int(float(price_str))
                except (ValueError, TypeError):
                    logger.warning(f"Could not parse price: {cleaned_lead.get('price')}")
            
            # Convert year to integer if possible
            if 'year' in cleaned_lead and cleaned_lead['year']:
                try:
                    cleaned_lead['year'] = int(cleaned_lead['year'])
                except (ValueError, TypeError):
                    logger.warning(f"Could not parse year: {cleaned_lead.get('year')}")
            
            # Add to cleaned leads if it passes minimum year check
            min_year = int(self.config.get('MIN_VEHICLE_YEAR', 2018))
            try:
                if cleaned_lead.get('year', 0) >= min_year:
                    cleaned_leads.append(cleaned_lead)
                else:
                    logger.debug(f"Skipping lead with year {cleaned_lead.get('year')} < {min_year}")
            except (ValueError, TypeError):
                logger.warning(f"Year comparison failed for lead: {cleaned_lead.get('title')}")
                # If we can't determine the year, include the lead for manual review
                cleaned_leads.append(cleaned_lead)
        
        return cleaned_leads
    
    def filter_duplicates(self, leads_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter out leads that already exist in the sheet.
        
        Args:
            leads_data (list): List of lead dictionaries.
        
        Returns:
            list: Filtered leads that don't exist in the sheet.
        """
        if not self.sheet_service:
            if are_google_oauth_credentials_present():
                logger.warning("Sheets service not initialized for filter_duplicates. Attempting refresh.")
                if not self.refresh_google_connection():
                    logger.error("Failed to refresh Google connection for filter_duplicates. Assuming all leads are new.")
                    return leads_data # Cannot check duplicates, assume all new
            else:
                logger.warning("Sheets service not initialized and no OAuth. Assuming all leads are new for filter_duplicates.")
                return leads_data # Cannot check duplicates

        if not self.sheet_service:
             logger.error("Google Sheets service still unavailable for filter_duplicates. Assuming all leads are new.")
             return leads_data

        if not leads_data:
            return []
        
        try:
            request = self.sheet_service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range=self.leads_sheet_range
            )
            result = request.execute()
            existing_values = result.get('values', [])
            if not existing_values: return leads_data

            url_column_index = 7 # Default: Listing URL in column H (index 7)
            try: # Try to find 'listing_url' in headers
                headers = [h.lower().replace(' ', '_') for h in existing_values[0]]
                if 'listing_url' in headers:
                    url_column_index = headers.index('listing_url')
            except IndexError:
                logger.warning("Could not read headers for duplicate check, using default URL column index.")

            existing_urls = set()
            for row in existing_values[1:]:
                if len(row) > url_column_index and row[url_column_index]:
                    existing_urls.add(row[url_column_index])
            
            unique_leads = []
            for lead in leads_data:
                listing_url = lead.get('listing_url', '')
                if listing_url and listing_url not in existing_urls:
                    unique_leads.append(lead)
                elif listing_url in existing_urls:
                    logger.debug(f"Skipping duplicate lead: {lead.get('title')} - {listing_url}")
                else: # No URL, cannot reliably check for duplicates, include for manual review
                    logger.warning(f"Lead missing URL, cannot check for duplicate, including: {lead.get('title')}")
                    unique_leads.append(lead)
            
            logger.info(f"Found {len(leads_data) - len(unique_leads)} duplicates out of {len(leads_data)} leads.")
            return unique_leads
        
        except HttpError as error:
            logger.error(f"Error checking for duplicates: {error}")
            if error.resp.status in [401, 403]:
                logger.info(f"Google API returned {error.resp.status} for filter_duplicates. Attempting token refresh.")
                if self.refresh_google_connection():
                    logger.info("Token refreshed. Retrying filter_duplicates.")
                    return self.filter_duplicates(leads_data) # Retry
                else:
                    logger.error("Token refresh failed for filter_duplicates. Assuming all leads are new.")
                    return leads_data
            return leads_data # For other HttpErrors, assume all new
        except TimeoutError as error:
            logger.error(f"Timeout checking for duplicates: {error}. Check your network connection.")
            return leads_data  # Assume all new on timeout
        except Exception as error:
            logger.error(f"Unexpected error checking for duplicates: {error}")
            return leads_data  # Assume all new on error
    
    def _save_to_local_backup(self, leads_data: List[Dict[str, Any]]):
        """
        Save leads to a local JSON file as backup or for offline usage.
        
        Args:
            leads_data (list): List of lead dictionaries to save.
        """
        try:
            # Read existing leads if file exists
            existing_leads = []
            if os.path.exists(LOCAL_DATA_FILE):
                with open(LOCAL_DATA_FILE, 'r') as f:
                    try:
                        existing_leads = json.load(f)
                    except json.JSONDecodeError:
                        logger.error(f"Error reading local data file. Starting fresh.")
                        existing_leads = []
            
            # Add new leads
            for lead in leads_data:
                # Add a local ID and timestamp if not present
                if '_local_id' not in lead:
                    lead['_local_id'] = str(datetime.now().timestamp())
                if 'Date Scraped' not in lead:
                    lead['Date Scraped'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                existing_leads.append(lead)
            
            # Write back to file
            with open(LOCAL_DATA_FILE, 'w') as f:
                json.dump(existing_leads, f, indent=2)
            
            logger.info(f"Saved {len(leads_data)} leads to local backup file.")
        except Exception as e:
            logger.error(f"Error saving to local backup: {e}")
    
    def get_all_leads(self) -> List[Dict[str, Any]]:
        """
        Retrieve all leads from the Google Sheet or local backup.
        
        Returns:
            list: List of lead dictionaries.
        """
        if not self.sheet_service:
            if are_google_oauth_credentials_present():
                logger.warning("Sheets service not initialized for get_all_leads, but OAuth credentials seem present. Attempting to refresh connection.")
                if not self.refresh_google_connection():
                    logger.error("Failed to refresh Google connection. Falling back to local backup for get_all_leads.")
                    return self._get_leads_from_local_backup()
            else:
                logger.warning("Sheet service not initialized and no OAuth credentials. Falling back to local backup for get_all_leads.")
                return self._get_leads_from_local_backup()
        
        # If service became available after refresh or was already available
        if not self.sheet_service:
            logger.error("Google Sheets service still unavailable for get_all_leads. Falling back to local backup.")
            return self._get_leads_from_local_backup()
            
        try:
            request = self.sheet_service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range=self.leads_sheet_range
            )
            
            # Use the retry helper instead of direct execute
            try:
                result = self._execute_with_retry(request)
            except (HttpError, TimeoutError) as error:
                logger.error(f"Error retrieving leads from Google Sheet after retries: {error}")
                return self._get_leads_from_local_backup()
            
            values = result.get('values', [])
            
            if not values:
                logger.info("No leads found in Google Sheet.")
                return self._get_leads_from_local_backup()
            
            headers = [h.lower().replace(' ', '_') for h in values[0]]
            leads = []
            for row in values[1:]:
                padded_row = row + [''] * (len(headers) - len(row))
                lead = dict(zip(headers, padded_row))
                leads.append(lead)
            
            logger.info(f"Retrieved {len(leads)} leads from Google Sheet.")
            return leads
        
        except HttpError as error:
            logger.error(f"Error retrieving leads from Google Sheet: {error}")
            if error.resp.status in [401, 403]: # Unauthorized or Forbidden
                logger.info(f"Google API returned {error.resp.status} for get_all_leads. Attempting token refresh.")
                if self.refresh_google_connection():
                    logger.info("Token refreshed. Retrying get_all_leads operation.")
                    # Retry the get operation
                    try:
                        request = self.sheet_service.spreadsheets().values().get(
                            spreadsheetId=self.sheet_id,
                            range=self.leads_sheet_range
                        )
                        try:
                            result = self._execute_with_retry(request)
                        except (HttpError, TimeoutError) as retry_error:
                            logger.error(f"Error retrieving leads from Google Sheet after refresh and retries: {retry_error}")
                            return self._get_leads_from_local_backup()
                            
                        values = result.get('values', [])
                        if not values: return self._get_leads_from_local_backup()
                        headers = [h.lower().replace(' ', '_') for h in values[0]]
                        leads = [dict(zip(headers, r + [''] * (len(headers) - len(r)))) for r in values[1:]]
                        logger.info(f"Retrieved {len(leads)} leads from Google Sheet after refresh.")
                        return leads
                    except Exception as retry_error:
                        logger.error(f"Error retrieving leads from Google Sheet after refresh: {retry_error}")
                        return self._get_leads_from_local_backup() # Fallback on retry failure
                else:
                    logger.error("Token refresh failed. Falling back to local backup for get_all_leads.")
                    return self._get_leads_from_local_backup()
            return self._get_leads_from_local_backup() # Fallback for other HttpErrors
        except TimeoutError as error:
            logger.error(f"Timeout retrieving leads from Google Sheet: {error}. Falling back to local backup.")
            return self._get_leads_from_local_backup()
        except Exception as error:
            logger.error(f"Unexpected error retrieving leads from Google Sheet: {error}. Falling back to local backup.")
            return self._get_leads_from_local_backup()
    
    def _get_leads_from_local_backup(self) -> List[Dict[str, Any]]:
        """
        Retrieve leads from local backup file when Google Sheets is not available.
        
        Returns:
            list: List of lead dictionaries from local backup.
        """
        try:
            if os.path.exists(LOCAL_DATA_FILE):
                with open(LOCAL_DATA_FILE, 'r') as f:
                    leads = json.load(f)
                logger.info(f"Retrieved {len(leads)} leads from local backup.")
                return leads
            else:
                logger.warning("No local backup file found.")
                return []
        except Exception as e:
            logger.error(f"Error reading from local backup: {e}")
            return []
    
    def update_lead_status(self, lead_id: str, status: str, notes: Optional[str] = None) -> bool:
        """
        Update a lead's status and notes in the local backup file.
        
        Args:
            lead_id (str): The lead's ID.
            status (str): The new status to set.
            notes (str, optional): Optional notes to add or update.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            if not os.path.exists(LOCAL_DATA_FILE):
                logger.warning("No local backup file found to update lead status.")
                return False
            
            with open(LOCAL_DATA_FILE, 'r') as f:
                leads = json.load(f)
            
            # Find the lead by ID
            lead_found = False
            for lead in leads:
                if lead.get('_local_id') == lead_id:
                    lead['Status'] = status
                    if notes:
                        lead['Notes'] = notes
                    lead['Last_Updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    lead_found = True
                    break
            
            if lead_found:
                # Write back to file
                with open(LOCAL_DATA_FILE, 'w') as f:
                    json.dump(leads, f, indent=2)
                logger.info(f"Updated lead {lead_id} status to {status}")
                return True
            else:
                logger.warning(f"Lead with ID {lead_id} not found.")
                return False
        except Exception as e:
            logger.error(f"Error updating lead status in local backup: {e}")
            return False
    
    def update_thryv_status(self, row_index: int, thryv_status: str, thryv_lead_id: Optional[str] = None) -> bool:
        """
        Update the Thryv status and lead ID for a specific lead in the Google Sheet.
        
        Args:
            row_index (int): The 1-based row index in the sheet.
            thryv_status (str): Status to update ("Sent to Thryv", "Error", etc.).
            thryv_lead_id (str, optional): Thryv Lead ID if available.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        if not self.sheet_service:
            if are_google_oauth_credentials_present():
                logger.warning("Sheets service not initialized for update_thryv_status. Attempting refresh.")
                if not self.refresh_google_connection():
                    logger.error("Failed to refresh Google connection. Cannot update Thryv status in sheet.")
                    return False
            else:
                logger.warning("Sheets service not initialized and no OAuth. Cannot update Thryv status in sheet.")
                return False
        
        if not self.sheet_service:
             logger.error("Google Sheets service still unavailable for update_thryv_status.")
             return False
            
        try:
            # Define the range for Thryv status column (assume column L for status, M for ID)
            # This needs to be robust. Ideally, find column by header name.
            # For now, let's assume column L (index 11) for Thryv_Status and M (index 12) for Thryv_Lead_ID
            status_column_letter = 'L' # Placeholder
            lead_id_column_letter = 'M' # Placeholder

            # A more robust way: get headers and find column index
            try:
                request = self.sheet_service.spreadsheets().values().get(
                    spreadsheetId=self.sheet_id, 
                    range=f"{self.leads_sheet_range.split('!')[0]}!1:1"
                )
                header_result = request.execute()
                headers = [h.lower().replace(' ', '_') for h in header_result.get('values', [[]])[0]]
                if 'thryv_status' in headers:
                    status_column_letter = chr(ord('A') + headers.index('thryv_status'))
                if 'thryv_lead_id' in headers:
                    lead_id_column_letter = chr(ord('A') + headers.index('thryv_lead_id'))
            except Exception as header_e:
                logger.warning(f"Could not dynamically determine Thryv status columns, using defaults L & M: {header_e}")

            status_range = f"{self.leads_sheet_range.split('!')[0]}!{status_column_letter}{row_index}"
            lead_id_range_val = f"{self.leads_sheet_range.split('!')[0]}!{lead_id_column_letter}{row_index}"
            
            status_body = {
                'values': [[thryv_status]]
            }
            request = self.sheet_service.spreadsheets().values().update(
                spreadsheetId=self.sheet_id,
                range=status_range,
                valueInputOption='USER_ENTERED',
                body=status_body
            )
            request.execute()
            
            if thryv_lead_id:
                lead_id_body = {
                    'values': [[thryv_lead_id]]
                }
                request = self.sheet_service.spreadsheets().values().update(
                    spreadsheetId=self.sheet_id,
                    range=lead_id_range_val,
                    valueInputOption='USER_ENTERED',
                    body=lead_id_body
                )
                request.execute()
                
            logger.info(f"Updated Thryv status to '{thryv_status}' for row {row_index}")
            return True
            
        except HttpError as error:
            logger.error(f"Error updating Thryv status in Google Sheet: {error}")
            if error.resp.status in [401, 403]:
                logger.info(f"Google API returned {error.resp.status} for update_thryv_status. Attempting refresh.")
                if self.refresh_google_connection():
                    logger.info("Token refreshed. Retrying update_thryv_status.")
                    return self.update_thryv_status(row_index, thryv_status, thryv_lead_id) # Retry
                else:
                    logger.error("Token refresh failed for update_thryv_status.")
                    return False
            return False
        except TimeoutError as error:
            logger.error(f"Timeout updating Thryv status in Google Sheet: {error}. Check your network connection.")
            return False
        except Exception as error:
            logger.error(f"Unexpected error updating Thryv status in Google Sheet: {error}")
            return False

    def get_created_sheet_info(self) -> Optional[str]:
        """Returns the info message if a new sheet was created, None otherwise."""
        return self.config.pop('GOOGLE_SHEET_ID_CREATED_INFO', None)

    def get_sheet_error_info(self) -> Optional[str]:
        """Returns an error message related to sheet access or creation, if any."""
        return self.config.pop('GOOGLE_SHEET_ERROR_INFO', None)

    def _create_new_sheet(self) -> Optional[str]:
        """
        Creates a new Google Spreadsheet with a default title and header row.
        
        Returns:
            Optional[str]: The ID of the newly created spreadsheet, or None if creation failed.
        """
        if not self.sheet_service:
            logger.error("Cannot create new sheet: Google Sheets service is not available.")
            return None
            
        try:
            spreadsheet_title = f"Car Finder AI Leads - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            spreadsheet_body = {
                'properties': {
                    'title': spreadsheet_title
                }
            }
            request = self.sheet_service.spreadsheets().create(
                body=spreadsheet_body, 
                fields='spreadsheetId'
            )
            spreadsheet = request.execute()
            new_spreadsheet_id = spreadsheet.get('spreadsheetId')
            logger.info(f"Created new Google Spreadsheet with title '{spreadsheet_title}' and ID: {new_spreadsheet_id}")
            
            # Add header row
            header_row = [
                "Timestamp", "Title", "Year", "Make", "Model", "Price", "Source", 
                "Listing URL", "Description", "Seller Phone", "Date Posted",
                "Thryv_Status", "Thryv_Lead_ID" # Added Thryv columns
            ]
            value_range_body = {
                'values': [header_row]
            }
            request = self.sheet_service.spreadsheets().values().update(
                spreadsheetId=new_spreadsheet_id,
                range='A1', # Update the first row of the default 'Sheet1'
                valueInputOption='USER_ENTERED',
                body=value_range_body
            )
            request.execute()
            logger.info(f"Added header row to new sheet ID: {new_spreadsheet_id}")
            
            # Rename the first sheet to 'Leads' for consistency with self.leads_sheet_range
            rename_sheet_request_body = {
                "requests": [
                    {
                        "updateSheetProperties": {
                            "properties": {
                                "sheetId": 0,  # The first sheet created by default has sheetId 0
                                "title": "Leads"
                            },
                            "fields": "title"
                        }
                    }
                ]
            }
            request = self.sheet_service.spreadsheets().batchUpdate(
                spreadsheetId=new_spreadsheet_id,
                body=rename_sheet_request_body
            )
            request.execute()
            logger.info(f"Renamed default sheet to 'Leads' for new sheet ID: {new_spreadsheet_id}")

            return new_spreadsheet_id
        except HttpError as error:
            logger.error(f"Error creating new Google Sheet: {error}")
            return None
        except TimeoutError as error:
            logger.error(f"Timeout creating new Google Sheet: {error}. Check your network connection.")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred while creating new Google Sheet: {e}")
            return None 

    def _execute_with_retry(self, request, max_retries=3, retry_delay=2):
        """
        Execute a Google API request with retries for better resilience.
        
        Args:
            request: The Google API request object
            max_retries (int): Maximum number of retry attempts
            retry_delay (int): Delay between retries in seconds
            
        Returns:
            The API response or None if all attempts fail
            
        Raises:
            Original exception after all retries are exhausted
        """
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                return request.execute()
            except (HttpError, TimeoutError) as error:
                last_exception = error
                if isinstance(error, HttpError) and error.resp.status not in [429, 500, 502, 503, 504]:
                    # Don't retry if it's not a rate limit or server error
                    raise
                
                logger.warning(f"API request attempt {attempt+1}/{max_retries} failed: {error}. Retrying in {retry_delay}s...")
                time.sleep(retry_delay)
                # Increase delay for next retry (exponential backoff)
                retry_delay *= 2
                continue
        
        # If we get here, all retries failed
        if last_exception:
            raise last_exception
        return None 