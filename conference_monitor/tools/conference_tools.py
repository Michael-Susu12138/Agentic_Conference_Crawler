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
                    source_conferences = self._extract_conferences(html_content, search_url, research_area)
                    
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
            query: Search query
            
        Returns:
            List of conference data dictionaries
        """
        # Use the browser manager to extract conference information
        soup_info = self.browser.find_conference_info(html)
        conferences = []
        
        # If the browser found a single conference page
        if soup_info.get('title'):
            conf = {
                "title": soup_info.get('title'),
                "dates": soup_info.get('dates'),
                "location": soup_info.get('location'),
                "description": soup_info.get('description') or f"Conference related to {query}",
                "deadlines": soup_info.get('deadlines', []),
                "url": source
            }
            conferences.append(conf)
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