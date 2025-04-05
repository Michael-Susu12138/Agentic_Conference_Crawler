"""
Agent memory implementation for storing and retrieving agent data
"""
import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from conference_monitor.config import DATA_DIR

class AgentMemory:
    """Memory management for the conference monitoring agent"""
    
    def __init__(self, data_dir: Optional[Path] = None):
        """Initialize the agent memory
        
        Args:
            data_dir: Directory for storing agent data (uses default from config if not provided)
        """
        self.data_dir = data_dir or DATA_DIR
        
        # Create necessary subdirectories
        self.conferences_dir = self.data_dir / "conferences"
        self.papers_dir = self.data_dir / "papers"
        self.trends_dir = self.data_dir / "trends"
        self.collaborators_dir = self.data_dir / "collaborators"
        
        # Ensure directories exist
        for directory in [self.conferences_dir, self.papers_dir, 
                         self.trends_dir, self.collaborators_dir]:
            os.makedirs(directory, exist_ok=True)
        
        # Store metadata about the agent's state
        self.metadata_file = self.data_dir / "metadata.json"
        self._initialize_metadata()
    
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
    
    def save_conference(self, conference_data: Dict[str, Any]):
        """Save conference data to memory
        
        Args:
            conference_data: Dictionary containing conference information
        """
        if "id" not in conference_data:
            raise ValueError("Conference data must include an 'id' field")
        
        conference_id = conference_data["id"]
        file_path = self.conferences_dir / f"{conference_id}.json"
        
        # Add timestamp for tracking
        conference_data["_last_updated"] = datetime.now().isoformat()
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(conference_data, f, indent=2, ensure_ascii=False)
        
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
        conferences = []
        
        for file_path in self.conferences_dir.glob("*.json"):
            with open(file_path, 'r', encoding='utf-8') as f:
                conferences.append(json.load(f))
        
        return conferences
    
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