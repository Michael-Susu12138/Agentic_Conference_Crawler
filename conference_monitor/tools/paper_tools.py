"""
Paper search tools for finding and analyzing academic papers
"""
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime, timedelta

from scholarly import scholarly
import requests

from conference_monitor.tools.base import BaseTool
from conference_monitor.core.memory import AgentMemory
from conference_monitor.config import SEMANTIC_SCHOLAR_API_KEY, MAX_PAPERS_PER_QUERY

# Set up logging
logger = logging.getLogger(__name__)

class PaperSearchTool(BaseTool):
    """Tool for searching academic papers"""
    
    def __init__(self, memory: Optional[AgentMemory] = None):
        """Initialize the paper search tool
        
        Args:
            memory: AgentMemory instance
        """
        super().__init__(
            name="paper_search",
            description="Search for academic papers by topic, author, or keywords"
        )
        self.memory = memory or AgentMemory()
        
        # Set API key for Semantic Scholar if available
        self.has_semantic_scholar = bool(SEMANTIC_SCHOLAR_API_KEY)
    
    def _get_parameters_schema(self) -> Dict[str, Any]:
        """Get the schema for the tool's parameters"""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query (e.g., 'transformer models')"
                },
                "author": {
                    "type": "string",
                    "description": "Filter by author name"
                },
                "year_from": {
                    "type": "integer",
                    "description": "Filter papers published on or after this year"
                },
                "year_to": {
                    "type": "integer",
                    "description": "Filter papers published on or before this year"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of papers to return"
                }
            },
            "required": ["query"]
        }
    
    def _execute(self, query: str, author: Optional[str] = None,
                year_from: Optional[int] = None, year_to: Optional[int] = None,
                limit: Optional[int] = None) -> Dict[str, Any]:
        """Execute the paper search
        
        Args:
            query: The search query
            author: Filter by author name
            year_from: Filter papers published on or after this year
            year_to: Filter papers published on or before this year
            limit: Maximum number of papers to return
            
        Returns:
            Dictionary with search results
        """
        limit = min(limit or MAX_PAPERS_PER_QUERY, MAX_PAPERS_PER_QUERY)
        
        logger.info(f"Searching for papers: {query}")
        
        # Prepare search query with filters
        search_query = query
        if author:
            search_query = f"author:{author} {search_query}"
        
        # Default to recent papers if no year range specified
        if not year_from and not year_to:
            current_year = datetime.now().year
            year_from = current_year - 2  # Last 2 years
        
        try:
            # Use Google Scholar API through scholarly
            search_query = scholarly.search_pubs(search_query)
            papers = []
            
            for i, result in enumerate(search_query):
                if i >= limit:
                    break
                
                # Filter by year if specified
                pub_year = result.get('bib', {}).get('pub_year')
                if pub_year:
                    try:
                        pub_year = int(pub_year)
                        if (year_from and pub_year < year_from) or (year_to and pub_year > year_to):
                            continue
                    except (ValueError, TypeError):
                        # If we can't parse the year, include it anyway
                        pass
                
                # Extract relevant info
                paper_data = {
                    "id": result.get('pub_url', '').split('citation_for_view=')[-1] if result.get('pub_url') else f"paper_{i}",
                    "title": result.get('bib', {}).get('title', 'Untitled'),
                    "authors": result.get('bib', {}).get('author', []),
                    "year": pub_year,
                    "abstract": result.get('bib', {}).get('abstract', ''),
                    "url": result.get('pub_url', ''),
                    "citations": result.get('num_citations', 0),
                    "source": "Google Scholar"
                }
                
                papers.append(paper_data)
                
                # Store in memory
                self.memory.save_paper(paper_data)
            
            return {
                "papers": papers,
                "total_count": len(papers),
                "query": query,
                "source": "Google Scholar"
            }
            
        except Exception as e:
            logger.error(f"Error searching papers: {str(e)}")
            # Fall back to empty results
            return {
                "papers": [],
                "total_count": 0,
                "query": query,
                "error": str(e)
            }


