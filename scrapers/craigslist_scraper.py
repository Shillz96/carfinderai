import re
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import random
from utils.logger import setup_logger

# Set up logger
logger = setup_logger('craigslist_scraper')

class CraigslistScraper:
    def __init__(self, config):
        """
        Initialize the Craigslist scraper
        
        Args:
            config (dict): Configuration dictionary
        """
        self.urls = config['scraper']['craigslist_urls']
        self.min_year = config['scraper']['min_vehicle_year']
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        logger.info(f"Initialized CraigslistScraper with {len(self.urls)} URLs and min year {self.min_year}")
    
    def fetch_listing_page(self, url):
        """
        Fetch a Craigslist listing page
        
        Args:
            url (str): URL to fetch
            
        Returns:
            str: HTML content or None if request failed
        """
        try:
            logger.info(f"Fetching URL: {url}")
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch {url}. Status code: {response.status_code}")
                return None
            
            return response.text
        except requests.RequestException as e:
            logger.error(f"Request exception for {url}: {str(e)}")
            return None
    
    def parse_listings(self, html_content):
        """
        Parse Craigslist listings from HTML content
        
        Args:
            html_content (str): HTML content to parse
            
        Returns:
            list: List of listing dictionaries
        """
        if not html_content:
            logger.warning("No HTML content to parse")
            return []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            listings = []
            
            # Find all listing elements - try multiple selectors to adapt to different CL designs
            listing_elements = []
            
            # The most current Craigslist design
            main_content = soup.select_one('#search-results, .cl-search-results, .rows')
            if main_content:
                # Current grid/gallery layout
                listing_elements = main_content.select('li.cl-static-search-result, .gallery-card, .result-row')
            
            # Fallback to older design
            if not listing_elements:
                listing_elements = soup.select('.result-info, .gallery-card, .result-row, .cl-static-search-result')
            
            # Another fallback to even more generic selectors
            if not listing_elements:
                logger.warning("Could not find listing elements with standard selectors, trying generic approach")
                # Look for any list items or divs that might contain listings
                listing_elements = soup.select('ul > li, .result')
            
            logger.info(f"Found {len(listing_elements)} listing elements")
            
            for listing in listing_elements:
                try:
                    # Try multiple selectors for title/link
                    title_element = listing.select_one('a.posting-title, a.titlestring, h3 > a, .title > a, a[data-testid="listing-title"]')
                    if not title_element:
                        continue
                    
                    title = title_element.text.strip()
                    url = title_element.get('href')
                    
                    # If we have a relative URL, make it absolute
                    if url and url.startswith('/'):
                        # Extract base URL from our target URLs (assuming they're similar)
                        base_url_match = re.match(r'(https?://[^/]+)', self.urls[0])
                        if base_url_match:
                            base_url = base_url_match.group(1)
                            url = f"{base_url}{url}"
                    
                    # Extract price (try multiple selectors)
                    price_element = listing.select_one('.result-price, .priceinfo, .price, span[data-testid="listing-price"]')
                    price = price_element.text.strip() if price_element else "N/A"
                    
                    # Extract year, make, model from title using regex
                    year_match = re.search(r'\b(20[0-9]{2}|19[0-9]{2})\b', title)
                    year = int(year_match.group(1)) if year_match else None
                    
                    # Skip listings that don't meet the minimum year requirement
                    if not year or year < self.min_year:
                        continue
                    
                    # Create listing dictionary
                    listing_data = {
                        'title': title,
                        'price': price,
                        'url': url,
                        'year': year,
                        'make': self._extract_make(title),
                        'model': self._extract_model(title),
                        'date_found': datetime.now().isoformat(),
                        'source': 'craigslist'
                    }
                    
                    listings.append(listing_data)
                    logger.debug(f"Parsed listing: {listing_data['title']}")
                except Exception as e:
                    logger.error(f"Error parsing listing: {str(e)}")
            
            return listings
        except Exception as e:
            logger.error(f"Error parsing HTML content: {str(e)}")
            return []
    
    def _extract_make(self, title):
        """
        Extract car make from listing title
        
        Args:
            title (str): Listing title
            
        Returns:
            str: Car make or 'Unknown'
        """
        # Common car makes - this list could be expanded
        makes = ['toyota', 'honda', 'ford', 'chevrolet', 'chevy', 'nissan', 'hyundai', 'kia', 
                'mazda', 'subaru', 'lexus', 'bmw', 'mercedes', 'audi', 'volkswagen', 'vw', 
                'dodge', 'jeep', 'chrysler', 'acura', 'infiniti', 'mitsubishi', 'volvo']
        
        title_lower = title.lower()
        
        for make in makes:
            if make in title_lower:
                return make.title()
        
        return 'Unknown'
    
    def _extract_model(self, title):
        """
        Extract car model from listing title - this is a simplistic implementation
        Real-world implementation would need a more comprehensive approach
        
        Args:
            title (str): Listing title
            
        Returns:
            str: Model name or empty string
        """
        # This is a very simplified model extraction
        # In a real application, you would need a much more comprehensive model database
        # or use regex patterns specific to each make
        make = self._extract_make(title)
        if make == 'Unknown':
            return ''
        
        title_words = title.lower().split()
        make_index = -1
        
        for i, word in enumerate(title_words):
            if make.lower() in word:
                make_index = i
                break
        
        if make_index >= 0 and make_index + 1 < len(title_words):
            return title_words[make_index + 1].title()
        
        return ''
    
    def find_next_page(self, html_content, current_url):
        """
        Find next page URL if it exists
        
        Args:
            html_content (str): HTML content
            current_url (str): Current page URL
            
        Returns:
            str: Next page URL or None
        """
        if not html_content:
            return None
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Try multiple selectors for finding the next page link
            next_selectors = [
                '.button.next', 
                '.cl-next-page', 
                'a.next',
                'a[data-testid="pagination-next"]',
                'a[title="next page"]',
                'link[rel="next"]'
            ]
            
            for selector in next_selectors:
                next_button = soup.select_one(selector)
                if next_button and next_button.get('href'):
                    next_url = next_button.get('href')
                    
                    # Handle relative URLs
                    if next_url.startswith('/'):
                        # Extract base URL from current_url
                        base_url_match = re.match(r'(https?://[^/]+)', current_url)
                        if base_url_match:
                            base_url = base_url_match.group(1)
                            next_url = f"{base_url}{next_url}"
                    
                    logger.info(f"Found next page: {next_url}")
                    return next_url
            
            # If we can't find a next button, look for pagination and check if we're on the last page
            pagination = soup.select('.cl-pagination a, .pages a, .paginator a')
            if pagination:
                # If we found pagination links but no next button, we might be on the last page
                logger.info("Found pagination but no next page button")
            
            logger.info("No next page found")
            return None
        except Exception as e:
            logger.error(f"Error finding next page: {str(e)}")
            return None
    
    def fetch_and_parse_listing_details(self, listing_url):
        """
        Fetch and parse details from an individual listing page
        
        Args:
            listing_url (str): URL of the listing
            
        Returns:
            dict: Additional listing details or empty dict if failed
        """
        html_content = self.fetch_listing_page(listing_url)
        if not html_content:
            return {}
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            details = {}
            
            # Extract description
            description_selectors = [
                '#postingbody', 
                '.posting-body', 
                '[data-testid="listing-description"]'
            ]
            
            for selector in description_selectors:
                description_element = soup.select_one(selector)
                if description_element:
                    details['description'] = description_element.text.strip()
                    break
            
            # Extract contact info (might be hidden or require JavaScript)
            contact_selectors = [
                '.reply-button-row', 
                '.show-contact', 
                '[data-testid="contact-info"]'
            ]
            
            for selector in contact_selectors:
                contact_element = soup.select_one(selector)
                if contact_element:
                    # Check for phone numbers
                    phone_match = re.search(r'(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})', contact_element.text)
                    if phone_match:
                        details['phone_number'] = phone_match.group(1)
                    break
            
            return details
        except Exception as e:
            logger.error(f"Error parsing listing details: {str(e)}")
            return {}
    
    def scrape_listings(self):
        """
        Scrape Craigslist listings from all configured URLs
        
        Returns:
            list: List of listing dictionaries
        """
        all_listings = []
        
        for base_url in self.urls:
            url = base_url
            page_count = 1
            
            while url and page_count <= 10:  # Limit to 10 pages per search URL
                logger.info(f"Scraping page {page_count} from {url}")
                html_content = self.fetch_listing_page(url)
                
                if not html_content:
                    logger.warning(f"Failed to fetch content from {url}")
                    break
                
                listings = self.parse_listings(html_content)
                all_listings.extend(listings)
                
                logger.info(f"Scraped {len(listings)} listings from page {page_count}")
                
                # Find and fetch next page
                next_url = self.find_next_page(html_content, url)
                
                # Add a delay to avoid overloading the server
                time.sleep(random.uniform(1.0, 3.0))
                
                url = next_url
                page_count += 1
        
        # For each listing, we could fetch details from the individual listing page
        # This is optional and would make the scraping slower
        # Uncomment if you need more details
        """
        enhanced_listings = []
        for listing in all_listings[:5]:  # Limit to first 5 for testing
            if 'url' in listing and listing['url']:
                logger.info(f"Fetching details for: {listing['title']}")
                details = self.fetch_and_parse_listing_details(listing['url'])
                listing.update(details)
                time.sleep(random.uniform(1.0, 2.0))  # Be nice to the server
            enhanced_listings.append(listing)
        all_listings = enhanced_listings
        """
        
        logger.info(f"Total listings scraped: {len(all_listings)}")
        return all_listings 