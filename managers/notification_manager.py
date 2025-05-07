"""
Notification Manager module responsible for sending notifications to the client
about new leads via email and SMS.
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional

from utils.logger import setup_logger
from managers.messaging_manager import MessagingManager

# Set up logger
logger = setup_logger('notification_manager')

class NotificationManager:
    """
    Manages notifications to the client, including email and SMS.
    
    Args:
        config (dict): Configuration dictionary containing email settings and
                       client contact information.
        messaging_manager (MessagingManager): Instance of MessagingManager for SMS
    """
    
    def __init__(self, config: Dict[str, Any], messaging_manager: MessagingManager = None):
        """
        Initialize the NotificationManager with provided configuration.
        
        Args:
            config (dict): Configuration dictionary.
            messaging_manager (MessagingManager, optional): Instance of MessagingManager for SMS.
                           If None, will create a new instance.
        """
        self.config = config
        self.client_email = config.get('CLIENT_EMAIL')
        self.client_phone = config.get('CLIENT_PHONE_NUMBER')
        
        # Set up email configuration
        self.email_host = config.get('EMAIL_HOST', 'smtp.gmail.com')
        self.email_port = int(config.get('EMAIL_PORT', 587))
        self.email_username = config.get('EMAIL_USERNAME')
        self.email_password = config.get('EMAIL_PASSWORD')
        self.email_from = config.get('EMAIL_FROM', self.email_username)
        
        # Set up messaging manager for SMS (if not provided)
        self.messaging_manager = messaging_manager or MessagingManager(config)
    
    def send_email_notification(self, lead: Dict[str, Any], sms_status: str = "Not attempted") -> bool:
        """
        Send an email notification to the client about a new lead.
        
        Args:
            lead (dict): Lead information.
            sms_status (str): Status of SMS sent to seller (e.g., "Sent", "Failed", "Not attempted").
        
        Returns:
            bool: True if email sent successfully, False otherwise.
        """
        if not self.client_email or not self.email_username or not self.email_password:
            logger.warning("Email notification not sent: Missing email configuration or client email.")
            return False
        
        try:
            # Create email
            subject = f"New Car Lead: {lead.get('year', '')} {lead.get('make', '')} {lead.get('model', '')}"
            
            # Create a multipart email
            msg = MIMEMultipart()
            msg['From'] = self.email_from
            msg['To'] = self.client_email
            msg['Subject'] = subject
            
            # Create email body
            body = self._format_email_body(lead, sms_status)
            msg.attach(MIMEText(body, 'html'))
            
            # Send email
            server = smtplib.SMTP(self.email_host, self.email_port)
            server.starttls()
            server.login(self.email_username, self.email_password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email notification sent to {self.client_email} for lead: {lead.get('title')}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
            return False
    
    def _format_email_body(self, lead: Dict[str, Any], sms_status: str) -> str:
        """
        Format the email body with lead details.
        
        Args:
            lead (dict): Lead information.
            sms_status (str): Status of SMS sent to seller.
        
        Returns:
            str: Formatted HTML email body.
        """
        # HTML template for better formatting
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .lead-details {{ border: 1px solid #ddd; padding: 15px; border-radius: 5px; }}
                .lead-title {{ font-size: 18px; font-weight: bold; color: #333; }}
                .section {{ margin-top: 10px; }}
                .label {{ font-weight: bold; }}
                .value {{ margin-left: 5px; }}
                .contact {{ background-color: #f9f9f9; padding: 10px; margin-top: 15px; }}
                .status {{ margin-top: 15px; font-style: italic; }}
            </style>
        </head>
        <body>
            <p>A new car lead has been found:</p>
            
            <div class="lead-details">
                <div class="lead-title">{lead.get('year', '')} {lead.get('make', '')} {lead.get('model', '')}</div>
                
                <div class="section">
                    <span class="label">Price:</span>
                    <span class="value">${lead.get('price', 'N/A')}</span>
                </div>
                
                <div class="section">
                    <span class="label">Source:</span>
                    <span class="value">{lead.get('source', 'N/A')}</span>
                </div>
                
                <div class="section">
                    <span class="label">Listing URL:</span>
                    <span class="value"><a href="{lead.get('listing_url', '#')}">{lead.get('listing_url', 'N/A')}</a></span>
                </div>
                
                <div class="section">
                    <span class="label">Description:</span>
                    <div class="value">{lead.get('description', 'No description available.')}</div>
                </div>
                
                <div class="section">
                    <span class="label">Date Posted:</span>
                    <span class="value">{lead.get('date_posted', 'N/A')}</span>
                </div>
                
                <div class="contact">
                    <span class="label">Seller Phone:</span>
                    <span class="value">{lead.get('phone_number', 'Not available')}</span>
                </div>
                
                <div class="status">
                    <span class="label">Initial SMS to Seller:</span>
                    <span class="value">{sms_status}</span>
                </div>
            </div>
            
            <p>You can view all leads in the Google Sheet and the web interface.</p>
            
            <p>This is an automated message from your Car Lead Generation Agent.</p>
        </body>
        </html>
        """
        return html
    
    def send_sms_notification_to_client(self, lead: Dict[str, Any]) -> bool:
        """
        Send an SMS notification to the client about a new lead.
        
        Args:
            lead (dict): Lead information.
        
        Returns:
            bool: True if SMS sent successfully, False otherwise.
        """
        if not self.client_phone:
            logger.warning("SMS notification not sent: Missing client phone number.")
            return False
        
        if not self.messaging_manager:
            logger.warning("SMS notification not sent: Messaging manager not available.")
            return False
        
        # Create a concise SMS message
        message = (
            f"New Car Lead: {lead.get('year', '')} {lead.get('make', '')} {lead.get('model', '')} "
            f"- ${lead.get('price', 'N/A')} - {lead.get('source', 'N/A')}"
        )
        
        try:
            result = self.messaging_manager.send_sms(self.client_phone, message)
            if result:
                logger.info(f"SMS notification sent to client {self.client_phone}")
                return True
            else:
                logger.warning("SMS notification failed to send")
                return False
        except Exception as e:
            logger.error(f"Error sending SMS notification: {e}")
            return False
    
    def notify_client_about_lead(self, lead: Dict[str, Any], sms_status: str = "Not attempted") -> Dict[str, bool]:
        """
        Send both email and SMS notifications to the client about a new lead.
        
        Args:
            lead (dict): Lead information.
            sms_status (str): Status of SMS sent to seller.
        
        Returns:
            dict: Dictionary with 'email' and 'sms' keys, each with a boolean success value.
        """
        results = {
            'email': False,
            'sms': False
        }
        
        # Send email notification
        results['email'] = self.send_email_notification(lead, sms_status)
        
        # Send SMS notification
        results['sms'] = self.send_sms_notification_to_client(lead)
        
        logger.info(f"Notifications sent to client - Email: {results['email']}, SMS: {results['sms']}")
        
        return results 