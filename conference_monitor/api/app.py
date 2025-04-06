"""
Conference Monitor API
Flask-based API for the Conference Monitor application
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import logging
from dotenv import load_dotenv
import json
from pathlib import Path
from datetime import datetime
import sqlite3

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Import core functionality
from conference_monitor.core.agent import ConferenceAgent
from conference_monitor.core.memory import AgentMemory
from conference_monitor.core.browser import BrowserManager
from conference_monitor.services.monitor_service import MonitorService

# Initialize services
agent = ConferenceAgent()
memory = AgentMemory()
browser = BrowserManager()
monitor_service = MonitorService(agent=agent, memory=memory, browser=browser)

# Ensure data directories exist
data_dir = Path("data")
(data_dir / "papers").mkdir(parents=True, exist_ok=True)
(data_dir / "conferences").mkdir(parents=True, exist_ok=True)
(data_dir / "reports").mkdir(parents=True, exist_ok=True)

# API Routes

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get API status"""
    return jsonify({
        "status": "online",
        "version": "1.0.0",
        "api_provider": agent.provider
    })

@app.route('/api/conferences', methods=['GET'])
def get_conferences():
    """Get all tracked conferences"""
    research_area = request.args.get('area', None)
    tier = request.args.get('tier', None)
    
    try:
        # Use direct database access for better performance
        db_path = memory.db_file
        
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get current date
            current_date = datetime.now().isoformat()[:10]  # YYYY-MM-DD format
            
            query = """
            SELECT data FROM conferences 
            WHERE end_date >= ? 
            """
            params = [current_date]
            
            if research_area:
                query += "AND (research_areas LIKE ? OR title LIKE ? OR description LIKE ?)"
                search_term = f"%{research_area.lower()}%"
                params.extend([search_term, search_term, search_term])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Process results and deduplicate
            seen_titles = set()
            unique_conferences = []
            
            for row in rows:
                conf = json.loads(row['data'])
                title = conf.get('title', '').strip().lower()
                
                if title and title not in seen_titles:
                    # Apply tier filtering if specified
                    if tier and conf.get('tier') != tier:
                        continue
                        
                    seen_titles.add(title)
                    unique_conferences.append(conf)
            
            # Sort conferences by start_date (chronological order)
            sorted_conferences = sorted(
                unique_conferences,
                key=lambda x: x.get('start_date', '9999-12-31')  # Use far future date as default
            )
            
            conn.close()
            return jsonify(sorted_conferences)
    except Exception as e:
        logger.error(f"Database query error: {str(e)}")
        # Fall back to file-based approach if database fails
    
    # Fallback to the file-based approach
    conferences = memory.load_conferences()
    
    # Get current date
    current_date = datetime.now()
    
    # Filter out invalid conferences (missing required fields)
    valid_conferences = [
        conf for conf in conferences 
        if 'title' in conf and conf['title'] and 'id' in conf
    ]
    
    # Filter only upcoming conferences
    upcoming_conferences = []
    seen_titles = set()  # For deduplication
    
    for conf in valid_conferences:
        # Only add conference if its title hasn't been seen yet (deduplication)
        conf_title = conf.get('title', '').strip().lower()
        
        if conf_title in seen_titles:
            continue
        
        # Apply tier filtering
        if tier and conf.get('tier') != tier:
            continue
            
        # Check if conference is upcoming
        is_upcoming = True
        
        # Parse end_date if it exists
        if 'end_date' in conf and conf['end_date']:
            try:
                end_date = datetime.fromisoformat(conf['end_date'].replace('Z', '+00:00'))
                is_upcoming = end_date > current_date
            except (ValueError, TypeError):
                # If date parsing fails, try to guess from dates string
                dates_str = conf.get('dates', '').lower()
                if dates_str and any(year in dates_str for year in ['2020', '2021', '2022', '2023']):
                    is_upcoming = False
        
        if is_upcoming:
            upcoming_conferences.append(conf)
            seen_titles.add(conf_title)
    
    # Sort conferences by start_date (chronological order)
    sorted_conferences = sorted(
        upcoming_conferences,
        key=lambda x: x.get('start_date', '9999-12-31')  # Use far future date as default
    )
    
    # Apply research area filter if provided
    if research_area:
        filtered_conferences = [
            conf for conf in sorted_conferences 
            if research_area.lower() in conf.get('description', '').lower() or
               research_area.lower() in conf.get('title', '').lower() or
               research_area.lower() in ', '.join(conf.get('research_areas', [])).lower()
        ]
        return jsonify(filtered_conferences)
    
    return jsonify(sorted_conferences)

