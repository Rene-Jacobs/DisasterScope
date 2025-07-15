"""
Article Analyzer for Disaster Impact Analysis System

This module coordinates the process of analyzing articles about disaster impacts
on critical infrastructure, using specialized modules for various analysis tasks.
"""

import os
import re
import time
import logging
import asyncio
import traceback
from typing import Dict, List, Tuple, Optional, Any, Union

from urllib.parse import urlparse

# Import from specialized modules
from .content_fetcher import (
    fetch_article_with_retry,
    fetch_with_playwright,
    handle_document_file,
    extract_structured_data,
)
from .date_extractor import extract_and_normalize_date
from .content_parser import extract_title, extract_main_content, process_general_content
from .impact_analyzer import (
    calculate_sentiment,
    extract_structured_impact_details,
)


# Simple fallback for extract_impact_details_with_nlp
async def extract_impact_details_with_nlp(
    main_content, domain: str, disaster_type: str, full_text: str
):
    """
    Simple fallback implementation for impact details extraction.

    Args:
        main_content: HTML content container
        domain: Website domain
        disaster_type: Type of disaster
        full_text: Full article text

    Returns:
        ImpactInfo object or None
    """
    from .analyzer_models import ImpactInfo

    try:
        # Simple implementation - just extract basic content
        if main_content and hasattr(main_content, "text"):
            content_text = main_content.text()
        else:
            content_text = full_text

        if content_text and len(content_text.strip()) > 50:
            impact_info = ImpactInfo()
            impact_info.raw_content = content_text[:2000]  # Limit to 2000 chars
            return impact_info

    except Exception as e:
        logger.warning(f"Error in simple impact extraction: {e}")

    return None


