"""
Thryv API integration for sending leads to the Thryv CRM system.
"""

import os
import requests
import json
from typing import Dict, Any, Optional, Tuple
from utils.logger import setup_logger

# Set up logger
logger = setup_logger('thryv_integrator')

class ThryvIntegrator:
    """
    Manages integration with Thryv CRM system for lead creation and management.
    
    Args:
        config (dict): Configuration dictionary containing Thryv API credentials
                      and other configuration parameters.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the ThryvIntegrator with the provided configuration.
        
        Args:
            config (dict): Configuration dictionary.
        """
        self.config = config
        self.api_key = config.get('thryv', {}).get('api_key')
        self.account_id = config.get('thryv', {}).get('account_id')
        
        # Thryv API endpoints
        self.base_url = "https://api.thryv.com/v1"
        self.leads_endpoint = f"{self.base_url}/leads"
        
        if not self.api_key or not self.account_id:
            logger.warning("Thryv API key or account ID not configured.")
    
    def authenticate(self) -> bool:
        """
        Test authentication with Thryv API.
        
        Returns:
            bool: True if authentication successful, False otherwise.
        """
        if not self.api_key or not self.account_id:
            logger.error("Cannot authenticate: API key or account ID missing")
            return False
        
        try:
            # Make a simple test call to verify authentication
            headers = self._get_headers()
            response = requests.get(
                f"{self.base_url}/accounts/{self.account_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                logger.info("Successfully authenticated with Thryv API")
                return True
            else:
                logger.error(f"Thryv API authentication failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error during Thryv authentication: {e}")
            return False
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Get HTTP headers required for Thryv API requests.
        
        Returns:
            dict: HTTP headers with authentication.
        """
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def map_lead_to_thryv_format(self, lead: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert lead data to Thryv-compatible format.
        
        Args:
            lead (dict): Lead dictionary with our internal format.
        
        Returns:
            dict: Lead data mapped to Thryv format.
        """
        # Create a descriptive title for the lead
        lead_title = f"Used Car Lead - {lead.get('year', '')} {lead.get('make', '')} {lead.get('model', '')}"
        
        # Format the description with all available details
        description = f"""
        {lead.get('title', '')}
        
        Year: {lead.get('year', 'N/A')}
        Make: {lead.get('make', 'N/A')}
        Model: {lead.get('model', 'N/A')}
        Price: ${lead.get('price', 'N/A')}
        Source: {lead.get('source', 'N/A')}
        Date Posted: {lead.get('date_posted', 'N/A')}
        
        Description:
        {lead.get('description', 'No description available')}
        
        Listing URL: {lead.get('listing_url', 'N/A')}
        """
        
        # Map to Thryv lead format
        thryv_lead = {
            "accountId": self.account_id,
            "title": lead_title,
            "description": description.strip(),
            "status": "New",
            "source": f"CarFinderAI - {lead.get('source', 'Web Scraper')}",
            "priority": "Medium",
            "customFields": {
                "Vehicle Year": str(lead.get('year', '')),
                "Vehicle Make": lead.get('make', ''),
                "Vehicle Model": lead.get('model', ''),
                "Listing Price": f"${lead.get('price', '')}",
                "Original Listing URL": lead.get('listing_url', '')
            }
        }
        
        # Add contact information if available
        if lead.get('phone_number'):
            thryv_lead["contact"] = {
                "phoneNumbers": [
                    {
                        "number": lead.get('phone_number'),
                        "type": "MOBILE"
                    }
                ]
            }
        
        return thryv_lead
    
    def create_thryv_lead(self, lead: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Create a new lead in Thryv CRM.
        
        Args:
            lead (dict): Lead dictionary with our internal format.
        
        Returns:
            tuple: (success_flag, lead_id_or_error_message)
                - success_flag (bool): True if successful, False otherwise
                - lead_id_or_error_message (str): Thryv lead ID if successful, error message if failed
        """
        if not self.api_key or not self.account_id:
            return False, "Thryv API key or account ID missing"
        
        # Map lead to Thryv format
        thryv_lead = self.map_lead_to_thryv_format(lead)
        
        try:
            # Make API request to create lead
            headers = self._get_headers()
            response = requests.post(
                self.leads_endpoint,
                headers=headers,
                json=thryv_lead
            )
            
            # Process response
            if response.status_code in (200, 201):
                response_data = response.json()
                lead_id = response_data.get('id', 'Unknown')
                logger.info(f"Successfully created lead in Thryv with ID: {lead_id}")
                return True, lead_id
            else:
                error_msg = f"Error creating lead in Thryv: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return False, error_msg
        except Exception as e:
            error_msg = f"Exception during Thryv lead creation: {e}"
            logger.error(error_msg)
            return False, error_msg 