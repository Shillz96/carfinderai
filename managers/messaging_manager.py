import re
from utils.logger import setup_logger
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

# Set up logger
logger = setup_logger('messaging_manager')

class MessagingManager:
    def __init__(self, config):
        """
        Initialize the messaging manager
        
        Args:
            config (dict): Configuration dictionary
        """
        self.account_sid = config['twilio']['account_sid']
        self.auth_token = config['twilio']['auth_token']
        self.twilio_phone = config['twilio']['phone_number']
        
        # Initialize Twilio client
        try:
            self.client = Client(self.account_sid, self.auth_token)
            logger.info("Twilio client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Twilio client: {str(e)}")
            self.client = None
    
    def extract_phone_number(self, listing_data):
        """
        Extract phone number from listing data (if available)
        
        Args:
            listing_data (dict): Listing data dictionary
            
        Returns:
            str: Phone number or None
        """
        # Check if phone number is directly in the listing
        if 'phone_number' in listing_data and listing_data['phone_number']:
            return self._normalize_phone_number(listing_data['phone_number'])
        
        # Try to extract from listing description if available
        if 'description' in listing_data and listing_data['description']:
            return self._extract_phone_from_text(listing_data['description'])
        
        logger.info(f"No phone number found for listing: {listing_data.get('title', 'Unknown')}")
        return None
    
    def _extract_phone_from_text(self, text):
        """
        Extract phone number from text using regex
        
        Args:
            text (str): Text to search in
            
        Returns:
            str: Phone number or None
        """
        if not text:
            return None
        
        # Common US phone number patterns
        patterns = [
            r'(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})',  # 123-456-7890, 123.456.7890, 123 456 7890
            r'\((\d{3})\)[\s-]?\d{3}[-.\s]?\d{4}',  # (123) 456-7890, (123)456-7890
            r'\d{3}-\d{4}',  # Local number: 555-1234 (less reliable, might cause false positives)
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                return self._normalize_phone_number(matches[0])
        
        return None
    
    def _normalize_phone_number(self, phone):
        """
        Normalize phone number to E.164 format (+1XXXXXXXXXX for US)
        
        Args:
            phone (str): Raw phone number
            
        Returns:
            str: Normalized phone number
        """
        if not phone:
            return None
        
        # Remove non-digit characters
        digits_only = re.sub(r'\D', '', phone)
        
        # Handle US numbers (assuming all are US numbers for this project)
        if len(digits_only) == 10:
            return f"+1{digits_only}"
        elif len(digits_only) == 11 and digits_only.startswith('1'):
            return f"+{digits_only}"
        elif len(digits_only) == 7:  # Local number, assume Hawaii area code (808)
            return f"+1808{digits_only}"
        
        logger.warning(f"Unusual phone number format: {phone}, normalized to: {digits_only}")
        if len(digits_only) >= 10:  # At least has enough digits to be a phone number
            if not digits_only.startswith('1'):
                return f"+1{digits_only[-10:]}"  # Take the last 10 digits and add US country code
            else:
                return f"+{digits_only}"
        
        return None
    
    def send_sms(self, to_number, message_body):
        """
        Send SMS message using Twilio
        
        Args:
            to_number (str): Recipient phone number
            message_body (str): Message body
            
        Returns:
            dict: Dictionary with status and message_sid
        """
        if not self.client:
            logger.error("Twilio client not initialized")
            return {'status': 'failed', 'error': 'Twilio client not initialized'}
        
        # Normalize phone number
        normalized_number = self._normalize_phone_number(to_number)
        if not normalized_number:
            logger.error(f"Invalid phone number: {to_number}")
            return {'status': 'failed', 'error': 'Invalid phone number'}
        
        try:
            logger.info(f"Sending SMS to {normalized_number}")
            message = self.client.messages.create(
                from_=self.twilio_phone,
                to=normalized_number,
                body=message_body
            )
            
            logger.info(f"SMS sent successfully, SID: {message.sid}")
            return {
                'status': 'sent',
                'message_sid': message.sid,
                'to': normalized_number
            }
        except TwilioRestException as e:
            logger.error(f"Twilio error: {str(e)}")
            return {
                'status': 'failed',
                'error': str(e),
                'to': normalized_number
            }
        except Exception as e:
            logger.error(f"Error sending SMS: {str(e)}")
            return {
                'status': 'failed',
                'error': str(e),
                'to': normalized_number
            }
    
    def send_listing_inquiry(self, listing_data):
        """
        Send a standardized inquiry message for a car listing
        
        Args:
            listing_data (dict): Listing data
            
        Returns:
            dict: SMS sending result
        """
        # Extract phone number from listing
        phone_number = self.extract_phone_number(listing_data)
        if not phone_number:
            logger.warning(f"No phone number found for listing: {listing_data.get('title', 'Unknown')}")
            return {
                'status': 'failed',
                'error': 'No phone number found',
                'listing_id': listing_data.get('id', 'unknown')
            }
        
        # Create message using standard template
        year = listing_data.get('year', '')
        make = listing_data.get('make', '')
        model = listing_data.get('model', '')
        
        vehicle_info = f"{year} {make} {model}".strip()
        if vehicle_info == "":
            vehicle_info = listing_data.get('title', 'vehicle')
        
        message = f"Hi, I saw your listing for the {vehicle_info}. Is it still available?"
        
        # Send SMS
        result = self.send_sms(phone_number, message)
        result['listing_id'] = listing_data.get('id', 'unknown')
        
        return result 