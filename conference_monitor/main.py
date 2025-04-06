"""
Main entry point for the Conference Monitor Agent
"""
import argparse
import sys
import os
import logging
import time
from typing import List, Optional

from conference_monitor.core.agent import ConferenceAgent
from conference_monitor.core.memory import AgentMemory
from conference_monitor.core.browser import BrowserManager
from conference_monitor.services.monitor_service import MonitorService
from conference_monitor.services.report_service import ReportService
from conference_monitor.config import DEFAULT_RESEARCH_AREAS

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('conference_monitor.log')
    ]
)

logger = logging.getLogger(__name__)

def setup_services():
    """Set up the agent and services
    
    Returns:
        Tuple of (agent, memory, browser, monitor_service, report_service)
    """
    # Create agent
    agent = ConferenceAgent()
    
    # Create memory
    memory = AgentMemory()
    
    # Create browser
    browser = BrowserManager()
    
    # Create services
    monitor_service = MonitorService(agent=agent, memory=memory, browser=browser)
    report_service = ReportService(agent=agent, memory=memory)
    
    return agent, memory, browser, monitor_service, report_service

def run_monitor(research_areas: Optional[List[str]] = None, run_once: bool = False):
    """Run the monitor service
    
    Args:
        research_areas: List of research areas to monitor
        run_once: Whether to run once and exit
    """
    logger.info("Starting Conference Monitor Agent")
    
    # Set up services
    agent, memory, browser, monitor_service, report_service = setup_services()
    
    # Set research areas if provided
    if research_areas:
        monitor_service.set_research_areas(research_areas)
    
    if run_once:
        # Run once and exit
        logger.info("Running one-time refresh")
        
        # Get research areas from metadata if not provided
        if not research_areas:
            metadata = memory.load_metadata()
            research_areas = metadata.get("tracked_research_areas", DEFAULT_RESEARCH_AREAS)
        
        # Refresh conferences and papers
        conf_results = monitor_service.refresh_conferences(research_areas)
        paper_results = monitor_service.refresh_papers(research_areas)
        
        total_conferences = conf_results.get("total_conferences", 0)
        total_papers = paper_results.get("total_papers", 0)
        
        logger.info(f"Refresh completed. Found {total_conferences} conferences and {total_papers} papers.")
        
    else:
        # Run continuously
        logger.info("Starting continuous monitoring")
        
        def callback(data):
            """Callback function for the monitor service
            
            Args:
                data: Data from the monitor refresh
            """
            total_conferences = data.get("conferences", {}).get("total_conferences", 0)
            total_papers = data.get("papers", {}).get("total_papers", 0)
            
            logger.info(f"Refresh completed at {data.get('timestamp', '')}. "
                      f"Found {total_conferences} conferences and {total_papers} papers.")
        
        # Start monitoring with callback
        monitor_service.start_monitoring(callback=callback)
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Stopping monitoring due to keyboard interrupt")
            monitor_service.stop_monitoring()

def run_api(port: int = 5000):
    """Run the Flask API server
    
    Args:
        port: Port to run the API server on
    """
    # Import here to avoid dependency if not using the API
    from conference_monitor.api import app
    
    logger.info(f"Starting API server on port {port}")
    
    try:
        app.run(debug=True, host='0.0.0.0', port=port)
    except KeyboardInterrupt:
        logger.info("Stopping API server due to keyboard interrupt")
    except Exception as e:
        logger.error(f"Error running API server: {str(e)}")

def generate_report(report_type: str, research_area: Optional[str] = None):
    """Generate a report
    
    Args:
        report_type: Type of report to generate (conferences, papers, trends)
        research_area: Research area for the report
    """
    # Set up services
    agent, memory, browser, monitor_service, report_service = setup_services()
    
    logger.info(f"Generating {report_type} report")
    
    if report_type == "conferences":
        report = report_service.generate_conference_report(research_area=research_area)
        logger.info(f"Generated conference report with {report.get('conference_count', 0)} conferences")
    
    elif report_type == "papers":
        if not research_area:
            # Get from metadata
            metadata = memory.load_metadata()
            research_areas = metadata.get("tracked_research_areas", DEFAULT_RESEARCH_AREAS)
            research_area = research_areas[0] if research_areas else DEFAULT_RESEARCH_AREAS[0]
        
        report = report_service.generate_paper_report(research_area=research_area)
        logger.info(f"Generated paper report with {report.get('paper_count', 0)} papers")
    
    elif report_type == "trends":
        report = report_service.generate_trends_report()
        logger.info(f"Generated trends report across {len(report.get('research_areas', []))} research areas")
    
    else:
        logger.error(f"Unknown report type: {report_type}")
        return
    
    logger.info(f"Report generated: {report.get('id', '')}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Conference Monitor Agent")
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Monitor command
    monitor_parser = subparsers.add_parser("monitor", help="Run the monitor service")
    monitor_parser.add_argument(
        "--areas", "-a", nargs="+", help="Research areas to monitor"
    )
    monitor_parser.add_argument(
        "--once", "-o", action="store_true", help="Run once and exit"
    )
    
    # API command
    api_parser = subparsers.add_parser("api", help="Run the API server")
    api_parser.add_argument(
        "--port", "-p", type=int, default=5000, help="Port to run the API server on"
    )
    
    # Report command
    report_parser = subparsers.add_parser("report", help="Generate a report")
    report_parser.add_argument(
        "type", choices=["conferences", "papers", "trends"], help="Type of report to generate"
    )
    report_parser.add_argument(
        "--area", "-a", help="Research area for the report"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Run the appropriate command
    if args.command == "monitor":
        run_monitor(research_areas=args.areas, run_once=args.once)
    elif args.command == "api":
        run_api(port=args.port)
    elif args.command == "report":
        generate_report(report_type=args.type, research_area=args.area)
    else:
        # Default to API if no command specified
        run_api()

if __name__ == "__main__":
    main() 