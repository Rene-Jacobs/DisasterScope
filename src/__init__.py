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

# Import shared configuration lists
from .config import (
    PRIORITY_1_SECTORS,
    PRIORITY_2_SECTORS,
    ALL_SECTORS,
    DISASTER_TYPES,
)

# Local imports
from .utils.article_analyzer import analyze_article, analyze_articles
from .utils.impact_analyzer import extract_structured_impact_details
from .utils.report_generator import generate_excel_report
from .utils.search_api import search_articles

__version__ = "1.0.0"
__author__ = "Disaster Impact Analysis Team"

# The infrastructure sector lists and supported disaster types are
# defined in :mod:`src.config` and imported above for convenience.

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
