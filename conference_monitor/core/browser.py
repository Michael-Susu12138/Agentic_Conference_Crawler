"""
Browser management for web scraping
"""
import requests
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup
import logging
from urllib.parse import urljoin, urlparse
import re
import time
import random

# Set up logging
logger = logging.getLogger(__name__)

class BrowserManager:
    """Manages web browsing and content extraction"""
    
    def __init__(self, headers: Optional[Dict[str, str]] = None, timeout: int = 10):
        """Initialize the browser manager
        
        Args:
            headers: Custom headers for HTTP requests
            timeout: Timeout for HTTP requests in seconds
        """
        self.timeout = timeout
        self.headers = headers or {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5"
        }
        
        # Used to avoid overloading servers
        self.last_request_time = 0
        self.min_request_interval = 1  # seconds
    
    def _throttle_requests(self):
        """Throttle requests to avoid overloading servers"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def get_page(self, url: str) -> Optional[str]:
        """Fetch a web page
        
        Args:
            url: URL to fetch
            
        Returns:
            HTML content as string or None if failed
        """
        self._throttle_requests()
        
        try:
            # Add jitter to be more human-like
            time.sleep(random.uniform(0.5, 1.5))
            
            response = requests.get(
                url, 
                headers=self.headers, 
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return response.text
            else:
                logger.warning(f"Failed to fetch {url}, status code: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            return None
    
    def extract_links(self, html: str, base_url: str) -> List[Dict[str, str]]:
        """Extract links from HTML content
        
        Args:
            html: HTML content to parse
            base_url: Base URL for resolving relative links
            
        Returns:
            List of dictionaries with link info
        """
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            text = a_tag.get_text(strip=True)
            
            # Skip empty or anchor links
            if not href or href.startswith('#'):
                continue
            
            # Resolve relative URLs
            full_url = urljoin(base_url, href)
            
            links.append({
                'url': full_url,
                'text': text,
                'is_external': urlparse(full_url).netloc != urlparse(base_url).netloc
            })
        
        return links
    
    def find_conference_info(self, html: str) -> Dict[str, Any]:
        """Extract conference information from HTML
        
        Args:
            html: HTML content to parse
            
        Returns:
            Dictionary with extracted conference information
        """
        if not html:
            return {}
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Initialize conference info
        conf_info = {
            'title': None,
            'dates': None,
            'location': None,
            'deadlines': [],
            'website': None,
            'description': None
        }
        
        # Extract title (usually in h1 or h2 tags)
        title_tags = soup.find_all(['h1', 'h2', 'h3'])
        for tag in title_tags:
            text = tag.get_text(strip=True)
            if len(text) > 5 and len(text) < 150:  # Reasonable length for a title
                conf_info['title'] = text
                break
        
        # Look for dates (using regex patterns)
        date_pattern = r'\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2}(?:-|–|to|\s+through\s+)?\d{1,2}?,?\s+\d{4}\b'
        text_content = soup.get_text()
        date_matches = re.findall(date_pattern, text_content, re.IGNORECASE)
        if date_matches:
            conf_info['dates'] = date_matches[0]
        
        # Look for submission deadlines
        deadline_patterns = [
            r'(?:submission|paper|abstract)(?:\s+(?:deadline|due|date))?\s*(?::|is|are|on|by)?\s*([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
            r'(?:deadline|due date)(?:\s+for)?(?:\s+(?:submissions|papers|abstracts))?\s*(?::|is|are|on|by)?\s*([A-Za-z]+\s+\d{1,2},?\s+\d{4})'
        ]
        
        for pattern in deadline_patterns:
            deadline_matches = re.findall(pattern, text_content, re.IGNORECASE)
            conf_info['deadlines'].extend(deadline_matches)
        
        # Try to extract location
        location_patterns = [
            r'(?:held|located|location|venue|take[s]? place|will be in)(?:\s+in|\s+at)?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s+[A-Za-z\s]+)',
            r'(?:in|at)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s+[A-Za-z\s]+)'
        ]
        
        for pattern in location_patterns:
            location_matches = re.findall(pattern, text_content)
            if location_matches:
                conf_info['location'] = location_matches[0]
                break
        
        # Extract description (look for paragraphs with a reasonable length)
        paragraphs = soup.find_all('p')
        for p in paragraphs:
            text = p.get_text(strip=True)
            if len(text) > 100 and len(text) < 1000:  # Reasonable length for a description
                conf_info['description'] = text
                break
        
        return conf_info 