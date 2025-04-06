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
    
    def __init__(self, headers: Optional[Dict[str, str]] = None, timeout: int = 10, mock_mode: bool = False):
        """Initialize the browser manager
        
        Args:
            headers: Custom headers for HTTP requests
            timeout: Timeout for HTTP requests in seconds
            mock_mode: Whether to run in mock mode
        """
        self.timeout = timeout
        self.headers = headers or {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5"
        }
        self.mock_mode = mock_mode
        
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

    def fetch_url(self, url: str) -> str:
        """Fetch content from a URL
        
        Args:
            url: URL to fetch
            
        Returns:
            HTML content
        """
        if self.mock_mode:
            return self._get_mock_content(url)
        
        try:
            # Set headers to mimic a browser
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5"
            }
            
            # Disable SSL verification as a workaround for certificate issues
            response = requests.get(url, headers=headers, timeout=10, verify=False)
            
            # Log warning about SSL verification
            if "https" in url:
                logger.warning("SSL certificate verification disabled for: %s", url)
                # Suppress only the InsecureRequestWarning from urllib3
                import urllib3
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            # Check status code
            if response.status_code == 200:
                return response.text
            else:
                logger.error(f"Error fetching {url}: Status code {response.status_code}")
                return ""
        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            return ""

    def _get_mock_content(self, url: str) -> str:
        """Get mock content for the given URL
        
        Args:
            url: URL to get mock content for
            
        Returns:
            Mock HTML content
        """
        # Parse the domain from the URL
        domain = urlparse(url).netloc
        
        # Return different mock content based on the domain
        if "ieee.org" in domain:
            return """
            <html>
                <head><title>IEEE Conferences</title></head>
                <body>
                    <h1>IEEE Conferences</h1>
                    <p>The world's largest professional organization dedicated to advancing technology.</p>
                    <div class="conferences">
                        <h2>Upcoming Conferences</h2>
                        <ul>
                            <li><a href="#">IEEE International Conference on Artificial Intelligence</a> - October 15-17, 2025</li>
                            <li><a href="#">IEEE International Conference on Machine Learning</a> - September 5-7, 2025</li>
                            <li><a href="#">IEEE Conference on Computer Vision</a> - November 20-22, 2025</li>
                        </ul>
                    </div>
                </body>
            </html>
            """
        elif "acm.org" in domain:
            return """
            <html>
                <head><title>ACM Conferences</title></head>
                <body>
                    <h1>ACM Conferences</h1>
                    <p>Association for Computing Machinery - Advancing Computing as a Science & Profession</p>
                    <div class="conferences">
                        <h2>Upcoming Events</h2>
                        <ul>
                            <li><a href="#">ACM Symposium on Machine Learning</a> - May 5-7, 2025</li>
                            <li><a href="#">ACM Conference on Data Mining</a> - June 10-12, 2025</li>
                            <li><a href="#">ACM Workshop on Natural Language Processing</a> - April 15-16, 2025</li>
                        </ul>
                    </div>
                </body>
            </html>
            """
        elif "neurips" in domain:
            return """
            <html>
                <head><title>NeurIPS Conference</title></head>
                <body>
                    <h1>Neural Information Processing Systems (NeurIPS)</h1>
                    <p>The premier machine learning conference.</p>
                    <div class="conference-info">
                        <h2>NeurIPS 2025</h2>
                        <p>Dates: December 1-7, 2025</p>
                        <p>Location: Vancouver, Canada</p>
                        <h3>Deadlines</h3>
                        <ul>
                            <li>Paper Submission: May 15, 2025</li>
                            <li>Registration: November 1, 2025</li>
                        </ul>
                    </div>
                </body>
            </html>
            """
        else:
            # Generic conference listing
            return """
            <html>
                <head><title>Academic Conferences</title></head>
                <body>
                    <h1>Academic Conferences</h1>
                    <p>Find the latest research conferences in your field.</p>
                    <div class="conferences">
                        <h2>Upcoming Conferences</h2>
                        <ul>
                            <li><a href="#">International Conference on Machine Learning</a> - July 15-17, 2025</li>
                            <li><a href="#">Global AI Summit</a> - August 20-22, 2025</li>
                            <li><a href="#">Annual Computer Science Symposium</a> - September 22-24, 2025</li>
                        </ul>
                    </div>
                </body>
            </html>
            """ 