from .analyzer_models import (
    DisasterAnalysisResult,
    PublicationInfo,
    ImpactInfo,
    AnalysisStatistics,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def analyze_article_async(
    article_url: str, disaster_type: str = "Hurricane"
) -> DisasterAnalysisResult:
    """
    Asynchronously fetches and analyzes an article about disaster impacts on communications.

    Args:
        article_url: URL of the article to analyze
        disaster_type: Type of disaster being analyzed

    Returns:
        DisasterAnalysisResult object containing structured analysis
    """
    start_time = time.time()
    result = DisasterAnalysisResult(url=article_url, disaster_type=disaster_type)
    stats = AnalysisStatistics()
    domain = "unknown"  # Initialize domain with default value

    logger.info(f"Analyzing article: {article_url} (Disaster type: {disaster_type})")

    try:
        # Parse domain information
        parsed_url = urlparse(article_url)
        domain = parsed_url.netloc if parsed_url.netloc else "unknown"
        file_extension = os.path.splitext(parsed_url.path)[1].lower()
        logger.info(f"Domain: {domain}, File extension: {file_extension}")

        # Handle different content types
        if file_extension in [".pdf", ".doc", ".docx"]:
            logger.info(f"Detected document type: {file_extension}")
            date_result, content_result = await handle_document_file(
                article_url, file_extension
            )
            result.publication_info.date = date_result
            result.impact_info.raw_content = content_result
            stats.extraction_methods_used.append("document_handler")
            stats.processing_time_ms = (time.time() - start_time) * 1000
            return result

        # Get article content with retry for regular webpages
        content, status_code, final_url = await fetch_article_with_retry(article_url)
        result.url = final_url
        article_url = final_url
        stats.extraction_methods_used.append("content_fetcher")

        if status_code != 200 or not content:
            error_msg = (
                f"Failed to retrieve article content. Status code: {status_code}"
            )
            logger.warning(error_msg)
            result.error = error_msg
            stats.error_count += 1
            stats.processing_time_ms = (time.time() - start_time) * 1000
            return result

        stats.content_length = len(content)

        # Check if content is very short (likely not a full article)
        if len(content) < 1000:
            logger.warning(f"Content is suspiciously short ({len(content)} bytes)")
            if len(content) < 200:
                result.error = "Retrieved content is too short to be a valid article."
                stats.error_count += 1
                stats.processing_time_ms = (time.time() - start_time) * 1000
                return result

        # Try rendering JavaScript-heavy pages if needed
        if (
            "<body></body>" in content
            or "window.onload" in content
            or len(content) < 3000
        ):
            logger.info(
                "Possible JavaScript-heavy page detected. Attempting to render with Playwright."
            )
            try:
                playwright_content = await fetch_with_playwright(article_url)
                if playwright_content and len(playwright_content) > len(content):
                    logger.info(
                        f"Successfully rendered page with Playwright. Content length: {len(playwright_content)} bytes"
                    )
                    stats.extraction_methods_used.append("playwright_renderer")
                    content = playwright_content
                    stats.content_length = len(content)
            except Exception as e:
                logger.warning(
                    f"Playwright rendering failed: {e}. Continuing with initial content."
                )
                stats.error_count += 1

        # Parse HTML
        from selectolax.parser import HTMLParser

        html = HTMLParser(content)

        # Check if we got a valid page structure
        if not html.css_first("body"):
            logger.warning("No body tag found in HTML")
            result.error = "Could not parse article content (no body tag found)."
            stats.error_count += 1
            stats.processing_time_ms = (time.time() - start_time) * 1000
            return result

        # Extract structured data using extruct - fix the type issue
        try:
            json_ld_data_dict = await extract_structured_data(content, article_url)
            # Convert dict to list format expected by other functions
            json_ld_data: List[Dict] = [json_ld_data_dict] if json_ld_data_dict else []
        except Exception as e:
            logger.warning(f"Failed to extract structured data: {e}")
            json_ld_data = []

        # Extract publication date
        publication_date = extract_and_normalize_date(
            html, domain, json_ld_data, article_url
        )
        stats.extraction_methods_used.append("date_extractor")
        result.publication_info.date = publication_date
        logger.info(f"Extracted publication date: {publication_date}")

        # Extract article title
        title = extract_title(html, json_ld_data)
        result.publication_info.title = title
        result.publication_info.source = domain

        # Extract main content
        main_content = extract_main_content(html, domain)
        stats.extraction_methods_used.append("content_parser")

        # Extract impact details with NLP enhancement
        impact_details = await extract_impact_details_with_nlp(
            main_content, domain, disaster_type, html.body.text() if html.body else ""
        )
        stats.extraction_methods_used.append("impact_analyzer")

        # Update result with extracted impact information
        if impact_details:
            # Handle different types of impact_details objects
            impact_dict = None

            # Try Pydantic v2 method first
            if hasattr(impact_details, "model_dump"):
                try:
                    impact_dict = impact_details.model_dump()
                except Exception as e:
                    logger.warning(f"Failed to use model_dump: {e}")

            # Try Pydantic v1 method
            elif hasattr(impact_details, "dict"):
                try:
                    impact_dict = impact_details.dict()
                except Exception as e:
                    logger.warning(f"Failed to use dict: {e}")

            # If it's already a dict
            elif isinstance(impact_details, dict):
                impact_dict = impact_details

            # If it's an ImpactInfo object, access attributes directly
            elif hasattr(impact_details, "__dict__"):
                impact_dict = impact_details.__dict__

            # Update the result's impact_info fields if we got a dict
            if impact_dict and isinstance(impact_dict, dict):
                for key, value in impact_dict.items():
                    if hasattr(result.impact_info, key) and value is not None:
                        setattr(result.impact_info, key, value)

            # Fallback: if impact_details has raw_content attribute, use it directly
            elif hasattr(impact_details, "raw_content") and impact_details.raw_content:
                result.impact_info.raw_content = impact_details.raw_content
        else:
            # If no specific impact details were found, process general content
            general_content = process_general_content(
                main_content, domain, html.body.text() if html.body else ""
            )
            if general_content:
                result.impact_info.raw_content = general_content

        # Calculate sentiment of impact information
        if result.impact_info.raw_content:
            result.sentiment = calculate_sentiment(result.impact_info.raw_content)

    except Exception as e:
        stack_trace = traceback.format_exc()
        logger.error(f"Error analyzing {article_url}: {e}\n{stack_trace}")
        result.error = f"Error analyzing article: {str(e)}"
        stats.error_count += 1

    # No fallback to current date. If no publication date is found, record "Date unknown" later.

    # Calculate processing time
    stats.processing_time_ms = (time.time() - start_time) * 1000
    logger.info(f"Analysis completed in {stats.processing_time_ms:.2f}ms")

    return result


def analyze_article(
    article_url: str, disaster_type: str = "Hurricane"
) -> Tuple[Optional[str], str]:
    """
    Synchronous wrapper for async article analysis function.

    Args:
        article_url: URL of the article to analyze
        disaster_type: Type of disaster being analyzed

    Returns:
        Tuple of (publication_date, impact_details)
    """
    # Get or create event loop
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    result = loop.run_until_complete(analyze_article_async(article_url, disaster_type))

    # Extract publication date and impact details
    publication_date = result.publication_info.date if result.publication_info else None

    # Ensure impact_details is always a string, never None
    if result.error:
        impact_details = result.error
    elif result.impact_info and result.impact_info.raw_content:
        impact_details = result.impact_info.raw_content
    else:
        impact_details = "No impact details extracted."

    return publication_date, impact_details


async def analyze_multiple_articles(
    urls: List[str], disaster_type: str = "Hurricane"
) -> List[DisasterAnalysisResult]:
    """
    Analyze multiple articles concurrently.

    Args:
        urls: List of article URLs to analyze
        disaster_type: Type of disaster being analyzed

    Returns:
        List of DisasterAnalysisResult objects
    """
    logger.info(f"Starting concurrent analysis of {len(urls)} articles")

    # Determine the best concurrency approach based on number of URLs
    if len(urls) <= 5:
        # For small batches, use gather for simplicity
        tasks = [analyze_article_async(url, disaster_type) for url in urls]
        return await asyncio.gather(*tasks)
    else:
        # For larger batches, use semaphore to limit concurrent network requests
        semaphore = asyncio.Semaphore(10)  # Limit concurrent requests

        async def analyze_with_semaphore(url):
            async with semaphore:
                return await analyze_article_async(url, disaster_type)

        tasks = [analyze_with_semaphore(url) for url in urls]
        return await asyncio.gather(*tasks)


def analyze_articles(
    urls: List[str], disaster_type: str = "Hurricane"
) -> List[Dict[str, Any]]:
    """
    Synchronous wrapper for async multiple article analysis function.

    Args:
        urls: List of article URLs to analyze
        disaster_type: Type of disaster being analyzed

    Returns:
        List of dictionary representations of the analysis results
    """
    # Get or create event loop
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    results = loop.run_until_complete(analyze_multiple_articles(urls, disaster_type))
    return [result.to_dict() for result in results]


# Example usage with single URL
def test_analyzer():
    """
    Simple test function for the article analyzer.
    """
    url = "https://example.com/article.html"
    publication_date, impact_details = analyze_article(url, "Hurricane")
    print(f"Publication date: {publication_date}")
    print(f"Impact details: {impact_details[:200]}...")


if __name__ == "__main__":
    test_analyzer()