class PaperSummaryTool(BaseTool):
    """Tool for summarizing academic papers"""
    
    def __init__(self, agent=None, memory: Optional[AgentMemory] = None):
        """Initialize the paper summary tool
        
        Args:
            agent: ConferenceAgent instance for LLM access
            memory: AgentMemory instance
        """
        super().__init__(
            name="paper_summary",
            description="Summarize an academic paper and extract key information"
        )
        self.agent = agent  # Will be set by service
        self.memory = memory or AgentMemory()
    
    def _get_parameters_schema(self) -> Dict[str, Any]:
        """Get the schema for the tool's parameters"""
        return {
            "type": "object",
            "properties": {
                "paper_id": {
                    "type": "string",
                    "description": "ID of the paper to summarize"
                },
                "paper_url": {
                    "type": "string",
                    "description": "URL of the paper to summarize (alternative to paper_id)"
                }
            },
            "required": ["paper_id"]
        }
    
    def _execute(self, paper_id: str, paper_url: Optional[str] = None) -> Dict[str, Any]:
        """Execute the paper summary
        
        Args:
            paper_id: ID of the paper to summarize
            paper_url: URL of the paper to summarize (alternative to paper_id)
            
        Returns:
            Dictionary with paper summary
        """
        # Check if agent is available
        if not self.agent:
            return {
                "error": "Agent not available for paper summarization"
            }
        
        # Try to retrieve paper from memory
        paper_data = self.memory.get_paper(paper_id)
        
        if not paper_data and paper_url:
            # Try to fetch paper data from URL
            # This would require a paper extractor in a real implementation
            return {
                "error": "Paper data not found and paper extraction from URL not implemented"
            }
        
        if not paper_data:
            return {
                "error": f"Paper with ID {paper_id} not found in memory"
            }
        
        # Use the agent to analyze the paper
        try:
            analysis = self.agent.analyze_paper(paper_data)
            
            # Add the analysis to the paper data and save
            paper_data['analysis'] = analysis.get('analysis', '')
            self.memory.save_paper(paper_data)
            
            return {
                "paper_id": paper_id,
                "title": paper_data.get('title', ''),
                "authors": paper_data.get('authors', []),
                "year": paper_data.get('year'),
                "summary": analysis.get('analysis', ''),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error summarizing paper: {str(e)}")
            return {
                "paper_id": paper_id,
                "error": str(e),
                "success": False
            }


class RecentPapersMonitorTool(BaseTool):
    """Tool for monitoring recently published papers in specific research areas"""
    
    def __init__(self, memory: Optional[AgentMemory] = None):
        """Initialize the recent papers monitor tool
        
        Args:
            memory: AgentMemory instance
        """
        super().__init__(
            name="recent_papers_monitor",
            description="Monitor recently published papers in specific research areas"
        )
        self.memory = memory or AgentMemory()
    
    def _get_parameters_schema(self) -> Dict[str, Any]:
        """Get the schema for the tool's parameters"""
        return {
            "type": "object",
            "properties": {
                "research_area": {
                    "type": "string",
                    "description": "The research area to monitor"
                },
                "days_back": {
                    "type": "integer",
                    "description": "Number of days to look back for recent papers"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of papers to return"
                }
            },
            "required": ["research_area"]
        }
    
    def _execute(self, research_area: str, days_back: Optional[int] = 30,
                limit: Optional[int] = None) -> Dict[str, Any]:
        """Execute the recent papers monitor
        
        Args:
            research_area: The research area to monitor
            days_back: Number of days to look back
            limit: Maximum number of papers to return
            
        Returns:
            Dictionary with recent papers
        """
        limit = min(limit or MAX_PAPERS_PER_QUERY, MAX_PAPERS_PER_QUERY)
        
        # Get the current date
        now = datetime.now()
        cutoff_date = now - timedelta(days=days_back)
        
        logger.info(f"Monitoring recent papers in: {research_area} (last {days_back} days)")
        
        # Create a paper search tool to find recent papers
        search_tool = PaperSearchTool(memory=self.memory)
        
        # Current year and last year
        current_year = now.year
        
        search_results = search_tool.execute(
            query=research_area,
            year_from=current_year - 1,  # Include papers from last year
            limit=limit
        )
        
        papers = search_results.get('papers', [])
        
        # Filter to include only recent papers
        # Note: This assumes we have paper dates in a parseable format
        # In a real implementation, we'd need more robust date parsing
        
        # For this demo, just return what we found
        return {
            "research_area": research_area,
            "days_back": days_back,
            "recent_papers": papers,
            "total_count": len(papers)
        } 