"""
Simplified Impact Analyzer Module for Disaster Impact Analysis System

This module focuses on extracting and analyzing impact details from article content,
specifically related to how disasters affect critical infrastructure.
"""

import re
import logging
from typing import Dict, List, Set, Optional, Any, Union
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def calculate_sentiment(text: str) -> float:
    """
    Calculate sentiment score for impact information.

    Args:
        text: Text to analyze

    Returns:
        Sentiment score between -1.0 (negative) and 1.0 (positive)
    """
    # Simple rule-based sentiment analysis
    positive_words = [
        "restored",
        "recovery",
        "repair",
        "rebuild",
        "progress",
        "improving",
        "resolved",
        "successful",
        "working",
        "operational",
        "fixed",
        "resumed",
        "reestablished",
        "reconnected",
        "responding",
        "rescue",
        "saved",
        "helping",
        "aid",
        "assistance",
        "resilient",
        "prepared",
        "minimized",
    ]

    negative_words = [
        "outage",
        "down",
        "failure",
        "damaged",
        "destroyed",
        "disrupted",
        "collapsed",
        "interrupted",
        "critical",
        "severe",
        "disaster",
        "catastrophic",
        "devastating",
        "emergency",
        "crisis",
        "dangerous",
        "threatened",
        "loss",
        "casualties",
        "fatalities",
        "trapped",
        "stranded",
        "suffering",
        "widespread",
    ]

    # Count occurrences
    text_lower = text.lower()
    positive_count = sum(1 for word in positive_words if word in text_lower)
    negative_count = sum(1 for word in negative_words if word in text_lower)

    # Calculate sentiment score
    total = positive_count + negative_count
    if total == 0:
        return 0.0

    return (positive_count - negative_count) / total


