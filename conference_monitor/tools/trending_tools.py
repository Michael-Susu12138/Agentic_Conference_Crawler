"""
Trending topic analysis tools for academic research
"""
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
import uuid

from conference_monitor.tools.base import BaseTool
from conference_monitor.core.memory import AgentMemory
from conference_monitor.tools.paper_tools import PaperSearchTool

# Set up logging
logger = logging.getLogger(__name__)

class TrendingTopicsTool(BaseTool):
    """Tool for identifying trending topics in research papers"""
    
    def __init__(self, agent=None, memory: Optional[AgentMemory] = None):
        """Initialize the trending topics tool
        
        Args:
            agent: ConferenceAgent instance for LLM access
            memory: AgentMemory instance
        """
        super().__init__(
            name="trending_topics",
            description="Identify trending topics and research directions from recent papers"
        )
        self.agent = agent  # Will be set by service
        self.memory = memory or AgentMemory()
    
    def _get_parameters_schema(self) -> Dict[str, Any]:
        """Get the schema for the tool's parameters"""
        return {
            "type": "object",
            "properties": {
                "research_area": {
                    "type": "string",
                    "description": "The research area to analyze trends for"
                },
                "paper_count": {
                    "type": "integer",
                    "description": "Number of recent papers to analyze"
                },
                "include_papers": {
                    "type": "boolean",
                    "description": "Whether to include paper details in the response"
                }
            },
            "required": ["research_area"]
        }
    
    def _execute(self, research_area: str, paper_count: Optional[int] = 20,
                include_papers: Optional[bool] = False) -> Dict[str, Any]:
        """Execute the trending topics analysis
        
        Args:
            research_area: The research area to analyze trends for
            paper_count: Number of recent papers to analyze
            include_papers: Whether to include paper details in the response
            
        Returns:
            Dictionary with trending topics
        """
        # Check if agent is available
        if not self.agent:
            return {
                "error": "Agent not available for trending topic analysis"
            }
        
        # Get recent papers in the research area
        paper_search = PaperSearchTool(memory=self.memory)
        paper_results = paper_search.execute(
            query=research_area,
            limit=paper_count
        )
        
        papers = paper_results.get('papers', [])
        
        if not papers:
            return {
                "error": f"No papers found for research area: {research_area}",
                "trends": [],
                "research_area": research_area
            }
        
        # Use the agent to identify trending topics
        try:
            trends = self.agent.identify_trending_topics(papers)
            
            # Create a trend report
            trend_report = {
                "id": f"trend_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}",
                "research_area": research_area,
                "trends": trends,
                "paper_count": len(papers),
                "date": datetime.now().isoformat()
            }
            
            # Include paper details if requested
            if include_papers:
                trend_report["papers"] = [
                    {
                        "id": p.get("id", ""),
                        "title": p.get("title", ""),
                        "authors": p.get("authors", []),
                        "year": p.get("year", ""),
                        "url": p.get("url", "")
                    }
                    for p in papers
                ]
            
            # Save the trend report to memory
            self.memory.save_trend(trend_report)
            
            return trend_report
            
        except Exception as e:
            logger.error(f"Error analyzing trending topics: {str(e)}")
            return {
                "research_area": research_area,
                "error": str(e),
                "success": False
            }


class ConferenceTopicsTool(BaseTool):
    """Tool for analyzing topics at specific conferences"""
    
    def __init__(self, agent=None, memory: Optional[AgentMemory] = None):
        """Initialize the conference topics tool
        
        Args:
            agent: ConferenceAgent instance for LLM access
            memory: AgentMemory instance
        """
        super().__init__(
            name="conference_topics",
            description="Analyze topics and themes at specific academic conferences"
        )
        self.agent = agent  # Will be set by service
        self.memory = memory or AgentMemory()
    
    def _get_parameters_schema(self) -> Dict[str, Any]:
        """Get the schema for the tool's parameters"""
        return {
            "type": "object",
            "properties": {
                "conference_id": {
                    "type": "string",
                    "description": "ID of the conference to analyze"
                },
                "conference_name": {
                    "type": "string",
                    "description": "Name of the conference to analyze (alternative to conference_id)"
                },
                "year": {
                    "type": "integer",
                    "description": "Year of the conference to analyze"
                }
            }
        }
    
    def _execute(self, conference_id: Optional[str] = None, 
                conference_name: Optional[str] = None,
                year: Optional[int] = None) -> Dict[str, Any]:
        """Execute the conference topics analysis
        
        Args:
            conference_id: ID of the conference to analyze
            conference_name: Name of the conference to analyze
            year: Year of the conference to analyze
            
        Returns:
            Dictionary with conference topics
        """
        # Check if agent is available
        if not self.agent:
            return {
                "error": "Agent not available for conference topic analysis"
            }
        
        # Try to get conference data
        conference_data = None
        
        if conference_id:
            conference_data = self.memory.get_conference(conference_id)
        
        if not conference_data and conference_name:
            # Try to find conference by name in memory
            conferences = self.memory.list_conferences()
            for conf in conferences:
                if conference_name.lower() in conf.get('title', '').lower():
                    conference_data = conf
                    break
        
        if not conference_data:
            return {
                "error": "Conference data not found",
                "conference_id": conference_id,
                "conference_name": conference_name
            }
        
        # Use paper search to find papers related to this conference
        paper_search = PaperSearchTool(memory=self.memory)
        
        # Create a query using conference name and year
        conf_title = conference_data.get('title', '')
        query = conf_title
        
        if year:
            query = f"{query} {year}"
        
        paper_results = paper_search.execute(
            query=query,
            limit=30
        )
        
        papers = paper_results.get('papers', [])
        
        if not papers:
            return {
                "error": f"No papers found for conference: {conf_title}",
                "conference_id": conference_data.get('id'),
                "conference_name": conf_title
            }
        
        # Use the agent to identify topics for this conference
        try:
            topics = self.agent.identify_trending_topics(papers)
            
            # Create a conference topic report
            topic_report = {
                "id": f"conf_topic_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}",
                "conference_id": conference_data.get('id'),
                "conference_name": conf_title,
                "year": year or "unknown",
                "topics": topics,
                "paper_count": len(papers),
                "date": datetime.now().isoformat()
            }
            
            return topic_report
            
        except Exception as e:
            logger.error(f"Error analyzing conference topics: {str(e)}")
            return {
                "conference_id": conference_data.get('id'),
                "conference_name": conf_title,
                "error": str(e),
                "success": False
            } 