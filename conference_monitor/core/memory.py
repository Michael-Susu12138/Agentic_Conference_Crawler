"""
Agent memory implementation for storing and retrieving agent data
"""
import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import logging
import sqlite3

from conference_monitor.config import DATA_DIR

logger = logging.getLogger(__name__)

class AgentMemory:
    """Memory management for the conference monitoring agent"""
    
    def __init__(self, data_dir: str = "data"):
        """Initialize memory
        
        Args:
            data_dir: Directory for storing data
        """
        self.data_dir = Path(data_dir)
        self.conferences_dir = self.data_dir / "conferences"
        self.papers_dir = self.data_dir / "papers"
        self.metadata_file = self.data_dir / "metadata.json"
        self.db_file = self.data_dir / "conference_monitor.db"
        
        # Create directories if they don't exist
        self.conferences_dir.mkdir(parents=True, exist_ok=True)
        self.papers_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize metadata if needed
        if not self.metadata_file.exists():
            self._initialize_metadata()
            
        # Initialize database if needed
        self._initialize_database()
    
    def _initialize_metadata(self):
        """Initialize or load metadata file"""
        if not self.metadata_file.exists():
            metadata = {
                "last_updated": datetime.now().isoformat(),
                "tracked_conferences": [],
                "tracked_research_areas": [],
                "version": "1.0.0"
            }
            self.save_metadata(metadata)
        
    def save_metadata(self, metadata: Dict[str, Any]):
        """Save metadata to file
        
        Args:
            metadata: Dictionary of metadata to save
        """
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    def load_metadata(self) -> Dict[str, Any]:
        """Load metadata from file
        
        Returns:
            Dictionary of metadata
        """
        if not self.metadata_file.exists():
            self._initialize_metadata()
        
        with open(self.metadata_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _initialize_database(self):
        """Initialize the SQLite database with required tables"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Create conferences table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS conferences (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                url TEXT,
                description TEXT,
                dates TEXT,
                start_date TEXT,
                end_date TEXT,
                location TEXT,
                source TEXT,
                research_areas TEXT,
                last_updated TEXT,
                data JSON
            )
            ''')
            
            # Create papers table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS papers (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                url TEXT,
                authors TEXT,
                abstract TEXT,
                year TEXT,
                research_area TEXT,
                last_updated TEXT,
                data JSON
            )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
    
    def save_conference(self, conference_data: Dict[str, Any]):
        """Save conference data to memory
        
        Args:
            conference_data: Dictionary containing conference information
        """
        if "id" not in conference_data:
            raise ValueError("Conference data must include an 'id' field")
        
        conference_id = conference_data["id"]
        
        # Add timestamp for tracking
        conference_data["_last_updated"] = datetime.now().isoformat()
        
        # Save to file system (for backward compatibility)
        file_path = self.conferences_dir / f"{conference_id}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(conference_data, f, indent=2, ensure_ascii=False)
        
        # Save to database
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Extract main fields for efficient querying
            title = conference_data.get('title', '')
            url = conference_data.get('url', '')
            description = conference_data.get('description', '')
            dates = conference_data.get('dates', '')
            start_date = conference_data.get('start_date', '')
            end_date = conference_data.get('end_date', '')
            location = conference_data.get('location', '')
            source = conference_data.get('source', '')
            research_areas = ','.join(conference_data.get('research_areas', []))
            last_updated = conference_data.get('_last_updated', datetime.now().isoformat())
            
            # Store full data as JSON
            data_json = json.dumps(conference_data, ensure_ascii=False)
            
            # Insert or replace existing record
            cursor.execute('''
            INSERT OR REPLACE INTO conferences
            (id, title, url, description, dates, start_date, end_date, location, source, research_areas, last_updated, data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (conference_id, title, url, description, dates, start_date, end_date, location, source, research_areas, last_updated, data_json))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error saving conference to database: {str(e)}")
        
        # Update metadata
        metadata = self.load_metadata()
        if conference_id not in metadata["tracked_conferences"]:
            metadata["tracked_conferences"].append(conference_id)
            self.save_metadata(metadata)
    
    def get_conference(self, conference_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve conference data by ID
        
        Args:
            conference_id: ID of the conference to retrieve
            
        Returns:
            Conference data dictionary or None if not found
        """
        # Try to get from database first
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute("SELECT data FROM conferences WHERE id = ?", (conference_id,))
            result = cursor.fetchone()
            
            conn.close()
            
            if result and result[0]:
                return json.loads(result[0])
        except Exception as e:
            logger.error(f"Error retrieving conference from database: {str(e)}")
        
        # Fall back to file system
        file_path = self.conferences_dir / f"{conference_id}.json"
        
        if not file_path.exists():
            return None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def list_conferences(self) -> List[Dict[str, Any]]:
        """List all tracked conferences
        
        Returns:
            List of conference data dictionaries
        """
        # Try to get from database first
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Get conferences, focusing on upcoming ones
            cursor.execute('''
            SELECT data FROM conferences 
            ORDER BY start_date DESC
            ''')
            
            results = cursor.fetchall()
            conn.close()
            
            if results:
                conferences = [json.loads(row[0]) for row in results]
                return conferences
        except Exception as e:
            logger.error(f"Error listing conferences from database: {str(e)}")
        
        # Fall back to file system
        conferences = []
        
        for file_path in self.conferences_dir.glob("*.json"):
            with open(file_path, 'r', encoding='utf-8') as f:
                conferences.append(json.load(f))
        
        return conferences
    
    def load_conferences(self) -> List[Dict[str, Any]]:
        """Load all tracked conferences
        
        Returns:
            List of conference data dictionaries
        """
        return self.list_conferences()
    
    def save_paper(self, paper_data: Dict[str, Any]):
        """Save paper data to memory
        
        Args:
            paper_data: Dictionary containing paper information
        """
        if "id" not in paper_data:
            raise ValueError("Paper data must include an 'id' field")
        
        paper_id = paper_data["id"]
        file_path = self.papers_dir / f"{paper_id}.json"
        
        # Add timestamp for tracking
        paper_data["_last_updated"] = datetime.now().isoformat()
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(paper_data, f, indent=2, ensure_ascii=False)
    
    def get_paper(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve paper data by ID
        
        Args:
            paper_id: ID of the paper to retrieve
            
        Returns:
            Paper data dictionary or None if not found
        """
        file_path = self.papers_dir / f"{paper_id}.json"
        
        if not file_path.exists():
            return None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def list_papers(self, filter_dict: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """List papers, optionally filtered by properties
        
        Args:
            filter_dict: Dictionary of key-value pairs to filter papers by
            
        Returns:
            List of paper data dictionaries
        """
        papers = []
        
        for file_path in self.papers_dir.glob("*.json"):
            with open(file_path, 'r', encoding='utf-8') as f:
                paper = json.load(f)
                
                # Apply filter if provided
                if filter_dict:
                    matches = True
                    for key, value in filter_dict.items():
                        if key not in paper or paper[key] != value:
                            matches = False
                            break
                    
                    if not matches:
                        continue
                
                papers.append(paper)
        
        return papers
    
    def load_papers(self, filter_dict: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Load papers, optionally filtered by properties
        
        Args:
            filter_dict: Dictionary of key-value pairs to filter papers by
            
        Returns:
            List of paper data dictionaries
        """
        return self.list_papers(filter_dict)
    
    def save_trend(self, trend_data: Dict[str, Any]):
        """Save trend data to memory
        
        Args:
            trend_data: Dictionary containing trend information
        """
        if "id" not in trend_data:
            # Use timestamp as ID if not provided
            trend_data["id"] = f"trend_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        trend_id = trend_data["id"]
        file_path = self.trends_dir / f"{trend_id}.json"
        
        # Add timestamp
        trend_data["_created"] = datetime.now().isoformat()
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(trend_data, f, indent=2, ensure_ascii=False)
    
    def get_latest_trends(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get latest trend reports
        
        Args:
            limit: Maximum number of trends to return
            
        Returns:
            List of trend data dictionaries, sorted by date (newest first)
        """
        trends = []
        
        for file_path in self.trends_dir.glob("*.json"):
            with open(file_path, 'r', encoding='utf-8') as f:
                trends.append(json.load(f))
        
        # Sort by date (newest first)
        trends.sort(key=lambda x: x.get("_created", ""), reverse=True)
        
        return trends[:limit] 