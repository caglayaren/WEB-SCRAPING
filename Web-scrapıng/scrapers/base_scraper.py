import requests
from bs4 import BeautifulSoup
from abc import ABC, abstractmethod
import time
import random
from datetime import datetime
import logging
from urllib.parse import urljoin, urlparse
import sqlite3
import hashlib

class BaseScraper(ABC):
    """Base class for all news scrapers"""
    
    def __init__(self, base_url, name, delay_range=(1, 3)):
        self.base_url = base_url
        self.name = name
        self.delay_range = delay_range
        self.session = requests.Session()
        self.session.headers.update({
            # Daha gerçekçi ve güçlü bir User-Agent
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0'
        })

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(f"{self.name}_scraper")
    
    def get_page(self, url, timeout=15, retries=2):
        """Fetch a web page with retry on failure"""
        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=timeout)
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                self.logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt == retries - 1:
                    self.logger.error(f"Failed after {retries} attempts: {url}")
        return None
    
    def random_delay(self):
        """Add random delay between requests"""
        delay = random.uniform(*self.delay_range)
        time.sleep(delay)
    
    def clean_text(self, text):
        """Clean and normalize text"""
        if not text:
            return ""
        return ' '.join(text.strip().split())
    
    def generate_article_id(self, title, url):
        """Generate unique ID for article"""
        content = f"{title}_{url}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def is_valid_url(self, url):
        """Check if URL is valid"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def make_absolute_url(self, url):
        """Convert relative URL to absolute"""
        if not url:
            return ""
        return urljoin(self.base_url, url)
    
    @abstractmethod
    def get_article_links(self):
        """Get list of article URLs - must be implemented by subclasses"""
        pass
    
    @abstractmethod
    def scrape_article(self, url):
        """Scrape individual article - must be implemented by subclasses"""
        pass
    
    def scrape_all(self, max_articles=50):
        """Scrape multiple articles"""
        articles = []
        article_links = self.get_article_links()
        
        if not article_links:
            self.logger.warning(f"No article links found for {self.name}")
            return articles
        
        for i, url in enumerate(article_links[:max_articles]):
            if not self.is_valid_url(url):
                url = self.make_absolute_url(url)
            
            self.logger.info(f"Scraping article {i+1}/{min(len(article_links), max_articles)}: {url}")
            
            article = self.scrape_article(url)
            if article:
                article['source'] = self.name
                article['scraped_at'] = datetime.now().isoformat()
                article['id'] = self.generate_article_id(article.get('title', ''), url)
                articles.append(article)
            
            self.random_delay()
        
        self.logger.info(f"Successfully scraped {len(articles)} articles from {self.name}")
        return articles
    
    def save_to_database(self, articles, db_path="news.db"):
        """Save articles to SQLite database"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create table if it doesn't exist
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
                image_url TEXT
            )
        ''')
        
        # Insert articles
        for article in articles:
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO articles 
                    (id, title, content, summary, author, published_date, url, source, category, scraped_at, image_url)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    article.get('id'),
                    article.get('title', ''),
                    article.get('content', ''),
                    article.get('summary', ''),
                    article.get('author', ''),
                    article.get('published_date', ''),
                    article.get('url', ''),
                    article.get('source', ''),
                    article.get('category', ''),
                    article.get('scraped_at', ''),
                    article.get('image_url', '')
                ))
            except sqlite3.Error as e:
                self.logger.error(f"Database error for article {article.get('title', 'Unknown')}: {e}")
        
        conn.commit()
        conn.close()
        self.logger.info(f"Saved {len(articles)} articles to database")

