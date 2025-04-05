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
                 refresh_interval: int = DEFAULT_REFRESH_INTERVAL_DAYS,
                 mock_mode: bool = True):
        """Initialize the monitor service
        
        Args:
            agent: ConferenceAgent instance
            memory: AgentMemory instance
            browser: BrowserManager instance
            refresh_interval: Interval for automatic refresh in days
            mock_mode: Whether to run in mock mode without API calls
        """
        self.memory = memory or AgentMemory()
        self.browser = browser or BrowserManager()
        self.agent = agent or ConferenceAgent(mock_mode=mock_mode)
        self.mock_mode = mock_mode
        
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
        
        if self.mock_mode:
            # Create mock data
            mock_conferences = []
            
            # Create relevant mock data for each research area
            for area in research_areas:
                area_clean = area.lower().strip()
                mock_conferences.extend([
                    {
                        "id": f"mock_conf_{area_clean}_1",
                        "title": f"International Conference on {area}",
                        "dates": "October 15-17, 2025",
                        "location": "San Francisco, CA",
                        "description": f"Leading conference on {area} research and applications.",
                        "deadlines": ["Paper submission: June 1, 2025", "Registration: September 1, 2025"],
                        "url": "https://example.com/conf"
                    },
                    {
                        "id": f"mock_conf_{area_clean}_2",
                        "title": f"{area} Summit",
                        "dates": "May 5-7, 2025",
                        "location": "London, UK",
                        "description": f"Industry and academic summit on {area}.",
                        "deadlines": ["Abstract submission: February 1, 2025", "Registration: April 1, 2025"],
                        "url": "https://example.com/summit"
                    }
                ])
            
            # Add general conferences that include multiple topics
            mock_conferences.extend([
                {
                    "id": "mock_conf_general_1",
                    "title": "World AI and Machine Learning Conference",
                    "dates": "November 10-12, 2025",
                    "location": "Berlin, Germany",
                    "description": "Global conference covering AI, Machine Learning, and Data Science topics.",
                    "deadlines": ["Paper submission: July 15, 2025", "Registration: October 1, 2025"],
                    "url": "https://example.com/world-ai"
                },
                {
                    "id": "mock_conf_general_2",
                    "title": "Annual Computer Science Symposium",
                    "dates": "September 22-24, 2025",
                    "location": "Tokyo, Japan",
                    "description": "Broad computer science conference covering AI, algorithms, and computing systems.",
                    "deadlines": ["Paper submission: May 30, 2025", "Registration: August 15, 2025"],
                    "url": "https://example.com/cs-symposium"
                }
            ])
            
            # Save mock conferences to memory
            for conf in mock_conferences:
                self.memory.save_conference(conf)
            
            # Add to results
            results["conferences"] = mock_conferences
            results["total_conferences"] = len(mock_conferences)
            return results
        
        # Search for conferences in each research area
        for area in research_areas:
            try:
                area_results = self.conference_search.execute(
                    research_area=area
                )
                
                conferences = area_results.get("conferences", [])
                results["conferences"].extend(conferences)
                
                logger.info(f"Found {len(conferences)} conferences for {area}")
            except Exception as e:
                logger.error(f"Error refreshing conferences for {area}: {str(e)}")
        
        results["total_conferences"] = len(results["conferences"])
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
        
        if self.mock_mode:
            # Create mock data
            mock_papers = []
            
            # Create relevant mock data for each research area
            for area in research_areas:
                area_clean = area.lower().strip()
                mock_papers.extend([
                    {
                        "id": f"mock_paper_{area_clean}_1",
                        "title": f"Recent Advances in {area}",
                        "authors": ["Jane Smith", "John Doe", "Alice Johnson"],
                        "year": 2025,
                        "citations": 42,
                        "abstract": f"This paper presents the latest advances in {area}, focusing on novel approaches and methodologies. We demonstrate significant improvements over baseline methods.",
                        "url": "https://example.com/paper1",
                        "research_area": area
                    },
                    {
                        "id": f"mock_paper_{area_clean}_2",
                        "title": f"{area} for Real-World Applications",
                        "authors": ["Bob Williams", "Sarah Miller"],
                        "year": 2025,
                        "citations": 28,
                        "abstract": f"We explore practical applications of {area} in industry settings. Our findings show promising results for deployment in production environments.",
                        "url": "https://example.com/paper2",
                        "research_area": area
                    },
                    {
                        "id": f"mock_paper_{area_clean}_3",
                        "title": f"A Survey of {area} Techniques",
                        "authors": ["Chris Taylor", "David Brown", "Emily Davis"],
                        "year": 2024,
                        "citations": 76,
                        "abstract": f"This comprehensive survey reviews the state-of-the-art in {area}, categorizing approaches and identifying future research directions.",
                        "url": "https://example.com/paper3",
                        "research_area": area
                    }
                ])
            
            # Save mock papers to memory
            for paper in mock_papers:
                self.memory.save_paper(paper)
            
            # Add to results
            results["papers"] = mock_papers
            results["total_papers"] = len(mock_papers)
            return results
        
        # Search for papers in each research area
        for area in research_areas:
            try:
                area_results = self.paper_search.execute(
                    query=area,
                    limit=20
                )
                
                papers = area_results.get("papers", [])
                results["papers"].extend(papers)
                
                logger.info(f"Found {len(papers)} papers for {area}")
            except Exception as e:
                logger.error(f"Error refreshing papers for {area}: {str(e)}")
        
        results["total_papers"] = len(results["papers"])
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
        
        if self.mock_mode:
            # Return mock data
            for area in research_areas:
                results["trends"][area] = [
                    f"1. Recent advances in {area}",
                    f"2. Applications of {area} in healthcare",
                    f"3. {area} for sustainable development",
                    f"4. Ethical considerations in {area}",
                    f"5. Future directions of {area}"
                ]
            results["total_trends"] = len(research_areas) * 5
            return results
        
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