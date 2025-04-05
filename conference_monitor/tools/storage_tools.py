"""
Storage tools for managing agent data
"""
from typing import Dict, List, Any, Optional
import logging
import json
from pathlib import Path
import os
from datetime import datetime

from conference_monitor.tools.base import BaseTool
from conference_monitor.core.memory import AgentMemory
from conference_monitor.config import DATA_DIR

# Set up logging
logger = logging.getLogger(__name__)

class ExportDataTool(BaseTool):
    """Tool for exporting agent data to a file"""
    
    def __init__(self, memory: Optional[AgentMemory] = None):
        """Initialize the export data tool
        
        Args:
            memory: AgentMemory instance
        """
        super().__init__(
            name="export_data",
            description="Export agent data to a file"
        )
        self.memory = memory or AgentMemory()
    
    def _get_parameters_schema(self) -> Dict[str, Any]:
        """Get the schema for the tool's parameters"""
        return {
            "type": "object",
            "properties": {
                "data_type": {
                    "type": "string",
                    "description": "Type of data to export (conferences, papers, trends, all)"
                },
                "format": {
                    "type": "string",
                    "description": "Format to export data in (json, csv)"
                },
                "file_path": {
                    "type": "string",
                    "description": "Path to export data to (default: auto-generated)"
                }
            },
            "required": ["data_type"]
        }
    
    def _execute(self, data_type: str, format: Optional[str] = "json",
                file_path: Optional[str] = None) -> Dict[str, Any]:
        """Execute the data export
        
        Args:
            data_type: Type of data to export
            format: Format to export data in
            file_path: Path to export data to
            
        Returns:
            Dictionary with export results
        """
        if format != "json":
            return {
                "error": f"Unsupported export format: {format}. Only 'json' is currently supported."
            }
        
        # Determine data to export
        export_data = {}
        
        if data_type == "conferences" or data_type == "all":
            export_data["conferences"] = self.memory.list_conferences()
        
        if data_type == "papers" or data_type == "all":
            export_data["papers"] = self.memory.list_papers()
        
        if data_type == "trends" or data_type == "all":
            export_data["trends"] = self.memory.get_latest_trends(limit=100)
        
        if not export_data:
            return {
                "error": f"Invalid data type: {data_type}. Valid types are: conferences, papers, trends, all"
            }
        
        # Generate file path if not provided
        if not file_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = os.path.join(DATA_DIR, f"export_{data_type}_{timestamp}.json")
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Export data
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            return {
                "success": True,
                "file_path": file_path,
                "data_type": data_type,
                "record_count": sum(len(data) for data in export_data.values())
            }
        except Exception as e:
            logger.error(f"Error exporting data: {str(e)}")
            return {
                "error": f"Error exporting data: {str(e)}",
                "data_type": data_type
            }


class ImportDataTool(BaseTool):
    """Tool for importing agent data from a file"""
    
    def __init__(self, memory: Optional[AgentMemory] = None):
        """Initialize the import data tool
        
        Args:
            memory: AgentMemory instance
        """
        super().__init__(
            name="import_data",
            description="Import agent data from a file"
        )
        self.memory = memory or AgentMemory()
    
    def _get_parameters_schema(self) -> Dict[str, Any]:
        """Get the schema for the tool's parameters"""
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file to import data from"
                },
                "data_types": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Types of data to import (conferences, papers, trends, all)"
                },
                "replace_existing": {
                    "type": "boolean",
                    "description": "Whether to replace existing data with the same ID"
                }
            },
            "required": ["file_path"]
        }
    
    def _execute(self, file_path: str, 
                data_types: Optional[List[str]] = None,
                replace_existing: Optional[bool] = False) -> Dict[str, Any]:
        """Execute the data import
        
        Args:
            file_path: Path to the file to import data from
            data_types: Types of data to import
            replace_existing: Whether to replace existing data with the same ID
            
        Returns:
            Dictionary with import results
        """
        data_types = data_types or ["all"]
        
        # Check if file exists
        if not os.path.exists(file_path):
            return {
                "error": f"File not found: {file_path}"
            }
        
        # Import data
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            import_stats = {
                "conferences": 0,
                "papers": 0,
                "trends": 0
            }
            
            # Import conferences
            if "all" in data_types or "conferences" in data_types:
                conferences = import_data.get("conferences", [])
                for conf in conferences:
                    if "id" in conf:
                        self.memory.save_conference(conf)
                        import_stats["conferences"] += 1
            
            # Import papers
            if "all" in data_types or "papers" in data_types:
                papers = import_data.get("papers", [])
                for paper in papers:
                    if "id" in paper:
                        self.memory.save_paper(paper)
                        import_stats["papers"] += 1
            
            # Import trends
            if "all" in data_types or "trends" in data_types:
                trends = import_data.get("trends", [])
                for trend in trends:
                    if "id" in trend:
                        self.memory.save_trend(trend)
                        import_stats["trends"] += 1
            
            return {
                "success": True,
                "file_path": file_path,
                "import_stats": import_stats,
                "total_imported": sum(import_stats.values())
            }
        except Exception as e:
            logger.error(f"Error importing data: {str(e)}")
            return {
                "error": f"Error importing data: {str(e)}",
                "file_path": file_path
            } 