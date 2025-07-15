# src/main.py
"""
Command-line interface for the Disaster Impact Analysis System.

This module provides the main entry point for running the disaster impact analysis
from the command line. It handles user input, coordinates the analysis workflow,
and generates the final Excel report.

Functions:
    main: Primary application entry point
    get_disaster_type_from_user: Interactive disaster type selection
    get_disaster_name_from_user: Interactive disaster name input
    get_sectors_from_user: Interactive sector selection
    display_available_options: Show available disaster types and sectors
"""

# Standard library imports
import os
import sys
from typing import List, Optional, Tuple

# Third-party imports
from dotenv import load_dotenv

# Local imports
from utils.article_analyzer import analyze_article
from utils.report_generator import generate_excel_report
from utils.search_api import search_articles

# Configuration constants
DEFAULT_MAX_RESULTS = 30
DEFAULT_OUTPUT_FILE = "disaster_impact_report.xlsx"
MIN_DISASTER_NAME_LENGTH = 2
MAX_DISASTER_NAME_LENGTH = 100

# Define available sectors (moved to constants for better maintainability)
PRIORITY_1_SECTORS = [
    "Chemical",
    "Commercial Facilities",
    "Communications",
    "Critical Manufacturing",
    "Dams",
    "Emergency Services",
    "Information Technology",
    "Nuclear",  # Shortened from "Nuclear Reactors, Materials, and Waste"
    "Transportation",  # Shortened from "Transportation Systems"
    "Government Facilities",
]

PRIORITY_2_SECTORS = [
    "Energy",
    "Water",  # Shortened from "Water and Wastewater Systems"
    "Defense",  # Shortened from "Defense Industrial Base"
    "Financial",  # Shortened from "Financial Services"
    "Healthcare",  # Shortened from "Healthcare and Public Health"
    "Food and Agriculture",
]

ALL_SECTORS = PRIORITY_1_SECTORS + PRIORITY_2_SECTORS

# Define disaster types
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


def main() -> None:
    """
    Main entry point for the disaster impact analysis application.

    Coordinates the entire analysis workflow:
    1. Loads environment configuration
    2. Gathers user input for analysis parameters
    3. Searches for relevant articles
    4. Analyzes article content for impact details
    5. Generates comprehensive Excel report

    Raises:
        SystemExit: If configuration is invalid or critical errors occur
    """
    print("=== Disaster Impact Analysis System ===")
    print("Analyzing disaster impacts on critical infrastructure sectors\n")

    try:
        # Load environment variables
        load_dotenv()
        api_key, search_engine_id = _load_api_configuration()

        # Get analysis parameters from user
        disaster_type, disaster_name = _get_disaster_information()
        selected_sectors = _get_target_sectors()

        # Configure analysis settings
        max_results = DEFAULT_MAX_RESULTS
        output_file = DEFAULT_OUTPUT_FILE

        print(f"\n=== Analysis Configuration ===")
        print(f"Disaster: {disaster_name} ({disaster_type})")
        print(f"Target sectors: {', '.join(selected_sectors)}")
        print(f"Maximum results: {max_results}")
        print(f"Output file: {output_file}")

        # Execute the analysis workflow
        _execute_analysis_workflow(
            disaster_type=disaster_type,
            disaster_name=disaster_name,
            selected_sectors=selected_sectors,
            api_key=api_key,
            search_engine_id=search_engine_id,
            max_results=max_results,
            output_file=output_file,
        )

        print(f"\n=== Analysis Complete ===")
        print(f"Results saved to: {output_file}")
        print("Thank you for using the Disaster Impact Analysis System!")

    except KeyboardInterrupt:
        print("\n\nAnalysis interrupted by user. Exiting...")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {str(e)}")
        print("Please check your configuration and try again.")
        sys.exit(1)


def _load_api_configuration() -> Tuple[str, str]:
    """
    Load and validate API configuration from environment variables.

    Returns:
        Tuple of (api_key, search_engine_id)

    Raises:
        ValueError: If required API credentials are missing
    """
    api_key = os.getenv("api_key")
    search_engine_id = os.getenv("search_engine_id")

    if not api_key:
        raise ValueError(
            "Google API key not found. Please set 'api_key' in your .env file."
        )

    if not search_engine_id:
        raise ValueError(
            "Search engine ID not found. Please set 'search_engine_id' in your .env file."
        )

    return api_key, search_engine_id


