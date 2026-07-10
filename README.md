# Soil Monitoring & Web Scraping Pipeline (MRV)

This repository contains a **Soil Monitoring & Decision Tool** Streamlit application and a **Web Scraping Pipeline** designed to monitor and evaluate **Monitoring, Reporting, and Verification (MRV)** frameworks applied to soil health and carbon sequestration.

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [Folder Structure](#folder-structure)
3. [Streamlit Application (`soil_app`)](#streamlit-application-soil_app)
4. [Data Pipeline & Web Scraping](#data-pipeline--web-scraping)
5. [Requirements & Installation](#requirements--installation)
6. [How to Run](#how-to-run)

---

## Project Overview
The project is built on two primary pillars:
1. **MRV Decision Tool & Explorer (Streamlit)**: An interactive frontend interface displaying statistics, cards, and tables representing 96 distinct soil health and carbon sequestration MRV frameworks. The frameworks come from three separate data sources:
   - Scientific literature review (via Scopus)
   - Web Scraping of certification platforms and methodology docs
   - AI search engines
2. **Company Scraping & Data Pipeline**: Scripts to scrape company domains, search keywords, query autocomplete suggestions, and match similarity (Jaccard similarity) between search terms and domains to dynamically resolve corporate URL details, syncing results to Google Sheets.

---

## Folder Structure
```text
scraping-soil-monitoring/
├── README.md                 # Project documentation (this file)
├── requirements.txt          # Python dependencies
├── main.py                   # Main parallel scraping execution script
├── data/
│   ├── db_articles-11-04-26.txt    # In-scope literature review dataset (Scopus)
│   ├── db_webscraping-27-04-26.txt   # In-scope web-scraped methodologies dataset
│   ├── db_AI-13-04-26.txt          # In-scope AI search dataset
│   └── variables.json              # JSON structure defining database schema & variables
├── soil_app/
│   ├── app.py                # Streamlit Web Application
│   └── app_illustrations/    # Soil landscapes and headers gallery (.jpg illustrations)
└── utils/
    ├── fonctions.py          # Similarity calculations, Jaccard scores, and parsing helpers
    ├── serpscrapor3000.py    # Selenium-based Google Autocomplete scraping script
    └── main_scrap_lambda.py  # Standalone scraping runner syncing to Google Sheets
```

---

## Streamlit Application (`soil_app`)
The Streamlit application provides a premium, dark-themed dashboard designed to help researchers and decision-makers browse and compare MRV protocols:
- **🌐 Bilingual Support**:
  - A dynamic selector in the sidebar allows you to switch between **Français** and **English** on the fly, translating all filters, charts, guide descriptions, metadata, and Pokemon Card statistics.
- **🏠 Home Page**:
  - Displays high-level database metrics (Total frameworks, count per source category).
  - Framework distribution charts based on **Land Use** and **Spatial Scale** (matplotlib/seaborn plots).
  - Searchable **Decision Variables Structure** table describing variables defined in `data/variables.json`.
  - Grid-based uniform **Soil Illustration Gallery** showcasing landscape visuals.
- **🔎 Decision Tool**:
  - Sidebar filters for searching based on search mode (Matching score vs. Strict filtering), Land Uses, Scales, Purpose, Measured Parameters, Data Types, and Verification/Auditing schemes.
  - Excludes variables with >30% missing data (`Auditor`, `Data Sharing`, `Uncertainty`, `Threshold`) from active filtering to avoid categorical statistical bias, while keeping them transparently displayed in the profile.
  - Generates detailed, interactive spec profiles for any selected framework in a split-screen container:
    - **Left Column**: The custom **Pokemon Card** of the selected protocol.
    - **Right Column**: Semantically divided technical specs tabs (*General & Source*, *Context & Stakeholders*, *Monitoring*, *Reporting & Verification*).
- **🗂️ Pokedex (MRV Explorer)**:
  - Select any of the 96 frameworks to see it modeled as a custom, gaming-style **Pokemon Card**!
  - **Refined Card Structure**:
    - **Top-Right Value**: Displays the unique MRV ID (e.g. `MRV5 🌱`) instead of HP.
    - **Center Specs Box (Context)**: Shows Land Uses, Scales, Purpose, and Status.
    - **Three MRV Abilities**:
      1. *Monitoring Component*: Measured parameters and data types.
      2. *Reporting Component*: Report format and baseline thresholds.
      3. *Verification Component*: Verification scheme and auditor type.
    - **Card Footer**: Showcases key categorical metrics (**Status**, **Source**, and **Country**).
- **📚 Articles (Bibliography)**:
  - Search and browse unique publications and platforms associated with the database. Includes external source links and collapsible dropdowns revealing all MRV frameworks linked to each paper.
- **📊 MRV Guide**:
  - Comprehensive technical guide outlining the definitions, variables, and real-time database distribution percentages for all categorical and binary filters.

---

## Data Pipeline & Web Scraping
The data pipeline resides in the root and `utils/` folder:
- **`main.py`**: Executes parallel web-scraping processes utilizing `multiprocessing` worker pools. It reads inputs from a Google Sheet, extracts absent URLs, splits workloads across CPU cores, and performs Jaccard similarity parsing to find optimal domain URLs.
- **`utils/fonctions.py`**: Houses core helper functions:
  - Punctuation removal and text tokenization.
  - URL shortening and domain extraction.
  - **Jaccard Similarity** index calculator (`J = len(intersection) / len(union)`) comparing company names with target search result domains.
  - Exclusions filter (filtering out non-corporate URLs such as Wikipedia, LinkedIn, government sites, etc.).
- **`utils/serpscrapor3000.py`**: Uses Selenium Webdriver to accept cookies on Google, input search terms, fetch Google Autocomplete suggestions, score suggestions, and update runs statistics in a Google Sheet.
- **`utils/main_scrap_lambda.py`**: A sequential scraper script that reads lists of companies, scrapes Google FR search results, cleans outputs, maps Jaccard scores, and updates Google Sheets while firing email notifications on execution status.

---

## Requirements & Installation
Ensure you have Python 3.11+ installed. Install the required python libraries using pip:

```bash
pip install -r requirements.txt
```

*Note: For Selenium features inside `serpscrapor3000.py`, ensure your Google Chrome browser and a matching version of ChromeDriver are installed and in your system path.*

---

## How to Run

### Run the Streamlit Dashboard:
```bash
streamlit run soil_app/app.py
```

### Run the Main Web-scraping Script:
```bash
python main.py
```

---
*Developed for Soil Health and Carbon Sequestration Monitoring Database (MRV).*