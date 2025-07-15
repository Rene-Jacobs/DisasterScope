# Disaster Impact Analysis System Documentation

This document provides a detailed explanation of the Disaster Impact Analysis System, a Python-based tool designed to analyze how disasters affect communications infrastructure in the United States. I'll explain each file in the system to help you understand the purpose and functionality, even if you have no programming experience.

## Overview of the System

The Disaster Impact Analysis System searches for articles about specific disasters and analyzes how these disasters have impacted communications systems like cell towers, internet services, and phone lines. The system automatically collects information from the web, processes it, and generates a structured report that highlights the communications impacts.

## Files in the System

Let's look at each file and its purpose:

### 1. main.py

 **Purpose** : This is the main entry point for the command-line version of the application.

 **What it does** :

* Loads API credentials from a .env file
* Gets a disaster name from the user
* Performs a search for articles about that disaster's impact on communications
* Processes each article to extract relevant information
* Generates an Excel report with the findings

 **How it works** :

* The program starts by asking you to type in a disaster name (like "Hurricane Katrina")
* It constructs a search query based on your input
* It calls other parts of the system to search for articles, analyze them, and create a report
* The results are saved to an Excel file named "communications_hurricane_report.xlsx"

This file essentially coordinates the workflow of the entire application when running it from the command line.

### 2. gui_app.py

 **Purpose** : This provides a graphical user interface (GUI) for the application, making it easier to use for non-technical users.

 **What it does** :

* Creates windows, buttons, text fields, and other visual elements
* Lets users input disaster names, configuration options, and output file locations
* Shows progress of the analysis in real-time
* Manages the analysis process in the background so the interface stays responsive

 **How it works** :

* The application window has two tabs: "Search" and "Settings"
* The Search tab contains:
  * Fields to enter the disaster name and maximum results to retrieve
  * A field to specify where to save the Excel report
  * Buttons to start/stop the analysis and open the results file
  * A log area that shows what's happening in real-time
  * A progress bar to show completion status
* The Settings tab contains:
  * Fields for Google API key and Search Engine ID
  * A button to save these settings
  * Help text explaining how to use the application

This file handles everything related to the visual interface, allowing users to interact with the application through a window rather than typing commands.

### 3. search_api.py

 **Purpose** : This file handles communication with Google's Custom Search API to find relevant articles about disaster impacts.

 **What it does** :

* Connects to Google's search service
* Sends queries about disasters and communications impacts
* Processes the search results
* Filters out irrelevant articles

 **How it works** :

* The `search_articles` function:
  * Connects to Google's Custom Search API
  * Makes up to 3 requests to get a maximum of 30 results
  * For each batch of results, it checks whether each article is relevant
  * It collects all relevant articles up to the maximum requested
* The `is_relevant_article` function:
  * Checks if an article mentions the disaster name
  * Verifies that it talks about communications systems
  * Makes sure it's related to the US (if that was part of the search)

This file is responsible for the first stage of the process: finding articles that might contain information about how a disaster affected communications systems.

### 4. article_analyzer.py

 **Purpose** : This file is responsible for extracting detailed information from each article found by the search.

 **What it does** :

* Visits each article's webpage
* Extracts the publication date
* Identifies paragraphs that mention communications impacts
* Structures this information for easier analysis

 **How it works** :
The file contains several functions that work together:

* `analyze_article`: The main function that:
  * Retrieves the article content from the web
  * Extracts publication date
  * Extracts impact details
  * Formats the extracted information
* `extract_publication_date`: Tries multiple methods to find when the article was published, including:
  * Looking for date meta tags
  * Checking structured data
  * Searching for date patterns in the text
  * Examining time tags and date classes
* `extract_impact_details`: Finds information about how communications were affected:
  * Scores paragraphs based on their relevance to communications impacts
  * Identifies sentences with high impact value
  * Formats the information with clear sections
* `extract_main_content`: Identifies the main content area of the article to focus analysis there.
* `process_general_content`: Processes the main content to find communications-related information.
* `format_impact_details`: Makes the impact information more readable by organizing it with bullet points.
* `extract_structured_impact_data`: Extracts impact information from structured data like tables and lists.

This file does the detailed analysis work, acting like a researcher who reads each article and pulls out the most relevant information about communications impacts.

### 5. report_generator.py

 **Purpose** : This file creates the final Excel report that organizes all the gathered information.

 **What it does** :

* Takes the processed article information
* Extracts additional structured data about impacts
* Creates and formats an Excel spreadsheet
* Organizes the information into clear categories

 **How it works** :

