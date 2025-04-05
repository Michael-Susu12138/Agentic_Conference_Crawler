"""
JSON utilities for serialization and deserialization
"""
import json
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import logging

# Set up logging
logger = logging.getLogger(__name__)

class DateTimeEncoder(json.JSONEncoder):
    """JSON Encoder that handles datetime objects"""
    
    def default(self, obj):
        """Convert datetime objects to ISO format strings
        
        Args:
            obj: Object to encode
            
        Returns:
            JSON serializable version of the object
        """
        if isinstance(obj, datetime):
            return obj.isoformat()
        
        return super().default(obj)

def serialize_to_json(data: Any) -> str:
    """Serialize data to JSON string
    
    Args:
        data: Data to serialize
        
    Returns:
        JSON string
    """
    try:
        return json.dumps(data, cls=DateTimeEncoder, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error serializing to JSON: {str(e)}")
        # Return a minimal JSON with error info
        return json.dumps({"error": f"Serialization error: {str(e)}"})

def deserialize_from_json(json_str: str) -> Any:
    """Deserialize data from JSON string
    
    Args:
        json_str: JSON string to deserialize
        
    Returns:
        Deserialized data
    """
    try:
        return json.loads(json_str)
    except Exception as e:
        logger.error(f"Error deserializing from JSON: {str(e)}")
        return None

def parse_dates_in_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse ISO date strings into datetime objects in a dictionary
    
    Args:
        data: Dictionary potentially containing date strings
        
    Returns:
        Dictionary with date strings converted to datetime objects
    """
    result = {}
    
    for key, value in data.items():
        if isinstance(value, str) and key.endswith(('date', 'time', 'datetime')):
            try:
                result[key] = datetime.fromisoformat(value)
            except (ValueError, TypeError):
                result[key] = value
        elif isinstance(value, dict):
            result[key] = parse_dates_in_dict(value)
        elif isinstance(value, list):
            result[key] = [
                parse_dates_in_dict(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            result[key] = value
    
    return result

def save_to_json_file(data: Any, file_path: str) -> bool:
    """Save data to a JSON file
    
    Args:
        data: Data to save
        file_path: Path to the file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, cls=DateTimeEncoder, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving to JSON file {file_path}: {str(e)}")
        return False

def load_from_json_file(file_path: str, parse_dates: bool = False) -> Optional[Any]:
    """Load data from a JSON file
    
    Args:
        file_path: Path to the file
        parse_dates: Whether to parse ISO date strings into datetime objects
        
    Returns:
        Loaded data or None if loading failed
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if parse_dates and isinstance(data, dict):
            return parse_dates_in_dict(data)
        
        return data
    except Exception as e:
        logger.error(f"Error loading from JSON file {file_path}: {str(e)}")
        return None

def merge_json_objects(base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
    """Merge two JSON objects (dictionaries)
    
    Args:
        base: Base dictionary
        update: Dictionary with updates (takes precedence)
        
    Returns:
        Merged dictionary
    """
    result = base.copy()
    
    for key, value in update.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_json_objects(result[key], value)
        else:
            result[key] = value
    
    return result 