@app.route('/api/conferences/refresh', methods=['POST'])
def refresh_conferences():
    """Refresh conference data"""
    data = request.json or {}
    research_areas = data.get('research_areas', ['artificial intelligence', 'machine learning'])
    
    try:
        results = monitor_service.refresh_conferences(research_areas)
        return jsonify({
            "success": True,
            "message": f"Found {results.get('total_conferences', 0)} conferences",
            "results": results
        })
    except Exception as e:
        logger.error(f"Error refreshing conferences: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error: {str(e)}"
        }), 500

@app.route('/api/papers', methods=['GET'])
def get_papers():
    """Get all tracked papers"""
    research_area = request.args.get('area', None)
    papers = memory.load_papers()
    
    if research_area:
        # Filter by research area if provided
        filtered_papers = [
            paper for paper in papers 
            if research_area.lower() in paper.get('research_area', '').lower() or
               research_area.lower() in paper.get('title', '').lower()
        ]
        return jsonify(filtered_papers)
    
    return jsonify(papers)

@app.route('/api/papers/refresh', methods=['POST'])
def refresh_papers():
    """Refresh paper data"""
    data = request.json or {}
    research_areas = data.get('research_areas', ['artificial intelligence', 'machine learning'])
    
    try:
        results = monitor_service.refresh_papers(research_areas)
        return jsonify({
            "success": True,
            "message": f"Found {results.get('total_papers', 0)} papers",
            "results": results
        })
    except Exception as e:
        logger.error(f"Error refreshing papers: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error: {str(e)}"
        }), 500

@app.route('/api/trends', methods=['GET'])
def get_trends():
    """Get trending topics"""
    research_area = request.args.get('area', 'artificial intelligence')
    paper_count = int(request.args.get('count', 10))
    
    try:
        results = monitor_service.analyze_trending_topics([research_area], paper_count=paper_count)
        return jsonify(results)
    except Exception as e:
        logger.error(f"Error analyzing trends: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error: {str(e)}"
        }), 500

@app.route('/api/query', methods=['POST'])
def run_query():
    """Run a direct query against the AI agent"""
    data = request.json
    if not data or 'query' not in data:
        return jsonify({"error": "Missing query parameter"}), 400
    
    query = data.get('query')
    try:
        response = agent.run_query(query)
        return jsonify({
            "success": True,
            "response": response
        })
    except Exception as e:
        logger.error(f"Error running query: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error: {str(e)}"
        }), 500

@app.route('/api/research-areas', methods=['GET'])
def get_research_areas():
    """Get tracked research areas"""
    metadata = memory.load_metadata()
    research_areas = metadata.get("tracked_research_areas", [])
    return jsonify(research_areas)

@app.route('/api/research-areas', methods=['POST'])
def update_research_areas():
    """Update tracked research areas"""
    data = request.json
    if not data or 'research_areas' not in data:
        return jsonify({"error": "Missing research_areas parameter"}), 400
    
    research_areas = data.get('research_areas')
    if not isinstance(research_areas, list):
        return jsonify({"error": "research_areas must be a list"}), 400
    
    try:
        monitor_service.set_research_areas(research_areas)
        return jsonify({
            "success": True,
            "message": f"Updated research areas: {', '.join(research_areas)}"
        })
    except Exception as e:
        logger.error(f"Error updating research areas: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error: {str(e)}"
        }), 500 