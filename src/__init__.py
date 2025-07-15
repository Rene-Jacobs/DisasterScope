# src/__init__.py
"""
Disaster Impact Analysis System

A Python application for analyzing the impact of natural disasters
on US infrastructure sectors.

This package provides both GUI and command-line interfaces for:
- Searching for relevant articles about various natural disasters
- Analyzing their impact on critical infrastructure sectors
- Generating comprehensive Excel reports
"""

__version__ = "1.0.0"
__author__ = "Disaster Impact Analysis Team"

# Make key components available from the top-level package
from .utils.search_api import search_articles
from .utils.article_analyzer import analyze_article, analyze_articles
from .utils.report_generator import generate_excel_report

# Also expose some of the new modules' functionality
from .utils.impact_analyzer import extract_structured_impact_details

# Define common data available throughout the package
PRIORITY_1_SECTORS = [
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

PRIORITY_2_SECTORS = [
    "Energy",
    "Water",
    "Defense",
    "Financial",
    "Healthcare",
    "Food and Agriculture",
]

ALL_SECTORS = PRIORITY_1_SECTORS + PRIORITY_2_SECTORS

DISASTER_TYPES = [
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
