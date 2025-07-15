# Disaster Impact Analysis System

A Python application for analyzing the impact of hurricanes and other disasters on US communications infrastructure. This tool searches for relevant articles, extracts key information, and generates a comprehensive Excel report about communication system outages and disruptions caused by specific disasters.

## Features

* **Automated Article Search** : Uses Google Custom Search API to find articles about specific disasters and their impact on US communications systems
* **Content Analysis** : Extracts publication dates and relevant impact details from articles. If a date can't be determined, the system records "Date unknown".
* **Data Extraction** : Identifies mentions of communications infrastructure damage and outages
* **Report Generation** : Creates Excel reports with organized findings
* **User-friendly GUI** : Easy-to-use interface for setting search parameters and viewing progress
* **Configurable** : Customizable search depth and output locations

### Prerequisites

* Python 3.8 or higher
* Google API Key and Custom Search Engine ID

### Setup

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/disaster-impact-analyzer.gitcd disaster-impact-analyzer
   ```
2. Install required packages:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the root directory with your Google API credentials:
   ```
   api_key=YOUR_GOOGLE_API_KEYsearch_engine_id=YOUR_SEARCH_ENGINE_ID
   ```

## Usage

### GUI Application

1. Launch the GUI application:
   ```
   python src/gui_app.py
   ```
2. Enter the disaster name (e.g., "Hurricane Katrina")
3. Configure search options (number of results, output file path)
4. Click "Start Analysis" to begin
5. Monitor progress in the log window
6. Open the generated Excel report when complete

### Command Line Interface

You can also run the program from the command line:

```
python src/main.py
```

Follow the prompts to enter the disaster name. The program will create an Excel report in the current directory.

## Configuration

### Google Custom Search API

This application uses Google's Custom Search API, which requires:

1. A Google API Key
2. A Custom Search Engine ID

To obtain these:

1. Create a project in the [Google Cloud Console](https://console.cloud.google.com/)
2. Enable the Custom Search API
3. Create API credentials
4. Create a [Custom Search Engine](https://cse.google.com/cse/all) configured to search the entire web

### Search Settings

You can customize:

* Maximum number of search results (up to 100)
* Output file location
* Disaster name and query focus

## Project Structure

* `src/gui_app.py` - Main GUI application
* `src/main.py` - Command-line entry point
* `src/search_api.py` - Google search API integration
* `src/article_analyzer.py` - Web scraping and content analysis
* `src/report_generator.py` - Excel report creation

## Output Format

The generated Excel report includes:

* Article Title
* Source URL
* Affected Sectors (Communications)
* Sector Priority Level
* Date of Publication
* Key Impact Details

## Limitations

* Relies on third-party websites remaining structurally stable
* Google Custom Search API has a free tier limit of 100 searches per day
* May not extract data from all article formats correctly
* Network connectivity required

## Acknowledgements

* This project uses Google's Custom Search API
* Web scraping is performed using BeautifulSoup4
