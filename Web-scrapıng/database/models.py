#!/usr/bin/env python3
"""
Database models for the news scraper application
"""

import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import logging

class DatabaseManager:
    """Handles all database operations for the news scraper"""
    
    def __init__(self, db_path: str = "news.db"):
        self.db_path = db_path
        self.logger = logging.getLogger('DatabaseManager')
        self.init_database()
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Initialize database with all required tables"""
        with self.get_connection() as conn:
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
                    url TEXT UNIQUE NOT NULL,
                    source TEXT NOT NULL,
                    category TEXT,
                    scraped_at TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    image_url TEXT,
                    word_count INTEGER DEFAULT 0,
                    sentiment_score REAL DEFAULT 0.0,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            # Sources table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    base_url TEXT,
                    last_scraped TEXT,
                    total_articles INTEGER DEFAULT 0,
                    articles_today INTEGER DEFAULT 0,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Categories table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    display_name TEXT,
                    description TEXT,
                    color TEXT DEFAULT '#3B82F6',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # User preferences
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT DEFAULT 'default',
                    preferred_sources TEXT,  -- JSON array
                    preferred_categories TEXT,  -- JSON array
                    keywords TEXT,  -- JSON array
                    update_frequency INTEGER DEFAULT 3600,  -- seconds
                    max_articles INTEGER DEFAULT 50,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Scraping logs
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scraping_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    articles_found INTEGER DEFAULT 0,
                    articles_saved INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'running',  -- running, completed, failed
                    error_message TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_source ON articles(source)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_category ON articles(category)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_created_at ON articles(created_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_published_date ON articles(published_date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_url ON articles(url)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_active ON articles(is_active)')
            
            # Insert default categories
            default_categories = [
                ('world', 'World News', 'International news and global events', '#EF4444'),
                ('technology', 'Technology', 'Tech news and innovations', '#3B82F6'),
                ('business', 'Business', 'Business and finance news', '#10B981'),
                ('politics', 'Politics', 'Political news and analysis', '#8B5CF6'),
                ('health', 'Health', 'Health and medical news', '#F59E0B'),
                ('science', 'Science', 'Scientific discoveries and research', '#06B6D4'),
                ('sports', 'Sports', 'Sports news and updates', '#F97316'),
                ('entertainment', 'Entertainment', 'Entertainment and celebrity news', '#EC4899'),
                ('general', 'General', 'General news and miscellaneous', '#6B7280')
            ]
            
            for name, display_name, description, color in default_categories:
                cursor.execute('''
                    INSERT OR IGNORE INTO categories (name, display_name, description, color)
                    VALUES (?, ?, ?, ?)
                ''', (name, display_name, description, color))
            
            # Insert default sources
            default_sources = [
                ('BBC News', 'https://www.bbc.com'),
                ('CNN', 'https://www.cnn.com'),
                ('Reuters', 'https://www.reuters.com')
            ]
            
            for name, base_url in default_sources:
                cursor.execute('''
                    INSERT OR IGNORE INTO sources (name, base_url)
                    VALUES (?, ?)
                ''', (name, base_url))
            
            conn.commit()
            self.logger.info("Database initialized successfully")


class Article:
    """Article model for handling article data"""
    
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.title = kwargs.get('title', '')
        self.content = kwargs.get('content', '')
        self.summary = kwargs.get('summary', '')
        self.author = kwargs.get('author', '')
        self.published_date = kwargs.get('published_date', '')
        self.url = kwargs.get('url', '')
        self.source = kwargs.get('source', '')
        self.category = kwargs.get('category', 'general')
        self.scraped_at = kwargs.get('scraped_at', '')
        self.created_at = kwargs.get('created_at', datetime.now().isoformat())
        self.image_url = kwargs.get('image_url', '')
        self.word_count = kwargs.get('word_count', 0)
        self.sentiment_score = kwargs.get('sentiment_score', 0.0)
    
    def to_dict(self) -> Dict:
        """Convert article to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'summary': self.summary,
            'author': self.author,
            'published_date': self.published_date,
            'url': self.url,
            'source': self.source,
            'category': self.category,
            'scraped_at': self.scraped_at,
            'created_at': self.created_at,
            'image_url': self.image_url,
            'word_count': self.word_count,
            'sentiment_score': self.sentiment_score
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Article':
        """Create article from dictionary"""
        return cls(**data)


