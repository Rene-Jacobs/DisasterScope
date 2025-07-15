# src/config.py
"""
Configuration management for the Disaster Impact Analysis System.

This module centralizes all configuration constants, default values,
and settings used throughout the application. It provides a single
point of configuration management and environment-specific settings.

Constants are organized by functional area:
- Application metadata and versioning
- Infrastructure sector definitions
- Disaster type classifications
- API and network settings
- File and content processing limits
- User interface configuration
"""

# Standard library imports
import os
from typing import Dict, List, Union

# Application metadata
APP_NAME = "Disaster Impact Analysis System"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Disaster Impact Analysis Team"
APP_DESCRIPTION = "Analyzing disaster impacts on critical infrastructure sectors"

# Infrastructure sector definitions
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
DEFAULT_TARGET_SECTORS: List[str] = ["Communications"]

# Disaster type classifications
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

# API and network configuration
DEFAULT_MAX_RESULTS = 30
MAX_SEARCH_RESULTS = 100
GOOGLE_SEARCH_URL = "https://www.googleapis.com/customsearch/v1"
MAX_RESULTS_PER_REQUEST = 10
MAX_SEARCH_REQUESTS = 3
REQUEST_TIMEOUT_SECONDS = 30
NETWORK_RETRY_ATTEMPTS = 2
NETWORK_RETRY_DELAY_MIN = 1
NETWORK_RETRY_DELAY_MAX = 5

# Content processing limits
MAX_CONTENT_LENGTH = 50000
MIN_ARTICLE_LENGTH = 200
MIN_PARAGRAPH_LENGTH = 50
MIN_DISASTER_NAME_LENGTH = 2
MAX_DISASTER_NAME_LENGTH = 100
CONTENT_TRUNCATION_LIMIT = 500000  # ~500KB

# File and output configuration
DEFAULT_OUTPUT_FILE = "disaster_impact_report.xlsx"
EXCEL_MAX_COLUMN_WIDTH = 100
EXCEL_IMPACT_DETAILS_WIDTH = 100
EXCEL_URL_COLUMN_WIDTH = 45
EXCEL_SECTOR_COLUMN_WIDTH = 45
EXCEL_ROW_HEIGHT = 120

# Environment and credentials
ENV_FILE = ".env"
API_KEY_ENV_VAR = "api_key"
SEARCH_ENGINE_ID_ENV_VAR = "search_engine_id"

# Analysis configuration
DEFAULT_ANALYSIS_TIMEOUT = 30
MAX_ANALYSIS_TIMEOUT = 300  # 5 minutes
RELEVANCE_THRESHOLD = 0.3
SENTIMENT_ANALYSIS_ENABLED = True
NLP_ANALYSIS_ENABLED = True

# Date validation constants
MIN_VALID_YEAR = 1990
MAX_VALID_YEAR = 2030
DATE_UNKNOWN_PLACEHOLDER = "Date unknown"

# GUI configuration
GUI_WINDOW_TITLE = "Disaster Impact Analyzer"
GUI_DEFAULT_SIZE = "900x700"
GUI_MIN_SIZE = (900, 700)
GUI_LOG_HEIGHT = 15
GUI_PROGRESS_UPDATE_INTERVAL = 100  # milliseconds

# Logging configuration
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
LOG_LEVEL = "INFO"
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 5

# Cache configuration
ENABLE_CACHING = True
CACHE_TTL_SECONDS = 3600  # 1 hour
MAX_CACHE_SIZE = 1000

# Security settings
ALLOWED_URL_SCHEMES = ["http", "https"]
MAX_REDIRECT_FOLLOWS = 5
SSL_VERIFY = True

# Performance settings
MAX_CONCURRENT_REQUESTS = 10
ASYNC_BATCH_SIZE = 5
RATE_LIMIT_REQUESTS_PER_MINUTE = 60

