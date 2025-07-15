# src/main.py
import os
from dotenv import load_dotenv
from utils.search_api import search_articles
from utils.article_analyzer import analyze_article
from utils.report_generator import generate_excel_report


# Define available sectors
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


def main():
    # Load environment variables
    load_dotenv()

    # Configuration Variables
    API_KEY = os.getenv("api_key")
    SEARCH_ENGINE_ID = os.getenv("search_engine_id")
    MAX_RESULTS = 30
    OUTPUT_FILE = "disaster_impact_report.xlsx"

    # Get the disaster type and name from the user
    print("\nAvailable disaster types:")
    for i, disaster_type in enumerate(DISASTER_TYPES, 1):
        print(f"{i}. {disaster_type}")

    print(
        "\nSelect disaster type (number) or enter 'other' to specify a different type:"
    )
    disaster_type_input = input("> ")

    if disaster_type_input.lower() == "other":
        disaster_type = input("Enter disaster type: ")
    else:
        try:
            disaster_type = DISASTER_TYPES[int(disaster_type_input) - 1]
        except (ValueError, IndexError):
            print("Invalid input. Please select a valid disaster type.")
            # Keep prompting until valid input is received
            while True:
                disaster_type_input = input("Select disaster type (number): ")
                try:
                    disaster_type = DISASTER_TYPES[int(disaster_type_input) - 1]
                    break
                except (ValueError, IndexError):
                    print("Invalid input. Please try again.")

    disaster_name = input(
        f"Enter the {disaster_type} name or event (e.g., Katrina, Camp Fire): "
    )

    # Ask for sectors to analyze
    print("\nAvailable sectors:")
    print("Priority 1 Sectors:")
    for i, sector in enumerate(PRIORITY_1_SECTORS, 1):
        print(f"{i}. {sector}")

    print("\nPriority 2 Sectors:")
    for i, sector in enumerate(PRIORITY_2_SECTORS, 1):
        print(f"{i+len(PRIORITY_1_SECTORS)}. {sector}")

    print(
        "\nSelect sectors to analyze (comma-separated numbers, 0 for all, or 'c' for Communications only):"
    )
    sector_input = input("> ")

    selected_sectors = []
    if sector_input.lower() == "c":
        selected_sectors = ["Communications"]
    elif sector_input == "0":
        selected_sectors = ALL_SECTORS
    else:
        try:
            sector_indices = [int(idx.strip()) - 1 for idx in sector_input.split(",")]
            for idx in sector_indices:
                if 0 <= idx < len(ALL_SECTORS):
                    selected_sectors.append(ALL_SECTORS[idx])
        except ValueError:
            print("Invalid input. Defaulting to Communications sector only.")
            selected_sectors = ["Communications"]

    print(f"Selected sectors: {', '.join(selected_sectors)}")

    # Construct the query
    query = f"{disaster_name} {disaster_type.lower()} effects on US infrastructure"

    # Search for articles
    print("Searching for articles...")
    results = search_articles(
        query, API_KEY, SEARCH_ENGINE_ID, selected_sectors, MAX_RESULTS, disaster_type
    )

    print(f"Found {len(results)} articles")

    # Process each article result to extract additional details
    articles = []
    for i, result in enumerate(results):
        print(f"Processing article {i+1}/{len(results)}: {result.get('title')}")
        publication_date, impact_details = analyze_article(
            result["link"], disaster_type
        )
        result["publication_date"] = publication_date
        result["disaster_type"] = disaster_type

        # If we couldn't extract impact details, use the snippet as a fallback
        if not impact_details.strip():
            print(f"  - No specific impact details found, using snippet as fallback")
            impact_details = result.get("snippet", "")
        else:
            print(f"  - Found {len(impact_details.split())} words of impact details")

        result["impact_details"] = impact_details
        articles.append(result)

    # Generate Excel output report
    generate_excel_report(articles, OUTPUT_FILE)
    print(f"Excel report generated: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