def extract_structured_impact_details(text: str) -> Dict:
    """
    Extract structured impact details from article text.

    Args:
        text: The article content or relevant paragraphs

    Returns:
        Dictionary containing categorized impact information
    """
    # Initialize impact structure
    impact_structure = {
        "affected_services": set(),
        "affected_areas": set(),
        "impact_type": set(),
        "duration": None,
        "scale": None,
        "restoration_efforts": None,
    }

    # Lowercase text for consistent matching
    text_lower = text.lower()

    # Extract affected services
    service_patterns = {
        "cellular": [
            r"\bcellular( network| service| tower| communication)?s?\b",
            r"\bcell( service| tower| network)?s?\b",
            r"\bmobile( network| service)?s?\b",
            r"\b(4G|5G)( network| service)?\b",
            r"\bwireless (network|communication|service)s?\b",
        ],
        "internet": [
            r"\binternet( service| connection| access)?s?\b",
            r"\bbroadband\b",
            r"\b(fiber optic|cable)( connection| internet)?\b",
            r"\bDSL( internet| service)?\b",
            r"\bslow internet\b",
            r"\bconnectivity (issue|problem)s?\b",
            r"\bno internet\b",
        ],
        "landline": [
            r"\blandline(s)?\b",
            r"\b(phone|telephone)( line| service)?s?\b",
            r"\bwired( phone| telephone)?s?\b",
            r"\bplain old telephone service\b",
            r"\bPOTS\b",
            r"\bvoice line(s)?\b",
        ],
        "satellite": [
            r"\bsatellite( (communication|service|phone|internet))?s?\b",
            r"\bsatellite (down|outage|failure)\b",
        ],
        "emergency communications": [
            r"\bemergency (communications|services|systems)\b",
            r"\b911 service\b",
            r"\bemergency responder (communications|systems)\b",
            r"\bpublic safety network\b",
            r"\bfirst responder communication(s)?\b",
            r"\bemergency dispatch\b",
        ],
        "telecommunications": [
            r"\btelecommunications( infrastructure| system| network)?s?\b",
            r"\btelecom(s)?\b",
            r"\btelco\b",
        ],
        "data centers": [
            r"\bdata center(s)?\b",
            r"\bserver (farm|center)s?\b",
            r"\bdata (hub|facility)\b",
            r"\bserver outage\b",
            r"\bhosting facility\b",
        ],
        "broadcasting": [
            r"\b(television|radio|tv)( broadcast| station)?s?\b",
            r"\bbroadcast tower\b",
            r"\btransmission failure\b",
            r"\bbroadcast interruption\b",
            r"\bTV outage\b",
        ],
        "power systems": [
            r"\bpower (outage|failure|interruption)s?\b",
            r"\belectrical grid\b",
            r"\butility outage\b",
        ],
    }

    for service, patterns in service_patterns.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                impact_structure["affected_services"].add(service)

    # Extract affected areas (simple US location extraction)
    us_locations = [
        "alabama",
        "alaska",
        "arizona",
        "arkansas",
        "california",
        "colorado",
        "connecticut",
        "delaware",
        "florida",
        "georgia",
        "hawaii",
        "idaho",
        "illinois",
        "indiana",
        "iowa",
        "kansas",
        "kentucky",
        "louisiana",
        "maine",
        "maryland",
        "massachusetts",
        "michigan",
        "minnesota",
        "mississippi",
        "missouri",
        "montana",
        "nebraska",
        "nevada",
        "new hampshire",
        "new jersey",
        "new mexico",
        "new york",
        "north carolina",
        "north dakota",
        "ohio",
        "oklahoma",
        "oregon",
        "pennsylvania",
        "rhode island",
        "south carolina",
        "south dakota",
        "tennessee",
        "texas",
        "utah",
        "vermont",
        "virginia",
        "washington",
        "west virginia",
        "wisconsin",
        "wyoming",
        "district of columbia",
        "new york city",
        "los angeles",
        "chicago",
        "houston",
        "phoenix",
        "philadelphia",
        "san antonio",
        "san diego",
        "dallas",
        "san jose",
        "austin",
        "jacksonville",
        "fort worth",
        "columbus",
        "charlotte",
        "san francisco",
        "indianapolis",
        "seattle",
        "denver",
        "boston",
        "miami",
        "new orleans",
        "tampa",
        "orlando",
    ]

    for location in us_locations:
        location_pattern = r"\b" + location.replace(" ", r"\s+") + r"\b"
        if re.search(location_pattern, text_lower):
            impact_structure["affected_areas"].add(location.title())

    # Extract type of impact
    impact_types = {
        "outage": [
            r"\boutage(s)?\b",
            r"\b(service|system|network) (down|offline)\b",
            r"\b(disruption|interruption|unavailable)\b",
            r"\bfailure(s)?\b",
        ],
        "damage": [
            r"\bdamage(d|s)?\b",
            r"\bdestroy(ed|s)?\b",
            r"\bbroken\b",
            r"\bdestruction\b",
            r"\bcracked\b",
            r"\bfracture(d)?\b",
            r"\bcollapse(d)?\b",
        ],
        "degraded service": [
            r"\bslow (internet|connection|response)\b",
            r"\bspotty (service|connection)\b",
            r"\bintermittent (service|signal|connectivity)\b",
            r"\bdegraded (performance|service)\b",
            r"\bpoor (service|connection|performance)\b",
            r"\blatency issues\b",
        ],
        "infrastructure failure": [
            r"\binfrastructure (failure|collapse|damage)\b",
            r"\btower (collapse|failure|down(ed)?)\b",
            r"\bline(s)? (down|damaged|cut|severed)\b",
            r"\bbackbone (failure|damage)\b",
            r"\bnetwork equipment failure\b",
        ],
        "power related": [
            r"\bpower (outage|loss|failure|cut|interruption)\b",
            r"\blost power\b",
            r"\bno electricity\b",
            r"\belectric(ity)? (failure|issue|outage|cut)\b",
        ],
    }

    for impact, patterns in impact_types.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                impact_structure["impact_type"].add(impact)

    # Try to extract duration information
    duration_patterns = [
        r"\blast(ed|ing)? (\d+|\w+)?\s?(hour|day|week|month)s?\b",
        r"\b(outage|disruption|service loss) (of|for) (\d+|\w+)?\s?(hour|day|week|month)s?\b",
        r"\b(without|lost|lacking) (service|connection|communication) for (\d+|\w+)?\s?(hour|day|week|month)s?\b",
        r"\b(restore|restored|restoring)\s+(service|connection|communication)\s+(after|within|in)\s+(\d+|\w+)?\s?(hour|day|week|month)s?\b",
        r"\b(remain|remained|remaining)\s+(down|offline|disrupted)\s+(for|over|about|approximately)?\s*(\d+|\w+)?\s?(hour|day|week|month)s?\b",
    ]

    for pattern in duration_patterns:
        duration_matches = re.search(pattern, text_lower)
        if duration_matches:
            impact_structure["duration"] = duration_matches.group(0)
            break

    # Try to extract scale information
    scale_patterns = [
        r"\b(\d+)(\s?(thousand|million|billion))?\s+(people|residents|customers|homes|households)\s+(affected|impacted|without (power|service|communication))\b",
        r"\baffecting\s+(\d+)(\s?(thousand|million|billion))?\s+(people|residents|customers|homes|households)\b",
        r"\b(up to|around|approximately)?\s?(\d+)%\s+of\s+(people|residents|customers|homes|households|the population|the area)\b",
    ]

    for pattern in scale_patterns:
        scale_matches = re.search(pattern, text_lower)
        if scale_matches:
            impact_structure["scale"] = scale_matches.group(0)
            break

    # Try to extract restoration efforts
    restoration_patterns = [
        r"\b(restoration|repair)( efforts| work| crews)?\b",
        r"\b(emergency|rapid) (restoration|repair)\b",
        r"\bworking to (restore|repair|fix)\b",
        r"\bcrews (deployed|working|dispatched|mobilized)\b",
        r"\btemporary (service|solution|fix|restoration)\b",
    ]

    for pattern in restoration_patterns:
        restoration_matches = re.search(pattern, text_lower)
        if restoration_matches:
            # Find the sentence containing this match
            sentences = text.split(".")
            for sentence in sentences:
                if restoration_matches.group(0) in sentence.lower():
                    impact_structure["restoration_efforts"] = sentence.strip()
                    break
            break

    # Convert sets to sorted lists for better output
    for key in ["affected_services", "affected_areas", "impact_type"]:
        impact_structure[key] = sorted(list(impact_structure[key]))

    return impact_structure


