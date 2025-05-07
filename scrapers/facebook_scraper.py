"""""
Facebook Marketplace Scraper Module

This module will contain the logic for scraping listings from Facebook Marketplace.
Due to the dynamic nature of Facebook, this might involve more complex techniques
like browser automation if static scraping is not feasible.
"""

import logging
import time
import random
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os
from dotenv import load_dotenv

# Importing Selenium components
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

# Setup logging - eventually use the project's logger
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

MIN_YEAR = 2018  # As per project specifications

# Common user agents to rotate through
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:93.0) Gecko/20100101 Firefox/93.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:93.0) Gecko/20100101 Firefox/93.0'
]

# Constants for Selenium
SCROLL_PAUSE_TIME = 1.5
MAX_SCROLLS = 10  # Limit scrolling to prevent overloading
FACEBOOK_LOAD_TIMEOUT = 30  # Seconds to wait for Facebook to load elements

def fetch_page_content_statically(url):
    """
    Fetches page content using requests with rotating user agents.
    
    Args:
        url (str): The URL to fetch content from
        
    Returns:
        str or None: HTML content if successful, None otherwise
    """
    try:
        user_agent = random.choice(USER_AGENTS)
        headers = {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://www.facebook.com/",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        
        logger.info(f"Fetching {url} with static approach")
        response = requests.get(url, timeout=20, headers=headers)
        
        if response.status_code == 200:
            logger.info(f"Successfully fetched {url}")
            return response.text
        else:
            logger.warning(f"Failed to fetch {url}: Status code {response.status_code}")
            return None
            
    except requests.RequestException as e:
        logger.error(f"Error fetching {url} statically: {e}")
        return None


def parse_fb_listings(html_content):
    """
    Parses listings from Facebook HTML content.
    
    Args:
        html_content (str): HTML content from Facebook Marketplace
        
    Returns:
        list: List of dictionaries containing listing details
    """
    listings = []
    
    if not html_content:
        logger.error("No HTML content to parse")
        return listings
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    try:
        # Note: This is a placeholder for actual Facebook parsing logic
        # We'll need to adjust these selectors based on actual FB Marketplace HTML inspection
        
        # Look for product cards/containers
        # This will need to be adjusted based on FB's actual structure
        listing_containers = soup.select('div[data-testid="marketplace_feed_item"]')
        
        if not listing_containers:
            # Try alternative selectors if the primary one fails
            listing_containers = soup.select('div.kbiprv82')  # Example class name, will need adjustment
        
        if not listing_containers:
            logger.warning("No listing containers found - selector may need updating")
            # Dump a section of the HTML for debugging, but keep it small
            logger.debug(f"Sample HTML snippet: {html_content[:300]}...")
            return listings
        
        logger.info(f"Found {len(listing_containers)} potential listing containers")
        
        for container in listing_containers:
            try:
                # These selectors are placeholders and will need to be updated based on actual FB structure
                title_element = container.select_one('span.a8c37x1j')
                price_element = container.select_one('span.d2edcug0')
                link_element = container.select_one('a[href*="/marketplace/item/"]')
                
                if not (title_element and price_element and link_element):
                    logger.debug("Missing required elements for a listing, skipping")
                    continue
                
                title = title_element.text.strip()
                price_text = price_element.text.strip()
                
                # Try to extract price as a number
                price = None
                price_match = re.search(r'\$?([0-9,]+(?:\.\d+)?)', price_text)
                if price_match:
                    price = float(price_match.group(1).replace(',', ''))
                
                # Extract URL
                url = link_element.get('href')
                if not url.startswith('http'):
                    url = f"https://www.facebook.com{url}"
                
                # Trying to extract year, make, model from title
                # This is a simplified approach, would need refinement
                year = None
                year_match = re.search(r'\b(19[7-9]\d|20[0-2]\d)\b', title)
                if year_match:
                    year = int(year_match.group(1))
                
                # Only include listings from MIN_YEAR (2018) and newer
                if year and year >= MIN_YEAR:
                    listing = {
                        'title': title,
                        'price': price,
                        'url': url,
                        'year': year,
                        'source': 'Facebook Marketplace',
                        'date_scraped': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    # Try to extract make and model - this needs refinement
                    # For now, just a very basic approach
                    title_words = title.split()
                    
                    # Filter out the year and common words to attempt to identify make/model
                    if year:
                        title_words = [w for w in title_words if not w.startswith(str(year))]
                    
                    if len(title_words) >= 2:
                        listing['make'] = title_words[0].capitalize()
                        listing['model'] = title_words[1].capitalize()
                    
                    listings.append(listing)
                    logger.info(f"Found valid listing: {year} {title} - ${price}")
                else:
                    logger.debug(f"Listing filtered out due to year: {title}")
                    
            except Exception as e:
                logger.error(f"Error parsing individual listing: {e}")
                continue
    
    except Exception as e:
        logger.error(f"Error parsing Facebook Marketplace listings: {e}")
    
    return listings


def extract_listing_from_element(element):
    """
    Extract listing information from a Selenium WebElement.
    
    Args:
        element (WebElement): Selenium WebElement containing listing information
        
    Returns:
        dict or None: Dictionary with listing details or None if unsuccessful
    """
    try:
        # These selectors need to be adjusted based on actual FB Marketplace structure
        # They are placeholders that will need refinement
        
        # Try to get title - multiple potential selectors
        title_element = None
        for selector in ['a[aria-label]', 'span.x1lliihq', 'span.x193iq5w']:
            try:
                title_element = element.find_element(By.CSS_SELECTOR, selector)
                break
            except NoSuchElementException:
                continue
        
        if not title_element:
            return None
            
        title = title_element.text.strip()
        
        # Try to get price
        price_element = None
        for selector in ['span.x193iq5w', 'span.x1s928wf']:
            try:
                price_element = element.find_element(By.CSS_SELECTOR, selector)
                break
            except NoSuchElementException:
                continue
                
        price = None
        if price_element:
            price_text = price_element.text.strip()
            price_match = re.search(r'\$?([0-9,]+(?:\.\d+)?)', price_text)
            if price_match:
                price = float(price_match.group(1).replace(',', ''))
        
        # Get URL - again multiple potential selectors
        url = None
        link_element = None
        for selector in ['a[href*="/marketplace/item/"]', 'a[href*="marketplace"]']:
            try:
                link_element = element.find_element(By.CSS_SELECTOR, selector)
                url = link_element.get_attribute('href')
                break
            except NoSuchElementException:
                continue
                
        if not url:
            return None
        
        # Extract year from title
        year = None
        year_match = re.search(r'\b(19[7-9]\d|20[0-2]\d)\b', title)
        if year_match:
            year = int(year_match.group(1))
        
        # Only include listings from MIN_YEAR (2018) and newer
        if year and year >= MIN_YEAR:
            listing = {
                'title': title,
                'price': price,
                'url': url,
                'year': year,
                'source': 'Facebook Marketplace',
                'date_scraped': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Try to extract make and model - this needs refinement
            title_words = title.split()
            if year:
                title_words = [w for w in title_words if not w.startswith(str(year))]
            
            if len(title_words) >= 2:
                listing['make'] = title_words[0].capitalize()
                listing['model'] = title_words[1].capitalize()
            
            logger.info(f"Found valid listing: {year} {title} - ${price}")
            return listing
        else:
            logger.debug(f"Listing filtered out due to year: {title}")
            return None
            
    except Exception as e:
        logger.error(f"Error extracting listing data: {e}")
        return None


def scrape_facebook_marketplace(config):
    """
    Main function to orchestrate the scraping of Facebook Marketplace.

    Args:
        config (dict): Configuration dictionary containing necessary parameters
                       like target URLs, potential login details (if absolutely necessary
                       and handled securely), etc.

    Returns:
        list: A list of dictionaries, where each dictionary represents a scraped lead.
    """
    logger.info("Starting Facebook Marketplace scrape.")
    scraped_leads = []
    
    # Get target URLs from config
    target_urls = config.get("FACEBOOK_MARKETPLACE_URLS", [])
    
    if not target_urls:
        logger.warning("No Facebook Marketplace URLs provided in config")
        return scraped_leads
    
    # Static scraping approach first
    use_selenium = False
    static_success = False
    
    for url in target_urls:
        logger.info(f"Processing Facebook URL: {url}")
        
        # Try static scraping first
        html_content = fetch_page_content_statically(url)
        
        if html_content:
            leads_on_page = parse_fb_listings(html_content)
            
            if leads_on_page:
                static_success = True
                scraped_leads.extend(leads_on_page)
                logger.info(f"Static scraping successful for {url}, found {len(leads_on_page)} leads")
            else:
                logger.warning(f"Static scraping failed to find listings for {url}")
                use_selenium = True
        else:
            logger.warning(f"Static scraping failed to fetch content from {url}")
            use_selenium = True
        
        # Be polite with delays between requests
        delay = random.uniform(5, 10)
        logger.debug(f"Sleeping for {delay:.2f} seconds before next request")
        time.sleep(delay)
    
    # If static scraping wasn't successful, try Selenium
    if use_selenium and not static_success:
        logger.info("Static scraping approach was not successful. Switching to Selenium-based approach.")
        selenium_leads = scrape_with_selenium(config)
        scraped_leads.extend(selenium_leads)
    
    logger.info(f"Facebook Marketplace scrape completed. Found {len(scraped_leads)} potential leads.")
    return scraped_leads


def scrape_with_selenium(config):
    """
    Selenium-based scraping approach for Facebook Marketplace.
    
    Args:
        config (dict): Configuration dictionary
        
    Returns:
        list: List of scraped leads
    """
    logger.info("Starting Selenium-based Facebook scraping")
    scraped_leads = []
    driver = None
    
    try:
        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode (no GUI)
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument(f"user-agent={random.choice(USER_AGENTS)}")
        
        # Additional options to avoid detection
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        
        # Initialize WebDriver
        try:
            driver = webdriver.Chrome(options=chrome_options)
            # Mask Selenium's automated nature
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        except WebDriverException as e:
            logger.error(f"Failed to initialize Chrome WebDriver: {e}")
            return scraped_leads
            
        # Process each URL
        target_urls = config.get("FACEBOOK_MARKETPLACE_URLS", [])
        
        for url in target_urls:
            try:
                logger.info(f"Navigating to {url} with Selenium")
                driver.get(url)
                
                # Wait for the page to load
                WebDriverWait(driver, FACEBOOK_LOAD_TIMEOUT).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # Check for login prompts and handle them if necessary
                if "Log in to Facebook" in driver.title or "Log Into Facebook" in driver.page_source:
                    logger.warning("Facebook login required. Attempting to bypass or using limited content.")
                    # We could implement login here if necessary using secure credentials
                    # For now, we'll try to work with what's visible without login
                
                # Sleep to allow dynamic content to load
                time.sleep(5)
                
                # Scroll to load more content
                scroll_count = 0
                last_height = driver.execute_script("return document.body.scrollHeight")
                
                while scroll_count < MAX_SCROLLS:
                    # Scroll down
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    
                    # Wait for new content to load
                    time.sleep(SCROLL_PAUSE_TIME)
                    
                    # Calculate new scroll height
                    new_height = driver.execute_script("return document.body.scrollHeight")
                    
                    # Break if we've reached the bottom or no new content loaded
                    if new_height == last_height:
                        break
                        
                    last_height = new_height
                    scroll_count += 1
                    
                    # Add random delay between scrolls to appear more human-like
                    time.sleep(random.uniform(0.5, 1.5))
                
                # Find listing elements - these selectors need to be adjusted based on actual FB structure
                # Try multiple potential selectors for marketplace items
                listing_elements = []
                selectors = [
                    "div[data-testid='marketplace_feed_item']",
                    "div.x1n2onr6",  # Example class, would need adjustment
                    "a[href*='/marketplace/item/']",
                    "div.x6s0dn4"  # Another example class
                ]
                
                for selector in selectors:
                    try:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        if elements:
                            listing_elements = elements
                            logger.info(f"Found {len(elements)} listings using selector: {selector}")
                            break
                    except Exception as e:
                        logger.debug(f"Selector {selector} failed: {e}")
                
                if not listing_elements:
                    logger.warning(f"No listing elements found on {url}")
                    continue
                
                # Process each listing element
                leads_on_page = []
                for element in listing_elements:
                    listing = extract_listing_from_element(element)
                    if listing:
                        leads_on_page.append(listing)
                
                # Add leads from this page to our overall results
                scraped_leads.extend(leads_on_page)
                logger.info(f"Found {len(leads_on_page)} leads on {url} using Selenium")
                
                # Be polite with delays between URLs
                delay = random.uniform(5, 10)
                logger.debug(f"Sleeping for {delay:.2f} seconds before next URL")
                time.sleep(delay)
                
            except TimeoutException:
                logger.error(f"Timeout while loading {url}")
                continue
                
            except Exception as e:
                logger.error(f"Error processing {url} with Selenium: {e}")
                continue
    
    except Exception as e:
        logger.error(f"Selenium scraping failed: {e}")
    
    finally:
        # Clean up
        if driver:
            try:
                driver.quit()
                logger.info("Selenium WebDriver closed successfully")
            except Exception as e:
                logger.error(f"Error closing WebDriver: {e}")
    
    return scraped_leads


if __name__ == '__main__':
    # This is for direct testing of the scraper
    print("Testing Facebook Scraper module...")
    
    # Load configuration from .env file
    load_dotenv()
    
    # Example configuration - in production this would come from .env or another source
    hawaii_fb_urls = os.getenv('FACEBOOK_MARKETPLACE_URLS', '').split(',')
    
    if not hawaii_fb_urls or hawaii_fb_urls[0] == '':
        # Fallback URLs for testing
        hawaii_fb_urls = [
            "https://www.facebook.com/marketplace/honolulu/vehicles/",
            "https://www.facebook.com/marketplace/maui/vehicles/"
        ]
    
    mock_config = {
        "FACEBOOK_MARKETPLACE_URLS": hawaii_fb_urls,
    }
    
    leads = scrape_facebook_marketplace(mock_config)
    print(f"Found {len(leads)} leads:")
    for i, lead in enumerate(leads, 1):
        print(f"\n{i}. {lead.get('year', 'N/A')} {lead.get('make', '')} {lead.get('model', '')}")
        print(f"   Price: ${lead.get('price', 'N/A')}")
        print(f"   URL: {lead.get('url', 'N/A')}") 