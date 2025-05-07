"""
Mock versions of the manager classes for testing.
These use the mock services instead of real APIs.
"""

import logging
from datetime import datetime

# Set up logger
logger = logging.getLogger('mock_managers')

class MockMessagingManager:
    """Mock messaging manager for sending SMS messages."""
    
    def __init__(self, config, mock_twilio_service=None):
        """
        Initialize the mock messaging manager.
        
        Args:
            config (dict): Configuration dictionary
            mock_twilio_service (MockTwilioService): Mock Twilio service
        """
        self.config = config
        self.mock_twilio = mock_twilio_service
        self.from_number = config['twilio']['phone_number']
        logger.info("Initialized MockMessagingManager")
    
    def send_sms(self, to_number, message_body):
        """
        Send an SMS message to a recipient.
        
        Args:
            to_number (str): Recipient phone number
            message_body (str): Message content
            
        Returns:
            dict: Message information on success, None on failure
        """
        if not to_number or not message_body:
            logger.warning("Cannot send SMS: Missing phone number or message body")
            return None
        
        try:
            message = self.mock_twilio.send_message(
                to=to_number,
                from_=self.from_number,
                body=message_body
            )
            
            logger.info(f"Mock SMS sent to {to_number}: {message_body[:30]}...")
            return message
        
        except Exception as e:
            logger.error(f"Error sending mock SMS: {str(e)}")
            return None
    
    def send_listing_inquiry(self, listing_data):
        """
        Send an inquiry SMS about a listing to the seller.
        
        Args:
            listing_data (dict): Listing information including phone_number
            
        Returns:
            dict: Message information on success, None on failure
        """
        if not listing_data.get('phone_number'):
            logger.warning(f"No phone number found for listing: {listing_data.get('title')}")
            return None
        
        year = listing_data.get('year', '')
        make = listing_data.get('make', '')
        model = listing_data.get('model', '')
        
        # Create message using standard template
        message_body = f"Hi, I saw your listing for the {year} {make} {model}. Is it still available?"
        
        return self.send_sms(listing_data['phone_number'], message_body)


class MockDataManager:
    """Mock data manager for storing and retrieving listing data."""
    
    def __init__(self, config, mock_sheets_service=None):
        """
        Initialize the mock data manager.
        
        Args:
            config (dict): Configuration dictionary
            mock_sheets_service (MockGoogleSheetsService): Mock Google Sheets service
        """
        self.config = config
        self.mock_sheets = mock_sheets_service
        self.sheet_id = config['google_sheets']['sheet_id']
        logger.info("Initialized MockDataManager")
    
    def append_leads_to_sheet(self, leads_data):
        """
        Append new leads to the Google Sheet.
        
        Args:
            leads_data (list): List of lead dictionaries
            
        Returns:
            bool: Success status
        """
        if not leads_data:
            logger.warning("No leads to append")
            return False
        
        # Convert leads to rows for the sheet
        rows = []
        for lead in leads_data:
            # Add current date as Date Added
            lead['date_added'] = datetime.now().strftime('%Y-%m-%d')
            
            row = [
                lead.get('title', ''),
                lead.get('year', ''),
                lead.get('make', ''),
                lead.get('model', ''),
                lead.get('price', ''),
                lead.get('description', ''),
                lead.get('listing_url', ''),
                lead.get('phone_number', ''),
                lead.get('source', ''),
                lead.get('date_posted', ''),
                lead.get('date_added', ''),
                '',  # Thryv Status
                ''   # Thryv ID
            ]
            rows.append(row)
        
        try:
            # Use mock sheets service to append
            result = self.mock_sheets.append(
                spreadsheet_id=self.sheet_id,
                range_name='Leads!A:M',
                value_input_option='USER_ENTERED',
                insert_data_option='INSERT_ROWS',
                body={'values': rows}
            )
            
            logger.info(f"Appended {len(rows)} leads to mock Google Sheet")
            return True
            
        except Exception as e:
            logger.error(f"Error appending leads to mock Google Sheet: {str(e)}")
            return False
    
    def get_all_leads(self):
        """
        Get all leads from the Google Sheet.
        
        Returns:
            list: List of lead dictionaries
        """
        try:
            # Get data from mock sheets
            result = self.mock_sheets.get_values(
                spreadsheet_id=self.sheet_id,
                range_name='Leads!A:M'
            )
            
            values = result.get('values', [])
            
            if not values or len(values) <= 1:
                logger.warning("No leads found in mock Google Sheet")
                return []
            
            # Convert rows to dictionaries
            headers = ['title', 'year', 'make', 'model', 'price', 'description', 'listing_url', 
                      'phone_number', 'source', 'date_posted', 'date_added', 'thryv_status', 'thryv_id']
            
            leads = []
            for i, row in enumerate(values[1:], start=2):  # Skip header, start from row 2
                lead = {}
                
                # Add row index for updating
                lead['_row_index'] = i
                
                # Map columns to keys
                for j, header in enumerate(headers):
                    if j < len(row):
                        lead[header] = row[j]
                    else:
                        lead[header] = ''
                
                leads.append(lead)
            
            logger.info(f"Retrieved {len(leads)} leads from mock Google Sheet")
            return leads
            
        except Exception as e:
            logger.error(f"Error getting leads from mock Google Sheet: {str(e)}")
            return []
    
    def update_thryv_status(self, row_index, status, thryv_id=None):
        """
        Update the Thryv status for a lead.
        
        Args:
            row_index (int): Row index in the sheet
            status (str): Status to set
            thryv_id (str, optional): Thryv lead ID
            
        Returns:
            bool: Success status
        """
        try:
            # Create update values
            values = [[status, thryv_id if thryv_id else '']]
            
            # Update using mock sheets
            result = self.mock_sheets.update(
                spreadsheet_id=self.sheet_id,
                range_name=f'Leads!L{row_index}:M{row_index}',
                value_input_option='USER_ENTERED',
                body={'values': values}
            )
            
            logger.info(f"Updated Thryv status for row {row_index} to '{status}'")
            return True
            
        except Exception as e:
            logger.error(f"Error updating Thryv status in mock Google Sheet: {str(e)}")
            return False


