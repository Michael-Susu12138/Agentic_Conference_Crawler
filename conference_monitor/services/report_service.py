"""
Report service for generating reports and summaries
"""
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
import uuid
import os
import json

from conference_monitor.core.agent import ConferenceAgent
from conference_monitor.core.memory import AgentMemory
from conference_monitor.config import DATA_DIR

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReportService:
    """Service for generating reports and summaries"""
    
    def __init__(self, 
                 agent: Optional[ConferenceAgent] = None,
                 memory: Optional[AgentMemory] = None):
        """Initialize the report service
        
        Args:
            agent: ConferenceAgent instance
            memory: AgentMemory instance
        """
        self.agent = agent or ConferenceAgent()
        self.memory = memory or AgentMemory()
        
        # Create reports directory
        self.reports_dir = os.path.join(DATA_DIR, "reports")
        os.makedirs(self.reports_dir, exist_ok=True)
        
        logger.info("Report service initialized")
    
    def generate_conference_report(self, 
                                 research_area: Optional[str] = None,
                                 max_conferences: int = 10) -> Dict[str, Any]:
        """Generate a report on upcoming conferences
        
        Args:
            research_area: Research area to filter by
            max_conferences: Maximum number of conferences to include
            
        Returns:
            Dictionary with report data
        """
        # Get conferences from memory
        conferences = self.memory.list_conferences()
        
        # Filter by research area if provided
        if research_area:
            filtered_conferences = []
            research_area_lower = research_area.lower()
            
            for conf in conferences:
                # Check title and description for the research area
                title = conf.get('title', '').lower()
                desc = conf.get('description', '').lower()
                
                if research_area_lower in title or research_area_lower in desc:
                    filtered_conferences.append(conf)
            
            conferences = filtered_conferences
        
        # Sort by dates (would need proper date parsing in a full implementation)
        # For now, just take the most recently added
        conferences = sorted(
            conferences, 
            key=lambda c: c.get('_last_updated', ''), 
            reverse=True
        )[:max_conferences]
        
        # Prepare conference data for report
        conference_data = []
        for conf in conferences:
            conf_data = {
                "id": conf.get('id', ''),
                "title": conf.get('title', 'Untitled Conference'),
                "dates": conf.get('dates', 'Unknown dates'),
                "location": conf.get('location', 'Unknown location'),
                "url": conf.get('url', ''),
                "deadlines": conf.get('deadlines', [])
            }
            conference_data.append(conf_data)
        
        # Generate report
        report_id = f"conf_report_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}"
        
        report = {
            "id": report_id,
            "title": f"Upcoming Conferences Report",
            "subtitle": f"Research area: {research_area}" if research_area else "All research areas",
            "generated_date": datetime.now().isoformat(),
            "conferences": conference_data,
            "conference_count": len(conference_data)
        }
        
        # Save report
        report_path = os.path.join(self.reports_dir, f"{report_id}.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        return report
    
    def generate_paper_report(self,
                            research_area: str,
                            max_papers: int = 10) -> Dict[str, Any]:
        """Generate a report on recent papers
        
        Args:
            research_area: Research area to report on
            max_papers: Maximum number of papers to include
            
        Returns:
            Dictionary with report data
        """
        # Get papers from memory
        papers = self.memory.list_papers()
        
        # Filter to match research area
        filtered_papers = []
        research_area_lower = research_area.lower()
        
        for paper in papers:
            # Check title and abstract for the research area
            title = paper.get('title', '').lower()
            abstract = paper.get('abstract', '').lower()
            
            if research_area_lower in title or research_area_lower in abstract:
                filtered_papers.append(paper)
        
        # Sort by citations or recency
        sorted_papers = sorted(
            filtered_papers, 
            key=lambda p: p.get('citations', 0), 
            reverse=True
        )[:max_papers]
        
        # Prepare paper data for report
        paper_data = []
        for paper in sorted_papers:
            paper_data.append({
                "id": paper.get('id', ''),
                "title": paper.get('title', 'Untitled'),
                "authors": paper.get('authors', []),
                "year": paper.get('year', ''),
                "citations": paper.get('citations', 0),
                "url": paper.get('url', ''),
                "abstract": paper.get('abstract', ''),
                "analysis": paper.get('analysis', '')
            })
        
        # Use LLM to summarize the papers as a group
        if paper_data and self.agent:
            papers_text = "\n\n".join([
                f"Title: {p['title']}\nAuthors: {', '.join(p['authors']) if isinstance(p['authors'], list) else p['authors']}\nAbstract: {p['abstract'][:200]}..."
                for p in paper_data[:5]  # Limit to 5 papers for the summary
            ])
            
            summary_query = f"""
            Summarize the following collection of recent papers in {research_area}:
            
            {papers_text}
            
            Please identify:
            1. Common themes across these papers
            2. Notable advances or findings
            3. Potential directions for future research
            """
            
            try:
                collection_summary = self.agent.run_query(summary_query)
            except Exception as e:
                logger.error(f"Error generating collection summary: {str(e)}")
                collection_summary = "Error generating summary."
        else:
            collection_summary = "No papers found or agent not available."
        
        # Generate report
        report_id = f"paper_report_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}"
        
        report = {
            "id": report_id,
            "title": f"Recent Papers Report: {research_area}",
            "generated_date": datetime.now().isoformat(),
            "research_area": research_area,
            "papers": paper_data,
            "paper_count": len(paper_data),
            "collection_summary": collection_summary
        }
        
        # Save report
        report_path = os.path.join(self.reports_dir, f"{report_id}.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        return report
    
    def generate_trends_report(self,
                             research_areas: Optional[List[str]] = None,
                             max_trends_per_area: int = 5) -> Dict[str, Any]:
        """Generate a report on research trends
        
        Args:
            research_areas: Research areas to report on
            max_trends_per_area: Maximum number of trends per area
            
        Returns:
            Dictionary with report data
        """
        if not research_areas:
            # Get from metadata
            metadata = self.memory.load_metadata()
            research_areas = metadata.get("tracked_research_areas", [])
            
            if not research_areas:
                return {
                    "error": "No research areas specified for trends report",
                    "success": False
                }
        
        # Get latest trends from memory
        trends_data = self.memory.get_latest_trends(limit=100)
        
        # Organize by research area
        trends_by_area = {}
        
        for trend in trends_data:
            area = trend.get('research_area', '').lower()
            
            # Skip if not in requested areas
            if not any(ra.lower() == area for ra in research_areas):
                continue
            
            if area not in trends_by_area:
                trends_by_area[area] = []
            
            trends_by_area[area].append(trend)
        
        # Take top trends for each area
        report_data = {}
        
        for area, trends in trends_by_area.items():
            # Sort by date (newest first)
            sorted_trends = sorted(
                trends, 
                key=lambda t: t.get('_created', ''), 
                reverse=True
            )
            
            # Take only the first trend report
            if sorted_trends:
                latest_trend = sorted_trends[0]
                
                report_data[area] = {
                    "trends": latest_trend.get('trends', [])[:max_trends_per_area],
                    "date": latest_trend.get('date', ''),
                    "paper_count": latest_trend.get('paper_count', 0)
                }
        
        # Generate big picture analysis if we have an agent
        if self.agent and report_data:
            # Prepare trends text for summary
            trends_text = ""
            for area, data in report_data.items():
                trends_text += f"\nResearch Area: {area}\n"
                for i, trend in enumerate(data.get('trends', []), 1):
                    trends_text += f"{i}. {trend}\n"
            
            big_picture_query = f"""
            Analyze the following research trends across different areas:
            
            {trends_text}
            
            Please provide:
            1. Cross-cutting themes or connections between different research areas
            2. Overall direction of the field
            3. Emerging interdisciplinary opportunities
            """
            
            try:
                big_picture_analysis = self.agent.run_query(big_picture_query)
            except Exception as e:
                logger.error(f"Error generating big picture analysis: {str(e)}")
                big_picture_analysis = "Error generating analysis."
        else:
            big_picture_analysis = "No trends found or agent not available."
        
        # Generate report
        report_id = f"trends_report_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}"
        
        report = {
            "id": report_id,
            "title": "Research Trends Report",
            "generated_date": datetime.now().isoformat(),
            "research_areas": research_areas,
            "trends_by_area": report_data,
            "big_picture_analysis": big_picture_analysis
        }
        
        # Save report
        report_path = os.path.join(self.reports_dir, f"{report_id}.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        return report
    
    def list_reports(self, max_reports: int = 10) -> List[Dict[str, Any]]:
        """List available reports
        
        Args:
            max_reports: Maximum number of reports to return
            
        Returns:
            List of report metadata
        """
        reports = []
        
        for file_name in os.listdir(self.reports_dir):
            if not file_name.endswith('.json'):
                continue
            
            file_path = os.path.join(self.reports_dir, file_name)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    report = json.load(f)
                
                reports.append({
                    "id": report.get('id', ''),
                    "title": report.get('title', ''),
                    "generated_date": report.get('generated_date', ''),
                    "type": "conference" if "conferences" in report else 
                           "paper" if "papers" in report else 
                           "trends" if "trends_by_area" in report else "unknown"
                })
            except Exception as e:
                logger.error(f"Error loading report {file_name}: {str(e)}")
        
        # Sort by date (newest first)
        reports.sort(key=lambda r: r.get('generated_date', ''), reverse=True)
        
        return reports[:max_reports]
    
    def get_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific report by ID
        
        Args:
            report_id: ID of the report to get
            
        Returns:
            Report data or None if not found
        """
        # Check if report exists
        report_path = os.path.join(self.reports_dir, f"{report_id}.json")
        
        if not os.path.exists(report_path):
            return None
        
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading report {report_id}: {str(e)}")
            return None 