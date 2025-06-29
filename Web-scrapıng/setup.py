#!/usr/bin/env python3
"""
Easy setup script for the News Scraper project
"""

import os
import sys
import subprocess
import platform

def print_banner():
    """Print welcome banner"""
    print("=" * 60)
    print("   📰 Personal News Dashboard - Setup Script 📰")
    print("=" * 60)
    print()

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print("❌ Python 3.7 or higher is required")
        print(f"   Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    
    print(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
    return True

def install_dependencies():
    """Install required Python packages"""
    print("\n📦 Installing dependencies...")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")
    
    directories = [
        'logs',
        'static/css',
        'static/js',
        'templates/components'
    ]
    
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"✅ Created: {directory}")
        except Exception as e:
            print(f"❌ Failed to create {directory}: {e}")
            return False
    
    return True

def setup_database():
    """Initialize database"""
    print("\n🗄️  Setting up database...")
    
    try:
        # Import here to avoid import errors before dependencies are installed
        from database.models import DatabaseManager
        from database.migrations import MigrationManager
        
        # Initialize database
        db_manager = DatabaseManager()
        print("✅ Database initialized")
        
        # Run migrations
        migration_manager = MigrationManager()
        success = migration_manager.migrate_up()
        
        if success:
            print("✅ Database migrations completed")
            return True
        else:
            print("❌ Database migrations failed")
            return False
            
    except ImportError as e:
        print(f"❌ Database setup failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def test_scrapers():
    """Test scraper functionality"""
    print("\n🔍 Testing scrapers...")
    
    try:
        from scrapers.bbc_scraper import BBCScraper
        from scrapers.cnn_scraper import CNNScraper
        from scrapers.reuters_scraper import ReutersScraper
        
        scrapers = [
            ('BBC News', BBCScraper()),
            ('CNN', CNNScraper()),
            ('Reuters', ReutersScraper())
        ]
        
        for name, scraper in scrapers:
            try:
                # Test basic functionality
                links = scraper.get_article_links()
                if links:
                    print(f"✅ {name}: {len(links)} links found")
                else:
                    print(f"⚠️  {name}: No links found (may be temporary)")
            except Exception as e:
                print(f"❌ {name}: Error - {e}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Scraper test failed: {e}")
        return False

def run_initial_scrape():
    """Run initial news scraping"""
    print("\n📰 Running initial news scraping...")
    
    try:
        from news_scraper import NewsAggregator
        
        aggregator = NewsAggregator()
        total_articles, new_articles = aggregator.run_scraping_cycle(max_articles_per_source=5)
        
        print(f"✅ Scraping completed:")
        print(f"   📄 Total articles: {total_articles}")
        print(f"   🆕 New articles: {new_articles}")
        
        return True
        
    except Exception as e:
        print(f"❌ Initial scraping failed: {e}")
        print("   You can run scraping later with: python run.py scrape")
        return False

def show_next_steps():
    """Show next steps to user"""
    print("\n" + "=" * 60)
    print("🎉 Setup completed successfully!")
    print("=" * 60)
    print("\n📋 Next steps:")
    print("   1. Start the web server:")
    print("      python run.py serve")
    print()
    print("   2. Open your browser and go to:")
    print("      http://localhost:5000")
    print()
    print("   3. Other useful commands:")
    print("      python run.py scrape    # Scrape latest news")
    print("      python run.py status    # Check system status")
    print("      python run.py test      # Test scrapers")
    print()
    print("📖 For more information, see README.md")
    print("=" * 60)

def main():
    """Main setup function"""
    print_banner()
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Setup failed at dependency installation")
        sys.exit(1)
    
    # Create directories
    if not create_directories():
        print("\n❌ Setup failed at directory creation")
        sys.exit(1)
    
    # Setup database
    if not setup_database():
        print("\n❌ Setup failed at database initialization")
        sys.exit(1)
    
    # Test scrapers
    test_scrapers()  # Non-critical, continue even if fails
    
    # Run initial scrape
    run_initial_scrape()  # Non-critical, continue even if fails
    
    # Show next steps
    show_next_steps()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error during setup: {e}")
        sys.exit(1)