def format_structured_impact(impact_structure: Dict) -> str:
    """
    Format the structured impact details into a readable string.

    Args:
        impact_structure: Dictionary containing categorized impact information

    Returns:
        str: Formatted impact information
    """
    formatted_sections = []

    # Affected Services
    if impact_structure["affected_services"]:
        services_str = ", ".join(impact_structure["affected_services"])
        formatted_sections.append(f"Affected Services: {services_str}")

    # Affected Areas
    if impact_structure["affected_areas"]:
        areas_str = ", ".join(impact_structure["affected_areas"])
        formatted_sections.append(f"Affected Areas: {areas_str}")

    # Impact Type
    if impact_structure["impact_type"]:
        impact_str = ", ".join(impact_structure["impact_type"])
        formatted_sections.append(f"Impact Type: {impact_str}")

    # Scale (if available)
    if impact_structure["scale"]:
        formatted_sections.append(f"Scale: {impact_structure['scale']}")

    # Duration (if available)
    if impact_structure["duration"]:
        formatted_sections.append(f"Duration: {impact_structure['duration']}")

    # Restoration Efforts (if available)
    if impact_structure["restoration_efforts"]:
        formatted_sections.append(
            f"Restoration Efforts: {impact_structure['restoration_efforts']}"
        )

    # Join all sections with newlines
    return "\n".join(formatted_sections)


async def extract_impact_details_with_nlp(
    main_content: Any, domain: str, disaster_type: str, full_text: str
) -> Optional[Any]:
    """
    Simplified impact details extraction without heavy NLP dependencies.

    Args:
        main_content: HTML parser object containing the main content
        domain: Domain of the website
        disaster_type: Type of disaster being analyzed
        full_text: Full text of the article

    Returns:
        ImpactInfo object or None
    """
    from .analyzer_models import ImpactInfo

    try:
        # Get text content
        if main_content and hasattr(main_content, "text"):
            content_text = main_content.text()
        else:
            content_text = full_text

        if not content_text or len(content_text.strip()) < 100:
            logger.warning("No substantial text content found for impact analysis")
            return None

        # Create ImpactInfo object
        impact_info = ImpactInfo()

        # Extract structured impact details
        impact_structure = extract_structured_impact_details(content_text)

        # Populate the ImpactInfo object
        if impact_structure["affected_services"]:
            impact_info.affected_services = impact_structure["affected_services"]

        if impact_structure["affected_areas"]:
            impact_info.affected_areas = impact_structure["affected_areas"]

        if impact_structure["impact_type"]:
            impact_info.impact_types = impact_structure["impact_type"]

        if impact_structure["duration"]:
            impact_info.duration = impact_structure["duration"]

        if impact_structure["scale"]:
            impact_info.scale = impact_structure["scale"]

        if impact_structure["restoration_efforts"]:
            impact_info.restoration_efforts = impact_structure["restoration_efforts"]

        # Set raw content (limit to reasonable size)
        impact_info.raw_content = (
            content_text[:2000] if len(content_text) > 2000 else content_text
        )

        logger.info(
            f"Extracted impact details: {len(impact_info.affected_services)} services, {len(impact_info.affected_areas)} areas"
        )

        return impact_info

    except Exception as e:
        logger.error(f"Error in simplified impact extraction: {e}")
        return None


__all__ = [
    "calculate_sentiment",
    "extract_structured_impact_details",
    "format_structured_impact",
    "extract_impact_details_with_nlp",
]
