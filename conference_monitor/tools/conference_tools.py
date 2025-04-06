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
            description="Search for academic conferences based on research area, date range, or keywords"
        )
        self.browser = browser_manager or BrowserManager()
        self.memory = memory or AgentMemory()
    
    def _get_parameters_schema(self) -> Dict[str, Any]:
        """Get the schema for the tool's parameters"""
        return {
            "type": "object",
            "properties": {
                "research_area": {
                    "type": "string",
                    "description": "The research area or field to search for (e.g., 'machine learning')"
                },
                "keywords": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Additional keywords to narrow the search"
                },
                "start_date": {
                    "type": "string",
                    "description": "Start date for conference date range (YYYY-MM-DD)"
                },
                "end_date": {
                    "type": "string",
                    "description": "End date for conference date range (YYYY-MM-DD)"
                },
                "sources": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of URLs to search for conferences"
                }
            },
            "required": ["research_area"]
        }
    
    def _execute(self, research_area: str, keywords: Optional[List[str]] = None,
                start_date: Optional[str] = None, end_date: Optional[str] = None,
                sources: Optional[List[str]] = None) -> Dict[str, Any]:
        """Execute the conference search
        
        Args:
            research_area: The research area to search for
            keywords: Additional keywords to narrow the search
            start_date: Start date for conference date range
            end_date: End date for conference date range
            sources: List of URLs to search for conferences
            
        Returns:
            Dictionary with search results
        """
        keywords = keywords or []
        sources = sources or DEFAULT_CONFERENCE_SOURCES
        
        # Combine search terms
        search_terms = [research_area] + keywords
        search_query = " ".join(search_terms)
        
        logger.info(f"Searching for conferences: {search_query}")
        
        conferences = []
        sources_results = {}
        
        # Search each source
        for source_url in sources:
            try:
                source_name = urlparse(source_url).netloc
                logger.info(f"Searching source: {source_name}")
                
                # Get the source page
                html = self.browser.get_page(source_url)
                if not html:
                    sources_results[source_name] = {"error": "Failed to retrieve page"}
                    continue
                
                # Extract links that might be conferences
                links = self.browser.extract_links(html, source_url)
                
                # Filter links that match our search terms
                matching_links = []
                for link in links:
                    link_text = link.get('text', '').lower()
                    if any(term.lower() in link_text for term in search_terms):
                        matching_links.append(link)
                
                # For each matching link, try to extract conference info
                source_conferences = []
                for link in matching_links[:5]:  # Limit to 5 links per source
                    link_url = link.get('url')
                    if not link_url:
                        continue
                    
                    link_html = self.browser.get_page(link_url)
                    if not link_html:
                        continue
                    
                    # Extract conference info
                    conf_info = self.browser.find_conference_info(link_html)
                    
                    # Generate a unique ID for this conference
                    if conf_info.get('title'):
                        # Create a unique ID based on title and URL
                        conf_id = hashlib.md5(f"{conf_info['title']}_{link_url}".encode()).hexdigest()
                        
                        # Add the source and URL info
                        conf_info['id'] = conf_id
                        conf_info['url'] = link_url
                        conf_info['source'] = source_name
                        
                        # Filter by date if provided
                        if start_date or end_date:
                            # Skip if we can't parse the conference date
                            if not conf_info.get('dates'):
                                continue
                            
                            # TODO: Implement date filtering
                            # For now, include all conferences with dates
                        
                        source_conferences.append(conf_info)
                        
                        # Store in memory
                        self.memory.save_conference(conf_info)
                
                sources_results[source_name] = {
                    "count": len(source_conferences),
                    "conferences": source_conferences
                }
                
                conferences.extend(source_conferences)
                
            except Exception as e:
                logger.error(f"Error searching source {source_url}: {str(e)}")
                sources_results[source_url] = {"error": str(e)}
        
        return {
            "conferences": conferences,
            "sources": sources_results,
            "query": search_query,
            "total_count": len(conferences)
        }

    def execute(self, query: str) -> List[Dict[str, Any]]:
        """Execute the conference search tool
        
        Args:
            query: Search query for conferences
            
        Returns:
            List of conference data dictionaries
        """
        logger.info(f"Searching for conferences: {query}")
        sources = DEFAULT_CONFERENCE_SOURCES
        conferences = []
        
        for source in sources:
            logger.info(f"Searching source: {source}")
            try:
                # Fetch HTML from source
                html = self.browser.fetch_url(source)
                
                if not html:
                    logger.warning(f"No HTML content found for {source}")
                    continue
                
                # Extract conference information based on source
                conf_data = self._extract_conferences(html, source, query)
                if conf_data:
                    # Create unique IDs for conferences if not present
                    for conf in conf_data:
                        if "id" not in conf:
                            # Create a safe ID for the conference
                            title = conf.get("title", "unknown")
                            safe_title = re.sub(r'[\\/:*?"<>|]', '_', title)
                            conf["id"] = f"{safe_title}_{uuid.uuid4().hex[:8]}"
                    conferences.extend(conf_data)
            except Exception as e:
                logger.error(f"Error processing source {source}: {str(e)}")
        
        return conferences

    def _extract_conferences(self, html: str, source: str, query: str) -> List[Dict[str, Any]]:
        """Extract conference information from HTML
        
        Args:
            html: HTML content
            source: Source URL
            query: Search query
            
        Returns:
            List of conference data dictionaries
        """
        # For now, use a very simple mock implementation that can be improved later
        # This is just to prevent errors while we're implementing the real functionality
        domain = urlparse(source).netloc
        
        if "ieee.org" in domain:
            # IEEE conferences (simplified mock for now)
            return [
                {
                    "title": f"IEEE International Conference on {query.title()}",
                    "dates": "October 15-17, 2025",
                    "location": "San Francisco, CA",
                    "description": f"IEEE conference focused on {query}.",
                    "deadlines": ["Paper submission: June 1, 2025", "Registration: September 1, 2025"],
                    "url": source
                }
            ]
        elif "acm.org" in domain:
            # ACM conferences
            return [
                {
                    "title": f"ACM Symposium on {query.title()}",
                    "dates": "May 5-7, 2025",
                    "location": "New York, NY",
                    "description": f"ACM symposium on {query} and related topics.",
                    "deadlines": ["Abstract submission: February 1, 2025", "Registration: April 1, 2025"],
                    "url": source
                }
            ]
        elif "neurips" in domain:
            # NeurIPS
            return [
                {
                    "title": "Neural Information Processing Systems (NeurIPS)",
                    "dates": "December 1-7, 2025",
                    "location": "Vancouver, Canada",
                    "description": "Premier conference on neural information processing systems and machine learning.",
                    "deadlines": ["Paper submission: May 15, 2025", "Registration: November 1, 2025"],
                    "url": source
                }
            ]
        else:
            # Generic conferences for other sources
            return [
                {
                    "title": f"International Conference on {query.title()}",
                    "dates": "November 10-12, 2025",
                    "location": "Berlin, Germany",
                    "description": f"Global conference covering {query} topics.",
                    "deadlines": ["Paper submission: July 15, 2025", "Registration: October 1, 2025"],
                    "url": source
                }
            ]

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