class ArticleRepository:
    """Repository for article database operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.logger = logging.getLogger('ArticleRepository')
    
    def save_article(self, article: Article) -> bool:
        """Save single article to database"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO articles 
                    (id, title, content, summary, author, published_date, url, source, 
                     category, scraped_at, image_url, word_count, sentiment_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    article.id, article.title, article.content, article.summary,
                    article.author, article.published_date, article.url, article.source,
                    article.category, article.scraped_at, article.image_url,
                    article.word_count, article.sentiment_score
                ))
                conn.commit()
                return True
        except sqlite3.Error as e:
            self.logger.error(f"Error saving article {article.title}: {e}")
            return False
    
    def save_articles(self, articles: List[Article]) -> Tuple[int, int]:
        """Save multiple articles, return (total_processed, new_articles)"""
        total_processed = 0
        new_articles = 0
        
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            for article in articles:
                try:
                    # Check if article exists
                    cursor.execute('SELECT id FROM articles WHERE url = ?', (article.url,))
                    exists = cursor.fetchone()
                    
                    if not exists:
                        cursor.execute('''
                            INSERT INTO articles 
                            (id, title, content, summary, author, published_date, url, source, 
                             category, scraped_at, image_url, word_count, sentiment_score)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            article.id, article.title, article.content, article.summary,
                            article.author, article.published_date, article.url, article.source,
                            article.category, article.scraped_at, article.image_url,
                            article.word_count, article.sentiment_score
                        ))
                        new_articles += 1
                    
                    total_processed += 1
                    
                except sqlite3.Error as e:
                    self.logger.error(f"Error saving article {article.title}: {e}")
            
            conn.commit()
        
        return total_processed, new_articles
    
    def get_articles(self, sources: Optional[List[str]] = None, 
                    categories: Optional[List[str]] = None,
                    keywords: Optional[List[str]] = None,
                    limit: int = 50, offset: int = 0) -> List[Dict]:
        """Get articles with filtering"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM articles WHERE is_active = 1"
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
            
            return [dict(row) for row in rows]
    
    def get_article_by_url(self, url: str) -> Optional[Dict]:
        """Get article by URL"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM articles WHERE url = ? AND is_active = 1', (url,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def delete_old_articles(self, days: int = 30) -> int:
        """Delete articles older than specified days"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE articles 
                SET is_active = 0 
                WHERE created_at < datetime('now', '-{} days')
            '''.format(days))
            deleted_count = cursor.rowcount
            conn.commit()
            self.logger.info(f"Marked {deleted_count} old articles as inactive")
            return deleted_count
    
    def get_statistics(self) -> Dict:
        """Get article statistics"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # Total articles
            cursor.execute('SELECT COUNT(*) FROM articles WHERE is_active = 1')
            stats['total_articles'] = cursor.fetchone()[0]
            
            # Recent articles (24h)
            cursor.execute('''
                SELECT COUNT(*) FROM articles 
                WHERE is_active = 1 AND created_at > datetime('now', '-24 hours')
            ''')
            stats['recent_articles'] = cursor.fetchone()[0]
            
            # Articles by source (24h)
            cursor.execute('''
                SELECT source, COUNT(*) as count 
                FROM articles 
                WHERE is_active = 1 AND created_at > datetime('now', '-24 hours')
                GROUP BY source
            ''')
            stats['articles_by_source'] = dict(cursor.fetchall())
            
            # Articles by category (24h)
            cursor.execute('''
                SELECT category, COUNT(*) as count 
                FROM articles 
                WHERE is_active = 1 AND created_at > datetime('now', '-24 hours')
                GROUP BY category
            ''')
            stats['articles_by_category'] = dict(cursor.fetchall())
            
            # Last update
            cursor.execute('SELECT MAX(created_at) FROM articles WHERE is_active = 1')
            last_update = cursor.fetchone()[0]
            stats['last_updated'] = last_update or 'Never'
            
            return stats


class ScrapingLogRepository:
    """Repository for scraping logs"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.logger = logging.getLogger('ScrapingLogRepository')
    
    def start_scraping_session(self, source: str) -> int:
        """Start a new scraping session and return log ID"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO scraping_logs (source, start_time, status)
                VALUES (?, ?, 'running')
            ''', (source, datetime.now().isoformat()))
            conn.commit()
            return cursor.lastrowid
    
    def end_scraping_session(self, log_id: int, articles_found: int, 
                           articles_saved: int, error_message: Optional[str] = None):
        """End scraping session with results"""
        status = 'failed' if error_message else 'completed'
        
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE scraping_logs 
                SET end_time = ?, articles_found = ?, articles_saved = ?, 
                    status = ?, error_message = ?
                WHERE id = ?
            ''', (
                datetime.now().isoformat(), articles_found, articles_saved,
                status, error_message, log_id
            ))
            conn.commit()
    
    def get_recent_logs(self, limit: int = 100) -> List[Dict]:
        """Get recent scraping logs"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM scraping_logs 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]


# Usage example and testing
if __name__ == "__main__":
    # Initialize database
    db_manager = DatabaseManager("test_news.db")
    article_repo = ArticleRepository(db_manager)
    
    # Create a test article
    test_article = Article(
        id="test_001",
        title="Test Article",
        content="This is a test article content.",
        summary="Test summary",
        author="Test Author",
        url="https://example.com/test",
        source="Test Source",
        category="technology"
    )
    
    # Save article
    success = article_repo.save_article(test_article)
    print(f"Article saved: {success}")
    
    # Get articles
    articles = article_repo.get_articles(limit=10)
    print(f"Found {len(articles)} articles")
    
    # Get statistics
    stats = article_repo.get_statistics()
    print("Statistics:", stats)
