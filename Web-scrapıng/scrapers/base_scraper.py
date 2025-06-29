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
    
    def __init__(self, base_url, name, delay_range=(2, 5)):  # Delay'i artırdık
        self.base_url = base_url
        self.name = name
        self.delay_range = delay_range
        self.session = requests.Session()
        
        # Daha güçlü headers ekledik
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        })
        
        # Adapter ile connection pooling ve retry stratejisi
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=3,
            pool_block=False
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(f"{self.name}_scraper")
    
    def get_page(self, url, timeout=30, retries=3):  # Timeout'u 30'a, retry'ı 3'e çıkardık
        """Fetch a web page with retry on failure"""
        for attempt in range(retries):
            try:
                # Her deneme öncesi kısa bekleme
                if attempt > 0:
                    wait_time = attempt * 2  # 2, 4, 6 saniye bekleme
                    self.logger.info(f"Waiting {wait_time} seconds before retry {attempt + 1}")
                    time.sleep(wait_time)
                
                response = self.session.get(
                    url, 
                    timeout=timeout,
                    allow_redirects=True,
                    stream=False  # Büyük dosyaları streaming yapmayalım
                )
                response.raise_for_status()
                return response
                
            except requests.exceptions.Timeout as e:
                self.logger.warning(f"Timeout on attempt {attempt + 1} for {url}: {e}")
            except requests.exceptions.ConnectionError as e:
                self.logger.warning(f"Connection error on attempt {attempt + 1} for {url}: {e}")
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"Request error on attempt {attempt + 1} for {url}: {e}")
            except Exception as e:
                self.logger.warning(f"Unexpected error on attempt {attempt + 1} for {url}: {e}")
                
            # Son deneme değilse bekle
            if attempt < retries - 1:
                self.logger.info(f"Retrying in 3 seconds...")
                time.sleep(3)
        
        self.logger.error(f"Failed after {retries} attempts: {url}")
        return None
    
    def random_delay(self):
        """Add random delay between requests"""
        delay = random.uniform(*self.delay_range)
        self.logger.debug(f"Waiting {delay:.2f} seconds...")
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
        
        self.logger.info(f"Starting scrape for {self.name}")
        
        try:
            article_links = self.get_article_links()
        except Exception as e:
            self.logger.error(f"Failed to get article links for {self.name}: {e}")
            return articles
        
        if not article_links:
            self.logger.warning(f"No article links found for {self.name}")
            return articles
        
        self.logger.info(f"Found {len(article_links)} article links for {self.name}")
        
        successful_scrapes = 0
        for i, url in enumerate(article_links[:max_articles]):
            if not self.is_valid_url(url):
                url = self.make_absolute_url(url)
            
            self.logger.info(f"Scraping article {i+1}/{min(len(article_links), max_articles)}: {url}")
            
            try:
                article = self.scrape_article(url)
                if article:
                    article['source'] = self.name
                    article['scraped_at'] = datetime.now().isoformat()
                    article['id'] = self.generate_article_id(article.get('title', ''), url)
                    articles.append(article)
                    successful_scrapes += 1
                    self.logger.info(f"Successfully scraped: {article.get('title', 'Unknown')[:50]}...")
                else:
                    self.logger.warning(f"No content extracted from: {url}")
                    
            except Exception as e:
                self.logger.error(f"Error scraping article {url}: {e}")
            
            # Her makale sonrası gecikme
            self.random_delay()
        
        self.logger.info(f"Scraping completed for {self.name}: {successful_scrapes}/{min(len(article_links), max_articles)} articles successful")
        return articles
    
    def save_to_database(self, articles, db_path="news.db"):
        """Save articles to SQLite database"""
        if not articles:
            self.logger.warning("No articles to save to database")
            return
            
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
        saved_count = 0
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
                saved_count += 1
            except sqlite3.Error as e:
                self.logger.error(f"Database error for article {article.get('title', 'Unknown')}: {e}")
        
        conn.commit()
        conn.close()
        self.logger.info(f"Saved {saved_count}/{len(articles)} articles to database")