class MockNotificationManager:
    """Mock notification manager for sending notifications to the client."""
    
    def __init__(self, config, messaging_manager, mock_email_service=None):
        """
        Initialize the mock notification manager.
        
        Args:
            config (dict): Configuration dictionary
            messaging_manager (MockMessagingManager): Mock messaging manager for SMS
            mock_email_service (MockEmailService): Mock email service
        """
        self.config = config
        self.messaging_manager = messaging_manager
        self.mock_email = mock_email_service
        self.client_email = config['client']['email']
        self.client_phone = config['client']['phone_number']
        logger.info("Initialized MockNotificationManager")
    
    def send_email(self, subject, body):
        """
        Send an email to the client.
        
        Args:
            subject (str): Email subject
            body (str): Email body (can be HTML)
            
        Returns:
            bool: Success status
        """
        try:
            result = self.mock_email.send_email(
                to=self.client_email,
                subject=subject,
                body=body,
                from_email=self.config.get('email', {}).get('from', 'noreply@carfinderai.com')
            )
            
            logger.info(f"Mock email sent to {self.client_email}: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending mock email: {str(e)}")
            return False
    
    def notify_client_about_lead(self, lead_data, sms_status="Not Attempted"):
        """
        Notify the client about a new lead via email and SMS.
        
        Args:
            lead_data (dict): Lead information
            sms_status (str): Status of seller SMS
            
        Returns:
            bool: Success status
        """
        # Prepare email subject and body
        year = lead_data.get('year', '')
        make = lead_data.get('make', '')
        model = lead_data.get('model', '')
        
        subject = f"New Car Lead: {year} {make} {model}"
        
        # Create HTML body
        body = f"""
        <html>
        <body>
            <h2>New Car Lead Found</h2>
            <p><strong>Vehicle:</strong> {year} {make} {model}</p>
            <p><strong>Price:</strong> ${lead_data.get('price', 'N/A')}</p>
            <p><strong>Description:</strong> {lead_data.get('description', 'N/A')}</p>
            <p><strong>Source:</strong> {lead_data.get('source', 'N/A')}</p>
            <p><strong>Date Posted:</strong> {lead_data.get('date_posted', 'N/A')}</p>
            <p><strong>Listing URL:</strong> <a href="{lead_data.get('listing_url', '#')}">{lead_data.get('listing_url', 'N/A')}</a></p>
            <p><strong>Seller Phone:</strong> {lead_data.get('phone_number', 'Not available')}</p>
            <p><strong>SMS to Seller:</strong> {sms_status}</p>
        </body>
        </html>
        """
        
        # Send email
        email_success = self.send_email(subject, body)
        
        # Send SMS notification
        sms_body = f"New Car Lead: {year} {make} {model} - ${lead_data.get('price', 'N/A')}. Check your email for details."
        sms_success = self.messaging_manager.send_sms(self.client_phone, sms_body)
        
        return email_success or sms_success != None


class MockThryvIntegrator:
    """Mock Thryv CRM integrator."""
    
    def __init__(self, config, mock_thryv_service=None):
        """
        Initialize the mock Thryv integrator.
        
        Args:
            config (dict): Configuration dictionary
            mock_thryv_service (MockThryvService): Mock Thryv service
        """
        self.config = config
        self.mock_thryv = mock_thryv_service
        self.authenticated = False
        logger.info("Initialized MockThryvIntegrator")
    
    def authenticate(self):
        """
        Authenticate with the Thryv API.
        
        Returns:
            bool: Authentication success
        """
        try:
            self.authenticated = self.mock_thryv.authenticate()
            logger.info("Successfully authenticated with mock Thryv API")
            return self.authenticated
            
        except Exception as e:
            logger.error(f"Error authenticating with mock Thryv API: {str(e)}")
            return False
    
    def create_thryv_lead(self, lead_data):
        """
        Create a lead in Thryv CRM.
        
        Args:
            lead_data (dict): Lead information
            
        Returns:
            tuple: (success, result) where result is lead ID on success or error message on failure
        """
        if not self.authenticated:
            return False, "Not authenticated with Thryv API"
        
        try:
            # Transform lead_data to Thryv format
            thryv_lead = {
                'businessId': self.config['thryv'].get('account_id', 'mock_account'),
                'firstName': 'Potential',
                'lastName': 'Buyer',
                'source': lead_data.get('source', 'Craigslist'),
                'notes': f"Vehicle: {lead_data.get('year', '')} {lead_data.get('make', '')} {lead_data.get('model', '')}\n"
                       f"Price: ${lead_data.get('price', 'N/A')}\n"
                       f"Description: {lead_data.get('description', 'N/A')}\n"
                       f"Listing URL: {lead_data.get('listing_url', 'N/A')}\n"
                       f"Seller Phone: {lead_data.get('phone_number', 'Not available')}\n"
                       f"Date Posted: {lead_data.get('date_posted', 'N/A')}"
            }
            
            # Create lead in mock Thryv
            success, result = self.mock_thryv.create_lead(thryv_lead)
            
            if success:
                logger.info(f"Successfully created lead in mock Thryv with ID {result}")
            else:
                logger.warning(f"Failed to create lead in mock Thryv: {result}")
            
            return success, result
            
        except Exception as e:
            logger.error(f"Error creating lead in mock Thryv: {str(e)}")
            return False, str(e) 