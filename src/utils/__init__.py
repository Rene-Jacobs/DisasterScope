"""
Utility modules for the Disaster Impact Analysis System.

This package provides core functionality for:
- Searching for disaster-related articles via Google API
- Analyzing web content for impact information
- Processing and extracting structured data
- Generating formatted Excel reports
- Content fetching and parsing
- Date extraction and normalization

The utilities are organized into specialized modules that handle different
aspects of the article analysis pipeline.
"""

# Standard library imports
from typing import Dict, List, Optional, Tuple

# Local imports - Core analysis functions
from .article_analyzer import analyze_article, analyze_articles
from .report_generator import clean_publication_date, generate_excel_report
from .search_api import search_articles

# Local imports - Specialized utility functions
from .analyzer_models import (
    AnalysisStatistics,
    BatchAnalysisResult,
    DisasterAnalysisResult,
    ImpactInfo,
    PublicationInfo,
)
from .content_fetcher import fetch_article_with_retry, fetch_with_playwright
from .content_parser import extract_main_content, process_general_content
from .date_extractor import extract_and_normalize_date
from .impact_analyzer import (
    extract_structured_impact_details,
    format_structured_impact,
)

__all__ = [
    # Core analysis functions
    "analyze_article",
    "analyze_articles",
    "generate_excel_report",
    "search_articles",
    # Utility functions
    "clean_publication_date",
    "extract_and_normalize_date",
    "extract_main_content",
    "extract_structured_impact_details",
    "fetch_article_with_retry",
    "fetch_with_playwright",
    "format_structured_impact",
    "process_general_content",
    # Data models
    "AnalysisStatistics",
    "BatchAnalysisResult",
    "DisasterAnalysisResult",
    "ImpactInfo",
    "PublicationInfo",
]
# End of src/utils/__init__.py
