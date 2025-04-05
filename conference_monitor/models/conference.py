"""
Conference data model
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ConferenceDeadline(BaseModel):
    """Conference deadline model"""
    name: str = Field(..., description="Name of the deadline (e.g., 'Paper submission')")
    date: str = Field(..., description="Deadline date as string")
    timestamp: Optional[datetime] = Field(None, description="Parsed deadline timestamp")
    is_passed: bool = Field(False, description="Whether the deadline has passed")


class Conference(BaseModel):
    """Conference data model"""
    id: str = Field(..., description="Unique identifier for the conference")
    title: str = Field(..., description="Title of the conference")
    url: Optional[str] = Field(None, description="URL of the conference website")
    description: Optional[str] = Field(None, description="Description of the conference")
    dates: Optional[str] = Field(None, description="Conference dates as string")
    start_date: Optional[datetime] = Field(None, description="Conference start date")
    end_date: Optional[datetime] = Field(None, description="Conference end date")
    location: Optional[str] = Field(None, description="Location of the conference")
    deadlines: List[ConferenceDeadline] = Field(default_factory=list, description="List of conference deadlines")
    research_areas: List[str] = Field(default_factory=list, description="List of research areas covered by the conference")
    organizers: List[str] = Field(default_factory=list, description="List of conference organizers")
    last_updated: datetime = Field(default_factory=datetime.now, description="When the conference data was last updated")
    source: Optional[str] = Field(None, description="Source of the conference data")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    def is_upcoming(self) -> bool:
        """Check if the conference is upcoming
        
        Returns:
            True if the conference end date is in the future, False otherwise
        """
        if not self.end_date:
            return True  # Assume upcoming if no end date
        
        return self.end_date > datetime.now()
    
    def get_nearest_deadline(self) -> Optional[ConferenceDeadline]:
        """Get the nearest upcoming deadline
        
        Returns:
            The nearest upcoming deadline, or None if there are no upcoming deadlines
        """
        upcoming_deadlines = [d for d in self.deadlines if not d.is_passed]
        
        if not upcoming_deadlines:
            return None
        
        # Sort by date (this assumes timestamps are properly parsed)
        # Fall back to string comparison if timestamps aren't available
        if all(d.timestamp for d in upcoming_deadlines):
            sorted_deadlines = sorted(upcoming_deadlines, key=lambda d: d.timestamp)
        else:
            sorted_deadlines = sorted(upcoming_deadlines, key=lambda d: d.date)
        
        return sorted_deadlines[0]
    

class ConferenceList(BaseModel):
    """List of conferences"""
    conferences: List[Conference] = Field(default_factory=list, description="List of conferences")
    total_count: int = Field(0, description="Total number of conferences")
    last_updated: datetime = Field(default_factory=datetime.now, description="When the list was last updated") 