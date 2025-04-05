"""
Date parsing and handling utilities
"""
from typing import Optional, List, Dict, Any, Tuple
import re
from datetime import datetime, timedelta
import calendar
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Common date formats
MONTH_NAMES = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12
}

def extract_dates_from_text(text: str) -> List[str]:
    """Extract potential date strings from text
    
    Args:
        text: Text to extract dates from
        
    Returns:
        List of date strings found in the text
    """
    if not text:
        return []
    
    # Pattern for common date formats
    date_patterns = [
        # Month DD, YYYY
        r'\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2}(?:st|nd|rd|th)?,\s+\d{4}\b',
        
        # MM/DD/YYYY or DD/MM/YYYY
        r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',
        
        # YYYY-MM-DD
        r'\b\d{4}-\d{1,2}-\d{1,2}\b',
        
        # DD-MM-YYYY
        r'\b\d{1,2}-\d{1,2}-\d{4}\b',
        
        # Month DD-DD, YYYY (ranges)
        r'\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2}(?:st|nd|rd|th)?[-–](?:\d{1,2})(?:st|nd|rd|th)?,\s+\d{4}\b'
    ]
    
    results = []
    for pattern in date_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        results.extend(matches)
    
    return results

def parse_deadline_date(date_str: str) -> Optional[datetime]:
    """Parse deadline date from string
    
    Args:
        date_str: String representation of a date
        
    Returns:
        Parsed datetime object or None if parsing failed
    """
    if not date_str:
        return None
    
    # Try various date formats
    
    # Try Month DD, YYYY format
    month_day_year_pattern = r'(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+(\d{1,2})(?:st|nd|rd|th)?,\s+(\d{4})'
    match = re.search(month_day_year_pattern, date_str, re.IGNORECASE)
    
    if match:
        month_str, day_str, year_str = match.groups()
        month = MONTH_NAMES.get(month_str.lower(), None)
        
        if month is not None:
            try:
                day = int(day_str)
                year = int(year_str)
                return datetime(year, month, day)
            except (ValueError, TypeError) as e:
                logger.warning(f"Error parsing date: {date_str} - {str(e)}")
    
    # Try YYYY-MM-DD format
    iso_pattern = r'(\d{4})-(\d{1,2})-(\d{1,2})'
    match = re.search(iso_pattern, date_str)
    
    if match:
        year_str, month_str, day_str = match.groups()
        try:
            year = int(year_str)
            month = int(month_str)
            day = int(day_str)
            return datetime(year, month, day)
        except (ValueError, TypeError) as e:
            logger.warning(f"Error parsing date: {date_str} - {str(e)}")
    
    # Try MM/DD/YYYY format
    mdy_pattern = r'(\d{1,2})/(\d{1,2})/(\d{4})'
    match = re.search(mdy_pattern, date_str)
    
    if match:
        month_str, day_str, year_str = match.groups()
        try:
            month = int(month_str)
            day = int(day_str)
            year = int(year_str)
            return datetime(year, month, day)
        except (ValueError, TypeError) as e:
            logger.warning(f"Error parsing date: {date_str} - {str(e)}")
    
    # If all else fails, try using dateutil
    try:
        from dateutil import parser
        return parser.parse(date_str, fuzzy=True)
    except Exception as e:
        logger.warning(f"Failed to parse date: {date_str} - {str(e)}")
        return None

def extract_date_range(text: str) -> Tuple[Optional[datetime], Optional[datetime]]:
    """Extract a date range from text
    
    Args:
        text: Text to extract date range from
        
    Returns:
        Tuple of (start_date, end_date) as datetime objects, or (None, None) if no valid range found
    """
    if not text:
        return None, None
    
    # Pattern for dates with ranges
    range_patterns = [
        # Month DD-DD, YYYY format
        r'(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+(\d{1,2})(?:st|nd|rd|th)?[-–](\d{1,2})(?:st|nd|rd|th)?,\s+(\d{4})',
        
        # Month DD - Month DD, YYYY format
        r'(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+(\d{1,2})(?:st|nd|rd|th)?[-–](Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+(\d{1,2})(?:st|nd|rd|th)?,\s+(\d{4})'
    ]
    
    # Check for Month DD-DD, YYYY format
    match = re.search(range_patterns[0], text, re.IGNORECASE)
    if match:
        month_str, day1_str, day2_str, year_str = match.groups()
        month = MONTH_NAMES.get(month_str.lower(), None)
        
        if month is not None:
            try:
                day1 = int(day1_str)
                day2 = int(day2_str)
                year = int(year_str)
                
                start_date = datetime(year, month, day1)
                end_date = datetime(year, month, day2)
                return start_date, end_date
            except (ValueError, TypeError) as e:
                logger.warning(f"Error parsing date range: {text} - {str(e)}")
    
    # Check for Month DD - Month DD, YYYY format
    match = re.search(range_patterns[1], text, re.IGNORECASE)
    if match:
        month1_str, day1_str, month2_str, day2_str, year_str = match.groups()
        month1 = MONTH_NAMES.get(month1_str.lower(), None)
        month2 = MONTH_NAMES.get(month2_str.lower(), None)
        
        if month1 is not None and month2 is not None:
            try:
                day1 = int(day1_str)
                day2 = int(day2_str)
                year = int(year_str)
                
                start_date = datetime(year, month1, day1)
                end_date = datetime(year, month2, day2)
                return start_date, end_date
            except (ValueError, TypeError) as e:
                logger.warning(f"Error parsing date range: {text} - {str(e)}")
    
    # If everything fails, look for individual dates and take the first two
    dates = extract_dates_from_text(text)
    if len(dates) >= 2:
        start_date = parse_deadline_date(dates[0])
        end_date = parse_deadline_date(dates[1])
        if start_date and end_date:
            return start_date, end_date
    
    return None, None

def is_date_in_future(date_obj: Optional[datetime]) -> bool:
    """Check if a date is in the future
    
    Args:
        date_obj: Datetime object to check
        
    Returns:
        True if the date is in the future, False otherwise or if date_obj is None
    """
    if not date_obj:
        return False
    
    return date_obj > datetime.now()

def format_date(date_obj: Optional[datetime], format_str: str = "%B %d, %Y") -> str:
    """Format a datetime object as a string
    
    Args:
        date_obj: Datetime object to format
        format_str: Format string (default: "%B %d, %Y")
        
    Returns:
        Formatted date string or empty string if date_obj is None
    """
    if not date_obj:
        return ""
    
    return date_obj.strftime(format_str)

def get_days_until(date_obj: Optional[datetime]) -> Optional[int]:
    """Get number of days until a date
    
    Args:
        date_obj: Target datetime object
        
    Returns:
        Number of days until the date or None if date_obj is None
    """
    if not date_obj:
        return None
    
    delta = date_obj - datetime.now()
    return delta.days 