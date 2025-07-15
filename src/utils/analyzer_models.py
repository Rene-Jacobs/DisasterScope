"""
Analyzer Models Module for Disaster Impact Analysis System.

This module defines the data models used for standardizing and validating
the data structures in the article analysis process. These models ensure
consistent data handling and provide type safety throughout the application.

Classes:
    PublicationInfo: Information about article publication metadata
    ImpactInfo: Details about disaster impacts on infrastructure
    DisasterAnalysisResult: Complete analysis result for a single article
    AnalysisOptions: Configuration options for the analysis process
    AnalysisStatistics: Performance and process statistics
    BatchAnalysisResult: Results from analyzing multiple articles
"""

# Standard library imports
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

# Third-party imports
from pydantic import BaseModel, Field, field_validator, computed_field

# Constants for validation
MIN_YEAR = 1990
MAX_YEAR = datetime.now().year + 1
DEFAULT_ANALYSIS_TIMEOUT = 30
MAX_CONTENT_LENGTH = 50000
DEFAULT_TARGET_SECTORS = ["Communications"]


class PublicationInfo(BaseModel):
    """
    Information about the publication of an article.

    This model stores metadata related to when and where an article
    was published, including author information if available.

    Attributes:
        date: Publication date in YYYY-MM-DD format or descriptive string
        source: Source domain or publisher of the article
        title: Title/headline of the article
        authors: List of article authors (if available)
    """

    date: Optional[str] = Field(
        default=None, description="Publication date of the article in YYYY-MM-DD format"
    )
    source: Optional[str] = Field(
        default=None, description="Source domain or publisher of the article"
    )
    title: Optional[str] = Field(
        default=None, description="Title or headline of the article"
    )
    authors: List[str] = Field(
        default=[], description="List of article authors if available"
    )

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate and normalize publication date.

        Args:
            v: Date string to validate

        Returns:
            Validated date string or None
        """
        if not v:
            return v

        # Convert to string if not already
        date_str = str(v).strip()

        # Allow special date indicators
        if date_str.startswith("Date unknown") or date_str.endswith("(future date)"):
            return date_str

        # Validate and normalize common date formats
        import re

        # Check for YYYY-MM-DD format (preferred)
        if re.match(r"\d{4}-\d{2}-\d{2}", date_str):
            return date_str

        # Try to normalize MM/DD/YYYY format
        mm_dd_yyyy = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", date_str)
        if mm_dd_yyyy:
            month, day, year = mm_dd_yyyy.groups()
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"

        # Try to normalize DD/MM/YYYY format
        dd_mm_yyyy = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", date_str)
        if dd_mm_yyyy:
            # Assume MM/DD/YYYY for US sources unless day > 12
            day, month, year = dd_mm_yyyy.groups()
            if int(day) > 12:  # Must be DD/MM/YYYY
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"

        return date_str  # Return as-is if no recognized format

    @field_validator("source")
    @classmethod
    def validate_source(cls, v: Optional[str]) -> Optional[str]:
        """Clean and validate source domain."""
        if not v:
            return v

        # Remove protocol and www prefix for consistency
        import re

        cleaned = re.sub(r"^https?://(www\.)?", "", v.lower())
        return cleaned.split("/")[0]  # Keep only domain part

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        """Clean and validate article title."""
        if not v:
            return v

        # Remove excessive whitespace and clean up
        cleaned = " ".join(v.split())

        # Truncate very long titles
        if len(cleaned) > 200:
            cleaned = cleaned[:197] + "..."

        return cleaned


class ImpactInfo(BaseModel):
    """
    Information about disaster impacts on communication infrastructure.

    This model captures various aspects of how a disaster affected
    infrastructure systems, including affected services, geographic
    scope, recovery efforts, and detailed impact descriptions.

    Attributes:
        affected_services: List of communication services that were impacted
        affected_areas: List of geographic areas affected by the disaster
        impact_types: List of types of impact observed (outage, damage, etc.)
        duration: Duration of the impact if known
        scale: Scale of the impact (number of customers, percentage, etc.)
        restoration_efforts: Information about recovery and restoration efforts
        raw_content: Raw extracted content related to impacts
    """

    affected_services: List[str] = Field(
        default=[], description="Communication services affected by the disaster"
    )
    affected_areas: List[str] = Field(
        default=[], description="Geographic areas affected by the disaster"
    )
    impact_types: List[str] = Field(
        default=[],
        description="Types of impact observed (outage, damage, disruption, etc.)",
    )
    duration: Optional[str] = Field(
        default=None, description="Duration of the impact if known"
    )
    scale: Optional[str] = Field(
        default=None,
        description="Scale of impact (customers affected, percentage, etc.)",
    )
    restoration_efforts: Optional[str] = Field(
        default=None, description="Details about restoration and recovery efforts"
    )
    raw_content: Optional[str] = Field(
        default=None, description="Raw extracted content related to impacts"
    )

    @field_validator("raw_content")
    @classmethod
    def validate_raw_content(cls, v: Optional[str]) -> Optional[str]:
        """Validate and clean raw content."""
        if not v:
            return v

        # Limit content length for performance
        if len(v) > MAX_CONTENT_LENGTH:
            v = v[:MAX_CONTENT_LENGTH] + "... [content truncated]"

        # Clean up excessive whitespace
        cleaned = " ".join(v.split())
        return cleaned if cleaned else None


class DisasterAnalysisResult(BaseModel):
    """
    Complete result of disaster article analysis.

    This is the main result object that contains all information
    extracted from analyzing a single article about disaster impacts.

    Attributes:
        url: URL of the analyzed article
        disaster_type: Type of disaster being analyzed
        publication_info: Publication metadata and information
        impact_info: Extracted impact information
        sentiment: Sentiment score of impact content (-1.0 to 1.0)
        error: Error message if analysis failed
    """

    url: str = Field(..., description="URL of the analyzed article")
    disaster_type: str = Field(..., description="Type of disaster being analyzed")
    publication_info: PublicationInfo = Field(
        default_factory=lambda: PublicationInfo(),
        description="Publication information and metadata",
    )
    impact_info: ImpactInfo = Field(
        default_factory=lambda: ImpactInfo(), description="Extracted impact information"
    )
    sentiment: Optional[float] = Field(
        default=None,
        description="Sentiment score of impact content (-1.0 to 1.0)",
        ge=-1.0,
        le=1.0,
    )
    error: Optional[str] = Field(
        default=None, description="Error message if analysis failed"
    )

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL format."""
        if not v:
            raise ValueError("URL cannot be empty")

        # Basic URL validation
        import re

        url_pattern = re.compile(
            r"^https?://"  # http:// or https://
            r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain...
            r"localhost|"  # localhost...
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
            r"(?::\d+)?"  # optional port
            r"(?:/?|[/?]\S+)$",
            re.IGNORECASE,
        )

        if not url_pattern.match(v):
            raise ValueError(f"Invalid URL format: {v}")

        return v

    @field_validator("disaster_type")
    @classmethod
    def validate_disaster_type(cls, v: str) -> str:
        """Validate disaster type."""
        if not v or not v.strip():
            raise ValueError("Disaster type cannot be empty")

        return v.strip().title()  # Normalize capitalization

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert result to a dictionary for JSON serialization.

        Returns:
            Dictionary representation of the analysis result
        """
        return {
            "url": self.url,
            "disaster_type": self.disaster_type,
            "publication_info": self.publication_info.model_dump(exclude_none=True),
            "impact_info": self.impact_info.model_dump(exclude_none=True),
            "sentiment": self.sentiment,
            "error": self.error,
        }


class AnalysisOptions(BaseModel):
    """
    Options for configuring the article analysis process.

    This model allows customization of how articles are analyzed,
    including performance settings and feature toggles.

    Attributes:
        max_content_length: Maximum length of content to analyze
        extract_sentiment: Whether to extract sentiment from articles
        use_nlp: Whether to use NLP for enhanced analysis
        target_sectors: Target infrastructure sectors to analyze
        include_related_sectors: Whether to include related sector information
        timeout_seconds: Maximum time to spend analyzing each article
    """

    max_content_length: int = Field(
        MAX_CONTENT_LENGTH,
        description="Maximum length of content to analyze",
        gt=0,
        le=100000,
    )
    extract_sentiment: bool = Field(
        True, description="Whether to extract sentiment from the article"
    )
    use_nlp: bool = Field(True, description="Whether to use NLP for enhanced analysis")
    target_sectors: List[str] = Field(
        default=["Communications"],
        description="Target infrastructure sectors to analyze",
    )
    include_related_sectors: bool = Field(
        False, description="Whether to include information about related sectors"
    )
    timeout_seconds: int = Field(
        DEFAULT_ANALYSIS_TIMEOUT,
        description="Maximum time to spend analyzing each article",
        gt=0,
        le=300,  # 5 minutes max
    )


class AnalysisStatistics(BaseModel):
    """
    Statistics about the analysis process.

    This model tracks performance metrics and process information
    for monitoring and optimization purposes.

    Attributes:
        processing_time_ms: Processing time in milliseconds
        content_length: Length of analyzed content in characters
        extraction_methods_used: List of successful extraction methods
        error_count: Number of non-critical errors encountered
        articles_processed: Number of articles successfully processed
        cache_hits: Number of cache hits during processing
    """

    processing_time_ms: float = Field(
        default=0.0, description="Processing time in milliseconds", ge=0.0
    )
    content_length: int = Field(
        default=0, description="Length of the analyzed content in characters", ge=0
    )
    extraction_methods_used: List[str] = Field(
        default=[], description="List of extraction methods that were successful"
    )
    error_count: int = Field(
        default=0, description="Number of non-critical errors encountered", ge=0
    )
    articles_processed: int = Field(
        default=0, description="Number of articles successfully processed", ge=0
    )
    cache_hits: int = Field(
        default=0, description="Number of cache hits during processing", ge=0
    )

    @field_validator("processing_time_ms")
    @classmethod
    def round_processing_time(cls, v: float) -> float:
        """Round processing time to 2 decimal places."""
        return round(v, 2)


class BatchAnalysisResult(BaseModel):
    """
    Result of analyzing multiple articles in a batch.

    This model aggregates results from multiple article analyses
    and provides overall statistics and summaries.

    Attributes:
        results: Results for each individual article
        statistics: Overall statistics for the batch analysis
        successful_count: Number of successfully analyzed articles
        failed_count: Number of articles that failed analysis
        total_processing_time_ms: Total time spent processing the batch
    """

    results: List[DisasterAnalysisResult] = Field(
        default=[], description="Results for each individual article"
    )
    statistics: AnalysisStatistics = Field(
        default_factory=lambda: AnalysisStatistics(),
        description="Overall statistics for the batch analysis",
    )
    total_processing_time_ms: float = Field(
        default=0.0, description="Total time spent processing the batch", ge=0.0
    )

    @computed_field
    @property
    def successful_count(self) -> int:
        """Number of successfully analyzed articles."""
        return sum(1 for r in self.results if not r.error)

    @computed_field
    @property
    def failed_count(self) -> int:
        """Number of articles that failed analysis."""
        return sum(1 for r in self.results if r.error)

    def get_success_rate(self) -> float:
        """
        Calculate the success rate of the batch analysis.

        Returns:
            Success rate as a percentage (0.0 to 100.0)
        """
        total = self.successful_count + self.failed_count
        if total == 0:
            return 0.0
        return (self.successful_count / total) * 100.0

    def get_average_processing_time(self) -> float:
        """
        Calculate average processing time per article.

        Returns:
            Average processing time in milliseconds
        """
        total = self.successful_count + self.failed_count
        if total == 0:
            return 0.0
        return self.total_processing_time_ms / total


__all__ = [
    "PublicationInfo",
    "ImpactInfo",
    "DisasterAnalysisResult",
    "AnalysisOptions",
    "AnalysisStatistics",
    "BatchAnalysisResult",
    "DEFAULT_TARGET_SECTORS",
    "MAX_CONTENT_LENGTH",
    "DEFAULT_ANALYSIS_TIMEOUT",
]
