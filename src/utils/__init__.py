"""
Utility modules for the Storm Impact Analysis System.

This package provides core functionality for:
- Searching for storm-related articles via Google API
- Analyzing web content for impact information
- Processing and extracting structured data
- Generating formatted Excel reports
"""

# Export main functions to simplify imports
from .search_api import search_articles
from .article_analyzer import analyze_article, analyze_articles
from .report_generator import generate_excel_report, clean_publication_date

# Import from the new modules
from .content_fetcher import fetch_article_with_retry, fetch_with_playwright
from .date_extractor import extract_and_normalize_date
from .content_parser import extract_main_content, process_general_content
from .impact_analyzer import extract_structured_impact_details, format_structured_impact
from .analyzer_models import DisasterAnalysisResult, ImpactInfo, PublicationInfo
