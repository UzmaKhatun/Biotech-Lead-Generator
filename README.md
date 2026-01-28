# 🔬 Biotech Lead Generator

A simple tool that finds and scores potential customers for 3D lab testing equipment.

## What It Does

1. **Finds researchers** - Searches PubMed for scientists working on 3D cell models, drug safety, and liver testing
2. **Gets their info** - Finds work emails, universities, and locations
3. **Scores them** - Gives each person a score (0-100) based on how likely they are to buy
4. **Shows results** - Displays everything in a clean table you can search and download

## Live Demo

👉 **[Try it here](https://biotech-lead-generator.streamlit.app/)**

## Quick Setup

1. **Install Python** if you don't have it
2. **Install requirements:**
```
pip install streamlit pandas requests beautifulsoup4 biopython plotly
```
3. **Run the app:**
```
streamlit run app.py
```

## How to Use
- Open the app in your browser
- Click "Scrape PubMed" in the sidebar
- Wait a few seconds for real data to load
- Search, filter, and download leads as CSV

## Project Structure
```
project/
├── app.py              # Main dashboard
├── requirements.txt    # Python packages
├── config/
│   └── keywords.json  # Search terms and scoring rules
├── src/
│   ├── scraper/       # Gets data from PubMed
│   ├── scoring/       # Calculates scores (0-100)
│   └── utils/         # Cleans data
└── data/              # Saved leads in CSV
```

## Scoring Rules  <br>
People get points for:

- Job title has "toxicology" or "safety" (+30)
- Recent paper in last 2 years (+40)
- Location in biotech hub like Boston (+10)
- Corresponding author (budget holder) (+15)
- University/company uses similar tech (+15)

Example:

- Junior scientist at small startup → Score: 15
- Director at funded biotech in Boston with recent paper → Score: 95

## Real Data Only
#### ⚠️ No fake data - This tool only shows real researchers from PubMed with real:

- Names and universities
- Work emails (not personal Gmail)
- Recent paper titles
- Actual locations

## Output Example

|Rank|	Name	|Title	|Company|	Location	|Score	Email|
|--|-|--|---|--|--|
|1	|Dr. Selene Perales|	Faculty	University of Tennessee	|Memphis, TN	|70	|sperales@uthsc.edu|
|2	|Jennifer Reinhart|	Researcher	University of Illinois|	Urbana, IL|	55	|jreinha2@illinois.edu|


## For Business Teams
### This helps sales teams:

- Find who to contact in research labs
- Know how likely they are to buy
- See where they're located (remote vs office)
- Get work emails for outreach
- Prioritize high-score leads first

## Made With
- Python
- Streamlit (for the web dashboard)
- PubMed API (for real researcher data)
- pandas (for data handling)

## Author
Uzma Khatun <br>
Email : uzmakhatun0205@gmail.com  <br>
Portfolio : https://portfolio-uzmakhatun.netlify.app/   <br>
LinkedIn : https://www.linkedin.com/in/uzma-khatun-88b990334/
