"""
Paper data model
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class Author(BaseModel):
    """Author model"""
    name: str = Field(..., description="Name of the author")
    affiliation: Optional[str] = Field(None, description="Author's affiliation")
    email: Optional[str] = Field(None, description="Author's email")
    orcid: Optional[str] = Field(None, description="Author's ORCID ID")
    is_corresponding: bool = Field(False, description="Whether this author is the corresponding author")


class Paper(BaseModel):
    """Paper data model"""
    id: str = Field(..., description="Unique identifier for the paper")
    title: str = Field(..., description="Title of the paper")
    abstract: Optional[str] = Field(None, description="Abstract of the paper")
    authors: List[Author] = Field(default_factory=list, description="List of authors")
    url: Optional[str] = Field(None, description="URL of the paper")
    pdf_url: Optional[str] = Field(None, description="URL of the PDF")
    publication_date: Optional[datetime] = Field(None, description="Publication date")
    year: Optional[int] = Field(None, description="Publication year")
    venue: Optional[str] = Field(None, description="Publication venue (journal/conference)")
    doi: Optional[str] = Field(None, description="Digital Object Identifier")
    keywords: List[str] = Field(default_factory=list, description="Keywords associated with the paper")
    citations: Optional[int] = Field(None, description="Number of citations")
    references: List[str] = Field(default_factory=list, description="List of references")
    analysis: Optional[str] = Field(None, description="AI-generated analysis of the paper")
    source: Optional[str] = Field(None, description="Source of the paper data")
    last_updated: datetime = Field(default_factory=datetime.now, description="When the paper data was last updated")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    def get_authors_string(self) -> str:
        """Get authors as a string
        
        Returns:
            String representation of authors (e.g., "Smith et al.")
        """
        if not self.authors:
            return "Unknown"
        
        if len(self.authors) == 1:
            return self.authors[0].name
        
        if len(self.authors) == 2:
            return f"{self.authors[0].name} and {self.authors[1].name}"
        
        return f"{self.authors[0].name} et al."
    
    def get_citation(self) -> str:
        """Get a citation for the paper
        
        Returns:
            Citation string
        """
        authors_str = ", ".join([a.name for a in self.authors])
        
        year_str = f" ({self.year})" if self.year else ""
        venue_str = f". {self.venue}" if self.venue else ""
        doi_str = f". DOI: {self.doi}" if self.doi else ""
        
        return f"{authors_str}{year_str}. \"{self.title}\"{venue_str}{doi_str}"
    

class PaperList(BaseModel):
    """List of papers"""
    papers: List[Paper] = Field(default_factory=list, description="List of papers")
    total_count: int = Field(0, description="Total number of papers")
    last_updated: datetime = Field(default_factory=datetime.now, description="When the list was last updated")
    query: Optional[str] = Field(None, description="Search query used to generate this list") 