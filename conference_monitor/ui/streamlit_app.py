"""
Streamlit UI for the Conference Monitor Agent
"""
import streamlit as st
import os
import sys
import threading
import time
from datetime import datetime
import pandas as pd
from typing import List, Dict, Any, Optional

# Add parent directory to path to import from conference_monitor
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from conference_monitor.core.agent import ConferenceAgent
from conference_monitor.core.memory import AgentMemory
from conference_monitor.core.browser import BrowserManager
from conference_monitor.services.monitor_service import MonitorService
from conference_monitor.services.report_service import ReportService
from conference_monitor.utils.date_utils import parse_deadline_date, format_date, get_days_until

# Initialize global services
@st.cache_resource
def get_services():
    """Initialize services for the app
    
    Returns:
        Dictionary of initialized services
    """
    # Setup LLM agent
    agent = ConferenceAgent(verbose=False)
    
    # Setup memory
    memory = AgentMemory()
    
    # Setup browser
    browser = BrowserManager()
    
    # Setup services
    monitor_service = MonitorService(agent=agent, memory=memory, browser=browser)
    report_service = ReportService(agent=agent, memory=memory)
    
    return {
        "agent": agent,
        "memory": memory,
        "browser": browser,
        "monitor_service": monitor_service,
        "report_service": report_service
    }