# Error handling configuration
MAX_ERROR_RETRY_ATTEMPTS = 3
ERROR_BACKOFF_FACTOR = 2
CIRCUIT_BREAKER_THRESHOLD = 5
CIRCUIT_BREAKER_TIMEOUT = 60

# Content extraction settings
PAYWALL_DETECTION_ENABLED = True
JAVASCRIPT_RENDERING_TIMEOUT = 45000  # milliseconds
CONTENT_QUALITY_THRESHOLD = 0.4

# Sector keyword mappings for content analysis
SECTOR_KEYWORDS: Dict[str, List[str]] = {
    "Chemical": [
        "chemical",
        "chemicals",
        "chlorine",
        "petroleum",
        "hazardous material",
        "chemical plant",
        "chemical facility",
        "chemical industry",
        "toxic",
        "spill",
        "hazmat",
        "refinery",
    ],
    "Commercial Facilities": [
        "mall",
        "stadium",
        "arena",
        "hotel",
        "convention center",
        "commercial building",
        "shopping center",
        "theme park",
        "commercial property",
        "retail",
        "casino",
        "resort",
        "entertainment venue",
    ],
    "Communications": [
        "communications",
        "telecommunication",
        "network",
        "cellular",
        "internet",
        "phone",
        "broadband",
        "wireless",
        "infrastructure",
        "outage",
        "service",
        "cell tower",
        "fiber optic",
        "telecom",
        "ISP",
        "coverage",
        "signal",
        "telephony",
    ],
    "Critical Manufacturing": [
        "manufacturing",
        "factory",
        "plant",
        "industrial",
        "production facility",
        "assembly",
        "fabrication",
        "machinery",
        "supply chain",
        "logistics",
        "shutdown",
    ],
    "Dams": [
        "dam",
        "reservoir",
        "hydroelectric",
        "levee",
        "flood control",
        "water management",
        "hydropower",
        "spillway",
        "overflow",
        "dam failure",
        "sluice gate",
    ],
    "Emergency Services": [
        "emergency",
        "first responder",
        "police",
        "fire department",
        "ambulance",
        "paramedic",
        "rescue",
        "emergency management",
        "dispatch",
        "response time",
        "incident command",
    ],
    "Information Technology": [
        "it infrastructure",
        "data center",
        "server",
        "cloud",
        "computing",
        "cyber",
        "information system",
        "it service",
        "system failure",
        "IT outage",
        "database",
        "network down",
        "server crash",
    ],
    "Nuclear": [
        "nuclear",
        "reactor",
        "radioactive",
        "nuclear power",
        "nuclear plant",
        "nuclear facility",
        "nuclear waste",
        "nuclear material",
        "meltdown",
        "containment",
        "radiation leak",
        "coolant failure",
    ],
    "Transportation": [
        "transportation",
        "airport",
        "seaport",
        "highway",
        "railway",
        "railroad",
        "transit",
        "bridge",
        "road",
        "train",
        "bus",
        "subway",
        "tunnel",
        "runway",
        "port",
        "ferry",
        "transport hub",
        "logistics network",
    ],
    "Government Facilities": [
        "government",
        "federal building",
        "courthouse",
        "military base",
        "public building",
        "municipal building",
        "state building",
        "embassy",
        "capitol",
        "administrative office",
    ],
    "Energy": [
        "energy",
        "power plant",
        "electricity",
        "utility",
        "grid",
        "power outage",
        "power line",
        "transformer",
        "substation",
        "gas",
        "oil",
        "natural gas",
        "pipeline",
        "refinery",
        "blackout",
        "brownout",
        "energy disruption",
        "load shedding",
        "generation",
        "solar farm",
    ],
    "Water": [
        "water",
        "wastewater",
        "sewage",
        "drinking water",
        "water treatment",
        "water utility",
        "water infrastructure",
        "water system",
        "boil notice",
        "distribution system",
        "pumping station",
        "aquifer",
    ],
    "Defense": [
        "defense",
        "military",
        "contractor",
        "weapons",
        "defense contractor",
        "defense industry",
        "armament",
        "military equipment",
        "munition",
        "arsenal",
        "warfighter",
        "command center",
        "DoD",
    ],
    "Financial": [
        "bank",
        "financial",
        "atm",
        "credit union",
        "stock market",
        "financial services",
        "financial institution",
        "treasury",
        "payment system",
        "banking outage",
        "SWIFT",
        "transaction delay",
    ],
    "Healthcare": [
        "healthcare",
        "hospital",
        "clinic",
        "medical",
        "pharmacy",
        "health system",
        "medical facility",
        "medical center",
        "public health",
        "ICU",
        "ER",
        "medical staff",
        "patient care",
        "triage",
        "infection control",
    ],
    "Food and Agriculture": [
        "agriculture",
        "farm",
        "food",
        "crop",
        "livestock",
        "farming",
        "food processing",
        "food production",
        "food supply",
        "food recall",
        "distribution center",
        "supply chain disruption",
        "processing plant",
    ],
}

