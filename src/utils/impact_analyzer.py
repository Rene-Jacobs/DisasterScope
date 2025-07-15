"""
Impact Analyzer Module for Disaster Impact Analysis System

This module focuses on extracting and analyzing impact details from article content,
specifically related to how disasters affect critical infrastructure.
"""

import re
import logging
from typing import Dict, List, Set, Optional, Any, Union
from collections import defaultdict
import nltk
from nltk.tokenize import sent_tokenize

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Ensure NLTK data is available
try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt", quiet=True)


def safe_sent_tokenize(text):
    """
    A safer version of sentence tokenization that falls back to regex if NLTK fails.

    Args:
        text: Text to tokenize into sentences

    Returns:
        List of sentences
    """
    try:
        # Try standard NLTK tokenization first
        return sent_tokenize(text)
    except LookupError:
        # If that fails, try to download punkt
        try:
            nltk.download("punkt", quiet=True)
            return sent_tokenize(text)
        except:
            # If both fail, use a simple regex
            # Simple regex-based sentence splitter
            return re.split(r"(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s", text)


async def extract_impact_details_with_nlp(
    main_content, domain, disaster_type, full_text
) -> Dict:
    """
    Extract impact details with NLP enhancements.

    Args:
        main_content: HTML parser object containing the main content
        domain: Domain of the website
        disaster_type: Type of disaster being analyzed
        full_text: Full text of the article

    Returns:
        Dictionary containing structured impact data
    """
    from .analyzer_models import ImpactInfo

    impact_info = ImpactInfo()

    # Get text content
    if main_content:
        content_text = main_content.text()
    else:
        content_text = full_text

    if not content_text:
        logger.warning("No text content found for NLP analysis")
        return impact_info

    # Use NLP to process the text
    try:
        import spacy

        try:
            nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("SpaCy model not found. Downloading model...")
            spacy.cli.download("en_core_web_sm")
            nlp = spacy.load("en_core_web_sm")

        doc = nlp(content_text[:10000])  # Limit to avoid processing too much text

        # Extract locations (geographic areas affected)
        locations = set()
        for ent in doc.ents:
            if ent.label_ in ["GPE", "LOC"]:
                locations.add(ent.text)
        impact_info.affected_areas = list(locations)
    except Exception as e:
        logger.warning(f"Failed to use spaCy for NLP analysis: {e}")
        # Fallback: Use regex to find known US states and cities
        areas = extract_affected_areas_regex(content_text)
        impact_info.affected_areas = list(areas)

    # Extract impact details using multiple methods
    # 1. Basic keyword approach
    comm_systems_keywords = [
        "cellular tower",
        "cell tower",
        "base station",
        "transmission tower",
        "fiber optic",
        "cable",
        "landline",
        "phone line",
        "telephone pole",
        "data center",
        "server farm",
        "switching station",
        "5g",
        "4g",
        "3g",
        "satellite",
        "microwave relay",
        "radio tower",
        "emergency communication",
        "broadcast tower",
        "network hub",
        "telecom infrastructure",
        "internet provider",
        "connectivity equipment",
        "telecommunications center",
    ]

    providers_keywords = [
        "at&t",
        "verizon",
        "t-mobile",
        "sprint",
        "comcast",
        "xfinity",
        "cox",
        "charter",
        "spectrum",
        "centurylink",
        "frontier",
        "dish network",
        "directv",
        "hughes",
        "starlink",
        "fcc",
    ]

    impact_verbs = [
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
        "submerge",
        "burn",
        "inundate",
        "collapse",
        "bury",
        "freeze",
        "blow away",
        "topple",
        "shatter",
        "erode",
        "demolish",
    ]

    impact_nouns = [
        "outage",
        "blackout",
        "downtime",
        "disruption",
        "interruption",
        "failure",
        "breakdown",
        "collapse",
        "malfunction",
        "damage",
        "destruction",
        "loss of service",
        "power loss",
        "flooding",
        "fire damage",
        "earthquake damage",
        "storm damage",
        "wind damage",
        "water damage",
        "eruption damage",
        "ash fall",
        "avalanche",
        "debris flow",
        "drought impact",
        "surge",
        "blizzard effect",
    ]

    comm_services_keywords = [
        "internet",
        "phone service",
        "cell service",
        "cellular service",
        "broadband",
        "wifi",
        "wireless",
        "telecommunications",
        "communications",
        "911",
        "emergency services",
        "call",
        "text",
        "data service",
        "voice service",
        "mobile service",
        "internet access",
        "broadband connection",
        "satellite communication",
        "radio communication",
        "network connectivity",
        "cell coverage",
    ]

    # Find affected services
    affected_services = set()
    for service in comm_services_keywords + comm_systems_keywords:
        if service.lower() in content_text.lower():
            affected_services.add(service)
    impact_info.affected_services = list(affected_services)

    # Find impact types
    impact_types = set()
    for impact in impact_nouns:
        if impact.lower() in content_text.lower():
            impact_types.add(impact)
    impact_info.impact_types = list(impact_types)

    # Use NLP to extract sentences containing impact information
    impact_sentences = []

    # Tokenize text into sentences
    sentences = safe_sent_tokenize(content_text)

    # Find sentences containing impact information
    for sentence in sentences:
        sentence_lower = sentence.lower()
        if any(
            keyword in sentence_lower
            for keyword in comm_systems_keywords
            + providers_keywords
            + comm_services_keywords
        ):
            if any(verb in sentence_lower for verb in impact_verbs) or any(
                noun in sentence_lower for noun in impact_nouns
            ):
                impact_sentences.append(sentence)

    # Find duration information
    duration_patterns = [
        r"lasted (\w+\s)?(hour|day|week|month)s?",
        r"(hour|day|week|month)s? without (service|connection|communication)",
        r"outage of (\w+\s)?(hour|day|week|month)s?",
        r"restore\w+ (service|connection) (after|within|in) (\w+\s)?(hour|day|week|month)s?",
        r"remain\w+ down for (\w+\s)?(hour|day|week|month)s?",
    ]

    for pattern in duration_patterns:
        duration_matches = re.search(pattern, content_text, re.IGNORECASE)
        if duration_matches:
            impact_info.duration = duration_matches.group(0)
            break

    # Find scale information
    scale_patterns = [
        r"(\d+)( thousand| million| billion)? (people|residents|customers|homes|households) (affected|impacted|without service)",
        r"affecting (\d+)( thousand| million| billion)? (people|residents|customers|homes|households)",
        r"(\d+)% of (people|residents|customers|homes|households|the population|the area)",
    ]

    for pattern in scale_patterns:
        scale_matches = re.search(pattern, content_text, re.IGNORECASE)
        if scale_matches:
            impact_info.scale = scale_matches.group(0)
            break

    # Find restoration efforts
    restoration_patterns = [
        r"(restoration|repair) (efforts|work|crews)",
        r"working to restore",
        r"emergency (restoration|repair)",
        r"crews (deployed|working)",
        r"temporary (service|solution|fix)",
    ]

    for pattern in restoration_patterns:
        restoration_matches = re.search(pattern, content_text, re.IGNORECASE)
        if restoration_matches:
            # Extract the sentence containing restoration information
            for sentence in sentences:
                if restoration_matches.group(0) in sentence.lower():
                    impact_info.restoration_efforts = sentence.strip()
                    break

    # Set raw content from impact sentences
    if impact_sentences:
        impact_info.raw_content = "\n\n".join(impact_sentences)

    return impact_info


