"""
Analyzer Models Module for Disaster Impact Analysis System

This module defines the data models used for standardizing and validating
the data structures in the article analysis process.
"""

from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime


class PublicationInfo(BaseModel):
    """Information about the publication of the article"""

    date: Optional[str] = Field(None, description="Publication date of the article")
    source: Optional[str] = Field(None, description="Source domain of the article")
    title: Optional[str] = Field(None, description="Title of the article")
    authors: List[str] = Field(
        default_factory=list, description="Authors of the article"
    )

    @validator("date")
    def validate_date(cls, v):
        """Validate date format if exists"""
        if v and not isinstance(v, str):
            v = str(v)

        if v and not v.startswith("Date unknown") and not v.endswith("(future date)"):
            import re

            if not re.match(r"\d{4}-\d{2}-\d{2}", v):
                try:
                    # Try to normalize common date formats
                    if re.match(r"\d{1,2}/\d{1,2}/\d{4}", v):
                        parts = v.split("/")
                        v = f"{parts[2]}-{parts[0].zfill(2)}-{parts[1].zfill(2)}"
                except:
                    pass
        return v


class ImpactInfo(BaseModel):
    """Information about disaster impacts on communication infrastructure"""

    affected_services: List[str] = Field(
        default_factory=list, description="Communication services affected"
    )
    affected_areas: List[str] = Field(
        default_factory=list, description="Geographic areas affected"
    )
    impact_types: List[str] = Field(
        default_factory=list, description="Types of impact observed"
    )
    duration: Optional[str] = Field(None, description="Duration of the impact")
    scale: Optional[str] = Field(
        None, description="Scale of the impact (e.g., number of customers affected)"
    )
    restoration_efforts: Optional[str] = Field(
        None, description="Details about restoration efforts"
    )
    raw_content: Optional[str] = Field(
        None, description="Raw extracted content related to impacts"
    )


class DisasterAnalysisResult(BaseModel):
    """Complete result of disaster article analysis"""

    url: str = Field(..., description="URL of the analyzed article")
    disaster_type: str = Field(..., description="Type of disaster being analyzed")
    publication_info: PublicationInfo = Field(
        default_factory=PublicationInfo, description="Publication information"
    )
    impact_info: ImpactInfo = Field(
        default_factory=ImpactInfo, description="Impact information"
    )
    sentiment: Optional[float] = Field(
        None, description="Sentiment score of impact content (-1.0 to 1.0)"
    )
    error: Optional[str] = Field(None, description="Error message if analysis failed")

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to a dictionary for JSON serialization"""
        return {
            "url": self.url,
            "disaster_type": self.disaster_type,
            "publication_info": self.publication_info.dict(exclude_none=True),
            "impact_info": self.impact_info.dict(exclude_none=True),
            "sentiment": self.sentiment,
            "error": self.error,
        }


class AnalysisOptions(BaseModel):
    """Options for configuring the article analysis process"""

    max_content_length: int = Field(
        10000, description="Maximum length of content to analyze"
    )
    extract_sentiment: bool = Field(
        True, description="Whether to extract sentiment from the article"
    )
    use_nlp: bool = Field(True, description="Whether to use NLP for enhanced analysis")
    target_sectors: List[str] = Field(
        default_factory=lambda: ["Communications"],
        description="Target sectors to analyze",
    )
    include_related_sectors: bool = Field(
        False, description="Whether to include information about related sectors"
    )


class AnalysisStatistics(BaseModel):
    """Statistics about the analysis process"""

    processing_time_ms: float = Field(
        default=0.0, description="Processing time in milliseconds"
    )
    content_length: int = Field(
        default=0, description="Length of the analyzed content in characters"
    )
    extraction_methods_used: List[str] = Field(
        default_factory=list,
        description="List of extraction methods that were successful",
    )
    error_count: int = Field(
        default=0, description="Number of non-critical errors encountered"
    )

    @validator("processing_time_ms")
    def round_processing_time(cls, v):
        """Round processing time to 2 decimal places"""
        return round(v, 2)


class BatchAnalysisResult(BaseModel):
    """Result of analyzing multiple articles in a batch"""

    results: List[DisasterAnalysisResult] = Field(
        default_factory=list, description="Results for each article"
    )
    statistics: AnalysisStatistics = Field(
        default_factory=lambda: AnalysisStatistics(),
        description="Overall statistics for the batch analysis",
    )
    successful_count: int = Field(
        0, description="Number of successfully analyzed articles"
    )
    failed_count: int = Field(0, description="Number of articles that failed analysis")

    @validator("successful_count", "failed_count", pre=True, always=True)
    def calculate_counts(cls, v, values):
        """Calculate successful and failed counts from results"""
        if "results" in values:
            if v.field.name == "successful_count":
                return sum(1 for r in values["results"] if not r.error)
            elif v.field.name == "failed_count":
                return sum(1 for r in values["results"] if r.error)
        return v
