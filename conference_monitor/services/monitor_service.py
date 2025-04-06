"""
Monitoring service for academic conferences and papers
"""
from typing import Dict, List, Any, Optional, Callable
import threading
import time
import logging
from datetime import datetime

from conference_monitor.core.agent import ConferenceAgent
from conference_monitor.core.memory import AgentMemory
from conference_monitor.core.browser import BrowserManager
from conference_monitor.tools.conference_tools import ConferenceSearchTool, ConferenceDeadlineTool
from conference_monitor.tools.paper_tools import PaperSearchTool, PaperSummaryTool, RecentPapersMonitorTool
from conference_monitor.tools.trending_tools import TrendingTopicsTool
from conference_monitor.tools.storage_tools import ExportDataTool, ImportDataTool
from conference_monitor.config import DEFAULT_RESEARCH_AREAS, DEFAULT_REFRESH_INTERVAL_DAYS

# Set up logging
logger = logging.getLogger(__name__)

class MonitorService:
    """Service for monitoring conferences and papers"""
    
    def __init__(self, 
                 agent: Optional[ConferenceAgent] = None,
                 memory: Optional[AgentMemory] = None,
                 browser: Optional[BrowserManager] = None,
                 refresh_interval: int = DEFAULT_REFRESH_INTERVAL_DAYS):
        """Initialize the monitor service
        
        Args:
            agent: ConferenceAgent instance
            memory: AgentMemory instance
            browser: BrowserManager instance
            refresh_interval: Interval for automatic refresh in days
        """
        self.memory = memory or AgentMemory()
        self.browser = browser or BrowserManager()
        self.agent = agent or ConferenceAgent()
        
        # Load research areas from metadata or use defaults
        metadata = self.memory.load_metadata()
        self.research_areas = metadata.get("tracked_research_areas", DEFAULT_RESEARCH_AREAS)
        
        self.refresh_interval = refresh_interval
        self.monitoring_thread = None
        self.stop_event = threading.Event()
        
        # Initialize tools
        self._initialize_tools()
        
        logger.info(f"Monitor service initialized with {len(self.research_areas)} research areas")
    
    def _initialize_tools(self):
        """Initialize monitoring tools"""
        # Conference tools
        self.conference_search = ConferenceSearchTool(
            browser_manager=self.browser,
            memory=self.memory
        )
        
        self.deadline_tool = ConferenceDeadlineTool(
            memory=self.memory
        )
        
        # Paper tools
        self.paper_search = PaperSearchTool(
            memory=self.memory
        )
        
        self.paper_summary = PaperSummaryTool(
            agent=self.agent,
            memory=self.memory
        )
        
        self.recent_papers = RecentPapersMonitorTool(
            memory=self.memory
        )
        
        # Trend tools
        self.trending_topics = TrendingTopicsTool(
            agent=self.agent,
            memory=self.memory
        )
        
        # Storage tools
        self.export_tool = ExportDataTool(
            memory=self.memory
        )
        
        self.import_tool = ImportDataTool(
            memory=self.memory
        )
    
    def set_research_areas(self, research_areas: List[str]):
        """Set research areas to track
        
        Args:
            research_areas: List of research areas to track
        """
        self.research_areas = research_areas
        
        # Update metadata
        metadata = self.memory.load_metadata()
        metadata["tracked_research_areas"] = research_areas
        metadata["last_updated"] = datetime.now().isoformat()
        self.memory.save_metadata(metadata)
        
        logger.info(f"Updated research areas: {', '.join(research_areas)}")
    
    def add_research_area(self, research_area: str):
        """Add a research area to track
        
        Args:
            research_area: Research area to add
        """
        if research_area not in self.research_areas:
            self.research_areas.append(research_area)
            
            # Update metadata
            metadata = self.memory.load_metadata()
            metadata["tracked_research_areas"] = self.research_areas
            metadata["last_updated"] = datetime.now().isoformat()
            self.memory.save_metadata(metadata)
            
            logger.info(f"Added research area: {research_area}")
    
    def remove_research_area(self, research_area: str):
        """Remove a research area from tracking
        
        Args:
            research_area: Research area to remove
        """
        if research_area in self.research_areas:
            self.research_areas.remove(research_area)
            
            # Update metadata
            metadata = self.memory.load_metadata()
            metadata["tracked_research_areas"] = self.research_areas
            metadata["last_updated"] = datetime.now().isoformat()
            self.memory.save_metadata(metadata)
            
            logger.info(f"Removed research area: {research_area}")
    
    def refresh_conferences(self, research_areas: Optional[List[str]] = None) -> Dict[str, Any]:
        """Refresh conference data
        
        Args:
            research_areas: List of research areas to refresh (uses tracked areas if None)
            
        Returns:
            Dictionary with refresh results
        """
        research_areas = research_areas or self.research_areas
        logger.info(f"Refreshing conferences for {len(research_areas)} research areas")
        
        if not research_areas:
            return {
                "error": "No research areas specified for refresh",
                "timestamp": datetime.now().isoformat()
            }
        
        results = {
            "areas": research_areas,
            "start_time": datetime.now().isoformat(),
            "conferences": [],
            "total_conferences": 0
        }
        
        # Use tools to search for conferences
        all_conferences = []
        
        for area in research_areas:
            # Search for conferences in this area
            conferences = self.conference_search.execute(query=area)
            
            if conferences:
                # Process and save conferences
                for conf in conferences:
                    # Add to memory
                    self.memory.save_conference(conf)
                
                # Add to results
                all_conferences.extend(conferences)
                logger.info(f"Found {len(conferences)} conferences for {area}")
            else:
                logger.info(f"Found 0 conferences for {area}")
        
        # Update results
        results["conferences"] = all_conferences
        results["total_conferences"] = len(all_conferences)
        results["end_time"] = datetime.now().isoformat()
        
        return results
    
    def refresh_papers(self, research_areas: Optional[List[str]] = None) -> Dict[str, Any]:
        """Refresh paper data
        
        Args:
            research_areas: List of research areas to refresh (uses tracked areas if None)
            
        Returns:
            Dictionary with refresh results
        """
        research_areas = research_areas or self.research_areas
        logger.info(f"Refreshing papers for {len(research_areas)} research areas")
        
        if not research_areas:
            return {
                "error": "No research areas specified for refresh",
                "timestamp": datetime.now().isoformat()
            }
        
        results = {
            "areas": research_areas,
            "start_time": datetime.now().isoformat(),
            "papers": [],
            "total_papers": 0
        }
        
        # Use tools to search for papers
        all_papers = []
        
        for area in research_areas:
            # Search for papers in this area
            papers = self.paper_search.execute(query=area)
            
            if papers:
                # Process papers with the agent
                processed_papers = []
                for paper in papers:
                    # Add analysis
                    try:
                        analysis = self.agent.analyze_paper(paper)
                        if analysis:
                            paper["analysis"] = analysis
                    except Exception as e:
                        logger.error(f"Error analyzing paper: {str(e)}")
                    
                    # Save to memory
                    self.memory.save_paper(paper)
                    processed_papers.append(paper)
                
                # Add to results
                all_papers.extend(processed_papers)
                logger.info(f"Found {len(processed_papers)} papers for {area}")
            else:
                logger.info(f"Found 0 papers for {area}")
        
        # Update results
        results["papers"] = all_papers
        results["total_papers"] = len(all_papers)
        results["end_time"] = datetime.now().isoformat()
        
        return results
    
    def get_upcoming_deadlines(self, days_ahead: int = 30) -> Dict[str, Any]:
        """Get upcoming conference deadlines
        
        Args:
            days_ahead: Number of days ahead to look for deadlines
            
        Returns:
            Dictionary with deadline results
        """
        return self.deadline_tool.execute(days_ahead=days_ahead)
    
    def analyze_trending_topics(self, 
                              research_areas: Optional[List[str]] = None,
                              paper_count: int = 20) -> Dict[str, Any]:
        """Analyze trending topics in research areas
        
        Args:
            research_areas: List of research areas to analyze (uses tracked areas if None)
            paper_count: Number of papers to analyze per research area
            
        Returns:
            Dictionary with trending topics
        """
        research_areas = research_areas or self.research_areas
        logger.info(f"Analyzing trending topics for {len(research_areas)} research areas")
        
        if not research_areas:
            return {
                "error": "No research areas specified for analysis",
                "timestamp": datetime.now().isoformat()
            }
        
        results = {
            "areas": research_areas,
            "start_time": datetime.now().isoformat(),
            "trends": {},
            "total_trends": 0
        }
        
        # Analyze trends for each research area
        for area in research_areas:
            try:
                area_results = self.trending_topics.execute(
                    research_area=area,
                    paper_count=paper_count
                )
                
                trends = area_results.get("trends", [])
                results["trends"][area] = trends
                
                logger.info(f"Found {len(trends)} trends for {area}")
            except Exception as e:
                logger.error(f"Error analyzing trends for {area}: {str(e)}")
        
        # Count total trends
        results["total_trends"] = sum(len(trends) for trends in results["trends"].values())
        results["end_time"] = datetime.now().isoformat()
        
        return results
    
    def start_monitoring(self, callback: Optional[Callable] = None):
        """Start monitoring conferences and papers
        
        Args:
            callback: Optional callback function to call after each refresh
        """
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            logger.warning("Monitoring already running")
            return
        
        self.stop_event.clear()
        self.monitoring_thread = threading.Thread(target=self.monitor_loop, args=(callback,))
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        
        logger.info("Started monitoring thread")
    
    def monitor_loop(self, callback: Optional[Callable] = None):
        """Monitor loop that runs periodically"""
        logger.info("Monitoring thread started")
        
        while not self.stop_event.is_set():
            try:
                # Refresh conferences and papers
                conf_results = self.refresh_conferences()
                paper_results = self.refresh_papers()
                
                # Create result object
                result = {
                    "timestamp": datetime.now().isoformat(),
                    "conferences": conf_results,
                    "papers": paper_results
                }
                
                # Call callback if provided
                if callback:
                    try:
                        callback(result)
                    except Exception as e:
                        logger.error(f"Error in monitoring callback: {str(e)}")
                
                # Log results
                total_conferences = conf_results.get("total_conferences", 0)
                total_papers = paper_results.get("total_papers", 0)
                
                logger.info(f"Monitoring refresh completed: {total_conferences} conferences, {total_papers} papers")
                
                # Wait for the next refresh interval
                # Convert days to seconds
                interval_seconds = self.refresh_interval * 24 * 60 * 60
                
                # Check stop event every minute while waiting
                for _ in range(interval_seconds // 60):
                    if self.stop_event.is_set():
                        break
                    time.sleep(60)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                # Wait for a shorter time after an error
                time.sleep(60 * 30)  # 30 minutes
        
        logger.info("Monitoring thread stopped")
    
    def stop_monitoring(self):
        """Stop the monitoring thread"""
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.stop_event.set()
            self.monitoring_thread.join(timeout=1.0)
            logger.info("Monitoring thread stopped")
        else:
            logger.warning("No monitoring thread running") 