def _get_disaster_information() -> Tuple[str, str]:
    """
    Gather disaster type and name from user input.

    Returns:
        Tuple of (disaster_type, disaster_name)
    """
    disaster_type = _get_disaster_type_from_user()
    disaster_name = _get_disaster_name_from_user(disaster_type)

    return disaster_type, disaster_name


def _get_disaster_type_from_user() -> str:
    """
    Interactive disaster type selection with input validation.

    Returns:
        Selected disaster type string
    """
    print("\nAvailable disaster types:")
    for i, disaster_type in enumerate(DISASTER_TYPES, 1):
        print(f"{i:2d}. {disaster_type}")

    while True:
        print(
            f"\nSelect disaster type (1-{len(DISASTER_TYPES)}) or enter 'other' for custom type:"
        )
        user_input = input("> ").strip()

        if user_input.lower() == "other":
            custom_type = input("Enter custom disaster type: ").strip()
            if custom_type:
                return custom_type
            else:
                print("Custom disaster type cannot be empty. Please try again.")
                continue

        try:
            selection = int(user_input)
            if 1 <= selection <= len(DISASTER_TYPES):
                return DISASTER_TYPES[selection - 1]
            else:
                print(f"Please enter a number between 1 and {len(DISASTER_TYPES)}.")
        except ValueError:
            print("Invalid input. Please enter a number or 'other'.")


def _get_disaster_name_from_user(disaster_type: str) -> str:
    """
    Get disaster name from user with validation.

    Args:
        disaster_type: Type of disaster for context in prompt

    Returns:
        Validated disaster name
    """
    while True:
        disaster_name = input(
            f"Enter the {disaster_type} name or event (e.g., Katrina, Camp Fire): "
        ).strip()

        if not disaster_name:
            print("Disaster name cannot be empty. Please try again.")
            continue

        if len(disaster_name) < MIN_DISASTER_NAME_LENGTH:
            print(
                f"Disaster name must be at least {MIN_DISASTER_NAME_LENGTH} characters. Please try again."
            )
            continue

        if len(disaster_name) > MAX_DISASTER_NAME_LENGTH:
            print(
                f"Disaster name must be less than {MAX_DISASTER_NAME_LENGTH} characters. Please try again."
            )
            continue

        return disaster_name


def _get_target_sectors() -> List[str]:
    """
    Interactive sector selection with multiple options.

    Returns:
        List of selected infrastructure sectors
    """
    _display_available_sectors()

    while True:
        print("\nSelect sectors to analyze:")
        print("  • Enter comma-separated numbers (e.g., 1,3,5)")
        print("  • Enter '0' for all sectors")
        print("  • Enter 'p1' for all Priority 1 sectors")
        print("  • Enter 'p2' for all Priority 2 sectors")
        print("  • Enter 'c' for Communications only")

        user_input = input("> ").strip().lower()

        # Handle special selections
        if user_input == "0":
            return ALL_SECTORS.copy()
        elif user_input == "p1":
            return PRIORITY_1_SECTORS.copy()
        elif user_input == "p2":
            return PRIORITY_2_SECTORS.copy()
        elif user_input == "c":
            return ["Communications"]

        # Handle numeric selections
        try:
            sector_indices = [int(idx.strip()) for idx in user_input.split(",")]
            selected_sectors = []

            for idx in sector_indices:
                if 1 <= idx <= len(ALL_SECTORS):
                    selected_sectors.append(ALL_SECTORS[idx - 1])
                else:
                    print(
                        f"Invalid sector number: {idx}. Please use numbers 1-{len(ALL_SECTORS)}."
                    )
                    break
            else:
                # All indices were valid
                if selected_sectors:
                    return selected_sectors
                else:
                    print("No sectors selected. Please select at least one sector.")
        except ValueError:
            print(
                "Invalid input format. Please use comma-separated numbers or special commands."
            )