# App title and description
st.set_page_config(
    page_title="Conference Monitor Agent",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize services
services = get_services()
agent = services["agent"]
memory = services["memory"]
monitor_service = services["monitor_service"]
report_service = services["report_service"]

# Initialize session state for UI
if "refresh_in_progress" not in st.session_state:
    st.session_state.refresh_in_progress = False
if "notification" not in st.session_state:
    st.session_state.notification = None
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "Conferences"
if "selected_research_area" not in st.session_state:
    # Get from metadata
    metadata = memory.load_metadata()
    research_areas = metadata.get("tracked_research_areas", ["artificial intelligence"])
    st.session_state.selected_research_area = research_areas[0] if research_areas else ""

# Add notification
def set_notification(message, type="info"):
    """Set a notification message in session state
    
    Args:
        message: Message to display
        type: Type of notification (info, success, warning, error)
    """
    st.session_state.notification = {"message": message, "type": type}

# Sidebar
with st.sidebar:
    st.title("Conference Monitor")
    
    st.subheader("Research Areas")
    
    # Get research areas
    metadata = memory.load_metadata()
    research_areas = metadata.get("tracked_research_areas", [])
    
    # Input for adding research areas
    with st.form("add_research_area_form"):
        new_area = st.text_input("Add Research Area")
        add_submitted = st.form_submit_button("Add")
        
        if add_submitted and new_area:
            monitor_service.add_research_area(new_area)
            st.experimental_rerun()
    
    # List of research areas
    if research_areas:
        for area in research_areas:
            col1, col2 = st.columns([4, 1])
            col1.write(area)
            if col2.button("🗑️", key=f"delete_{area}"):
                monitor_service.remove_research_area(area)
                st.experimental_rerun()
    else:
        st.write("No research areas added yet.")
    
    st.divider()
    
    # Monitoring controls
    st.subheader("Monitoring")
    
    if monitor_service.monitoring_thread and monitor_service.monitoring_thread.is_alive():
        if st.button("Stop Monitoring"):
            monitor_service.stop_monitoring()
            set_notification("Monitoring stopped")
            st.experimental_rerun()
        st.write("Status: 🟢 Active")
    else:
        if st.button("Start Monitoring"):
            monitor_service.start_monitoring()
            set_notification("Monitoring started")
            st.experimental_rerun()
        st.write("Status: 🔴 Inactive")
    
    # Manual refresh button
    if st.button("Manual Refresh"):
        st.session_state.refresh_in_progress = True
        
        # Start a background thread to avoid blocking the UI
        def background_refresh():
            try:
                research_areas = metadata.get("tracked_research_areas", [])
                monitor_service.refresh_conferences(research_areas)
                monitor_service.refresh_papers(research_areas)
                set_notification("Refresh completed successfully", "success")
            except Exception as e:
                set_notification(f"Error during refresh: {str(e)}", "error")
            finally:
                st.session_state.refresh_in_progress = False
        
        threading.Thread(target=background_refresh).start()
    
    if st.session_state.refresh_in_progress:
        st.write("Refresh in progress...")
    
    st.divider()
    
    # About
    st.subheader("About")
    st.write("Conference Monitor Agent helps you track academic conferences, papers, and research trends.")
    st.write("© 2023")

# Display notification if present
if st.session_state.notification:
    notification = st.session_state.notification
    message = notification["message"]
    type = notification["type"]
    
    if type == "info":
        st.info(message)
    elif type == "success":
        st.success(message)
    elif type == "warning":
        st.warning(message)
    elif type == "error":
        st.error(message)
    
    # Clear notification after displaying
    st.session_state.notification = None

# Main content
st.title("Academic Conference & Paper Monitor")

# Tabs for different sections
tab1, tab2, tab3, tab4 = st.tabs(["Conferences", "Papers", "Trends", "Reports"])

# Conference tab
with tab1:
    st.header("Upcoming Conferences")
    
    # Research area selector
    metadata = memory.load_metadata()
    research_areas = metadata.get("tracked_research_areas", [])
    
    col1, col2 = st.columns([3, 1])
    selected_research_area = col1.selectbox(
        "Filter by Research Area",
        ["All"] + research_areas,
        index=0
    )
    
    generate_report = col2.button("Generate Report")
    
    if generate_report:
        area = None if selected_research_area == "All" else selected_research_area
        report = report_service.generate_conference_report(research_area=area)
        set_notification(f"Report generated: {report['title']}", "success")
    
    # Get conferences from memory
    conferences = memory.list_conferences()
    
    # Filter by research area if selected
    if selected_research_area != "All":
        filtered_conferences = []
        selected_area_lower = selected_research_area.lower()
        
        for conf in conferences:
            title = conf.get('title', '').lower()
            desc = conf.get('description', '').lower()
            
            if selected_area_lower in title or selected_area_lower in desc:
                filtered_conferences.append(conf)
        
        conferences = filtered_conferences
    
    # Display conferences
    if conferences:
        # Create DataFrame for better display
        conf_data = []
        
        for conf in conferences:
            deadlines = conf.get('deadlines', [])
            deadline_str = ", ".join(deadlines[:2]) if deadlines else "N/A"
            
            conf_data.append({
                "Title": conf.get('title', 'Untitled'),
                "Dates": conf.get('dates', 'N/A'),
                "Location": conf.get('location', 'N/A'),
                "Deadlines": deadline_str,
                "URL": conf.get('url', '')
            })
        
        df = pd.DataFrame(conf_data)
        st.dataframe(df, use_container_width=True)
        
        # Allow viewing full conference details
        st.subheader("Conference Details")
        conf_titles = [conf.get('title', f"Untitled ({conf.get('id', '')})") for conf in conferences]
        selected_conf_idx = st.selectbox("Select a conference to view details", range(len(conf_titles)), format_func=lambda i: conf_titles[i])
        
        if selected_conf_idx is not None:
            selected_conf = conferences[selected_conf_idx]
            
            st.write(f"## {selected_conf.get('title', 'Untitled Conference')}")
            
            col1, col2 = st.columns(2)
            col1.write(f"**Dates:** {selected_conf.get('dates', 'N/A')}")
            col1.write(f"**Location:** {selected_conf.get('location', 'N/A')}")
            
            if selected_conf.get('url'):
                col2.write(f"**Website:** [{selected_conf.get('url')}]({selected_conf.get('url')})")
            
            # Display deadlines
            deadlines = selected_conf.get('deadlines', [])
            if deadlines:
                st.write("### Deadlines")
                for deadline in deadlines:
                    st.write(f"- {deadline}")
            
            # Display description
            if selected_conf.get('description'):
                st.write("### Description")
                st.write(selected_conf.get('description'))
    else:
        st.write("No conferences found. Try refreshing the data or adding more research areas.")

# Papers tab
with tab2:
    st.header("Recent Papers")
    
    # Research area selector
    metadata = memory.load_metadata()
    research_areas = metadata.get("tracked_research_areas", [])
    
    col1, col2 = st.columns([3, 1])
    
    selected_research_area = col1.selectbox(
        "Select Research Area",
        research_areas,
        index=0 if research_areas else None
    )
    
    generate_paper_report = col2.button("Generate Paper Report")
    
    if generate_paper_report and selected_research_area:
        report = report_service.generate_paper_report(research_area=selected_research_area)
        set_notification(f"Paper report generated: {report['title']}", "success")
    
    # Get papers for the selected research area
    if selected_research_area:
        st.session_state.selected_research_area = selected_research_area
        
        # Get papers from memory
        papers = memory.list_papers()
        
        # Filter by research area
        filtered_papers = []
        selected_area_lower = selected_research_area.lower()
        
        for paper in papers:
            title = paper.get('title', '').lower()
            abstract = paper.get('abstract', '').lower()
            
            if selected_area_lower in title or selected_area_lower in abstract:
                filtered_papers.append(paper)
        
        # Display papers
        if filtered_papers:
            # Sort by citations
            sorted_papers = sorted(filtered_papers, key=lambda p: p.get('citations', 0), reverse=True)
            
            # Create DataFrame for better display
            paper_data = []
            
            for paper in sorted_papers:
                authors = paper.get('authors', [])
                if isinstance(authors, list):
                    authors_str = ", ".join(authors[:3])
                    if len(authors) > 3:
                        authors_str += " et al."
                else:
                    authors_str = str(authors)
                
                paper_data.append({
                    "Title": paper.get('title', 'Untitled'),
                    "Authors": authors_str,
                    "Year": paper.get('year', 'N/A'),
                    "Citations": paper.get('citations', 0),
                    "URL": paper.get('url', '')
                })
            
            df = pd.DataFrame(paper_data)
            st.dataframe(df, use_container_width=True)
            
            # Allow viewing full paper details
            st.subheader("Paper Details")
            paper_titles = [paper.get('title', f"Untitled ({paper.get('id', '')})") for paper in sorted_papers]
            selected_paper_idx = st.selectbox("Select a paper to view details", range(len(paper_titles)), format_func=lambda i: paper_titles[i])
            
            if selected_paper_idx is not None:
                selected_paper = sorted_papers[selected_paper_idx]
                
                st.write(f"## {selected_paper.get('title', 'Untitled Paper')}")
                
                # Authors
                authors = selected_paper.get('authors', [])
                if authors:
                    if isinstance(authors, list):
                        st.write(f"**Authors:** {', '.join(authors)}")
                    else:
                        st.write(f"**Authors:** {authors}")
                
                # Publication details
                col1, col2 = st.columns(2)
                col1.write(f"**Year:** {selected_paper.get('year', 'N/A')}")
                col1.write(f"**Citations:** {selected_paper.get('citations', 0)}")
                
                if selected_paper.get('url'):
                    col2.write(f"**URL:** [{selected_paper.get('url')}]({selected_paper.get('url')})")
                
                # Abstract
                if selected_paper.get('abstract'):
                    st.write("### Abstract")
                    st.write(selected_paper.get('abstract'))
                
                # Analysis
                if selected_paper.get('analysis'):
                    st.write("### Analysis")
                    st.write(selected_paper.get('analysis'))
                else:
                    if st.button("Analyze Paper"):
                        with st.spinner("Analyzing paper..."):
                            # Get paper ID
                            paper_id = selected_paper.get('id')
                            
                            if paper_id:
                                # Initialize the paper summary tool
                                from conference_monitor.tools.paper_tools import PaperSummaryTool
                                summary_tool = PaperSummaryTool(agent=agent, memory=memory)
                                
                                # Analyze the paper
                                analysis_result = summary_tool.execute(paper_id=paper_id)
                                
                                if "error" not in analysis_result:
                                    st.success("Analysis completed")
                                    st.experimental_rerun()
                                else:
                                    st.error(f"Error analyzing paper: {analysis_result.get('error')}")
        else:
            st.write(f"No papers found for {selected_research_area}. Try refreshing the data.")
    else:
        st.write("Please select a research area.")

# Trends tab
with tab3:
    st.header("Research Trends")
    
    # Research area selector
    metadata = memory.load_metadata()
    research_areas = metadata.get("tracked_research_areas", [])
    
    col1, col2 = st.columns([3, 1])
    
    selected_research_area = col1.selectbox(
        "Select Research Area for Trend Analysis",
        research_areas,
        index=0 if research_areas else None,
        key="trend_research_area"
    )
    
    analyze_trends = col2.button("Analyze Trends")
    
    if analyze_trends and selected_research_area:
        with st.spinner("Analyzing trends..."):
            # Initialize the trending topics tool
            from conference_monitor.tools.trending_tools import TrendingTopicsTool
            trend_tool = TrendingTopicsTool(agent=agent, memory=memory)
            
            # Analyze trends
            trend_result = trend_tool.execute(
                research_area=selected_research_area,
                paper_count=20
            )
            
            if "error" not in trend_result:
                set_notification("Trend analysis completed", "success")
                st.experimental_rerun()
            else:
                set_notification(f"Error analyzing trends: {trend_result.get('error')}", "error")
    
    # Get and display trends
    trends_data = memory.get_latest_trends()
    
    if trends_data:
        # Filter by selected research area if any
        if selected_research_area:
            filtered_trends = []
            for trend in trends_data:
                if trend.get('research_area', '').lower() == selected_research_area.lower():
                    filtered_trends.append(trend)
            
            trends_data = filtered_trends
        
        if trends_data:
            # Sort by date (newest first)
            sorted_trends = sorted(trends_data, key=lambda t: t.get('date', ''), reverse=True)
            
            for trend in sorted_trends:
                st.write(f"## Trends in {trend.get('research_area', 'Unknown Area')}")
                st.write(f"*Analyzed {trend.get('paper_count', 0)} papers on {trend.get('date', 'unknown date')}*")
                
                trends_list = trend.get('trends', [])
                if trends_list:
                    for i, t in enumerate(trends_list, 1):
                        st.write(f"**{i}.** {t}")
                else:
                    st.write("No specific trends identified.")
                
                st.divider()
        else:
            st.write(f"No trend data found for {selected_research_area}. Try running a trend analysis.")
    else:
        st.write("No trend data available. Try running a trend analysis for a research area.")
    
    # Generate comprehensive trends report
    st.subheader("Generate Trends Report")
    if st.button("Generate Comprehensive Trends Report"):
        with st.spinner("Generating trends report..."):
            report = report_service.generate_trends_report()
            set_notification(f"Trends report generated: {report.get('title', 'Report')}", "success")

# Reports tab
with tab4:
    st.header("Generated Reports")
    
    # Get list of reports
    reports = report_service.list_reports()
    
    if reports:
        # Create DataFrame for better display
        report_data = []
        
        for report in reports:
            report_data.append({
                "Title": report.get('title', 'Untitled Report'),
                "Type": report.get('type', 'unknown').capitalize(),
                "Date": report.get('generated_date', '')[:10],  # Just the date part
                "ID": report.get('id', '')
            })
        
        df = pd.DataFrame(report_data)
        st.dataframe(df, use_container_width=True)
        
        # Allow viewing full report
        st.subheader("View Report")
        report_titles = [report.get('title', f"Untitled ({report.get('id', '')})") for report in reports]
        selected_report_idx = st.selectbox("Select a report to view", range(len(report_titles)), format_func=lambda i: report_titles[i])
        
        if selected_report_idx is not None:
            selected_report = reports[selected_report_idx]
            report_id = selected_report.get('id', '')
            
            if report_id:
                # Get full report
                full_report = report_service.get_report(report_id)
                
                if full_report:
                    st.write(f"# {full_report.get('title', 'Untitled Report')}")
                    st.write(f"*Generated on: {full_report.get('generated_date', '')[:10]}*")
                    
                    # Handle different report types
                    if "conferences" in full_report:
                        # Conference report
                        st.write(f"## Conferences ({full_report.get('conference_count', 0)})")
                        
                        for conf in full_report.get('conferences', []):
                            st.write(f"### {conf.get('title', 'Untitled Conference')}")
                            st.write(f"**Dates:** {conf.get('dates', 'N/A')}")
                            st.write(f"**Location:** {conf.get('location', 'N/A')}")
                            
                            deadlines = conf.get('deadlines', [])
                            if deadlines:
                                st.write("**Deadlines:**")
                                for dl in deadlines:
                                    st.write(f"- {dl}")
                            
                            if conf.get('url'):
                                st.write(f"**URL:** [{conf.get('url')}]({conf.get('url')})")
                            
                            st.divider()
                    
                    elif "papers" in full_report:
                        # Paper report
                        st.write(f"## Papers in {full_report.get('research_area', '')} ({full_report.get('paper_count', 0)})")
                        
                        if "collection_summary" in full_report:
                            st.write("### Summary")
                            st.write(full_report.get('collection_summary', ''))
                        
                        st.write("### Papers")
                        for paper in full_report.get('papers', []):
                            st.write(f"#### {paper.get('title', 'Untitled Paper')}")
                            
                            authors = paper.get('authors', [])
                            if authors:
                                if isinstance(authors, list):
                                    st.write(f"**Authors:** {', '.join(authors)}")
                                else:
                                    st.write(f"**Authors:** {authors}")
                            
                            st.write(f"**Year:** {paper.get('year', 'N/A')}")
                            st.write(f"**Citations:** {paper.get('citations', 0)}")
                            
                            if paper.get('abstract'):
                                with st.expander("Abstract"):
                                    st.write(paper.get('abstract', ''))
                            
                            if paper.get('analysis'):
                                with st.expander("Analysis"):
                                    st.write(paper.get('analysis', ''))
                            
                            if paper.get('url'):
                                st.write(f"**URL:** [{paper.get('url')}]({paper.get('url')})")
                            
                            st.divider()
                    
                    elif "trends_by_area" in full_report:
                        # Trends report
                        st.write(f"## Research Trends across {len(full_report.get('research_areas', []))} Areas")
                        
                        if "big_picture_analysis" in full_report:
                            st.write("### Big Picture Analysis")
                            st.write(full_report.get('big_picture_analysis', ''))
                        
                        st.write("### Trends by Research Area")
                        for area, data in full_report.get('trends_by_area', {}).items():
                            st.write(f"#### {area}")
                            
                            trends = data.get('trends', [])
                            if trends:
                                for i, trend in enumerate(trends, 1):
                                    st.write(f"{i}. {trend}")
                            else:
                                st.write("No trends identified for this area.")
                            
                            st.divider()
                else:
                    st.error(f"Error loading report with ID: {report_id}")
    else:
        st.write("No reports found. Generate some reports from the other tabs.")

def main():
    """Main function for running the Streamlit app"""
    # The app is already set up above
    pass

if __name__ == "__main__":
    main() 