* The `generate_excel_report` function:
  * Processes each article to extract structured data
  * Creates a DataFrame (a table-like structure)
  * Formats and saves the data to an Excel file
  * Adjusts column widths and row heights for better readability
* Helper functions extract specific types of information:
  * `extract_affected_systems`: Identifies which communications systems were affected (cellular networks, landlines, internet, etc.)
  * `extract_impact_scope`: Determines the geographical extent of the impact
  * `extract_recovery_info`: Extracts information about recovery efforts and timelines
  * `format_impact_details`: Makes the impact information more readable

This file creates the final product - an organized Excel report that shows what communications systems were affected, how extensive the impact was, and what's being done to recover.

### 6. .env

 **Purpose** : This is a configuration file that stores API keys and other sensitive information.

 **What it does** :

* Stores your Google API key
* Stores your custom search engine ID
* Keeps this sensitive information separate from the code

 **How it works** :

* The file simply contains key-value pairs:
  * `api_key` stores your Google API key
  * `search_engine_id` stores your custom search engine ID
* The application reads these values when it starts

This file helps keep your private API credentials separate from the code, which is a security best practice.

## How These Files Work Together

1. The user starts either `main.py` (command line) or `gui_app.py` (graphical interface)
2. The application gets the disaster name and loads API credentials from `.env`
3. `search_api.py` is used to find relevant articles about the disaster
4. For each article found, `article_analyzer.py` extracts the publication date and impact details
5. Finally, `report_generator.py` takes all this information and creates an organized Excel report

The system automates what would otherwise be a manual research process:

1. Searching for information about disaster impacts on communications
2. Reading through articles to find relevant details
3. Organizing this information into a structured format

The end result is a spreadsheet that shows which communications systems were affected, the scope of the impact, and recovery status - all collected and organized automatically.

## Detailed Workflows

### Search Process:

1. The application constructs a specific search query using the disaster name (e.g., "Hurricane Katrina effects on US communications systems infrastructure")
2. It sends this query to Google's Custom Search API
3. The API returns links to relevant articles, along with titles and snippets
4. The application filters these results to ensure they're relevant to the disaster and communications impacts
5. Up to 30 of the most relevant results are selected for further analysis

### Article Analysis Process:

1. For each article link:
   * The application visits the webpage
   * It downloads the HTML content
   * It parses the HTML to extract text
   * It looks for the publication date using multiple methods
   * It identifies paragraphs about communications impacts
   * It scores these paragraphs based on relevance
   * It extracts the most informative content
2. Types of information extracted:
   * Affected systems (cell networks, landlines, fiber optic, etc.)
   * Impact scope (how many customers/areas affected)
   * Recovery information (timeline, current status)
   * Specific impact details (what happened and how)

### Report Generation Process:

1. The application organizes all the collected information into categories
2. It creates an Excel spreadsheet with columns for:
   * Article Title
   * Source URL
   * Affected Sectors (always "Communications" in this application)
   * Affected Systems (which specific systems were impacted)
   * Impact Scope (how widespread was the impact)
   * Recovery Status (what's being done to restore service)
   * Date of Publication
   * Key Impact Details (specific information about what happened)
3. It formats the spreadsheet for readability:
   * Adjusts column widths
   * Sets appropriate row heights for detailed text
   * Structures impact details with bullet points when possible

## Benefits of the System

1. **Time Efficiency** : Automatically collects information that would take hours or days to gather manually.
2. **Comprehensiveness** : Systematically searches for and processes multiple sources.
3. **Structured Output** : Organizes information into clear categories that highlight the most important aspects of communications impacts.
4. **User-Friendly** : Provides both command-line and graphical interfaces to accommodate different user preferences.
5. **Adaptability** : Can be used to analyze any disaster by simply changing the input name.

## Technical Aspects (For Those Interested)

* The system is built entirely in Python, a popular programming language.
* It uses several Python libraries:
  * `requests` for fetching web content
  * `BeautifulSoup` for parsing HTML
  * `pandas` for data manipulation and Excel creation
  * `tkinter` for the graphical interface
  * `re` (regular expressions) for pattern matching in text
  * `threading` for background processing in the GUI
  * `dotenv` for loading environment variables
* The article analysis uses a sophisticated scoring system to identify relevant content, considering:
  * Mentions of communications systems
  * References to specific providers
  * Impact verbs and nouns
  * Scope and location keywords
  * References to communications services
  * Duration and recovery information
* The report generator uses natural language processing techniques to extract structured information from unstructured text.

This documentation should provide a comprehensive understanding of the Disaster Impact Analysis System, whether you're a non-technical user or someone interested in the underlying technical details.