# Disaster-specific search term mappings
DISASTER_SPECIFIC_TERMS: Dict[str, List[str]] = {
    "hurricane": [
        "storm",
        "cyclone",
        "wind",
        "flooding",
        "storm surge",
        "tropical storm",
        "gale",
    ],
    "earthquake": [
        "quake",
        "tremor",
        "seismic",
        "richter",
        "aftershock",
        "epicenter",
        "fault line",
    ],
    "flood": [
        "flooding",
        "inundation",
        "water level",
        "submerged",
        "flash flood",
        "overflow",
        "levee breach",
    ],
    "fire": [
        "wildfire",
        "blaze",
        "burn",
        "smoke",
        "firestorm",
        "embers",
        "evacuation order",
    ],
    "tornado": ["twister", "wind", "funnel cloud", "supercell", "rotation", "EF scale"],
    "tsunami": [
        "tidal wave",
        "sea surge",
        "ocean",
        "wave height",
        "undersea quake",
        "run-up",
        "tsunami warning",
    ],
    "volcanic eruption": [
        "volcano",
        "ash",
        "lava",
        "magma",
        "pyroclastic",
        "eruption",
        "volcanic gas",
    ],
    "drought": [
        "dry",
        "water shortage",
        "arid",
        "crop failure",
        "water rationing",
        "heatwave",
    ],
    "landslide": [
        "mudslide",
        "rockslide",
        "debris flow",
        "slope failure",
        "land movement",
        "unstable terrain",
    ],
    "winter storm": [
        "blizzard",
        "snow",
        "ice",
        "freezing",
        "whiteout",
        "frostbite",
        "sleet",
        "wind chill",
    ],
}

# Generic disaster-related terms for fallback
GENERIC_DISASTER_TERMS: List[str] = [
    "disaster",
    "emergency",
    "catastrophe",
    "crisis",
    "impact",
    "damage",
    "affected",
    "incident",
    "hazard",
    "disruption",
    "devastation",
    "event",
    "outage",
    "evacuation",
    "response",
    "rescue",
    "fatalities",
    "casualties",
    "recovery",
]

# US location keywords for geographic filtering
US_LOCATION_KEYWORDS: List[str] = [
    "united states",
    "u.s.",
    " us ",
    "america",
    "american",
]

# Known paywall sites (for content extraction optimization)
PAYWALL_SITES: List[str] = [
    "nytimes.com",
    "wsj.com",
    "ft.com",
    "washingtonpost.com",
    "economist.com",
    "bloomberg.com",
    "barrons.com",
    "scientificamerican.com",
    "thetimes.co.uk",
    "newyorker.com",
    "theatlantic.com",
    "foreignpolicy.com",
    "wired.com",
    "hbr.org",
    "forbes.com",
    "medium.com",
]

