"""
Date Extractor Module for Disaster Impact Analysis System

This module is responsible for extracting and normalizing publication dates
from various HTML structures and formats commonly found in web articles.
"""

import re
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from urllib.parse import urlparse
from dateutil import parser as date_parser
import dateparser
from dateparser.search import search_dates
import json

# Configure logging only once
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


DATE_FIELDS = [
    "datePublished",
    "dateCreated",
    "dateModified",
    "date",
    "publishDate",
    "publishedDate",
    "created",
    "modified",
    "published",
]


def _search_json_ld_for_date(obj: Any) -> Optional[str]:
    """Recursively search JSON-LD object for known date fields."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key in DATE_FIELDS:
                return value
            result = _search_json_ld_for_date(value)
            if result:
                return result
    elif isinstance(obj, list):
        for item in obj:
            result = _search_json_ld_for_date(item)
            if result:
                return result
    return None


def extract_and_normalize_date(
    html, domain: str, json_ld_data: list, url: str
) -> Optional[str]:
    """
    Extract publication date using layered heuristics and normalize to YYYY-MM-DD.
    """
    # Load JSON-LD if not provided
    if not json_ld_data:
        scripts = html.css("script[type='application/ld+json']")
        json_ld_data = []
        for s in scripts:
            try:
                json_ld_data.append(json.loads(s.text()))
            except json.JSONDecodeError:
                continue

    # 1. JSON-LD date
    if json_ld_data:
        date_str = extract_date_from_json_ld(json_ld_data)
        if date_str:
            logger.info(f"Date from JSON-LD: {date_str}")
            return normalize_date(date_str)

    # 2. High-priority meta tags
    date_str = extract_date_from_meta_tags(html)
    if date_str:
        logger.info(f"Date from meta tags: {date_str}")
        return normalize_date(date_str)

    # 3. <time> elements
    date_str = extract_date_from_time_tags(html)
    if date_str:
        logger.info(f"Date from <time>: {date_str}")
        return normalize_date(date_str)

    # 4. Visible datelines via dateparser
    date_str = extract_date_via_dateparser(html)
    if date_str:
        logger.info(f"Date via dateparser: {date_str}")
        return normalize_date(date_str)

    # 5. Elements with date-related classes or IDs
    date_str = extract_date_from_class_elements(html)
    if date_str:
        logger.info(f"Date from class elements: {date_str}")
        return normalize_date(date_str)

    # 6. Generic text pattern search
    date_str = extract_date_from_text_patterns(html)
    if date_str:
        logger.info(f"Date from text patterns: {date_str}")
        return normalize_date(date_str)

    # 7. URL-based patterns
    date_str = extract_date_from_url(url)
    if date_str:
        logger.info(f"Date from URL: {date_str}")
        return normalize_date(date_str)

    # 8. Government site "Updated" stamps
    if domain and (".gov" in domain or ".mil" in domain):
        date_str = extract_date_from_government_site(html, domain)
        if date_str:
            logger.info(f"Date from gov/mil site: {date_str}")
            return normalize_date(date_str)
        # fallback: use current date
        today = datetime.now().strftime("%Y-%m-%d")
        logger.info(f"Fallback current date: {today}")
        return today

    logger.warning(f"No date found for {url}")
    return None


def extract_date_via_dateparser(html) -> Optional[str]:
    """
    Search visible text for dates using dateparser with multiple locales.
    """
    text = html.body.text() if html.body else ""
    text = text[:2000]  # limit to improve accuracy
    # Try to find a date expression
    results = search_dates(
        text,
        languages=["en"],
        settings={
            "RETURN_AS_TIMEZONE_AWARE": False,
            "PREFER_DAY_OF_MONTH": "first",
            "DATE_ORDER": "MDY",
        },
    )
    if results:
        # results is list of (matched_text, datetime)
        _, dt = results[0]
        return dt.strftime("%Y-%m-%d")
    return None


def extract_date_from_json_ld(json_ld_data: Any) -> Optional[str]:
    """Extract date from JSON-LD structured data."""
    if isinstance(json_ld_data, dict):
        items = [json_ld_data]
    elif isinstance(json_ld_data, list):
        items = json_ld_data
    else:
        return None

    for item in items:
        result = _search_json_ld_for_date(item)
        if result:
            return result
    return None


def extract_date_from_meta_tags(html) -> Optional[str]:
    """Extract date from meta tags."""
    meta_properties = [
        "article:published_time",
        "og:published_time",
        "published_time",
        "date",
        "datePublished",
        "pubdate",
        "publish_date",
        "dc.date",
        "dc.created",
        "release_date",
        "article:modified_time",
        "og:updated_time",
        "last-modified",
        "created",
        "article_date",
        "date_published",
        "datemodified",
        "datecreated",
        "dc.date.issued",
        "bt:pubDate",
        "sailthru.date",
        "meta-date",
        "article:published",
        "article:modified",
        "og:published",
        "og:modified",
        "publication-date",
        "release-date",
        "date-published",
        "date-created",
        "date-updated",
        "first_published",
        "first_published_at",
        "timestamp",
        "dateissued",
        "published-time",
    ]

    for prop in meta_properties:
        selectors = [
            f'meta[property="{prop}"]',
            f'meta[name="{prop}"]',
            f'meta[itemprop="{prop}"]',
            f'meta[http-equiv="{prop}"]',
        ]

        for selector in selectors:
            meta = html.css_first(selector)
            if meta and meta.attributes.get("content"):
                return meta.attributes.get("content")
    return None


def extract_date_from_time_tags(html) -> Optional[str]:
    """Extract date from time tags."""
    time_tags = html.css("time")
    for time_tag in time_tags:
        if time_tag.attributes.get("datetime"):
            return time_tag.attributes.get("datetime")
        if time_tag.attributes.get("data-time"):
            return time_tag.attributes.get("data-time")
        elif time_tag.text() and re.search(r"\d{4}", time_tag.text()):
            return time_tag.text().strip()
    return None


def extract_date_from_text_patterns(html) -> Optional[str]:
    """Extract dates using common text patterns."""
    full_text = html.body.text() if html.body else ""

    date_patterns = [
        # ISO format
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}",
        r"\d{4}-\d{2}-\d{2}",
        # Common US formats
        r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}",
        r"\d{1,2} (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}",
        r"\d{1,2}/\d{1,2}/\d{4}",
        r"\d{1,2}-\d{1,2}-\d{4}",
        # Other formats
        r"(January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2},? \d{4}",
        r"\d{1,2} (January|February|March|April|May|June|July|August|September|October|November|December),? \d{4}",
        r"Posted:?\s+\w+\s+\d{1,2}(st|nd|rd|th)?,?\s+\d{4}",
        r"Updated:?\s+\w+\s+\d{1,2}(st|nd|rd|th)?,?\s+\d{4}",
        r"Published:?\s+\w+\s+\d{1,2}(st|nd|rd|th)?,?\s+\d{4}",
    ]

    for pattern in date_patterns:
        matches = re.findall(pattern, full_text, re.IGNORECASE)
        if matches:
            return matches[0]
    return None


def extract_date_from_class_elements(html) -> Optional[str]:
    """Extract date from elements with date-related classes or IDs."""
    date_classes = [
        "date",
        "Date",
        "publish-date",
        "published",
        "post-date",
        "byline-date",
        "article-date",
        "article__date",
        "article-datetime",
        "page-date",
        "post-meta",
        "metadata",
        "meta",
        "article-time",
        "pub-date",
        "timestamp",
        "time",
        "posted-on",
        "post-on",
        "article-info",
        "entry-date",
        "entry-meta",
        "article-meta",
        "story-date",
        "story-time",
    ]

    for class_name in date_classes:
        # Try explicit class attribute
        selector = f'[class*="{class_name}"]'
        date_elements = html.css(selector)

        # Also try ID attribute
        id_selector = f'[id*="{class_name}"]'
        date_elements.extend(html.css(id_selector))

        for element in date_elements:
            text = element.text().strip()
            # Check if it looks like a date
            if re.search(r"\d{4}", text) and (
                re.search(r"\d{1,2}/\d{1,2}", text)
                or re.search(
                    r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)", text, re.I
                )
            ):
                return text
    return None


def extract_date_from_url(url: str) -> Optional[str]:
    """Extract date from URL path components."""
    path_parts = urlparse(url).path.split("/")

    # Look for date patterns in URL parts
    date_patterns = [
        # YYYY/MM/DD pattern
        r"^(\d{4})/(\d{1,2})/(\d{1,2})$",
        # YYYY-MM-DD pattern
        r"^(\d{4})-(\d{1,2})-(\d{1,2})$",
        # YYYYMMDD pattern
        r"^(\d{4})(\d{2})(\d{2})$",
        # Just year
        r"^(\d{4})$",
    ]

    for part in path_parts:
        for pattern in date_patterns:
            match = re.match(pattern, part)
            if match:
                # If it's just a year, add generic month/day
                if pattern == r"^(\d{4})$":
                    return f"{match.group(1)}-01-01"
                # Otherwise, format properly
                elif len(match.groups()) == 3:
                    year, month, day = match.groups()
                    # Ensure month and day are two digits
                    month = month.zfill(2)
                    day = day.zfill(2)
                    return f"{year}-{month}-{day}"
    return None


def extract_date_from_government_site(html, domain: str) -> Optional[str]:
    """Special handling for government websites."""
    full_text = html.body.text() if html.body else ""

    # Check for specific government site patterns
    last_updated_patterns = [
        r"(Last Updated|Last Modified|Page Last Updated|Last Review|Date Updated|Updated):?\s*(.*?\d{4})",
        r"(Posted|Published|Created|Release Date|Date Posted):?\s*(.*?\d{4})",
        r"(Current as of|As of):?\s*(.*?\d{4})",
    ]

    # Check in footer first (common for government sites)
    footer = html.css_first("footer")
    if footer:
        footer_text = footer.text()
        for pattern in last_updated_patterns:
            match = re.search(pattern, footer_text, re.I)
            if match:
                return match.group(2).strip()

    # Then check full text
    for pattern in last_updated_patterns:
        match = re.search(pattern, full_text, re.I)
        if match:
            return match.group(2).strip()

    return None


def normalize_date(date_str: str, method: str = "unknown") -> Optional[str]:
    """
    Normalize various date formats to YYYY-MM-DD.

    Args:
        date_str: The date string to normalize
        method: The extraction method (for logging)

    Returns:
        Normalized date string in YYYY-MM-DD format
    """
    if not date_str:
        return None

    date_str = str(date_str).strip()

    # If it's just a month name, add current year
    month_names = [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    ]
    if date_str in month_names:
        current_year = datetime.now().year
        return f"{current_year}-{month_names.index(date_str)+1:02d}-01"

    # If it's just a year
    if date_str.isdigit() and len(date_str) == 4:
        return f"{date_str}-01-01"

    # Try to parse with dateutil
    try:
        # Handle ISO format dates
        if "T" in date_str:
            # Try ISO format with timezone
            if date_str.endswith("Z"):
                date_str = date_str[:-1] + "+00:00"
            parsed_date = date_parser.parse(date_str)
        else:
            # For non-ISO formats
            parsed_date = date_parser.parse(date_str, fuzzy=True)

        # Get just the date part
        normalized = parsed_date.strftime("%Y-%m-%d")
        logger.debug(
            f"Normalized date from '{date_str}' to '{normalized}' (method: {method})"
        )
        return normalized

    except Exception as e:
        logger.warning(f"Failed to parse date '{date_str}' with dateutil: {e}")

        # Fallback: Try to extract year and basic patterns
        year_match = re.search(r"20\d{2}", date_str)
        if year_match:
            year = year_match.group(0)

            # Try to extract month
            month = 1  # Default to January
            month_patterns = [
                (
                    r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)",
                    {
                        "Jan": 1,
                        "Feb": 2,
                        "Mar": 3,
                        "Apr": 4,
                        "May": 5,
                        "Jun": 6,
                        "Jul": 7,
                        "Aug": 8,
                        "Sep": 9,
                        "Oct": 10,
                        "Nov": 11,
                        "Dec": 12,
                    },
                ),
                (
                    r"(January|February|March|April|May|June|July|August|September|October|November|December)",
                    {
                        "January": 1,
                        "February": 2,
                        "March": 3,
                        "April": 4,
                        "May": 5,
                        "June": 6,
                        "July": 7,
                        "August": 8,
                        "September": 9,
                        "October": 10,
                        "November": 11,
                        "December": 12,
                    },
                ),
            ]

            for pattern, month_map in month_patterns:
                month_match = re.search(pattern, date_str, re.I)
                if month_match:
                    month_name = month_match.group(1)
                    # Handle case insensitivity
                    for key, value in month_map.items():
                        if key.lower() == month_name.lower():
                            month = value
                            break
                    break

            # Try to extract day
            day = 1  # Default to first day
            day_match = re.search(r"\b(\d{1,2})(st|nd|rd|th)?\b", date_str)
            if day_match:
                day = int(day_match.group(1))
                # Validate day (in case of parsing errors)
                day = min(max(day, 1), 28)

            return f"{year}-{month:02d}-{day:02d}"

        # If we still can't extract a date, return the original
        logger.warning(f"Could not normalize date '{date_str}', returning as is")
        return date_str
