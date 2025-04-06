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
    conferences = memory.load_conferences()
    
    if research_area:
        # Filter by research area if provided
        filtered_conferences = [
            conf for conf in conferences 
            if research_area.lower() in conf.get('description', '').lower() or
               research_area.lower() in conf.get('title', '').lower()
        ]
        return jsonify(filtered_conferences)
    
    return jsonify(conferences)

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