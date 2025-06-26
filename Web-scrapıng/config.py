import os
from datetime import timedelta

class Config:
    # Database configuration
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'news.db')
    
    # Scraping configuration
    SCRAPING_INTERVAL = int(os.getenv('SCRAPING_INTERVAL', 3600))  # 1 hour in seconds
    ARTICLES_PER_CATEGORY = int(os.getenv('ARTICLES_PER_CATEGORY', 10))
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', 10))
    
    # News sources configuration
    NEWS_SOURCES = {
        'bbc': {
            'name': 'BBC News',
            'base_url': 'https://www.bbc.com',
            'enabled': True,
            'categories': {
                'world': '/news/world',
                'technology': '/news/technology',
                'business': '/news/business',
                'science': '/news/science-environment',
                'health': '/news/health',
                'politics': '/news/politics'
            }
        },
        'cnn': {
            'name': 'CNN',
            'base_url': 'https://www.cnn.com',
            'enabled': True,
            'categories': {
                'world': '/world',
                'technology': '/business/tech',
                'business': '/business',
                'politics': '/politics',
                'health': '/health'
            }
        },
        'reuters': {
            'name': 'Reuters',
            'base_url': 'https://www.reuters.com',
            'enabled': True,
            'categories': {
                'world': '/world/',
                'technology': '/technology/',
                'business': '/business/',
                'markets': '/markets/',
                'sustainability': '/sustainability/'
            }
        }
    }
    
    # Flask configuration
    FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
    
    # User agent for web scraping
    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    
    # Logging configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'news_scraper.log')