def extract_affected_areas_regex(text):
    """
    Extract affected geographic areas using regex patterns.

    Args:
        text: Article text

    Returns:
        Set of location names found
    """
    text_lower = text.lower()
    locations = set()

    # List of US states and major cities to look for
    states_and_cities = [
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

    for location in states_and_cities:
        location_pattern = r"\b" + location + r"\b"
        if re.search(location_pattern, text_lower):
            locations.add(location.title())  # Capitalize for output

    return locations


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
    positive_count = sum(1 for word in positive_words if word in text.lower())
    negative_count = sum(1 for word in negative_words if word in text.lower())

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

    # Extract affected areas (use the regex function)
    impact_structure["affected_areas"].update(extract_affected_areas_regex(text))

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
        "flooding impact": [
            r"\bflood(ed|ing)?\b",
            r"\bunderwater\b",
            r"\bsubmerged\b",
            r"\bwater damage\b",
            r"\bfloodwater\b",
            r"\brising water(s)?\b",
        ],
        "wind impact": [
            r"\bwind (damage|gust|impact)\b",
            r"\bblown (away|over|down)\b",
            r"\btoppled\b",
            r"\bgusts? up to\b",
            r"\bhigh winds\b",
        ],
        "access issues": [
            r"\binaccessible\b",
            r"\bblocked access\b",
            r"\bclosed (road|bridge|facility)\b",
            r"\bimpassable\b",
        ],
        "evacuation": [
            r"\bevacuate(d|ion)?\b",
            r"\bevacuating\b",
            r"\bdisplaced\b",
            r"\bforced to leave\b",
        ],
        "casualties": [
            r"\binjur(ed|ies)\b",
            r"\bfatalit(y|ies)\b",
            r"\bdeath(s)?\b",
            r"\bcasualt(y|ies)\b",
            r"\bmissing person(s)?\b",
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
        r"\bdowntime\s+(of|lasted)?\s*(\d+|\w+)?\s?(hour|day|week|month)s?\b",
        r"\b(no|lack of)\s+(access|connectivity|communication)\s+for\s+(\d+|\w+)?\s?(hour|day|week|month)s?\b",
    ]

    for pattern in duration_patterns:
        duration_matches = re.search(pattern, text_lower)
        if duration_matches:
            impact_structure["duration"] = duration_matches.group(0)
            break

    # Try to extract scale information (how many people/services affected)
    scale_patterns = [
        # Direct numeric expressions
        r"\b(\d+)(\s?(thousand|million|billion))?\s+(people|residents|customers|homes|households)\s+(affected|impacted|without (power|service|communication))\b",
        r"\baffecting\s+(\d+)(\s?(thousand|million|billion))?\s+(people|residents|customers|homes|households)\b",
        r"\b(leaving|left)\s+(\d+)(\s?(thousand|million|billion))?\s+(without|with no)\s+(power|service|communication)\b",
        r"\b(up to|around|approximately)?\s?(\d+)%\s+of\s+(people|residents|customers|homes|households|the population|the area)\b",
        # Word-based numerals
        r"\b(hundreds|thousands|millions)\s+of\s+(people|residents|customers|homes|households)\s+(affected|impacted|without (power|service|communication))\b",
        r"\bmore than\s+(\d+)(\s?(thousand|million|billion))?\s+(affected|impacted|displaced)\b",
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
        r"\b(power|service|connection) (being|was|has been)?\s?(restored|repaired)\b",
        r"\brestoration (underway|in progress|expected|complete|timeline)\b",
        r"\brepairs (ongoing|underway|in progress)\b",
        r"\brestored to (some|most|all) (areas|customers|residents|services)\b",
        r"\b(full|partial) restoration\b",
        r"\butilities (working|rushing|attempting) to restore\b",
        r"\b(make|bring) (repairs|restoration efforts)\b",
    ]

    for pattern in restoration_patterns:
        restoration_matches = re.search(pattern, text_lower)
        if restoration_matches:
            # Extract the sentence containing restoration information
            sentences = re.split(r"[.!?]", text)
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


def score_paragraph(paragraph: str, disaster_type: str) -> float:
    """
    Score a paragraph based on its relevance to communication impacts.

    Args:
        paragraph: Paragraph text to score
        disaster_type: Type of disaster being analyzed

    Returns:
        Relevance score (0.0 to 1.0)
    """
    paragraph_lower = paragraph.lower()
    score = 0.0

    # Keyword groups with weights
    keyword_groups = {
        "communication_systems": {
            "keywords": [
                "cellular",
                "tower",
                "cell",
                "network",
                "fiber",
                "cable",
                "landline",
                "phone",
                "broadband",
                "internet",
                "wifi",
                "telecommunications",
                "infrastructure",
                "service",
                "outage",
                "connection",
                "connectivity",
                "signal",
                "wireless",
                "5g",
                "4g",
                "data center",
                "satellite",
                "telco",
                "telecom",
            ],
            "weight": 0.4,
        },
        "impact_terms": {
            "keywords": [
                "outage",
                "down",
                "offline",
                "disruption",
                "interrupted",
                "damaged",
                "destroyed",
                "affected",
                "impact",
                "loss",
                "cut",
                "failure",
                "blackout",
                "disabled",
                "unavailable",
                "impaired",
                "hindered",
                "blocked",
                "crippled",
                "severed",
                "wiped out",
                "shut down",
                "failed",
                "collapsed",
                "broken",
            ],
            "weight": 0.3,
        },
        "disaster_terms": {
            "keywords": [
                disaster_type.lower(),
                "storm",
                "disaster",
                "emergency",
                "damage",
                "destruction",
                "flooding",
                "winds",
                "rain",
                "evacuation",
                "recovery",
                "response",
                "hit",
                "struck",
            ],
            "weight": 0.2,
        },
        "provider_terms": {
            "keywords": [
                "at&t",
                "verizon",
                "t-mobile",
                "sprint",
                "comcast",
                "xfinity",
                "cox",
                "charter",
                "spectrum",
                "provider",
                "company",
                "isp",
                "carrier",
            ],
            "weight": 0.1,
        },
    }

    # Calculate score based on keyword presence
    for group, info in keyword_groups.items():
        group_score = 0
        for keyword in info["keywords"]:
            if keyword in paragraph_lower:
                group_score += 1

        # Normalize by number of keywords and apply weight
        if info["keywords"]:
            normalized_score = min(group_score / len(info["keywords"]), 1.0)
            score += normalized_score * info["weight"]

    return score


def find_high_impact_paragraphs(
    paragraphs: List[str], disaster_type: str, threshold: float = 0.3
) -> List[str]:
    """
    Identify paragraphs with high impact relevance.

    Args:
        paragraphs: List of paragraph texts
        disaster_type: Type of disaster being analyzed
        threshold: Minimum score to consider as high impact

    Returns:
        List of high-impact paragraphs
    """
    high_impact_paragraphs = []

    for paragraph in paragraphs:
        if len(paragraph) < 40:  # Skip very short paragraphs
            continue

        score = score_paragraph(paragraph, disaster_type)
        if score >= threshold:
            high_impact_paragraphs.append(paragraph)

    return high_impact_paragraphs
