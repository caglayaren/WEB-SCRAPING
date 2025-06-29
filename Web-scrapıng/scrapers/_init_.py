#!/usr/bin/env python3
"""
Main news scraper runner
Collects news from multiple sources and saves to database
"""

import logging
import sqlite3
from datetime import datetime
import concurrent.futures
import threading

# Import scrapers
from bbc_scraper import BBCScraper
from cnn_scraper import CNNScraper
from reuters_scraper import ReutersScraper

class NewsScraperManager:
    """Manages multiple news scrapers"""
    
    def __init__(self, db_path="news.db"):
        self.db_path = db_path
        self.scrapers = {
            'BBC': BBCScraper(),
            'CNN': CNNScraper(),
            'Reuters': ReutersScraper()
        }
        self.setup_database()
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('news_scraper.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('NewsScraperManager')
    
    def setup_database(self):
        """Initialize database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Articles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT,
                summary TEXT,
                author TEXT,
                published_date TEXT,
                url TEXT UNIQUE,
                source TEXT,
                category TEXT,
                scraped_at TEXT,
                image_url TEXT,
                word_count INTEGER,
                sentiment_score REAL
            )
        ''')
        
        # Categories table for dashboard
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Sources table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                base_url TEXT,
                last_scraped TEXT,
                article_count INTEGER DEFAULT 0
            )
        ''')
        
        # User preferences for personalization
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT,
                source TEXT,
                keywords TEXT,
                priority INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        self.logger.info("Database initialized successfully")
    
    def scrape_source(self, source_name, max_articles=20):
        """Scrape articles from a single source"""
        try:
            scraper = self.scrapers[source_name]
            self.logger.info(f"Starting scrape for {source_name}")
            
            articles = scraper.scrape_all(max_articles=max_articles)
            
            if articles:
                # Add word count and basic sentiment
                for article in articles:
                    if article.get('content'):
                        article['word_count'] = len(article['content'].split())
                        # Simple sentiment: count positive/negative words
                        article['sentiment_score'] = self.calculate_basic_sentiment(article['content'])
                
                scraper.save_to_database(articles, self.db_path)
                self.update_source_stats(source_name, len(articles))
                self.logger.info(f"Successfully scraped {len(articles)} articles from {source_name}")
                return articles
            else:
                self.logger.warning(f"No articles scraped from {source_name}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error scraping {source_name}: {e}")
            return []
    
    def calculate_basic_sentiment(self, text):
        """Calculate basic sentiment score (-1 to 1)"""
        if not text:
            return 0.0
        
        positive_words = [
            'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 
            'positive', 'success', 'win', 'achieve', 'breakthrough', 'progress',
            'growth', 'improve', 'benefit', 'gain', 'rise', 'boost'
        ]
        
        negative_words = [
            'bad', 'terrible', 'awful', 'horrible', 'negative', 'fail', 'failure',
            'crisis', 'problem', 'issue', 'concern', 'worry', 'decline', 'fall',
            'drop', 'loss', 'damage', 'threat', 'risk', 'danger'
        ]
        
        words = text.lower().split()
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        
        total_sentiment_words = positive_count + negative_count
        if total_sentiment_