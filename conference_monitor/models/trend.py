"""
Trend data model
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from conference_monitor.models.paper import Paper


class Topic(BaseModel):
    """Research topic model"""
    name: str = Field(..., description="Name of the topic")
    description: Optional[str] = Field(None, description="Description of the topic")
    relevance_score: Optional[float] = Field(None, description="Relevance score (0-1)")
    related_topics: List[str] = Field(default_factory=list, description="Related topics")
    keywords: List[str] = Field(default_factory=list, description="Keywords associated with the topic")


class Trend(BaseModel):
    """Trend data model"""
    id: str = Field(..., description="Unique identifier for the trend")
    name: str = Field(..., description="Name of the trend")
    description: Optional[str] = Field(None, description="Description of the trend")
    research_area: str = Field(..., description="Research area the trend belongs to")
    topics: List[Topic] = Field(default_factory=list, description="List of topics in this trend")
    evidence_papers: List[Paper] = Field(default_factory=list, description="List of papers supporting this trend")
    popularity_score: Optional[float] = Field(None, description="Popularity score (0-1)")
    growth_rate: Optional[float] = Field(None, description="Growth rate")
    created_date: datetime = Field(default_factory=datetime.now, description="When the trend was created")
    last_updated: datetime = Field(default_factory=datetime.now, description="When the trend was last updated")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class TrendReport(BaseModel):
    """Trend report model"""
    id: str = Field(..., description="Unique identifier for the report")
    title: str = Field(..., description="Title of the report")
    research_area: str = Field(..., description="Research area the report covers")
    trends: List[Trend] = Field(default_factory=list, description="List of trends")
    generated_date: datetime = Field(default_factory=datetime.now, description="When the report was generated")
    time_period: str = Field("last 6 months", description="Time period covered by the report")
    paper_count: int = Field(0, description="Number of papers analyzed")
    source: str = Field("Conference Monitor Agent", description="Source of the report")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    def get_top_trends(self, limit: int = 5) -> List[Trend]:
        """Get top trends by popularity score
        
        Args:
            limit: Maximum number of trends to return
            
        Returns:
            List of top trends
        """
        sorted_trends = sorted(
            self.trends, 
            key=lambda t: t.popularity_score or 0, 
            reverse=True
        )
        return sorted_trends[:limit]
    
    def get_fastest_growing_trends(self, limit: int = 5) -> List[Trend]:
        """Get fastest growing trends by growth rate
        
        Args:
            limit: Maximum number of trends to return
            
        Returns:
            List of fastest growing trends
        """
        sorted_trends = sorted(
            self.trends, 
            key=lambda t: t.growth_rate or 0, 
            reverse=True
        )
        return sorted_trends[:limit] 