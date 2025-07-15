"""
Content Parser Module for Disaster Impact Analysis System

This module handles HTML parsing and main content extraction,
focusing on finding the relevant text sections in articles.
Enhanced with semantic analysis, structure-based extraction,
and site-specific adaptations.
"""

import re
import logging
from typing import Optional, Dict, List, Tuple, Set, Union
from urllib.parse import urlparse
import math
from collections import Counter
import string
from bs4 import BeautifulSoup
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Ensure NLTK data is available
try:
    nltk.data.find("tokenizers/punkt")
    nltk.data.find("corpora/stopwords")
except LookupError:
    nltk.download("punkt", quiet=True)
    nltk.download("stopwords", quiet=True)

# Known content templates by domain category
CONTENT_TEMPLATES = {
    "government": {
        "selectors": [
            ".main-content",
            ".block-system-main-block",
            "#main-content",
            ".usa-layout-docs__main",
            ".content-with-sidebar",
        ],
        "domains": [
            "gov",
            "mil",
            "fed.us",
            "state.us",
            "dot.gov",
            "noaa.gov",
            "nasa.gov",
            "epa.gov",
            "fema.gov",
            "weather.gov",
            "usgs.gov",
        ],
    },
    "news": {
        "selectors": [
            ".article-body",
            ".story-body",
            ".entry-content",
            ".article__body",
            ".story-text",
            ".article-content",
            ".post-content",
            ".story-content",
        ],
        "domains": [
            "cnn.com",
            "nytimes.com",
            "washingtonpost.com",
            "reuters.com",
            "apnews.com",
            "bbc.com",
            "nbcnews.com",
            "cbsnews.com",
            "abcnews.go.com",
            "foxnews.com",
            "usatoday.com",
            "wsj.com",
            "latimes.com",
            "npr.org",
            "theguardian.com",
        ],
    },
    "blog": {
        "selectors": [
            ".post",
            ".blog-post",
            ".post-content",
            ".entry",
            ".blog-entry",
            ".wordpress-post",
            ".blogger-post",
        ],
        "domains": [
            "medium.com",
            "wordpress.com",
            "blogger.com",
            "tumblr.com",
            "substack.com",
            "ghost.io",
            "wix.com",
            "squarespace.com",
            "typepad.com",
            "blogspot.com",
        ],
    },
    "scientific": {
        "selectors": [
            ".article-body",
            ".article-content",
            ".paper-content",
            ".research-article",
            ".journal-article-body",
            "#abstract",
            ".abstract",
            ".publication-content",
        ],
        "domains": [
            "springer.com",
            "nature.com",
            "science.org",
            "wiley.com",
            "sciencedirect.com",
            "cell.com",
            "plos.org",
            "pnas.org",
            "elsevier.com",
            "ieee.org",
            "acs.org",
            "arxiv.org",
            "biorxiv.org",
            "medrxiv.org",
            "researchgate.net",
        ],
    },
}

