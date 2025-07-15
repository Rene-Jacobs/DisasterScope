# src/__init__.py
"""
Disaster Impact Analysis System

A Python application for analyzing the impact of natural disasters
on US infrastructure sectors.

This package provides both GUI and command-line interfaces for:
- Searching for relevant articles about various natural disasters
- Analyzing their impact on critical infrastructure sectors
- Generating comprehensive Excel reports

Attributes:
    __version__ (str): Current version of the application
    __author__ (str): Development team information
    PRIORITY_1_SECTORS (List[str]): High-priority infrastructure sectors
    PRIORITY_2_SECTORS (List[str]): Secondary-priority infrastructure sectors
    ALL_SECTORS (List[str]): Combined list of all infrastructure sectors
    DISASTER_TYPES (List[str]): Supported disaster types for analysis
"""

# Standard library imports
from typing import List

# Local imports
from .utils.article_analyzer import analyze_article, analyze_articles
from .utils.impact_analyzer import extract_structured_impact_details
from .utils.report_generator import generate_excel_report
from .utils.search_api import search_articles

__version__ = "1.0.0"
__author__ = "Disaster Impact Analysis Team"

# Define common data available throughout the package
PRIORITY_1_SECTORS: List[str] = [
    "Chemical",
    "Commercial Facilities",
    "Communications",
    "Critical Manufacturing",
    "Dams",
    "Emergency Services",
    "Information Technology",
    "Nuclear",
    "Transportation",
    "Government Facilities",
]

PRIORITY_2_SECTORS: List[str] = [
    "Energy",
    "Water",
    "Defense",
    "Financial",
    "Healthcare",
    "Food and Agriculture",
]

ALL_SECTORS: List[str] = PRIORITY_1_SECTORS + PRIORITY_2_SECTORS

DISASTER_TYPES: List[str] = [
    "Hurricane",
    "Earthquake",
    "Flood",
    "Fire",
    "Tornado",
    "Tsunami",
    "Drought",
    "Landslide",
    "Volcanic Eruption",
    "Winter Storm",
    "Heat Wave",
]

__all__ = [
    # Version information
    "__version__",
    "__author__",
    # Core analysis functions
    "analyze_article",
    "analyze_articles",
    "extract_structured_impact_details",
    "generate_excel_report",
    "search_articles",
    # Data constants
    "PRIORITY_1_SECTORS",
    "PRIORITY_2_SECTORS",
    "ALL_SECTORS",
    "DISASTER_TYPES",
]
# End of src/__init__.py
