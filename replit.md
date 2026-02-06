# AI Health News to Instagram Pipeline

## Overview
This is a Python automation pipeline that:
1. Ingests health news from RSS feeds
2. Matches articles to supplement products from a catalog
3. Generates AI-powered captions
4. Posts content to Instagram via the Postly API

## Project Structure
- `main.py` - Main entry point, runs the daily pipeline
- `config.py` - Centralized configuration from environment variables
- `rss_ingest.py` - Fetches and parses RSS feeds
- `matcher.py` - Matches news articles to products
- `caption_writer.py` - Generates AI captions using OpenAI/Novita
- `safety_filter.py` - Filters out inappropriate content
- `postly_client.py` - Handles posting to Postly API
- `catalog_service.py` - Manages product catalog data
- `logger.py` - Logging to SQLite and Google Sheets
- `preview_post.py` - Preview functionality

## Data Files
- `Brands.csv` - Brand configuration
- `Product_Info.csv` - Product catalog
- `data/logs.sqlite` - SQLite database for logging

## Environment Variables
See `.env.example` for required configuration:
- `NOVITA_API_KEY` - API key for Novita AI
- `POSTLY_API_KEY` - API key for Postly
- `GOOGLE_SHEET_ID` - Google Sheet for logging
- `GOOGLE_SHEETS_CREDENTIALS_JSON` - Google Sheets credentials
- Various threshold and configuration settings

## Running
Execute `python main.py` to run the daily pipeline.
