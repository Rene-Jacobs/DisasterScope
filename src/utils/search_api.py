# src/utils/search_api.py
"""
Google Custom Search API integration for disaster impact analysis.

This module handles communication with Google's Custom Search API to find
relevant articles about disaster impacts on critical infrastructure sectors.
It includes intelligent filtering to identify articles that contain meaningful
information about communications and infrastructure impacts.

Functions:
    search_articles: Main function to search for disaster-related articles
    is_relevant_article: Determines article relevance based on content analysis
"""

# Standard library imports
from typing import Dict, List, Optional
from urllib.parse import urlparse

# Third-party imports
import requests

# Constants for search configuration
DEFAULT_SECTORS = ["Communications"]
MAX_RESULTS_PER_REQUEST = 10
MAX_SEARCH_REQUESTS = 3
DEFAULT_MAX_RESULTS = 30
REQUEST_TIMEOUT = 30

# Disaster-specific search terms for improved relevance
DISASTER_SPECIFIC_TERMS = {
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
GENERIC_DISASTER_TERMS = [
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
US_KEYWORDS = ["united states", "u.s.", " us ", "america", "american"]


def search_articles(
    query: str,
    api_key: str,
    search_engine_id: str,
    sectors: Optional[List[str]] = None,
    max_results: int = DEFAULT_MAX_RESULTS,
    disaster_type: str = "Hurricane",
) -> List[Dict[str, str]]:
    """
    Search Google Custom Search API for disaster-related articles.

    Uses intelligent filtering to identify articles that contain relevant
    information about infrastructure impacts from disasters.

    Args:
        query: The search query string
        api_key: Google API key for Custom Search
        search_engine_id: Google Custom Search Engine ID
        sectors: List of infrastructure sectors to search for.
                Defaults to ['Communications'] if None provided.
        max_results: Maximum number of results to return (up to 100)
        disaster_type: Type of natural disaster being analyzed

    Returns:
        List of dictionaries containing article information with keys:
        - title: Article headline
        - link: Article URL
        - snippet: Article preview text
        - sectors: List of identified relevant sectors
        - disaster_type: Type of disaster

    Raises:
        Exception: If API request fails or returns error status
        ValueError: If invalid parameters are provided

    Example:
        >>> articles = search_articles(
        ...     "Hurricane Katrina effects on US communications infrastructure",
        ...     api_key="your_key",
        ...     search_engine_id="your_engine_id",
        ...     sectors=["Communications", "Energy"],
        ...     max_results=20,
        ...     disaster_type="Hurricane"
        ... )
        >>> print(f"Found {len(articles)} relevant articles")
    """
    # Input validation
    if not api_key or not search_engine_id:
        raise ValueError("API key and search engine ID are required")

    if not query.strip():
        raise ValueError("Search query cannot be empty")

    if max_results <= 0 or max_results > 100:
        raise ValueError("max_results must be between 1 and 100")

    # Default to Communications sector if none provided
    if not sectors:
        sectors = DEFAULT_SECTORS.copy()

    # API endpoint
    url = "https://www.googleapis.com/customsearch/v1"
    all_results = []

    print(f"Starting search for: {query}")
    print(f"Target sectors: {', '.join(sectors)}")
    print(f"Disaster type: {disaster_type}")

    # Google Custom Search returns max 10 results per request
    # Make multiple requests to get up to max_results
    start_indices = list(range(1, min(max_results + 1, 31), MAX_RESULTS_PER_REQUEST))

    for batch_num, start_index in enumerate(start_indices, 1):
        if len(all_results) >= max_results:
            break

        remaining_results = max_results - len(all_results)
        batch_size = min(MAX_RESULTS_PER_REQUEST, remaining_results)

        params = {
            "key": api_key,
            "cx": search_engine_id,
            "q": query,
            "num": batch_size,
            "start": start_index,
        }

        try:
            print(
                f"Fetching search results batch {batch_num} (starting at {start_index})..."
            )
            response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)

            if response.status_code != 200:
                error_msg = (
                    f"API request failed with status code {response.status_code}"
                )
                print(f"Error: {error_msg}")

                # Only break on error if we already have some results
                if start_index > 1 and all_results:
                    print("Continuing with results obtained so far...")
                    break
                else:
                    raise Exception(error_msg)

            data = response.json()

            # Check for API errors in response
            if "error" in data:
                error_info = data["error"]
                error_msg = (
                    f"Google API error: {error_info.get('message', 'Unknown error')}"
                )
                print(f"Error: {error_msg}")
                raise Exception(error_msg)

            # Check if we got any results
            if "items" not in data:
                print(f"No more results found in batch {batch_num}")
                break

            # Process this batch of results
            batch_relevant_count = 0
            for item in data.get("items", []):
                link = item.get("link", "")
                # Skip direct links to PDF files
                parsed_path = urlparse(link).path.lower()
                file_format = item.get("fileFormat", "").lower()
                mime_type = item.get("mime", "").lower()
                if (
                    parsed_path.endswith(".pdf")
                    or file_format == "pdf"
                    or mime_type == "application/pdf"
                ):
                    title_preview = item.get("title", "")[:60]
                    print(f"✗ Skipping PDF file: {title_preview}...")
                    continue

                # Check if this is a relevant article before adding
                identified_sectors = _is_relevant_article(
                    item, query, sectors, disaster_type
                )

                if identified_sectors:
                    result = {
                        "title": item.get("title", ""),
                        "link": item.get("link", ""),
                        "snippet": item.get("snippet", ""),
                        "sectors": identified_sectors,
                        "disaster_type": disaster_type,
                    }
                    all_results.append(result)
                    batch_relevant_count += 1

                    # Print progress for relevant articles
                    title_preview = item.get("title", "")[:60]
                    print(
                        f"✓ Found relevant article for {identified_sectors}: {title_preview}..."
                    )
                else:
                    # Print skipped articles for debugging
                    title_preview = item.get("title", "")[:60]
                    print(f"✗ Skipping irrelevant article: {title_preview}...")

            print(f"Batch {batch_num}: Found {batch_relevant_count} relevant articles")

        except requests.RequestException as e:
            error_msg = f"Network error in batch {batch_num}: {str(e)}"
            print(f"Error: {error_msg}")

            # Only break on error if we already have some results
            if start_index > 1 and all_results:
                print("Continuing with results obtained so far...")
                break
            else:
                raise Exception(error_msg)

        except Exception as e:
            error_msg = f"Error fetching batch {batch_num}: {str(e)}"
            print(f"Error: {error_msg}")

            # Only break on error if we already have some results
            if start_index > 1 and all_results:
                print("Continuing with results obtained so far...")
                break
            else:
                raise

    print(f"Search completed. Total relevant articles found: {len(all_results)}")
    return all_results[:max_results]  # Ensure we don't return more than requested


def _is_relevant_article(
    item: Dict, query: str, sectors: List[str], disaster_type: str
) -> List[str]:
    """
    Determine if an article is relevant based on content analysis.

    Analyzes the article's title and snippet to identify relevance to
    disaster impacts on infrastructure sectors.

    Args:
        item: Article data from Google API containing title, link, snippet
        query: The original search query
        sectors: List of target infrastructure sectors
        disaster_type: Type of natural disaster

    Returns:
        List of identified sectors in the article, or empty list if not relevant

    Note:
        This is a private function used internally by search_articles.
        The relevance algorithm checks for:
        1. Disaster name/type mentions
        2. Infrastructure/sector-specific keywords
        3. US geographic references (if specified in query)
        4. Impact-related terminology
    """
    # Extract the important parts of the article preview
    title = item.get("title", "").lower()
    snippet = item.get("snippet", "").lower()
    combined_text = f"{title} {snippet}"

    # Get the main keywords from our query
    query_parts = query.lower().split()

    # Look for disaster name (assuming it's the first word in the query)
    disaster_name = query_parts[0] if query_parts else ""

    # Article must mention the disaster name or be clearly disaster-related
    if disaster_name and disaster_name not in combined_text:
        # If no specific disaster name, check for disaster type or generic terms
        if not _has_disaster_indicators(combined_text, disaster_type):
            return []

    # Check for US references if it was part of the query
    if any(us_term in query.lower() for us_term in ["us", "u.s.", "united states"]):
        if not _has_us_references(combined_text):
            return []

    # Check which sectors are mentioned in the article
    identified_sectors = _identify_sectors_in_text(combined_text, sectors)

    return identified_sectors


def _has_disaster_indicators(text: str, disaster_type: str) -> bool:
    """Check if text contains disaster-related indicators."""
    disaster_type_lower = disaster_type.lower()

    # Check for specific disaster type
    if disaster_type_lower in text:
        return True

    # Check for disaster-specific terms
    specific_terms = DISASTER_SPECIFIC_TERMS.get(disaster_type_lower, [])
    if any(term in text for term in specific_terms):
        return True

    # Check for generic disaster terms
    if any(term in text for term in GENERIC_DISASTER_TERMS):
        return True

    return False


def _has_us_references(text: str) -> bool:
    """Check if text contains US geographic references."""
    return any(keyword in text for keyword in US_KEYWORDS)


def _identify_sectors_in_text(text: str, target_sectors: List[str]) -> List[str]:
    """Identify which infrastructure sectors are mentioned in the text."""
    # Comprehensive sector keyword mapping
    sector_keywords = {
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

    identified_sectors = []

    for sector in target_sectors:
        if sector in sector_keywords:
            keywords = sector_keywords[sector]
            if any(keyword in text for keyword in keywords):
                identified_sectors.append(sector)

    return identified_sectors


# Legacy function name for backward compatibility
is_relevant_article = _is_relevant_article

__all__ = [
    "search_articles",
    "is_relevant_article",  # Backward compatibility
    "DEFAULT_SECTORS",
    "DISASTER_SPECIFIC_TERMS",
    "GENERIC_DISASTER_TERMS",
]
# End of src/utils/search_api.py
