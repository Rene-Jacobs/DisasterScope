import pandas as pd
import re
from datetime import datetime
from dateutil.relativedelta import relativedelta


def generate_excel_report(articles, output_file):
    """
    Generates an Excel report from the list of articles.

    Args:
        articles (list): List of dictionaries containing article information
        output_file (str): Path to the output Excel file

    Returns:
        None
    """
    # First, consolidate all sectors for each article
    article_data = {}

    for art in articles:
        url = art.get("link", "")
        if not url:
            continue

        # Get sectors associated with this article
        sectors = art.get("sectors", ["Communications"])

        # If this is the first time we've seen this article, initialize its entry
        if url not in article_data:
            # Process impact details
            impact_details = art.get("impact_details", "")

            # Fix failed impact details
            if (
                impact_details.startswith("Error analyzing article:")
                or impact_details.startswith("Failed to retrieve article")
                or impact_details.startswith("This is a .pdf document")
                or impact_details.startswith("Could not parse article")
            ):
                impact_details = "No detailed impact information available. Source may require direct access."

            # Clean publication date
            publication_date = clean_publication_date(art.get("publication_date", ""))

            # Initialize the article data
            article_data[url] = {
                "title": art.get("title", ""),
                "url": url,
                "sectors": set(sectors),
                "impact_details": impact_details,
                "publication_date": publication_date,
            }
        else:
            # Add any new sectors
            article_data[url]["sectors"].update(sectors)

    # Generate report data
    report_data = []

    for url, data in article_data.items():
        # Get all affected sectors as a comma-separated string
        sectors_str = ", ".join(sorted(data["sectors"]))
        impact_details = data["impact_details"]

        # Choose the primary sector for system extraction (first in the list)
        primary_sector = (
            next(iter(data["sectors"])) if data["sectors"] else "Communications"
        )

        # Extract affected systems and other data based on the primary sector
        affected_systems = extract_affected_systems(impact_details, primary_sector)
        impact_scope = extract_impact_scope(impact_details)
        recovery_info = extract_recovery_info(impact_details)

        report_data.append(
            {
                "Article Title": data["title"],
                "Source URL": url,
                "Affected Sector": sectors_str,
                "Affected Systems": affected_systems,
                "Impact Scope": impact_scope,
                "Recovery Status": recovery_info,
                "Date of Publication": data["publication_date"],
                "Key Impact Details": format_impact_details(
                    impact_details, primary_sector
                ),
            }
        )

    # Create DataFrame
    df = pd.DataFrame(report_data)

    # Format Excel output
    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Impact Report", index=False)

        # Get workbook and worksheet
        workbook = writer.book
        worksheet = writer.sheets["Impact Report"]

        # Auto-adjust columns width
        for idx, col in enumerate(df.columns):
            max_len = max(df[col].astype(str).apply(len).max(), len(col) + 2)
            worksheet.column_dimensions[chr(65 + idx)].width = min(
                max_len, 100
            )  # Limit max width

        # Set specific column widths
        worksheet.column_dimensions["B"].width = 45  # URL column
        worksheet.column_dimensions["C"].width = 45  # Affected Sector column
        worksheet.column_dimensions["H"].width = 100  # Key Impact Details

        # Format the Key Impact Details column for better readability
        for row in range(2, len(df) + 2):  # Excel rows start at 1, plus header
            # Set wrap text for Key Impact Details
            cell = worksheet.cell(row=row, column=8)  # Column H
            cell.alignment = cell.alignment.copy(wrapText=True, vertical="top")
            worksheet.row_dimensions[row].height = (
                120  # Set higher row height for impact details
            )

            # Add hyperlinks to URLs
            url_cell = worksheet.cell(row=row, column=2)  # Column B
            url = url_cell.value
            if (
                url
                and isinstance(url, str)
                and (url.startswith("http://") or url.startswith("https://"))
            ):
                url_cell.hyperlink = url
                url_cell.style = "Hyperlink"

    print(f"Generated Excel report at: {output_file}")