# Sites known to have paywalls or registration walls
PAYWALL_SITES = [
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

# Boilerplate patterns to exclude
BOILERPLATE_SELECTORS = [
    "nav",
    "header",
    "footer",
    "#nav",
    "#header",
    "#footer",
    ".nav",
    ".header",
    ".footer",
    ".navigation",
    ".menu",
    ".sidebar",
    "#sidebar",
    ".comments",
    "#comments",
    ".social",
    "#social",
    ".advertisement",
    ".ads",
    "#ads",
    ".ad",
    "#ad",
    ".banner",
    "#banner",
    ".cookie-notice",
    "#cookie-notice",
    ".subscription",
    "#subscription",
    ".newsletter",
    "#newsletter",
    ".related",
    "#related",
    ".recommended",
    "#recommended",
    ".promotion",
    "#promotion",
    ".popup",
    "#popup",
    ".modal",
    "#modal",
    ".subscribe-form",
    ".sign-up-form",
]


def extract_title(html, json_ld_data: Dict) -> Optional[str]:
    """
    Extract article title from HTML or JSON-LD data.

    Args:
        html: SelectoLax HTMLParser object
        json_ld_data: Extracted JSON-LD data

    Returns:
        Article title or None if not found
    """
    # Try JSON-LD first
    if json_ld_data:
        for item in json_ld_data:
            if isinstance(item, dict):
                if "headline" in item:
                    return item["headline"]
                elif "name" in item and (
                    "articleBody" in item
                    or "@type" in item
                    and item["@type"] in ["Article", "NewsArticle"]
                ):
                    return item["name"]

    # Try HTML title tag
    title_tag = html.css_first("title")
    if title_tag:
        title_text = title_tag.text().strip()
        # Clean up common title patterns (e.g., "Title | Site Name")
        if " | " in title_text:
            return title_text.split(" | ")[0].strip()
        if " - " in title_text:
            return title_text.split(" - ")[0].strip()
        return title_text

    # Try OpenGraph or other meta tags
    meta_titles = [
        html.css_first('meta[property="og:title"]'),
        html.css_first('meta[name="twitter:title"]'),
        html.css_first('meta[name="title"]'),
        html.css_first('meta[name="dc.title"]'),
    ]

    for meta in meta_titles:
        if meta and meta.attributes.get("content"):
            return meta.attributes.get("content")

    # Try H1 element
    h1 = html.css_first("h1")
    if h1:
        return h1.text().strip()

    return None


def identify_site_category(domain: str) -> Optional[str]:
    """
    Identify the category of a website based on its domain.

    Args:
        domain: Domain of the website

    Returns:
        Category name or None if not identified
    """
    domain_lower = domain.lower()

    for category, info in CONTENT_TEMPLATES.items():
        for domain_pattern in info["domains"]:
            if domain_pattern in domain_lower:
                logger.info(f"Identified site category: {category}")
                return category

    return None


def extract_main_content(html, domain: str) -> Optional[object]:
    """
    Extracts the main content container from the HTML using multiple strategies.

    Args:
        html: SelectoLax HTMLParser object
        domain: Domain of the website

    Returns:
        HTMLParser object containing the main content or None if not found
    """
    # Check for paywall
    if is_paywall_site(domain):
        logger.info(f"Potential paywall site detected: {domain}")

    # Step 1: Try site-specific selectors based on domain category
    site_category = identify_site_category(domain)
    if site_category:
        category_selectors = CONTENT_TEMPLATES[site_category]["selectors"]
        for selector in category_selectors:
            content = html.css_first(selector)
            if content and content.text() and len(content.text()) > 200:
                logger.info(
                    f"Found main content using {site_category} category selector: {selector}"
                )
                return content

    # Step 2: Try common content selectors
    general_selectors = [
        "article",
        "main",
        ".article",
        ".content",
        ".story",
        ".post",
        ".article-body",
        ".content-body",
        ".main-content",
        ".entry-content",
        ".page-content",
        "#content",
        "#main",
        "#article",
        "#story",
        "section.article",
        "section.content",
        "div.news",
        "#news",
        "[role='main']",
        "[itemprop='articleBody']",
        "[itemprop='mainContentOfPage']",
        ".inner-content",
    ]

    for selector in general_selectors:
        content = html.css_first(selector)
        if content and content.text() and len(content.text()) > 200:
            logger.info(
                f"Found main content container using general selector: {selector}"
            )
            return content

    # Step 3: Try content density analysis
    logger.info("Using content density analysis to locate main content...")
    content_blocks = identify_content_blocks_by_density(html)
    if content_blocks:
        logger.info(
            f"Found main content using content density analysis ({len(content_blocks[0].text())} chars)"
        )
        return content_blocks[0]

    # Step 4: Find the largest text block
    logger.info("Looking for largest text block...")
    text_blocks = []

    for node in html.css("div, section, main, article"):
        try:
            # Skip nodes that match boilerplate selectors
            if is_boilerplate(node):
                continue

            text = node.text()
            if text and len(text) > 200:
                # Calculate text-to-html ratio as a quality metric
                html_size = len(node.html)
                if html_size > 0:
                    ratio = len(text) / html_size
                    # Only consider blocks with a reasonable ratio
                    if ratio > 0.3:
                        text_blocks.append((node, len(text), ratio))
        except Exception as e:
            logger.warning(f"Error processing node during content extraction: {e}")
            continue

    # Sort by text length (descending)
    if text_blocks:
        # Sort by text length, prioritizing blocks with better text-to-html ratio
        text_blocks.sort(key=lambda x: (x[1] * (0.7 + 0.3 * x[2])), reverse=True)
        logger.info(
            f"Using largest text block: {text_blocks[0][1]} chars, ratio: {text_blocks[0][2]:.2f}"
        )
        return text_blocks[0][0]

    # If still no container, just use the body
    logger.info("No specific content container found. Using body tag.")
    return html.body


def is_boilerplate(node) -> bool:
    """
    Determine if a node is likely boilerplate content.

    Args:
        node: HTML node to check

    Returns:
        True if node appears to be boilerplate, False otherwise
    """
    # Check tag type
    if node.tag_name in ["nav", "header", "footer", "aside"]:
        return True

    # Check element ID and class
    node_id = node.attributes.get("id", "").lower()
    node_class = node.attributes.get("class", "").lower()

    # Check against known boilerplate patterns
    for pattern in [
        "nav",
        "menu",
        "header",
        "footer",
        "sidebar",
        "widget",
        "comment",
        "ad",
        "banner",
        "promo",
        "share",
        "social",
        "related",
    ]:
        if pattern in node_id or pattern in node_class:
            return True

    return False


def is_paywall_site(domain: str) -> bool:
    """
    Check if a site is known to have a paywall.

    Args:
        domain: Domain to check

    Returns:
        True if site likely has a paywall
    """
    return any(paywall_domain in domain.lower() for paywall_domain in PAYWALL_SITES)


def identify_content_blocks_by_density(html) -> List:
    """
    Identify main content blocks using text density analysis.

    Args:
        html: HTML parser object

    Returns:
        List of content blocks, ordered by relevance
    """
    candidates = []

    # Consider div elements with substantial content
    for div in html.css("div"):
        # Skip tiny divs and likely boilerplate
        if is_boilerplate(div):
            continue

        # Get text and calculate metrics
        text = div.text()
        if not text or len(text) < 200:
            continue

        # Count paragraph-like children
        p_count = len(div.css("p"))

        # Count text nodes directly inside this div
        text_nodes = 0
        for child in div.iter():
            if child.tag_name == None and child.text().strip():
                text_nodes += 1

        # Calculate metrics
        html_size = len(div.html)
        text_density = len(text) / max(html_size, 1)
        p_density = p_count / max(len(div.css("*")), 1)  # p tags relative to all tags

        # Calculate a composite score
        score = (0.5 * text_density) + (0.3 * p_density) + (0.2 * (len(text) / 1000))

        candidates.append((div, score, len(text)))

    # Sort by composite score
    candidates.sort(key=lambda x: x[1], reverse=True)

    # Return the div elements, sorted by score
    return [c[0] for c in candidates[:3]]  # Return top 3 candidates


def process_general_content(container, domain: str, full_text: str) -> str:
    """
    Process general content for communication impact info when specific impact details aren't found.

    Args:
        container: HTML parser object containing the content
        domain: Domain of the website
        full_text: Full text of the article

    Returns:
        Extracted general content as a string
    """
    if not container:
        logger.warning("No container provided for general content processing")
        return ""

    # Extract structured elements
    extracted_content = extract_structured_elements(container)
    if extracted_content:
        logger.info(
            f"Found structured content elements: {len(extracted_content)} chars"
        )
        return extracted_content

    # Get paragraphs
    paragraphs = container.css("p")
    logger.info(f"Found {len(paragraphs)} paragraphs in the container")

    # If no paragraphs, try to get text directly
    if not paragraphs:
        logger.info("No paragraph tags found. Extracting text directly.")
        text = container.text()
        if not text:
            logger.warning("Container has no text content")
            return ""

        # Split into reasonable paragraphs
        text_paragraphs = re.split(r"\n\s*\n", text)
        logger.info(f"Split text into {len(text_paragraphs)} paragraphs")
        return "\n\n".join(text_paragraphs[:5])  # Take first 5 paragraphs

    # Filter paragraphs for communications-related content
    comm_keywords = [
        "communications",
        "telecommunication",
        "network",
        "cellular",
        "cell service",
        "internet",
        "phone service",
        "broadband",
        "wireless",
        "5g",
        "4g",
        "fiber optic",
        "data center",
        "outage",
        "service disruption",
        "signal",
        "connection",
        "landline",
        "satellite",
        "radio",
        "transmission",
        "bandwidth",
        "connectivity",
        "infrastructure",
        "utility",
        "utilities",
        "power",
        "electricity",
        "technology",
        "digital",
        "emergency",
        "alert",
        "warning",
    ]

    # Use TF-IDF to find the most relevant paragraphs
    disaster_paragraphs = []
    for p in paragraphs:
        text = p.text()
        if not text or len(text) < 50:  # Skip very short paragraphs
            continue

        # Calculate relevance score
        relevance = calculate_relevance_score(text, comm_keywords)
        if relevance > 0.1:  # Threshold for relevance
            disaster_paragraphs.append((text, relevance))

    # Sort by relevance
    disaster_paragraphs.sort(key=lambda x: x[1], reverse=True)

    # If we found communications-related paragraphs, use those
    if disaster_paragraphs:
        logger.info(
            f"Found {len(disaster_paragraphs)} communications-related paragraphs"
        )
        return "\n\n".join(
            [p[0] for p in disaster_paragraphs[:5]]
        )  # Take top 5 paragraphs

    # Otherwise, take the first few substantial paragraphs
    logger.info(
        "No communications-specific paragraphs found. Using general paragraphs."
    )
    substantial_paragraphs = []
    for p in paragraphs:
        text = p.text()
        if text and len(text) > 100:  # Only substantial paragraphs
            substantial_paragraphs.append(text)
        if len(substantial_paragraphs) >= 3:
            break

    if substantial_paragraphs:
        return "\n\n".join(substantial_paragraphs)

    # Final fallback - get some text from the container
    logger.info("No substantial paragraphs found. Using container text as fallback.")
    all_text = container.text()
    if all_text:
        return all_text[:1000] + "..." if len(all_text) > 1000 else all_text

    return ""


def extract_structured_elements(container) -> str:
    """
    Extract structured elements like tables, lists, and blockquotes.

    Args:
        container: HTML container to process

    Returns:
        Formatted string with extracted structured content
    """
    structured_content = []

    # Extract tables
    tables = container.css("table")
    for i, table in enumerate(tables[:2]):  # Limit to 2 tables
        try:
            table_text = f"TABLE {i+1}:\n"
            for row in table.css("tr"):
                cells = []
                for cell in row.css("th, td"):
                    cell_text = cell.text().strip().replace("\n", " ")
                    cells.append(cell_text)
                if cells:
                    table_text += " | ".join(cells) + "\n"
            structured_content.append(table_text)
        except Exception as e:
            logger.warning(f"Error extracting table: {e}")

    # Extract lists
    lists = container.css("ul, ol")
    for i, list_elem in enumerate(lists[:3]):  # Limit to 3 lists
        try:
            list_text = f"LIST {i+1}:\n"
            for item in list_elem.css("li"):
                item_text = item.text().strip()
                if item_text:
                    list_text += f"• {item_text}\n"
            structured_content.append(list_text)
        except Exception as e:
            logger.warning(f"Error extracting list: {e}")

    # Extract blockquotes
    quotes = container.css("blockquote")
    for i, quote in enumerate(quotes[:2]):  # Limit to 2 blockquotes
        try:
            quote_text = quote.text().strip()
            if quote_text:
                structured_content.append(f"QUOTE: {quote_text}")
        except Exception as e:
            logger.warning(f"Error extracting blockquote: {e}")

    # Return combined structured content
    if structured_content:
        return "\n\n".join(structured_content)
    return ""


def extract_article_paragraphs(html) -> List[str]:
    """
    Extract paragraphs from an article.

    Args:
        html: HTML parser object

    Returns:
        List of paragraph texts
    """
    paragraphs = []

    # Try to get paragraphs from the article
    p_tags = html.css("p")
    for p in p_tags:
        text = p.text().strip()
        if text and len(text) > 30:  # Skip very short paragraphs
            paragraphs.append(text)

    return paragraphs


def extract_article_sections(html) -> List[str]:
    """
    Extract sections (divs, sections, etc.) from an article.

    Args:
        html: HTML parser object

    Returns:
        List of section texts
    """
    sections = []

    # Try to get content from semantic sections
    for selector in ["section", "div.section", "div[role='region']", "article > div"]:
        section_elements = html.css(selector)
        for section in section_elements:
            text = section.text().strip()
            if text and len(text) > 100:  # Only substantial sections
                sections.append(text)

    return sections


def extract_text_by_headers(html) -> Dict[str, str]:
    """
    Extract content organized by headers to understand document structure.

    Args:
        html: HTML parser object

    Returns:
        Dictionary mapping header text to content under that header
    """
    header_content = {}

    # Get all headers
    headers = html.css("h1, h2, h3, h4, h5, h6")

    # Process each header
    for i, header in enumerate(headers):
        header_text = header.text().strip()
        if not header_text:
            continue

        # Find content between this header and the next
        content = []
        current = header.next

        while current and (i == len(headers) - 1 or current != headers[i + 1]):
            if current.tag_name in ["p", "ul", "ol", "blockquote", "table", "div"]:
                text = current.text().strip()
                if text:
                    content.append(text)
            current = current.next

        # Join content and add to dictionary
        if content:
            header_content[header_text] = "\n\n".join(content)

    return header_content


def find_content_by_keywords(paragraphs: List[str], keywords: List[str]) -> List[str]:
    """
    Filter paragraphs by keywords.

    Args:
        paragraphs: List of paragraph texts
        keywords: List of keywords to search for

    Returns:
        List of paragraphs containing keywords
    """
    relevant_paragraphs = []

    for p in paragraphs:
        p_lower = p.lower()
        if any(keyword in p_lower for keyword in keywords):
            relevant_paragraphs.append(p)

    return relevant_paragraphs


def calculate_relevance_score(text: str, keywords: List[str]) -> float:
    """
    Calculate relevance score for a text using TF-IDF like approach.

    Args:
        text: Text to analyze
        keywords: Keywords to look for

    Returns:
        Relevance score (0.0 to 1.0)
    """
    # Lowercase the text
    text_lower = text.lower()

    # Tokenize the text
    tokens = nltk.word_tokenize(text_lower)

    # Remove stopwords and punctuation
    stop_words = set(stopwords.words("english"))
    tokens = [t for t in tokens if t not in stop_words and t not in string.punctuation]

    # Count token frequencies
    token_freq = Counter(tokens)

    # Calculate keyword frequency
    keyword_count = 0
    for keyword in keywords:
        # Check compound keywords
        if " " in keyword:
            if keyword in text_lower:
                keyword_count += 3  # Weight multi-word matches higher
        else:
            keyword_count += token_freq.get(keyword, 0)

    # Normalize by text length
    if not tokens:
        return 0.0

    relevance = (keyword_count / len(tokens)) * math.log(len(text_lower) + 1)

    # Calculate sentence score for disaster-related content
    sentences = sent_tokenize(text_lower)
    sentence_scores = []

    for sentence in sentences:
        # Check for disaster impact patterns
        impact_terms = [
            "impact",
            "affect",
            "damage",
            "destroy",
            "disrupt",
            "outage",
            "down",
            "fail",
        ]
        has_impact = any(term in sentence for term in impact_terms)

        # Check for infrastructure terms
        infra_terms = [
            "infrastructure",
            "network",
            "system",
            "service",
            "power",
            "utility",
        ]
        has_infra = any(term in sentence for term in infra_terms)

        # Check for location/scope terms
        location_terms = [
            "area",
            "region",
            "city",
            "county",
            "state",
            "nationwide",
            "residents",
        ]
        has_location = any(term in sentence for term in location_terms)

        # Calculate sentence score
        sent_score = (
            (0.5 if has_impact else 0)
            + (0.3 if has_infra else 0)
            + (0.2 if has_location else 0)
        )
        sentence_scores.append(sent_score)

    # Overall score is combination of keyword relevance and sentence scoring
    avg_sentence_score = sum(sentence_scores) / len(sentences) if sentences else 0
    final_score = (0.7 * relevance) + (0.3 * avg_sentence_score)

    return min(final_score, 1.0)  # Cap at 1.0


def extract_image_captions(html) -> List[str]:
    """
    Extract captions from images which often contain impact summaries.

    Args:
        html: HTML parser object

    Returns:
        List of image captions
    """
    captions = []

    # Look for figure captions
    figcaptions = html.css("figcaption")
    for caption in figcaptions:
        text = caption.text().strip()
        if text and len(text) > 20:  # Skip very short captions
            captions.append(text)

    # Look for image alt text
    imgs = html.css("img[alt]")
    for img in imgs:
        alt = img.attributes.get("alt", "").strip()
        if (
            alt
            and len(alt) > 20
            and not alt.lower().startswith(("image", "picture", "photo"))
        ):
            captions.append(alt)

    # Look for images with captions in various formats
    caption_containers = html.css(
        ".caption, .wp-caption-text, .image-caption, .gallery-caption"
    )
    for container in caption_containers:
        text = container.text().strip()
        if text and len(text) > 20:
            captions.append(text)

    return captions


def clean_extracted_text(text: str) -> str:
    """
    Clean extracted text by removing excessive whitespace, etc.

    Args:
        text: Text to clean

    Returns:
        Cleaned text
    """
    if not text:
        return ""

    # Replace non-breaking spaces with regular spaces
    text = text.replace("\xa0", " ")

    # Replace multiple newlines with a single newline
    text = re.sub(r"\n\s*\n", "\n\n", text)

    # Replace multiple spaces with a single space
    text = re.sub(r" +", " ", text)

    # Remove repeated punctuation (except ellipsis)
    text = re.sub(r"([!?])\1+", r"\1", text)

    # Handle common encoding issues
    text = text.replace("â€™", "'").replace("â€œ", '"').replace("â€", '"')

    # Remove common JavaScript artifacts
    text = re.sub(r"undefined|NaN|null|console\.log.*?;", "", text)

    # Trim leading/trailing whitespace
    text = text.strip()

    return text


def validate_extracted_content(text: str, disaster_type: str) -> Tuple[bool, float]:
    """
    Validate extracted content to confirm it's relevant to disaster impacts.

    Args:
        text: Extracted content
        disaster_type: Type of disaster being analyzed

    Returns:
        Tuple of (is_valid, confidence_score)
    """
    if not text or len(text) < 100:
        return False, 0.0

    text_lower = text.lower()

    # Check for basic disaster terms
    disaster_term = disaster_type.lower()
    disaster_terms = [
        disaster_term,
        "disaster",
        "emergency",
        "incident",
        "crisis",
        "catastrophe",
    ]
    has_disaster_term = any(term in text_lower for term in disaster_terms)

    # Check for impact terms
    impact_terms = [
        "impact",
        "affect",
        "damage",
        "destroy",
        "disrupt",
        "outage",
        "loss",
        "failure",
    ]
    has_impact_term = any(term in text_lower for term in impact_terms)

    # Check for communication/infrastructure terms
    infrastructure_terms = [
        "infrastructure",
        "communication",
        "network",
        "system",
        "service",
        "telephone",
        "cellular",
        "internet",
    ]
    has_infrastructure_term = any(term in text_lower for term in infrastructure_terms)

    # Calculate confidence score
    confidence = 0.0

    if has_disaster_term:
        confidence += 0.4
    if has_impact_term:
        confidence += 0.3
    if has_infrastructure_term:
        confidence += 0.3

    # Check if the content meets minimum criteria for validity
    is_valid = confidence >= 0.4

    return is_valid, confidence


def detect_truncated_content(text: str) -> bool:
    """
    Detect if content appears to be truncated.

    Args:
        text: Content to check

    Returns:
        True if content appears truncated
    """
    # Check for common truncation indicators
    truncation_markers = [
        "... read more",
        "...continue reading",
        "to continue reading",
        "full article",
        "subscribe to",
        "sign up for",
        "premium content",
        "paywall",
        "subscribe now",
    ]

    text_lower = text.lower()
    for marker in truncation_markers:
        if marker in text_lower:
            return True

    # Check for abrupt ending
    sentences = sent_tokenize(text)
    if sentences:
        last_sentence = sentences[-1].lower()

        # Check if last sentence ends with ellipsis
        if last_sentence.rstrip().endswith("..."):
            return True

        # Check for incomplete sentence
        if len(last_sentence) < 20 and not any(x in last_sentence[-1] for x in ".!?"):
            return True

    return False


def extract_content_with_confidence(
    html, domain: str, disaster_type: str
) -> Tuple[str, float]:
    """
    Extract content with confidence scoring.

    Args:
        html: HTML parser object
        domain: Domain of the website
        disaster_type: Type of disaster

    Returns:
        Tuple of (extracted_content, confidence_score)
    """
    # Extract main content container
    main_content = extract_main_content(html, domain)

    if not main_content:
        return "", 0.0

    # Process the content
    extracted_text = process_general_content(main_content, domain, html.body.text())
    extracted_text = clean_extracted_text(extracted_text)

    # Validate content
    is_valid, confidence = validate_extracted_content(extracted_text, disaster_type)

    # Check for truncation
    if detect_truncated_content(extracted_text):
        logger.warning("Content appears to be truncated")
        confidence *= 0.8  # Reduce confidence for truncated content

    return extracted_text, confidence
