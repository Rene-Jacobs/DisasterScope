"""
Content Fetcher Module for Disaster Impact Analysis System

This module handles all content retrieval operations including:
- HTTP content fetching with retry logic
- JavaScript rendering using Playwright
- Document file handling (PDF, DOC)
"""

import re
import aiohttp
import asyncio
import os
import random
import logging
import json
from typing import Tuple, Optional, Dict, Any
from urllib.parse import urlparse, urljoin
from tenacity import retry, stop_after_attempt, wait_exponential

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@retry(
    stop=stop_after_attempt(2),  # Reduced from 3 to 2 retry attempts
    wait=wait_exponential(multiplier=1, min=1, max=5),  # Reduced wait times
    reraise=True,
)
async def fetch_article_with_retry(url: str) -> Tuple[str, int, str]:
    """
    Fetches article content with retry and exponential backoff.
    Optimized for better performance.

    Args:
        url: URL to fetch

    Returns:
        Tuple of (content, status_code, final_url)
    """
    # Parse domain for domain-specific handling
    domain = urlparse(url).netloc

    # Add headers to mimic a browser request - helps avoid getting blocked
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.google.com/",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

    # Add a smaller random delay to avoid rate limiting
    await asyncio.sleep(random.uniform(0.5, 1.5))  # Reduced from 1-3 seconds

    # Set domain-specific timeout with shorter timeouts
    timeout_seconds = (
        30 if ".gov" in domain or ".mil" in domain else 15
    )  # Reduced from 60/30
    timeout = aiohttp.ClientTimeout(total=timeout_seconds)
    logger.info(f"Fetching {url} with timeout of {timeout_seconds} seconds")

    async with aiohttp.ClientSession() as session:
        try:
            # Use domain-specific timeout
            async with session.get(url, headers=headers, timeout=timeout) as response:
                final_url = str(response.url)
                if response.status != 200:
                    logger.warning(f"Received HTTP {response.status} from {url}")

                    # For redirects, follow them
                    if (
                        response.status in (301, 302, 307, 308)
                        and "Location" in response.headers
                    ):
                        redirect_url = response.headers["Location"]
                        logger.info(f"Following redirect to {redirect_url}")
                        # If it's a relative URL, make it absolute
                        if not redirect_url.startswith("http"):
                            base_url = f"{urlparse(url).scheme}://{domain}"
                            redirect_url = urljoin(base_url, redirect_url)
                        # Try the redirect URL - but don't retry to avoid infinite loops
                        try:
                            async with session.get(
                                redirect_url, headers=headers, timeout=timeout
                            ) as redirect_response:
                                final_url = str(redirect_response.url)
                                if redirect_response.status == 200:
                                    content_bytes = await redirect_response.read()
                                    # Try only the most common encodings
                                    for encoding in ["utf-8", "latin-1"]:
                                        try:
                                            content = content_bytes.decode(encoding)
                                            return content, 200, final_url
                                        except UnicodeDecodeError:
                                            continue
                                    # Fallback
                                    content = content_bytes.decode(
                                        "utf-8", errors="replace"
                                    )
                                    return content, 200, final_url
                        except Exception as redirect_error:
                            logger.error(f"Error following redirect: {redirect_error}")

                    return "", response.status, final_url

                try:
                    logger.info(
                        f"Successfully connected to {url}, retrieving content..."
                    )

                    # Try to get content with multiple encodings
                    content_bytes = await response.read()
                    content_length = len(content_bytes)
                    logger.info(f"Retrieved {content_length} bytes from {url}")

                    # Limit content size to improve performance
                    if content_length > 500000:  # Limit to ~500KB
                        content_bytes = content_bytes[:500000]
                        logger.info(f"Limited content to 500KB for performance")

                    # Preferred encoding from the response, if provided
                    encodings = []
                    if response.charset:
                        encodings.append(response.charset)
                    encodings.extend(["utf-8", "latin-1"])

                    for encoding in encodings:
                        try:
                            content = content_bytes.decode(encoding)
                            logger.info(
                                f"Successfully decoded content using {encoding} encoding"
                            )
                            return content, response.status, final_url
                        except UnicodeDecodeError:
                            continue

                    # Last resort: use UTF-8 with error handling
                    logger.warning(
                        f"Could not decode with standard encodings, using UTF-8 with error handling"
                    )
                    content = content_bytes.decode("utf-8", errors="replace")
                    return content, response.status, final_url

                except Exception as e:
                    logger.error(f"Error reading response content: {e}")
                    raise

        except aiohttp.ClientError as e:
            logger.error(f"aiohttp client error while fetching {url}: {e}")
            raise
        except asyncio.TimeoutError:
            logger.error(f"Request to {url} timed out after {timeout_seconds} seconds")
            # Skip the Playwright fallback for performance
            raise
        except Exception as e:
            logger.error(f"Unexpected error during fetch of {url}: {e}")
            raise


async def fetch_with_playwright(url: str) -> str:
    """
    Fetches JavaScript-heavy pages using Playwright.

    Args:
        url: URL to fetch

    Returns:
        HTML content as string
    """
    try:
        # Import here to avoid unnecessary dependency if not used
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                page = await browser.new_page()
                await page.goto(
                    url, wait_until="networkidle", timeout=45000
                )  # Increased timeout for gov sites
                # Wait a bit longer for JS to execute
                await asyncio.sleep(5)
                content = await page.content()
                return content
            finally:
                await browser.close()
    except ImportError:
        logger.error("Playwright not available. Install with: pip install playwright")
        raise
    except Exception as e:
        logger.error(f"Playwright error: {e}")
        raise


async def handle_document_file(url: str, file_extension: str) -> Tuple[str, str]:
    """
    Handle PDF, DOC, and other document formats.

    Args:
        url: URL of the document
        file_extension: Extension of the file (.pdf, .doc, etc.)

    Returns:
        Tuple of (publication_date, impact_details)
    """
    logger.info(f"Document handler called for {url}")
    # Try to get last part of URL for a potential date
    path_parts = urlparse(url).path.split("/")
    date_matches = [part for part in path_parts if re.match(r"\d{4}", part)]

    from datetime import datetime

    date_str = date_matches[-1] if date_matches else datetime.now().strftime("%Y-%m-%d")

    # Implementation for document parsing would go here
    # For now, just return a placeholder

    return (
        date_str,
        f"This is a {file_extension} document and cannot be parsed directly. Please download and view the document at {url}",
    )


async def extract_structured_data(html_content: str, url: str) -> Dict[str, Any]:
    """
    Extract structured data from HTML using simple JSON-LD extraction.

    Args:
        html_content: HTML content as string
        url: URL of the page

    Returns:
        Dictionary of structured data
    """
    try:
        # Simple JSON-LD extraction
        json_ld_pattern = (
            r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>'
        )
        matches = re.findall(json_ld_pattern, html_content, re.DOTALL | re.IGNORECASE)

        for match in matches:
            try:
                data = json.loads(match.strip())
                if isinstance(data, dict):
                    return data
                elif isinstance(data, list) and data:
                    return data[0] if isinstance(data[0], dict) else {}
            except json.JSONDecodeError:
                continue

    except Exception as e:
        logger.warning(f"Error extracting JSON-LD: {e}")

    return {}


__all__ = [
    "fetch_article_with_retry",
    "fetch_with_playwright",
    "handle_document_file",
    "extract_structured_data",
]
