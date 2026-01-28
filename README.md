# Product Price Tracker

A Python-based utility to monitor product prices and send email notifications.

## Features
- **Data Persistence:** Uses SQLite to store price history.
- **Automated Scraping:** Uses BeautifulSoup4 for HTML parsing.
- **Alert System:** SMTP integration for real-time notifications.

## Installation
1. Install dependencies: `pip install -r requirements.txt`
2. Update `notifier.py` with your email and App Password.
3. Run `python main.py`.

## Project Map
- `main.py`: Main execution loop.
- `database.py`: Handles SQL operations.
- `scraper.py`: Extracts price data from URLs.
- `notifier.py`: Email logic.