def _display_available_sectors() -> None:
    """Display available infrastructure sectors organized by priority."""
    print("\nAvailable infrastructure sectors:")

    print("\nPriority 1 Sectors:")
    for i, sector in enumerate(PRIORITY_1_SECTORS, 1):
        print(f"{i:2d}. {sector}")

    print("\nPriority 2 Sectors:")
    for i, sector in enumerate(PRIORITY_2_SECTORS, 1):
        sector_num = i + len(PRIORITY_1_SECTORS)
        print(f"{sector_num:2d}. {sector}")


def _execute_analysis_workflow(
    disaster_type: str,
    disaster_name: str,
    selected_sectors: List[str],
    api_key: str,
    search_engine_id: str,
    max_results: int,
    output_file: str,
) -> None:
    """
    Execute the complete analysis workflow.

    Args:
        disaster_type: Type of disaster being analyzed
        disaster_name: Specific name/event of the disaster
        selected_sectors: List of infrastructure sectors to analyze
        api_key: Google API key
        search_engine_id: Google Custom Search Engine ID
        max_results: Maximum number of search results to process
        output_file: Path for the output Excel report
    """
    # Construct search query
    query = f"{disaster_name} {disaster_type.lower()} effects on US infrastructure"

    print(f"\n=== Searching for Articles ===")
    print(f"Search query: {query}")

    # Search for articles
    results = search_articles(
        query=query,
        api_key=api_key,
        search_engine_id=search_engine_id,
        sectors=selected_sectors,
        max_results=max_results,
        disaster_type=disaster_type,
    )

    if not results:
        print("No relevant articles found. Please try:")
        print("• Different disaster name or type")
        print("• Broader sector selection")
        print("• Different search terms")
        return

    print(f"Found {len(results)} relevant articles")

    # Process articles for detailed analysis
    print(f"\n=== Analyzing Articles ===")
    articles = _process_articles(results, disaster_type)

    if not articles:
        print("No articles could be successfully analyzed.")
        return

    # Generate Excel report
    print(f"\n=== Generating Report ===")
    generate_excel_report(articles, output_file)

    print(f"Successfully analyzed {len(articles)} articles")


def _process_articles(results: List[dict], disaster_type: str) -> List[dict]:
    """
    Process search results to extract detailed article information.

    Args:
        results: List of search result dictionaries
        disaster_type: Type of disaster for analysis context

    Returns:
        List of processed article dictionaries with extracted details
    """
    articles = []
    total_articles = len(results)

    for i, result in enumerate(results, 1):
        article_title = result.get("title", "Unknown Title")
        article_url = result.get("link", "")

        print(f"Processing article {i}/{total_articles}: {article_title[:60]}...")

        try:
            # Analyze article for publication date and impact details
            publication_date, impact_details = analyze_article(
                article_url, disaster_type
            )

            # Update result with analysis
            result["publication_date"] = publication_date or "Date unknown"
            result["disaster_type"] = disaster_type

            # Handle impact details extraction
            if not impact_details or impact_details.strip() == "":
                print(
                    f"  → No specific impact details found, using snippet as fallback"
                )
                impact_details = result.get("snippet", "No details available")
            else:
                word_count = len(impact_details.split())
                print(f"  → Extracted {word_count} words of impact details")

            result["impact_details"] = impact_details
            articles.append(result)

        except Exception as e:
            print(f"  → Error analyzing article: {str(e)}")
            # Add article with error information for transparency
            result["publication_date"] = "Analysis failed"
            result["disaster_type"] = disaster_type
            result["impact_details"] = f"Error during analysis: {str(e)}"
            articles.append(result)

    return articles


def _validate_output_file(output_file: str) -> str:
    """
    Validate and prepare output file path.

    Args:
        output_file: Proposed output file path

    Returns:
        Validated output file path

    Raises:
        ValueError: If output path is invalid
    """
    if not output_file.endswith(".xlsx"):
        output_file += ".xlsx"

    # Ensure directory exists
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir, exist_ok=True)
        except OSError as e:
            raise ValueError(f"Cannot create output directory: {e}")

    return output_file


if __name__ == "__main__":
    main()
# End of src/main.py
