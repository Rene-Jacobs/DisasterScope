# src/utils/search_api.py
import requests


def search_articles(
    query,
    api_key,
    search_engine_id,
    sectors=None,
    max_results=30,
    disaster_type="Hurricane",
):
    """
    Searches Google Custom Search API with the given query and returns a list of results.
    Each result contains the title, URL, and snippet.

    Args:
        query (str): The search query string
        api_key (str): Google API key
        search_engine_id (str): Google Custom Search Engine ID
        sectors (list): List of sectors to search for (defaults to ['Communications'])
        max_results (int): Maximum number of results to return (up to 30)
        disaster_type (str): Type of natural disaster being analyzed

    Returns:
        list: List of dictionaries containing article information
    """
    url = "https://www.googleapis.com/customsearch/v1"
    all_results = []

    # Default to Communications sector if none provided
    if not sectors:
        sectors = ["Communications"]

    # Google Custom Search only returns 10 results per request
    # We need to make up to 3 requests to get 30 results
    for start_index in [1, 11, 21]:
        if len(all_results) >= max_results:
            break

        params = {
            "key": api_key,
            "cx": search_engine_id,
            "q": query,
            "num": 10,  # Max allowed per request is 10
            "start": start_index,
        }

        try:
            print(f"Fetching search results (batch starting at {start_index})...")
            response = requests.get(url, params=params)

            if response.status_code != 200:
                print(f"API request failed with status code {response.status_code}")
                if (
                    start_index > 1
                ):  # Only break on error if we already have some results
                    break
                else:
                    raise Exception(
                        f"Google API request failed with status code {response.status_code}"
                    )

            data = response.json()

            # Check if we got any results
            if "items" not in data:
                print(f"No more results found (batch {start_index})")
                break

            # Process this batch of results
            for item in data.get("items", []):
                # Check if this is a relevant article before adding
                identified_sectors = is_relevant_article(
                    item, query, sectors, disaster_type
                )
                if identified_sectors:
                    result = {
                        "title": item.get("title"),
                        "link": item.get("link"),
                        "snippet": item.get("snippet"),
                        "sectors": identified_sectors,
                        "disaster_type": disaster_type,
                    }
                    all_results.append(result)

                    # Print progress
                    print(
                        f"Found relevant article for sectors {identified_sectors}: {item.get('title')[:60]}..."
                    )
                else:
                    print(f"Skipping irrelevant article: {item.get('title')[:60]}...")

        except Exception as e:
            print(f"Error fetching results (batch {start_index}): {str(e)}")
            # Only break on error if we already have some results
            if start_index > 1 and all_results:
                break
            else:
                raise

    print(f"Total relevant articles found: {len(all_results)}")
    return all_results[:max_results]  # Ensure we don't return more than requested


def is_relevant_article(item, query, sectors, disaster_type):
    """
    Determines if an article is relevant based on its title and snippet,
    and identifies which sectors it covers.

    Args:
        item (dict): Article data from Google API
        query (str): The original search query
        sectors (list): List of sectors to check
        disaster_type (str): Type of natural disaster

    Returns:
        list: List of identified sectors in the article, or empty list if not relevant
    """
    # Extract the important parts of the article preview
    title = item.get("title", "").lower()
    snippet = item.get("snippet", "").lower()
    combined_text = title + " " + snippet

    # Get the main keywords from our query
    query_parts = query.lower().split()

    # Look for disaster name (assuming it's the first word in the query)
    disaster_name = query_parts[0] if query_parts else ""

    # Article must mention the disaster name
    if disaster_name and disaster_name not in combined_text:
        return []

    # Check for disaster type or generic disaster terms
    disaster_type_lower = disaster_type.lower()
    if disaster_type_lower not in combined_text:
        # Check for generic disaster terms as fallback
        generic_disaster_terms = [
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
        if not any(term in combined_text for term in generic_disaster_terms):
            # If neither specific disaster type nor generic terms found, check for type-specific terms
            disaster_specific_terms = {
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
                "tornado": [
                    "twister",
                    "wind",
                    "funnel cloud",
                    "supercell",
                    "rotation",
                    "EF scale",
                ],
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
            # Get terms for this disaster type or use generic list
            type_terms = disaster_specific_terms.get(
                disaster_type_lower, ["impact", "damage"]
            )
            if not any(term in combined_text for term in type_terms):
                return []

    # Check for US references
    us_keywords = ["united states", "u.s.", " us ", "america", "american"]

    # Check for US mention if it was part of the query
    if "us" in query_parts or "u.s." in query_parts:
        has_us_mention = any(keyword in combined_text for keyword in us_keywords)
        if not has_us_mention:
            return []

        # Rest of the function with sector keywords remains the same
        # Dictionary of sector keywords
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

    # Check which sectors are mentioned in the article
    identified_sectors = []
    for sector in sectors:
        if sector in sector_keywords:
            keywords = sector_keywords[sector]
            if any(keyword in combined_text for keyword in keywords):
                identified_sectors.append(sector)

    return identified_sectors