# Content quality indicators
IMPACT_KEYWORDS: List[str] = [
    "damage",
    "destroy",
    "disable",
    "disrupt",
    "interrupt",
    "cut off",
    "knock out",
    "take down",
    "impair",
    "affect",
    "hinder",
    "block",
    "cripple",
    "sever",
    "wipe out",
    "shut down",
    "fail",
    "collapse",
    "breakdown",
]

RECOVERY_KEYWORDS: List[str] = [
    "restore",
    "repair",
    "rebuild",
    "recovery",
    "fix",
    "resume",
    "reconnect",
    "reestablish",
    "operational",
    "working",
    "back online",
    "service restored",
]


# Environment-specific configuration
def get_env_config() -> Dict[str, Union[str, bool, int]]:
    """
    Get environment-specific configuration values.

    Returns:
        Dictionary of environment configuration
    """
    return {
        "api_key": os.getenv(API_KEY_ENV_VAR, ""),
        "search_engine_id": os.getenv(SEARCH_ENGINE_ID_ENV_VAR, ""),
        "log_level": os.getenv("LOG_LEVEL", LOG_LEVEL),
        "enable_caching": os.getenv("ENABLE_CACHING", str(ENABLE_CACHING)).lower()
        == "true",
        "max_results": int(os.getenv("MAX_RESULTS", str(DEFAULT_MAX_RESULTS))),
    }


def validate_config() -> bool:
    """
    Validate that required configuration is present and valid.

    Returns:
        True if configuration is valid, False otherwise
    """
    env_config = get_env_config()

    # Check required API credentials
    if not env_config["api_key"]:
        print(f"Warning: {API_KEY_ENV_VAR} not set in environment")
        return False

    if not env_config["search_engine_id"]:
        print(f"Warning: {SEARCH_ENGINE_ID_ENV_VAR} not set in environment")
        return False

    # Validate numeric settings
    try:
        max_results = env_config["max_results"]
        if isinstance(max_results, int) and not (
            1 <= max_results <= MAX_SEARCH_RESULTS
        ):
            print(f"Warning: MAX_RESULTS must be between 1 and {MAX_SEARCH_RESULTS}")
            return False
    except (ValueError, TypeError):
        print("Warning: MAX_RESULTS must be a valid integer")
        return False

    return True


# Export all configuration constants and functions
__all__ = [
    # Application metadata
    "APP_NAME",
    "APP_VERSION",
    "APP_AUTHOR",
    "APP_DESCRIPTION",
    # Sector definitions
    "PRIORITY_1_SECTORS",
    "PRIORITY_2_SECTORS",
    "ALL_SECTORS",
    "DEFAULT_TARGET_SECTORS",
    # Disaster types
    "DISASTER_TYPES",
    # API configuration
    "DEFAULT_MAX_RESULTS",
    "MAX_SEARCH_RESULTS",
    "GOOGLE_SEARCH_URL",
    "MAX_RESULTS_PER_REQUEST",
    "REQUEST_TIMEOUT_SECONDS",
    # Content processing
    "MAX_CONTENT_LENGTH",
    "MIN_ARTICLE_LENGTH",
    "MIN_DISASTER_NAME_LENGTH",
    "MAX_DISASTER_NAME_LENGTH",
    # File configuration
    "DEFAULT_OUTPUT_FILE",
    "EXCEL_MAX_COLUMN_WIDTH",
    # Analysis settings
    "DEFAULT_ANALYSIS_TIMEOUT",
    "RELEVANCE_THRESHOLD",
    "SENTIMENT_ANALYSIS_ENABLED",
    # GUI configuration
    "GUI_WINDOW_TITLE",
    "GUI_DEFAULT_SIZE",
    "GUI_MIN_SIZE",
    # Keywords and mappings
    "SECTOR_KEYWORDS",
    "DISASTER_SPECIFIC_TERMS",
    "GENERIC_DISASTER_TERMS",
    "US_LOCATION_KEYWORDS",
    "IMPACT_KEYWORDS",
    "RECOVERY_KEYWORDS",
    # Functions
    "get_env_config",
    "validate_config",
]
