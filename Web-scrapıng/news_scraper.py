#!/usr/bin/env python3
"""
Main NewsAggregator class that coordinates all scrapers
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import os
import sys

# Add scrapers directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'scrapers'))

from scrapers.bbc_scraper import BBCScraper
from scrapers.cnn_scraper import CNNScraper
from scrapers.reuters_scraper import ReutersScraper


class NewsAggregator:
    """Main class that manages all news scrapers and database operations"""
    
    def __init__(self, db_path="news.db"):
        self.db_path = db_path
        self.scrapers = {
            'BBC News': BBCScraper(),
            'CNN': CNNScraper(),
            'Reuters': ReutersScraper()
        }
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/scraper.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('NewsAggregator')
        
        # Ensure logs directory exists
        os.makedirs('logs', exist_ok=True)
        
        # Initialize database
        self.setup_database()
        self._lock = threading.Lock()
    
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
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                image_url TEXT,
                word_count INTEGER,
                sentiment_score REAL
            )
        ''')
        
        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_source ON articles(source)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_category ON articles(category)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON articles(created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_published_date ON articles(published_date)')
        
        # Sources tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sources (
                name TEXT PRIMARY KEY,
                last_scraped TEXT,
                total_articles INTEGER DEFAULT 0,
                articles_today INTEGER DEFAULT 0
            )
        ''')
        
        # Initialize sources
        for source_name in self.scrapers.keys():
            cursor.execute('''
                INSERT OR IGNORE INTO sources (name, last_scraped, total_articles, articles_today)
                VALUES (?, ?, 0, 0)
            ''', (source_name, ''))
        
        conn.commit()
        conn.close()
        self.logger.info("Database initialized successfully")
    
    def scrape_source(self, source_name, max_articles=25):
        """Scrape articles from a single source"""
        try:
            scraper = self.scrapers.get(source_name)
            if not scraper:
                self.logger.error(f"Unknown source: {source_name}")
                return []
            
            self.logger.info(f"Starting scrape for {source_name}")
            articles = scraper.scrape_all(max_articles=max_articles)
            
            if articles:
                # Add additional metadata
                for article in articles:
                    if article.get('content'):
                        article['word_count'] = len(article['content'].split())
                        article['sentiment_score'] = self.calculate_basic_sentiment(article['content'])
                    else:
                        article['word_count'] = 0
                        article['sentiment_score'] = 0.0
                
                # Save to database
                new_count = self.save_articles(articles)
                self.update_source_stats(source_name, len(articles), new_count)
                
                self.logger.info(f"Successfully scraped {len(articles)} articles from {source_name} ({new_count} new)")
                return articles
            else:
                self.logger.warning(f"No articles scraped from {source_name}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error scraping {source_name}: {e}")
            return []
    
    def save_articles(self, articles):
        """Save articles to database, return count of new articles"""
        if not articles:
            return 0
        
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            new_count = 0
            for article in articles:
                try:
                    # Check if article already exists
                    cursor.execute('SELECT id FROM articles WHERE url = ?', (article.get('url', ''),))
                    if cursor.fetchone():
                        continue  # Skip existing articles
                    
                    cursor.execute('''
                        INSERT INTO articles 
                        (id, title, content, summary, author, published_date, url, source, 
                         category, scraped_at, image_url, word_count, sentiment_score)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                        article.get('image_url', ''),
                        article.get('word_count', 0),
                        article.get('sentiment_score', 0.0)
                    ))
                    new_count += 1
                    
                except sqlite3.Error as e:
                    self.logger.error(f"Database error for article {article.get('title', 'Unknown')}: {e}")
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Saved {new_count} new articles to database")
            return new_count
    
    def update_source_stats(self, source_name, total_scraped, new_articles):
        """Update source statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE sources 
            SET last_scraped = ?, total_articles = total_articles + ?, articles_today = articles_today + ?
            WHERE name = ?
        ''', (datetime.now().isoformat(), new_articles, new_articles, source_name))
        
        conn.commit()
        conn.close()
    
    def run_scraping_cycle(self, max_articles_per_source=25):
        """Run a complete scraping cycle for all sources"""
        self.logger.info("Starting news scraping cycle")
        start_time = datetime.now()
        
        total_articles = 0
        new_articles = 0
        
        # Use ThreadPoolExecutor for concurrent scraping
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_source = {
                executor.submit(self.scrape_source, source_name, max_articles_per_source): source_name
                for source_name in self.scrapers.keys()
            }
            
            for future in as_completed(future_to_source):
                source_name = future_to_source[future]
                try:
                    articles = future.result()
                    if articles:
                        total_articles += len(articles)
                        # Count new articles (this is approximate since we're running concurrent)
                        new_articles += len(articles)
                except Exception as e:
                    self.logger.error(f"Error in scraping {source_name}: {e}")
        
        duration = datetime.now() - start_time
        self.logger.info(f"Scraping cycle completed in {duration.total_seconds():.2f} seconds. "
                        f"Total: {total_articles} articles, New: {new_articles}")
        
        return total_articles, new_articles
    
    def get_articles(self, sources=None, categories=None, keywords=None, limit=50, offset=0):
        """Get articles with filtering options"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        cursor = conn.cursor()
        
        # Build query
        query = "SELECT * FROM articles WHERE 1=1"
        params = []
        
        if sources:
            placeholders = ','.join(['?' for _ in sources])
            query += f" AND source IN ({placeholders})"
            params.extend(sources)
        
        if categories:
            placeholders = ','.join(['?' for _ in categories])
            query += f" AND LOWER(category) IN ({placeholders})"
            params.extend([cat.lower() for cat in categories])
        
        if keywords:
            keyword_conditions = []
            for keyword in keywords:
                if keyword.strip():
                    keyword_conditions.append("(LOWER(title) LIKE ? OR LOWER(content) LIKE ?)")
                    keyword_term = f"%{keyword.strip().lower()}%"
                    params.extend([keyword_term, keyword_term])
            
            if keyword_conditions:
                query += " AND (" + " OR ".join(keyword_conditions) + ")"
        
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Convert to dictionaries
        articles = []
        for row in rows:
            article = dict(row)
            # Add computed fields
            article['link'] = article['url']  # For template compatibility
            articles.append(article)
        
        conn.close()
        return articles
    
    def calculate_basic_sentiment(self, text):
        """Calculate basic sentiment score (-1 to 1)"""
        if not text:
            return 0.0
        
        positive_words = [
            'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 
            'positive', 'success', 'win', 'achieve', 'breakthrough', 'progress',
            'growth', 'improve', 'benefit', 'gain', 'rise', 'boost', 'strong',
            'effective', 'efficient', 'innovative', 'outstanding', 'remarkable'
        ]
        
        negative_words = [
            'bad', 'terrible', 'awful', 'horrible', 'negative', 'fail', 'failure',
            'crisis', 'problem', 'issue', 'concern', 'worry', 'decline', 'fall',
            'drop', 'loss', 'damage', 'threat', 'risk', 'danger', 'weak',
            'poor', 'disappointing', 'concerning', 'alarming', 'devastating'
        ]
        
        words = text.lower().split()
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        
        total_sentiment_words = positive_count + negative_count
        if total_sentiment_words == 0:
            return 0.0
        
        return (positive_count - negative_count) / total_sentiment_words
    
    def get_statistics(self):
        """Get aggregated statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        # Total articles
        cursor.execute('SELECT COUNT(*) FROM articles')
        stats['total_articles'] = cursor.fetchone()[0]
        
        # Articles in last 24 hours
        cursor.execute("SELECT COUNT(*) FROM articles WHERE created_at > datetime('now', '-24 hours')")
        stats['recent_articles'] = cursor.fetchone()[0]
        
        # Articles by source
        cursor.execute('''
            SELECT source, COUNT(*) as count 
            FROM articles 
            WHERE created_at > datetime('now', '-24 hours')
            GROUP BY source
        ''')
        stats['articles_by_source'] = dict(cursor.fetchall())
        
        # Articles by category
        cursor.execute('''
            SELECT category, COUNT(*) as count 
            FROM articles 
            WHERE created_at > datetime('now', '-24 hours')
            GROUP BY category
        ''')
        stats['articles_by_category'] = dict(cursor.fetchall())
        
        # Last update time
        cursor.execute('SELECT MAX(created_at) FROM articles')
        last_update = cursor.fetchone()[0]
        stats['last_updated'] = last_update or 'Never'
        
        conn.close()
        return stats


if __name__ == "__main__":
    # Test the news aggregator
    aggregator = NewsAggregator()
    total, new = aggregator.run_scraping_cycle(max_articles_per_source=5)
    print(f"Scraping completed: {total} total articles, {new} new articles")
    
    # Get some articles
    articles = aggregator.get_articles(limit=10)
    print(f"\nFound {len(articles)} articles:")
    for article in articles:
        print(f"- {article['title']} ({article['source']})")
