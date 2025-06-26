#!/usr/bin/env python3
"""
Main application runner for the news scraper project
"""

import os
import sys
import argparse
import logging
from datetime import datetime

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from news_scraper import NewsAggregator
from database.models import DatabaseManager
from database.migrations import MigrationManager


def setup_logging(level=logging.INFO):
    """Setup logging configuration"""
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/app.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )


def setup_directories():
    """Create necessary directories"""
    directories = [
        'logs',
        'templates',
        'static/css',
        'static/js',
        'database',
        'scrapers',
        'utils',
        'tests'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✓ Created directory: {directory}")


def run_migrations():
    """Run database migrations"""
    print("Running database migrations...")
    migration_manager = MigrationManager()
    success = migration_manager.migrate_up()
    
    if success:
        print("✓ Database migrations completed successfully")
    else:
        print("✗ Database migrations failed")
        return False
    
    return True


def test_scrapers():
    """Test individual scrapers"""
    print("Testing news scrapers...")
    
    try:
        from scrapers.bbc_scraper import BBCScraper
        from scrapers.cnn_scraper import CNNScraper
        from scrapers.reuters_scraper import ReutersScraper
        
        scrapers = {
            'BBC News': BBCScraper(),
            'CNN': CNNScraper(),
            'Reuters': ReutersScraper()
        }
        
        for name, scraper in scrapers.items():
            try:
                print(f"  Testing {name}...")
                links = scraper.get_article_links()
                print(f"    ✓ Found {len(links)} article links")
                
                if links:
                    # Test scraping first article
                    article = scraper.scrape_article(links[0])
                    if article:
                        print(f"    ✓ Successfully scraped sample article")
                        print(f"      Title: {article.get('title', 'N/A')[:50]}...")
                    else:
                        print(f"    ⚠ Could not scrape sample article")
                
            except Exception as e:
                print(f"    ✗ Error testing {name}: {e}")
        
        print("✓ Scraper testing completed")
        return True
        
    except ImportError as e:
        print(f"✗ Could not import scrapers: {e}")
        return False


def run_scraping_cycle():
    """Run a complete scraping cycle"""
    print("Running news scraping cycle...")
    
    try:
        aggregator = NewsAggregator()
        total_articles, new_articles = aggregator.run_scraping_cycle(max_articles_per_source=10)
        
        print(f"✓ Scraping completed:")
        print(f"  Total articles processed: {total_articles}")
        print(f"  New articles saved: {new_articles}")
        
        # Show some statistics
        stats = aggregator.get_statistics()
        print(f"  Database statistics:")
        print(f"    Total articles in database: {stats['total_articles']}")
        print(f"    Articles in last 24h: {stats['recent_articles']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error during scraping cycle: {e}")
        return False


def start_web_server(host='0.0.0.0', port=5000, debug=False):
    """Start the Flask web server"""
    print(f"Starting web server on {host}:{port}...")
    
    try:
        from app import app
        
        # Ensure templates directory exists and has content
        if not os.path.exists('templates/dashboard.html'):
            print("⚠ Warning: dashboard.html template not found")
            print("  The web interface may not work properly")
        
        print(f"✓ Web server starting...")
        print(f"  Access the dashboard at: http://{host}:{port}")
        print(f"  API endpoints available at: http://{host}:{port}/api/")
        
        app.run(host=host, port=port, debug=debug)
        
    except ImportError as e:
        print(f"✗ Could not import Flask app: {e}")
        return False
    except Exception as e:
        print(f"✗ Error starting web server: {e}")
        return False


def show_status():
    """Show current system status"""
    print("News Scraper System Status")
    print("=" * 50)
    
    # Check database
    try:
        db_manager = DatabaseManager()
        stats = db_manager.get_connection().execute('SELECT COUNT(*) FROM articles').fetchone()[0]
        print(f"✓ Database: Connected ({stats} articles)")
    except Exception as e:
        print(f"✗ Database: Error - {e}")
    
    # Check scrapers
    try:
        aggregator = NewsAggregator()
        print(f"✓ Scrapers: {len(aggregator.scrapers)} configured")
        for name in aggregator.scrapers.keys():
            print(f"    - {name}")
    except Exception as e:
        print(f"✗ Scrapers: Error - {e}")
    
    # Check directories
    required_dirs = ['logs', 'templates', 'static', 'database', 'scrapers']
    for directory in required_dirs:
        if os.path.exists(directory):
            print(f"✓ Directory: {directory}")
        else:
            print(f"✗ Directory: {directory} (missing)")
    
    # Check key files
    key_files = [
        'news_scraper.py',
        'app.py',
        'templates/dashboard.html',
        'scrapers/base_scraper.py'
    ]
    
    for file_path in key_files:
        if os.path.exists(file_path):
            print(f"✓ File: {file_path}")
        else:
            print(f"✗ File: {file_path} (missing)")


def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(description='News Scraper Application')
    parser.add_argument('command', choices=[
        'setup', 'migrate', 'test', 'scrape', 'serve', 'status'
    ], help='Command to run')
    
    parser.add_argument('--host', default='0.0.0.0', help='Web server host')
    parser.add_argument('--port', type=int, default=5000, help='Web server port')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level)
    
    logger = logging.getLogger('NewsScraperApp')
    logger.info(f"Starting news scraper application - Command: {args.command}")
    
    # Execute command
    success = True
    
    if args.command == 'setup':
        print("Setting up news scraper application...")
        setup_directories()
        success = run_migrations()
        if success:
            print("✓ Setup completed successfully!")
            print("\nNext steps:")
            print("  1. Run 'python run.py scrape' to collect initial news articles")
            print("  2. Run 'python run.py serve' to start the web dashboard")
    
    elif args.command == 'migrate':
        success = run_migrations()
    
    elif args.command == 'test':
        success = test_scrapers()
    
    elif args.command == 'scrape':
        success = run_scraping_cycle()
    
    elif args.command == 'serve':
        start_web_server(args.host, args.port, args.debug)
    
    elif args.command == 'status':
        show_status()
    
    if not success:
        sys.exit(1)


if __name__ == '__main__':
    main()