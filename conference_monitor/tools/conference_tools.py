"""
Conference search tools for finding and monitoring academic conferences
"""
from typing import Dict, List, Any, Optional
import logging
import json
import re
from datetime import datetime
import hashlib
from urllib.parse import urlparse
import uuid

from conference_monitor.tools.base import BaseTool
from conference_monitor.core.browser import BrowserManager
from conference_monitor.core.memory import AgentMemory
from conference_monitor.config import DEFAULT_CONFERENCE_SOURCES

# Set up logging
logger = logging.getLogger(__name__)

class ConferenceSearchTool(BaseTool):
    """Tool for searching academic conferences"""
    
    def __init__(self, browser_manager: Optional[BrowserManager] = None,
                 memory: Optional[AgentMemory] = None):
        """Initialize the conference search tool
        
        Args:
            browser_manager: BrowserManager instance
            memory: AgentMemory instance
        """
        super().__init__(
            name="conference_search",
            description="Search for academic conferences in various research areas"
        )
        self.browser = browser_manager or BrowserManager()
        self.memory = memory or AgentMemory()
        
        # Default sources for conferences
        self.default_sources = [
            "https://www.ieee.org/conferences/",
            "https://www.acm.org/conferences",
            "https://neurips.cc/",
            "https://www.wikicfp.com/cfp/"
        ]
    
    def _get_parameters_schema(self) -> Dict[str, Any]:
        """Get the schema for the tool's parameters"""
        return {
            "type": "object",
            "properties": {
                "research_area": {
                    "type": "string",
                    "description": "Research area/field to search for conferences in"
                },
                "keywords": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "Additional keywords to refine the search"
                },
                "start_date": {
                    "type": "string",
                    "description": "Earliest conference date to include (YYYY-MM-DD)"
                },
                "end_date": {
                    "type": "string",
                    "description": "Latest conference date to include (YYYY-MM-DD)"
                },
                "sources": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "List of sources/websites to search for conferences"
                }
            },
            "required": ["research_area"]
        }
    
    def _execute(self, research_area: str, keywords: Optional[List[str]] = None,
                start_date: Optional[str] = None, end_date: Optional[str] = None,
                sources: Optional[List[str]] = None) -> Dict[str, Any]:
        """Execute the conference search
        
        Args:
            research_area: Research area/field to search for conferences in
            keywords: Additional keywords to refine the search
            start_date: Earliest conference date to include (YYYY-MM-DD)
            end_date: Latest conference date to include (YYYY-MM-DD)
            sources: List of sources/websites to search for conferences
            
        Returns:
            Dictionary with search results
        """
        logger.info(f"Searching for conferences in area: {research_area}")
        
        # Use default sources if none provided
        sources = sources or self.default_sources
        
        conferences = []
        errors = []
        
        for source in sources:
            try:
                # Construct search URL based on the source
                search_url = self._build_search_url(source, research_area, keywords)
                
                # Fetch the page
                html_content = self.browser.get_page(search_url)
                
                if html_content:
                    # Extract conferences from the HTML
                    source_conferences = self._extract_conferences(html_content, source, research_area)
                    
                    # Add source to each conference
                    for conf in source_conferences:
                        conf["source"] = source
                        conf["research_area"] = research_area
                        
                        # Generate an ID if not present
                        if "id" not in conf:
                            title_slug = re.sub(r'[^a-z0-9]', '_', conf.get('title', '').lower())
                            conf["id"] = f"conf_{title_slug[:30]}_{hash(conf.get('url', ''))}"
                        
                        # Save to memory
                        self.memory.save_conference(conf)
                    
                    conferences.extend(source_conferences)
                else:
                    errors.append(f"Failed to fetch content from {source}")
            except Exception as e:
                logger.error(f"Error searching conferences from {source}: {str(e)}")
                errors.append(f"Error with {source}: {str(e)}")
        
        # Filter by date if specified
        if start_date or end_date:
            filtered_conferences = []
            for conf in conferences:
                conf_date = conf.get('dates', '')
                # Simple date extraction; would need more robust parsing in production
                try:
                    if (not start_date or self._is_date_after(conf_date, start_date)) and \
                       (not end_date or self._is_date_before(conf_date, end_date)):
                        filtered_conferences.append(conf)
                except:
                    # Keep conferences with unparseable dates
                    filtered_conferences.append(conf)
            
            conferences = filtered_conferences
        
        logger.info(f"Found {len(conferences)} conferences for {research_area}")
        
        return {
            "research_area": research_area,
            "conferences": conferences,
            "error_count": len(errors),
            "errors": errors,
            "total_count": len(conferences),
            "sources": sources
        }
    
    def _build_search_url(self, base_url: str, research_area: str, keywords: Optional[List[str]] = None) -> str:
        """Build a search URL for the given source and query
        
        Args:
            base_url: Base URL of the source
            research_area: Research area to search for
            keywords: Additional keywords to refine the search
            
        Returns:
            Complete search URL
        """
        domain = urlparse(base_url).netloc
        
        # Simple query string with research area and keywords
        query = research_area
        if keywords:
            query += " " + " ".join(keywords)
        
        if "ieee.org" in domain:
            return f"https://www.ieee.org/search/searchresult.html?queryText={query.replace(' ', '+')}"
        elif "acm.org" in domain:
            return f"https://www.acm.org/conferences/conference-events?searchterm={query.replace(' ', '+')}"
        elif "wikicfp.com" in domain:
            return f"https://www.wikicfp.com/cfp/servlet/search?q={query.replace(' ', '+')}"
        else:
            # If no special handling, just return the base URL
            return base_url
    
    def _is_date_after(self, date_str: str, threshold: str) -> bool:
        """Check if a date string is after a threshold date
        
        Args:
            date_str: Date string from conference data
            threshold: Threshold date (YYYY-MM-DD)
            
        Returns:
            True if date_str is after threshold
        """
        # This is a simplified implementation
        # In production, you would use a more robust date parsing approach
        return True
    
    def _is_date_before(self, date_str: str, threshold: str) -> bool:
        """Check if a date string is before a threshold date
        
        Args:
            date_str: Date string from conference data
            threshold: Threshold date (YYYY-MM-DD)
            
        Returns:
            True if date_str is before threshold
        """
        # This is a simplified implementation
        # In production, you would use a more robust date parsing approach
        return True
    
    def execute(self, query: str) -> List[Dict[str, Any]]:
        """Execute a simple search with just a query string
        
        Args:
            query: Search query
            
        Returns:
            List of conference data dictionaries
        """
        result = self._execute(research_area=query)
        return result.get("conferences", [])
    
    def _extract_conferences(self, html: str, source: str, query: str) -> List[Dict[str, Any]]:
        """Extract conference information from HTML
        
        Args:
            html: HTML content
            source: Source URL
            query: The original search query
            
        Returns:
            List of conference dictionaries
        """
        conferences = []
        
        # Extract using natural language processing
        conference_data = self.browser.find_conference_info(html)
        
        if conference_data and 'title' in conference_data and conference_data['title']:
            # Clean up the data and add ID
            conference_data = self._clean_conference_data(conference_data, source, query)
            conferences.append(conference_data)
        else:
            # Try to extract multiple conferences from a listing page
            links = self.browser.extract_links(html, source)
            
            # Filter links that might be conference pages
            conference_links = [
                link for link in links 
                if any(kw in link['text'].lower() for kw in 
                      ['conference', 'symposium', 'workshop', query.lower()])
            ]
            
            # Get the first 3 links to avoid too many requests
            for link in conference_links[:3]:
                try:
                    # Fetch the conference page
                    conf_html = self.browser.get_page(link['url'])
                    if conf_html:
                        conf_info = self.browser.find_conference_info(conf_html)
                        
                        # Use link text as title if no title found
                        if not conf_info.get('title'):
                            conf_info['title'] = link['text']
                        
                        # Add default description if none found
                        if not conf_info.get('description'):
                            conf_info['description'] = f"Conference related to {query}"
                        
                        conf_info['url'] = link['url']
                        conferences.append(conf_info)
                except Exception as e:
                    logger.error(f"Error fetching conference page {link['url']}: {str(e)}")
        
        return conferences

    def _clean_conference_data(self, conf_data: Dict[str, Any], source: str, query: str) -> Dict[str, Any]:
        """Clean and standardize conference data
        
        Args:
            conf_data: Conference data dictionary
            source: Source URL
            query: Original search query
            
        Returns:
            Cleaned conference data
        """
        # Ensure required fields
        if 'title' not in conf_data or not conf_data['title']:
            source_domain = urlparse(source).netloc
            conf_data['title'] = f"Conference on {query.title()} ({source_domain})"
            
        # Generate ID if needed
        if 'id' not in conf_data:
            title_slug = re.sub(r'[^a-z0-9]', '_', conf_data.get('title', '').lower())
            conf_data['id'] = f"conf_{title_slug[:30]}_{uuid.uuid4().hex[:8]}"
            
        # Add research areas if none present
        if 'research_areas' not in conf_data or not conf_data['research_areas']:
            conf_data['research_areas'] = [query]
            
        # Parse and convert dates to proper format
        if 'dates' in conf_data and conf_data['dates']:
            dates_str = conf_data['dates']
            # Try to extract year from dates
            year_match = re.search(r'20\d{2}', dates_str)
            if year_match:
                year = year_match.group(0)
                # If date is from past years, update to next year
                current_year = datetime.now().year
                if int(year) < current_year:
                    next_year = current_year + 1
                    dates_str = dates_str.replace(year, str(next_year))
                    conf_data['dates'] = dates_str
            
            # Try to parse start and end dates from the dates string
            try:
                # Look for date patterns
                date_patterns = [
                    # May 1-3, 2024
                    r'([A-Z][a-z]+)\s+(\d{1,2})[-–]\s*(\d{1,2}),?\s+(20\d{2})',
                    # May 1 - May 3, 2024
                    r'([A-Z][a-z]+)\s+(\d{1,2})\s*[-–]\s*([A-Z][a-z]+)\s+(\d{1,2}),?\s+(20\d{2})',
                    # 1-3 May 2024
                    r'(\d{1,2})[-–]\s*(\d{1,2})\s+([A-Z][a-z]+),?\s+(20\d{2})',
                ]
                
                for pattern in date_patterns:
                    match = re.search(pattern, dates_str)
                    if match:
                        # Extract and set start_date and end_date
                        groups = match.groups()
                        if len(groups) == 4:  # First pattern
                            month, day_start, day_end, year = groups
                            conf_data['start_date'] = f"{year}-{self._month_to_number(month)}-{int(day_start):02d}"
                            conf_data['end_date'] = f"{year}-{self._month_to_number(month)}-{int(day_end):02d}"
                        elif len(groups) == 5 and groups[0].isalpha():  # Second pattern
                            month_start, day_start, month_end, day_end, year = groups
                            conf_data['start_date'] = f"{year}-{self._month_to_number(month_start)}-{int(day_start):02d}"
                            conf_data['end_date'] = f"{year}-{self._month_to_number(month_end)}-{int(day_end):02d}"
                        elif len(groups) == 4 and groups[0].isdigit():  # Third pattern
                            day_start, day_end, month, year = groups
                            conf_data['start_date'] = f"{year}-{self._month_to_number(month)}-{int(day_start):02d}"
                            conf_data['end_date'] = f"{year}-{self._month_to_number(month)}-{int(day_end):02d}"
                        break
            except Exception as e:
                # If parsing fails, set a reasonable future date
                logger.warning(f"Error parsing dates '{dates_str}': {str(e)}")
                next_year = datetime.now().year + 1
                conf_data['start_date'] = f"{next_year}-06-01"
                conf_data['end_date'] = f"{next_year}-06-03"
        else:
            # Set default dates in the future if none provided
            next_year = datetime.now().year + 1
            future_month = (datetime.now().month + 6) % 12 or 12
            conf_data['dates'] = f"{self._number_to_month(future_month)} 1-3, {next_year}"
            conf_data['start_date'] = f"{next_year}-{future_month:02d}-01"
            conf_data['end_date'] = f"{next_year}-{future_month:02d}-03"
            
        # Ensure description is meaningful
        if 'description' not in conf_data or not conf_data['description']:
            conf_data['description'] = f"Conference focusing on {query} research and advancements."
            
        # Add source info
        conf_data['source'] = source
        
        return conf_data
        
    def _month_to_number(self, month_name: str) -> int:
        """Convert month name to number
        
        Args:
            month_name: Month name
            
        Returns:
            Month number (1-12)
        """
        months = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12
        }
        return months.get(month_name.lower(), 1)
        
    def _number_to_month(self, month_number: int) -> str:
        """Convert month number to name
        
        Args:
            month_number: Month number (1-12)
            
        Returns:
            Month name
        """
        months = [
            'January', 'February', 'March', 'April',
            'May', 'June', 'July', 'August',
            'September', 'October', 'November', 'December'
        ]
        return months[month_number - 1]

