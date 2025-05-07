"""
Mock service implementations for testing and development.
These services simulate the behavior of external APIs without making actual calls.
"""

import uuid
import json
import random
from datetime import datetime
from utils.logger import setup_logger

logger = setup_logger('mock_services')

class MockTwilioService:
    """Mock implementation of Twilio SMS service"""
    
    def __init__(self):
        self.sent_messages = []
        logger.info("Initialized Mock Twilio Service")
    
    def send_message(self, to, from_, body, **kwargs):
        """
        Simulate sending an SMS message
        
        Args:
            to (str): Recipient phone number
            from_ (str): Sender phone number
            body (str): Message content
            **kwargs: Additional parameters
            
        Returns:
            dict: Mock response with message SID
        """
        message_id = f"SM{uuid.uuid4().hex[:20]}"
        timestamp = datetime.now().isoformat()
        
        message = {
            'sid': message_id,
            'to': to,
            'from_': from_,
            'body': body,
            'date_created': timestamp,
            'status': 'sent'
        }
        
        self.sent_messages.append(message)
        logger.info(f"MOCK SMS: To: {to}, From: {from_}, Message: {body[:30]}...")
        
        return message


class MockGoogleSheetsService:
    """Mock implementation of Google Sheets API"""
    
    def __init__(self):
        self.data = [
            ["Title", "Year", "Make", "Model", "Price", "Description", "Listing URL", 
             "Phone Number", "Source", "Date Posted", "Date Added", "Thryv Status", "Thryv ID"]
        ]
        logger.info("Initialized Mock Google Sheets Service")
    
    def get_values(self, spreadsheet_id, range_name):
        """
        Get values from mock spreadsheet
        
        Args:
            spreadsheet_id (str): ID of the spreadsheet
            range_name (str): Range to retrieve
            
        Returns:
            dict: Mock response with values
        """
        logger.info(f"MOCK SHEETS: Getting values from {range_name}")
        return {'values': self.data}
    
    def append(self, spreadsheet_id, range_name, value_input_option, insert_data_option, body):
        """
        Append values to mock spreadsheet
        
        Args:
            spreadsheet_id (str): ID of the spreadsheet
            range_name (str): Range to append to
            value_input_option (str): How to interpret the values
            insert_data_option (str): How to insert the values
            body (dict): Values to append
            
        Returns:
            dict: Mock response
        """
        values = body.get('values', [])
        self.data.extend(values)
        
        logger.info(f"MOCK SHEETS: Appended {len(values)} rows")
        
        return {
            'spreadsheetId': spreadsheet_id,
            'updates': {
                'updatedRange': f"{range_name}!A{len(self.data)}:M{len(self.data) + len(values) - 1}",
                'updatedRows': len(values),
                'updatedColumns': 13,
                'updatedCells': len(values) * 13
            }
        }
    
    def update(self, spreadsheet_id, range_name, value_input_option, body):
        """
        Update values in mock spreadsheet
        
        Args:
            spreadsheet_id (str): ID of the spreadsheet
            range_name (str): Range to update
            value_input_option (str): How to interpret the values
            body (dict): Values to update
            
        Returns:
            dict: Mock response
        """
        # Parse the range to get row index
        # Example: 'Leads!L3:M3' would update row 3
        if 'L' in range_name and 'M' in range_name:
            try:
                row_index = int(range_name.split('!')[1].split(':')[0].replace('L', '')) - 1  # Convert to 0-indexed
                if row_index < len(self.data):
                    values = body.get('values', [[]])[0]
                    
                    # Update Thryv Status and Thryv ID (columns L and M)
                    if len(values) >= 1 and row_index > 0:
                        if len(self.data[row_index]) < 13:
                            self.data[row_index].extend([''] * (13 - len(self.data[row_index])))
                        
                        self.data[row_index][11] = values[0]  # Thryv Status
                        if len(values) > 1:
                            self.data[row_index][12] = values[1]  # Thryv ID
                    
                    logger.info(f"MOCK SHEETS: Updated row {row_index+1} with Thryv status: {values[0]}")
            except Exception as e:
                logger.error(f"MOCK SHEETS: Error updating range {range_name}: {str(e)}")
        
        return {
            'spreadsheetId': spreadsheet_id,
            'updatedRange': range_name,
            'updatedRows': 1,
            'updatedColumns': 2,
            'updatedCells': 2
        }


class MockThryvService:
    """Mock implementation of Thryv CRM API"""
    
    def __init__(self):
        self.leads = []
        self.authenticated = False
        logger.info("Initialized Mock Thryv Service")
    
    def authenticate(self):
        """
        Simulate authentication with Thryv API
        
        Returns:
            bool: Authentication success
        """
        self.authenticated = True
        logger.info("MOCK THRYV: Successfully authenticated")
        return True
    
    def create_lead(self, lead_data):
        """
        Create a mock lead in Thryv
        
        Args:
            lead_data (dict): Lead data to create
            
        Returns:
            tuple: (success, result) where result is lead ID on success or error message on failure
        """
        lead_id = f"TL{uuid.uuid4().hex[:8]}"
        
        lead_data['id'] = lead_id
        lead_data['created_at'] = datetime.now().isoformat()
        
        self.leads.append(lead_data)
        
        logger.info(f"MOCK THRYV: Created lead with ID {lead_id}")
        
        # Simulate occasional failures (10% chance)
        if random.random() < 0.1:
            logger.warning("MOCK THRYV: Simulating random failure")
            return False, "API timeout error"
        
        return True, lead_id


class MockEmailService:
    """Mock implementation of email service"""
    
    def __init__(self):
        self.sent_emails = []
        logger.info("Initialized Mock Email Service")
    
    def send_email(self, to, subject, body, from_email=None):
        """
        Simulate sending an email
        
        Args:
            to (str): Recipient email address
            subject (str): Email subject
            body (str): Email body (can be HTML)
            from_email (str, optional): Sender email address
            
        Returns:
            bool: Success status
        """
        email = {
            'to': to,
            'subject': subject,
            'body': body[:100] + '...' if len(body) > 100 else body,
            'from': from_email,
            'date': datetime.now().isoformat()
        }
        
        self.sent_emails.append(email)
        
        logger.info(f"MOCK EMAIL: To: {to}, Subject: {subject}")
        
        return True


def get_mock_services():
    """
    Get all mock service instances
    
    Returns:
        dict: Dictionary of mock service instances
    """
    return {
        'twilio': MockTwilioService(),
        'sheets': MockGoogleSheetsService(),
        'thryv': MockThryvService(),
        'email': MockEmailService()
    } 