def clean_publication_date(date_str):
    """
    Cleans and standardizes publication dates from various formats.

    Args:
        date_str (str): Raw date string

    Returns:
        str: Cleaned date in 'YYYY-MM-DD', 'Month YYYY', or 'Date unknown'
    """
    if (
        not date_str
        or str(date_str).strip().lower() in ["none", "", "nan"]
        or len(str(date_str)) < 4
    ):
        return "Date unknown"

    date_str = str(date_str).strip()

    # Handle abbreviated month only
    short_months = [
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
    if date_str in short_months:
        return f"{date_str} 2024"  # Default fallback year

    # Handle plain year
    if date_str.isdigit() and len(date_str) == 4:
        return date_str

    # Try known formats
    try:
        date_obj = None

        # Handle ISO 8601 format with optional 'Z'
        if "T" in date_str:
            date_obj = datetime.fromisoformat(date_str.replace("Z", "+00:00"))

        # Try common formats (YYYY-MM-DD, DD-MM-YYYY, MM/DD/YYYY, etc.)
        elif "-" in date_str or "/" in date_str or "." in date_str:
            for fmt in (
                "%Y-%m-%d",
                "%d-%m-%Y",
                "%m-%d-%Y",
                "%Y/%m/%d",
                "%d/%m/%Y",
                "%Y.%m.%d",
            ):
                try:
                    date_obj = datetime.strptime(date_str[:10], fmt)
                    break
                except ValueError:
                    continue

        # If parsed, check for future dates beyond 3 months
        if date_obj:
            future_cutoff = datetime.now() + relativedelta(months=3)
            if date_obj > future_cutoff:
                return date_obj.strftime("%Y-%m-%d") + " (future date)"
            return date_obj.strftime("%Y-%m-%d")

    except (ValueError, TypeError):
        pass

    # Attempt to extract a year
    year_match = re.search(r"20\d{2}", date_str)
    if year_match:
        return year_match.group(0)

    return "Date unknown"


def extract_affected_systems(text, sector):
    """
    Extracts information about affected systems from the impact details based on sector.
    """
    systems = []
    text_lower = text.lower()

    # Define patterns for different sectors
    sector_system_patterns = {
        "Communications": {
            "Cellular Networks": [
                r"cell(ular)?\s+(network|tower|service|coverage|infrastructure)",
                r"(mobile|wireless)\s+(network|service|coverage|infrastructure)",
                r"(3g|4g|5g)\s+(network|service|coverage)",
            ],
            "Landlines": [
                r"landline",
                r"(wired|fixed)\s+(phone|telephone)",
                r"phone\s+line",
            ],
            "Internet Service": [
                r"(internet|broadband)\s+(service|access|connection|provider)",
                r"(wifi|wi-fi|wireless\s+internet)",
            ],
            "Fiber Optic Networks": [r"fiber(\s+optic)?", r"optical\s+network"],
            "Satellite Communications": [
                r"satellite\s+(communication|internet|service|phone)"
            ],
            "Broadcast Systems": [r"(radio|tv|television)\s+(station|broadcast|tower)"],
            "Emergency Communications": [
                r"911",
                r"emergency\s+(communication|service|call)",
                r"first\s+responder\s+communication",
            ],
        },
        "Energy": {
            "Power Grid": [
                r"(power|electric)\s+(grid|network|infrastructure)",
                r"transmission\s+(line|system|network)",
                r"substation",
            ],
            "Power Generation": [
                r"(power|generation)\s+(plant|facility|station)",
                r"(coal|nuclear|gas|solar|wind)\s+plant",
                r"generator",
            ],
            "Fuel Distribution": [
                r"(gas|fuel|oil)\s+(pipeline|distribution|supply)",
                r"refinery",
                r"terminal",
            ],
            "Natural Gas": [r"natural\s+gas\s+(line|supply|distribution)"],
        },
        "Water": {
            "Water Treatment": [
                r"water\s+treatment\s+(plant|facility)",
                r"water\s+purification",
            ],
            "Water Distribution": [
                r"water\s+(main|line|pipe|supply|distribution)",
                r"pump\s+station",
            ],
            "Wastewater": [
                r"(wastewater|sewage)\s+(system|treatment|facility|plant)",
                r"sewer",
            ],
            "Drinking Water": [
                r"drinking\s+water",
                r"potable\s+water",
                r"water\s+quality",
            ],
        },
        "Transportation": {
            "Roads & Highways": [
                r"(road|highway|freeway|interstate|bridge)",
                r"traffic",
            ],
            "Railways": [
                r"(railway|railroad|train|rail)\s+(track|line|service|station)",
            ],
            "Airports": [
                r"airport",
                r"flight",
                r"air\s+traffic",
            ],
            "Maritime": [
                r"(port|harbor|seaport|dock)",
                r"(shipping|maritime)\s+(lane|traffic)",
            ],
            "Public Transit": [
                r"(bus|subway|metro|transit|rail)\s+(service|system|station)",
            ],
        },
        "Emergency Services": {
            "Police": [r"police", r"law\s+enforcement"],
            "Fire Services": [r"fire\s+(department|service|station|fighter)"],
            "Medical Response": [r"(ambulance|ems|paramedic|emergency\s+medical)"],
            "Emergency Management": [r"emergency\s+(management|response|center)"],
            "911 Services": [r"911", r"emergency\s+call"],
        },
        "Healthcare": {
            "Hospitals": [r"hospital", r"medical\s+center"],
            "Clinics": [r"(clinic|medical\s+office)"],
            "Long-term Care": [r"(nursing\s+home|care\s+facility|assisted\s+living)"],
            "Pharmacies": [r"pharmacy", r"prescription"],
            "Medical Supply": [r"medical\s+(supply|equipment)"],
        },
        "Chemical": {
            "Chemical Plants": [r"chemical\s+(plant|facility|factory)"],
            "Hazardous Materials": [
                r"(hazardous|toxic)\s+(material|chemical|substance)"
            ],
            "Storage Facilities": [r"chemical\s+(storage|tank|container)"],
            "Distribution": [r"chemical\s+(distribution|transport|pipeline)"],
        },
        "Government Facilities": {
            "Federal Buildings": [r"federal\s+(building|facility|office)"],
            "State/Local Offices": [
                r"(state|local|county|municipal)\s+(building|office|facility)"
            ],
            "Military Installations": [r"(military|base|fort|camp)"],
            "Courthouses": [r"(court|courthouse|judicial)"],
        },
        "Information Technology": {
            "Data Centers": [r"data\s+center"],
            "Network Infrastructure": [r"(it|network)\s+(infrastructure|system)"],
            "Cloud Services": [r"cloud\s+(service|computing|infrastructure)"],
            "Cybersecurity": [r"(cyber|security|hack|breach)"],
        },
        "Financial": {
            "Banks": [r"bank", r"financial\s+institution"],
            "Payment Systems": [r"(payment|transaction)\s+(system|process)"],
            "ATM Networks": [r"atm", r"cash\s+machine"],
            "Financial Markets": [r"(financial|stock|trading)\s+(market|exchange)"],
        },
        "Food and Agriculture": {
            "Farms": [r"farm", r"agricultural\s+land"],
            "Food Processing": [r"food\s+(processing|production|plant)"],
            "Distribution": [r"food\s+(distribution|supply|transport)"],
            "Storage": [r"(silo|warehouse|storage)\s+(facility|center)"],
        },
        "Dams": {
            "Dam Infrastructure": [r"dam\s+(structure|wall|barrier)"],
            "Reservoir": [r"reservoir", r"water\s+storage"],
            "Hydroelectric": [r"hydroelectric", r"hydro\s+power"],
            "Flood Control": [r"flood\s+(control|prevention|mitigation)"],
        },
    }

    # Default to Communications sector if not recognized
    if sector not in sector_system_patterns:
        sector = "Communications"

    # Check for each system type in the specified sector
    for system_name, patterns in sector_system_patterns[sector].items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                if system_name not in systems:
                    systems.append(system_name)

    # Check for specific providers/entities based on sector
    if sector == "Communications":
        provider_patterns = [
            r"(at&t|verizon|t-mobile|sprint|comcast|xfinity|cox|charter|spectrum|centurylink|frontier|dish)"
        ]
    elif sector == "Energy":
        provider_patterns = [
            r"(pg&e|duke energy|southern company|exelon|dominion|nextera|edison|entergy)"
        ]
    elif sector == "Water":
        provider_patterns = [r"(water authority|water district|water company)"]
    else:
        provider_patterns = []

    providers = []
    for pattern in provider_patterns:
        matches = re.findall(pattern, text_lower)
        providers.extend([m.strip() for m in matches if m.strip()])

    if providers:
        unique_providers = list(set(providers))
        provider_str = f"Providers: {', '.join(unique_providers)}"
        systems.append(provider_str)

    if not systems:
        systems = [f"General {sector} Systems"]

    return "; ".join(systems)


def extract_impact_scope(text):
    """
    Extracts information about the scope of the impact.
    """
    text_lower = text.lower()

    # Look for number of affected customers/people
    customer_match = re.search(
        r"(\d[\d,]*)\s+(customer|subscriber|user|people|resident|home)", text_lower
    )
    if customer_match:
        return f"Approximately {customer_match.group(1)} {customer_match.group(2)}s affected"

    # Look for percentage of affected service
    percent_match = re.search(r"(\d+)(\s*)(%|percent)", text_lower)
    if percent_match:
        return f"Approximately {percent_match.group(1)}% affected"

    # Look for geographic scope
    geo_patterns = {
        "Statewide": [r"(state(wide)?|entire\s+state|across\s+the\s+state)"],
        "Regional": [r"(region(al|wide)?|multi-county|several\s+counties)"],
        "Countywide": [r"(county(wide)?|entire\s+county)"],
        "Citywide": [r"(city(wide)?|entire\s+city|across\s+the\s+city)"],
        "Localized": [r"(local(ized)?|limited\s+area|specific\s+area)"],
    }

    for scope, patterns in geo_patterns.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                return scope

    # Look for impact descriptors
    if any(
        term in text_lower for term in ["widespread", "extensive", "massive", "major"]
    ):
        return "Widespread"
    elif any(
        term in text_lower for term in ["significant", "substantial", "considerable"]
    ):
        return "Significant"
    elif any(term in text_lower for term in ["partial", "limited", "minor", "minimal"]):
        return "Limited"

    return "Unspecified scope"


import re

# Precompile patterns
patterns = {
    "fully_restored": re.compile(
        r"\b(service|network|communication|system|facility|operation)\s+(has been|was|were|is)\s+restored\b"
    ),
    "partially_restored": re.compile(
        r"\b(partially|beginning to be|starting to be)\s+restored\b"
    ),
    "estimated_restoration": re.compile(
        r"\b(expected|estimated|projected|anticipate|hope|plan|scheduled)\s+to\s+(restore|resume|fix|repair).{0,50}?\b(by|within|in)\s+(\d+|\w+)\s+(hour|day|week)s?\b"
    ),
    "recovery_efforts": re.compile(
        r"\b(repair|recovery|restoration)\s+(effort|work|operation|activity|crew)s?\b"
    ),
    "still_down": re.compile(
        r"\b(still\s+down|remained\s+offline|continued\s+outage|ongoing\s+disruption|service\s+not\s+yet\s+restored)\b"
    ),
}


def extract_recovery_info(text):
    """
    Extracts high-level information about recovery efforts and timelines from article text.
    Returns one of:
        - 'Fully Restored'
        - 'Partially Restored'
        - 'Estimated restoration in X days/hours'
        - 'Recovery Efforts Underway'
        - 'Service Still Down'
        - 'Recovery Status Unknown'
    """
    text_lower = text.lower()

    if patterns["fully_restored"].search(text_lower):
        return "Fully Restored"

    if patterns["partially_restored"].search(text_lower):
        return "Partially Restored"

    est_match = patterns["estimated_restoration"].search(text_lower)
    if est_match:
        duration = est_match.group(4)
        unit = est_match.group(5)
        return f"Estimated restoration in {duration} {unit}{'s' if not duration.endswith('s') else ''}"

    if patterns["recovery_efforts"].search(text_lower):
        return "Recovery Efforts Underway"

    if patterns["still_down"].search(text_lower):
        return "Service Still Down"

    return "Recovery Status Unknown"


def clean_whitespace(text):
    """
    Removes excessive whitespace from text while preserving intentional formatting.

    Args:
        text (str): Input text with potential whitespace issues

    Returns:
        str: Cleaned text with normalized whitespace
    """
    if not text or not isinstance(text, str):
        return text

    # Remove leading/trailing whitespace
    text = text.strip()

    # Replace multiple consecutive spaces with single space
    text = re.sub(r" +", " ", text)

    # Replace multiple consecutive newlines with double newline (paragraph break)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)

    # Remove spaces at the beginning/end of lines
    text = re.sub(r"^\s+|\s+$", "", text, flags=re.MULTILINE)

    # Remove trailing spaces before newlines
    text = re.sub(r" +\n", "\n", text)

    # Normalize bullet point spacing
    text = re.sub(r"•\s+", "• ", text)

    return text


def format_impact_details(text, sector):
    """
    Formats the impact details for better readability in the report,
    highlighting information relevant to the specified sector.
    """
    # If it's an error message, return a clean message
    if (
        text.startswith("Error analyzing article:")
        or text.startswith("Failed to retrieve article")
        or text.startswith("This is a .pdf document")
        or text.startswith("Could not parse article")
    ):
        return "No detailed impact information available. Source may require direct access."

    # Clean whitespace first
    text = clean_whitespace(text)

    # If the text already has a structured format with bullet points, clean and return it
    if (
        text.startswith("KEY IMPACTS:")
        or text.startswith("STRUCTURED IMPACT DATA:")
        or text.startswith("IMPACT LIST:")
    ):
        return text

    # Otherwise, try to add some formatting
    formatted_text = text

    # Split into sentences and add bullet points for sentences with impact keywords
    impact_keywords = [
        "damage",
        "destroy",
        "disable",
        "disrupt",
        "outage",
        "down",
        "failure",
        "affected",
        "impact",
        "loss",
        "cut",
        "interrupt",
    ]

    # Sector-specific keywords
    sector_keywords = {
        "Communications": [
            "communication",
            "network",
            "cellular",
            "internet",
            "phone",
            "broadband",
        ],
        "Energy": ["power", "electricity", "energy", "grid", "outage", "generation"],
        "Water": ["water", "wastewater", "sewage", "drinking", "treatment"],
        "Transportation": [
            "road",
            "highway",
            "airport",
            "railway",
            "transit",
            "bridge",
        ],
        "Emergency Services": ["emergency", "police", "fire", "ambulance", "rescue"],
        "Healthcare": ["hospital", "medical", "healthcare", "patient", "clinic"],
        "Chemical": ["chemical", "hazardous", "toxic", "plant", "facility"],
        "Government Facilities": [
            "government",
            "federal",
            "state",
            "municipal",
            "building",
        ],
        "Information Technology": ["data", "server", "IT", "network", "cyber"],
        "Financial": ["bank", "financial", "payment", "ATM", "transaction"],
        "Food and Agriculture": ["food", "farm", "agriculture", "crop", "livestock"],
        "Dams": ["dam", "reservoir", "levee", "flood control", "hydroelectric"],
    }

    # Use Communications keywords as default if sector not found
    sector_specific_keywords = sector_keywords.get(
        sector, sector_keywords["Communications"]
    )

    sentences = re.split(r"(?<=[.!?])\s+", text)
    impact_sentences = []
    sector_sentences = []

    for sentence in sentences:
        # Clean each sentence
        sentence = clean_whitespace(sentence)
        if not sentence:  # Skip empty sentences
            continue

        sentence_lower = sentence.lower()
        is_impact = any(keyword in sentence_lower for keyword in impact_keywords)
        is_sector = any(
            keyword in sentence_lower for keyword in sector_specific_keywords
        )

        if is_impact and is_sector:
            impact_sentences.append(f"• {sentence}")
        elif is_sector:
            sector_sentences.append(f"• {sentence}")

    if impact_sentences:
        formatted_text = f"KEY {sector.upper()} IMPACTS:\n" + "\n".join(
            impact_sentences
        )

        # Add other sector-related sentences if available and not already included
        if sector_sentences and len(sector_sentences) > len(impact_sentences):
            formatted_text += (
                f"\n\nADDITIONAL {sector.upper()} INFORMATION:\n"
                + "\n".join(sector_sentences)
            )
    elif sector_sentences:
        formatted_text = f"{sector.upper()} INFORMATION:\n" + "\n".join(
            sector_sentences
        )

    # Final cleanup of the formatted text
    formatted_text = clean_whitespace(formatted_text)

    return formatted_text