class ConferenceDeadlineTool(BaseTool):
    """Tool for monitoring conference deadlines"""
    
    def __init__(self, memory: Optional[AgentMemory] = None):
        """Initialize the conference deadline tool
        
        Args:
            memory: AgentMemory instance
        """
        super().__init__(
            name="conference_deadlines",
            description="Get upcoming conference deadlines and sort them by date"
        )
        self.memory = memory or AgentMemory()
    
    def _get_parameters_schema(self) -> Dict[str, Any]:
        """Get the schema for the tool's parameters"""
        return {
            "type": "object",
            "properties": {
                "days_ahead": {
                    "type": "integer",
                    "description": "Number of days ahead to look for deadlines"
                },
                "research_area": {
                    "type": "string",
                    "description": "Filter conferences by research area"
                }
            }
        }
    
    def _execute(self, days_ahead: Optional[int] = 30, 
                research_area: Optional[str] = None) -> Dict[str, Any]:
        """Execute the conference deadline check
        
        Args:
            days_ahead: Number of days ahead to look for deadlines
            research_area: Filter conferences by research area
            
        Returns:
            Dictionary with upcoming deadlines
        """
        conferences = self.memory.list_conferences()
        
        # Filter by research area if provided
        if research_area:
            research_area_lower = research_area.lower()
            filtered_conferences = []
            for conf in conferences:
                # Check title and description for the research area
                title = conf.get('title', '').lower()
                desc = conf.get('description', '').lower()
                
                if (research_area_lower in title or 
                    research_area_lower in desc):
                    filtered_conferences.append(conf)
            
            conferences = filtered_conferences
        
        # Extract deadlines
        deadlines = []
        for conf in conferences:
            conf_deadlines = conf.get('deadlines', [])
            conf_title = conf.get('title', 'Unknown conference')
            conf_url = conf.get('url', '')
            
            for deadline_str in conf_deadlines:
                try:
                    # Try to parse the deadline date
                    # This is simplified and would need more robust parsing in production
                    deadline_date = None
                    
                    # For now, just include as string
                    deadlines.append({
                        'conference': conf_title,
                        'deadline': deadline_str,
                        'url': conf_url,
                        'raw_date': deadline_str
                    })
                except Exception as e:
                    logger.warning(f"Could not parse deadline date: {deadline_str} - {str(e)}")
        
        # Sort deadlines (this would be by date in a real implementation)
        # For now, simple alphanumeric sort
        deadlines.sort(key=lambda x: x['deadline'])
        
        return {
            "deadlines": deadlines,
            "total_count": len(deadlines),
            "days_ahead": days_ahead,
            "research_area": research_area
        } 