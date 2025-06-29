#!/usr/bin/env python3
"""
Database migrations for the news scraper application
"""

import sqlite3
import logging
from datetime import datetime
from typing import List, Callable, Dict

class Migration:
    """Base migration class"""
    
    def __init__(self, version: str, description: str):
        self.version = version
        self.description = description
        self.timestamp = datetime.now().isoformat()
    
    def up(self, cursor: sqlite3.Cursor):
        """Apply migration"""
        raise NotImplementedError("Migration must implement up() method")
    
    def down(self, cursor: sqlite3.Cursor):
        """Rollback migration"""
        raise NotImplementedError("Migration must implement down() method")


class MigrationManager:
    """Manages database migrations"""
    
    def __init__(self, db_path: str = "news.db"):
        self.db_path = db_path
        self.logger = logging.getLogger('MigrationManager')
        self.migrations: List[Migration] = []
        self._init_migration_table()
        self._register_migrations()
    
    def _init_migration_table(self):
        """Initialize migrations tracking table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS migrations (
                version TEXT PRIMARY KEY,
                description TEXT,
                applied_at TEXT,
                rollback_sql TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _register_migrations(self):
        """Register all available migrations"""
        self.migrations = [
            Migration001AddSentimentScoring(),
            Migration002AddUserPreferences(),
            Migration003AddScrapingLogs(),
            Migration004AddArticleIndexes(),
            Migration005AddImageSupport(),
            Migration006AddCategoryColors(),
            Migration007AddArticleWordCount(),
            Migration008AddSourceTracking()
        ]
    
    def get_applied_migrations(self) -> List[str]:
        """Get list of applied migration versions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT version FROM migrations ORDER BY applied_at')
        versions = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        return versions
    
    def apply_migration(self, migration: Migration) -> bool:
        """Apply a single migration"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check if already applied
            cursor.execute('SELECT version FROM migrations WHERE version = ?', (migration.version,))
            if cursor.fetchone():
                self.logger.info(f"Migration {migration.version} already applied")
                return True
            
            # Apply migration
            self.logger.info(f"Applying migration {migration.version}: {migration.description}")
            migration.up(cursor)
            
            # Record migration
            cursor.execute('''
                INSERT INTO migrations (version, description, applied_at)
                VALUES (?, ?, ?)
            ''', (migration.version, migration.description, datetime.now().isoformat()))
            
            conn.commit()
            self.logger.info(f"Migration {migration.version} applied successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error applying migration {migration.version}: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def rollback_migration(self, migration: Migration) -> bool:
        """Rollback a single migration"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            self.logger.info(f"Rolling back migration {migration.version}")
            migration.down(cursor)
            
            # Remove migration record
            cursor.execute('DELETE FROM migrations WHERE version = ?', (migration.version,))
            
            conn.commit()
            self.logger.info(f"Migration {migration.version} rolled back successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error rolling back migration {migration.version}: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def migrate_up(self) -> bool:
        """Apply all pending migrations"""
        applied_versions = self.get_applied_migrations()
        pending_migrations = [m for m in self.migrations if m.version not in applied_versions]
        
        if not pending_migrations:
            self.logger.info("No pending migrations")
            return True
        
        self.logger.info(f"Applying {len(pending_migrations)} pending migrations")
        
        for migration in pending_migrations:
            if not self.apply_migration(migration):
                self.logger.error(f"Failed to apply migration {migration.version}")
                return False
        
        self.logger.info("All migrations applied successfully")
        return True
    
    def migrate_down(self, steps: int = 1) -> bool:
        """Rollback specified number of migrations"""
        applied_versions = self.get_applied_migrations()
        
        if not applied_versions:
            self.logger.info("No migrations to rollback")
            return True
        
        # Get migrations to rollback (in reverse order)
        migrations_to_rollback = []
        for version in reversed(applied_versions[-steps:]):
            migration = next((m for m in self.migrations if m.version == version), None)
            if migration:
                migrations_to_rollback.append(migration)
        
        for migration in migrations_to_rollback:
            if not self.rollback_migration(migration):
                self.logger.error(f"Failed to rollback migration {migration.version}")
                return False
        
        self.logger.info(f"Rolled back {len(migrations_to_rollback)} migrations")
        return True


# Individual Migration Classes

class Migration001AddSentimentScoring(Migration):
    """Add sentiment scoring capability to articles"""
    
    def __init__(self):
        super().__init__("001", "Add sentiment scoring to articles")
    
    def up(self, cursor: sqlite3.Cursor):
        cursor.execute('ALTER TABLE articles ADD COLUMN sentiment_score REAL DEFAULT 0.0')
    
    def down(self, cursor: sqlite3.Cursor):
        # SQLite doesn't support DROP COLUMN, so we'd need to recreate table
        # For simplicity, we'll just set values to NULL
        cursor.execute('UPDATE articles SET sentiment_score = NULL')


class Migration002AddUserPreferences(Migration):
    """Add user preferences table"""
    
    def __init__(self):
        super().__init__("002", "Add user preferences functionality")
    
    def up(self, cursor: sqlite3.Cursor):
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT DEFAULT 'default',
                preferred_sources TEXT,
                preferred_categories TEXT,
                keywords TEXT,
                update_frequency INTEGER DEFAULT 3600,
                max_articles INTEGER DEFAULT 50,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    
    def down(self, cursor: sqlite3.Cursor):
        cursor.execute('DROP TABLE IF EXISTS user_preferences')


class Migration003AddScrapingLogs(Migration):
    """Add scraping logs table"""
    
    def __init__(self):
        super().__init__("003", "Add scraping logs for monitoring")
    
    def up(self, cursor: sqlite3.Cursor):
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scraping_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT,
                articles_found INTEGER DEFAULT 0,
                articles_saved INTEGER DEFAULT 0,
                status TEXT DEFAULT 'running',
                error_message TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    
    def down(self, cursor: sqlite3.Cursor):
        cursor.execute('DROP TABLE IF EXISTS scraping_logs')


class Migration004AddArticleIndexes(Migration):
    """Add database indexes for better performance"""
    
    def __init__(self):
        super().__init__("004", "Add database indexes for performance")
    
    def up(self, cursor: sqlite3.Cursor):
        indexes = [
            'CREATE INDEX IF NOT EXISTS idx_articles_source ON articles(source)',
            'CREATE INDEX IF NOT EXISTS idx_articles_category ON articles(category)',
            'CREATE INDEX IF NOT EXISTS idx_articles_created_at ON articles(created_at)',
            'CREATE INDEX IF NOT EXISTS idx_articles_published_date ON articles(published_date)',
            'CREATE INDEX IF NOT EXISTS idx_articles_url ON articles(url)',
            'CREATE INDEX IF NOT EXISTS idx_articles_sentiment ON articles(sentiment_score)'
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
    
    def down(self, cursor: sqlite3.Cursor):
        indexes = [
            'DROP INDEX IF EXISTS idx_articles_source',
            'DROP INDEX IF EXISTS idx_articles_category',
            'DROP INDEX IF EXISTS idx_articles_created_at',
            'DROP INDEX IF EXISTS idx_articles_published_date',
            'DROP INDEX IF EXISTS idx_articles_url',
            'DROP INDEX IF EXISTS idx_articles_sentiment'
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)


class Migration005AddImageSupport(Migration):
    """Add image URL support to articles"""
    
    def __init__(self):
        super().__init__("005", "Add image URL support to articles")
    
    def up(self, cursor: sqlite3.Cursor):
        cursor.execute('ALTER TABLE articles ADD COLUMN image_url TEXT')
    
    def down(self, cursor: sqlite3.Cursor):
        cursor.execute('UPDATE articles SET image_url = NULL')


class Migration006AddCategoryColors(Migration):
    """Add categories table with color support"""
    
    def __init__(self):
        super().__init__("006", "Add categories table with color support")
    
    def up(self, cursor: sqlite3.Cursor):
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
    
    def down(self, cursor: sqlite3.Cursor):
        cursor.execute('DROP TABLE IF EXISTS categories')


class Migration007AddArticleWordCount(Migration):
    """Add word count to articles"""
    
    def __init__(self):
        super().__init__("007", "Add word count to articles")
    
    def up(self, cursor: sqlite3.Cursor):
        cursor.execute('ALTER TABLE articles ADD COLUMN word_count INTEGER DEFAULT 0')
        
        # Update existing articles with word count
        cursor.execute('SELECT id, content FROM articles WHERE content IS NOT NULL')
        articles = cursor.fetchall()
        
        for article_id, content in articles:
            if content:
                word_count = len(content.split())
                cursor.execute('UPDATE articles SET word_count = ? WHERE id = ?', 
                             (word_count, article_id))
    
    def down(self, cursor: sqlite3.Cursor):
        cursor.execute('UPDATE articles SET word_count = NULL')


class Migration008AddSourceTracking(Migration):
    """Add source tracking and statistics"""
    
    def __init__(self):
        super().__init__("008", "Add source tracking and statistics")
    
    def up(self, cursor: sqlite3.Cursor):
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
        
        # Add is_active column to articles if it doesn't exist
        try:
            cursor.execute('ALTER TABLE articles ADD COLUMN is_active BOOLEAN DEFAULT 1')
        except sqlite3.OperationalError:
            # Column might already exist
            pass
        
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
    
    def down(self, cursor: sqlite3.Cursor):
        cursor.execute('DROP TABLE IF EXISTS sources')
        cursor.execute('UPDATE articles SET is_active = NULL')


class Migration009AddUpdatedAtColumn(Migration):
    """Add updated_at column to articles"""
    
    def __init__(self):
        super().__init__("009", "Add updated_at column to articles")
    
    def up(self, cursor: sqlite3.Cursor):
        try:
            cursor.execute('ALTER TABLE articles ADD COLUMN updated_at TEXT DEFAULT CURRENT_TIMESTAMP')
            # Update existing records
            cursor.execute('UPDATE articles SET updated_at = created_at WHERE updated_at IS NULL')
        except sqlite3.OperationalError:
            # Column might already exist
            pass
    
    def down(self, cursor: sqlite3.Cursor):
        cursor.execute('UPDATE articles SET updated_at = NULL')


class Migration010AddFullTextSearch(Migration):
    """Add full-text search capability"""
    
    def __init__(self):
        super().__init__("010", "Add full-text search capability")
    
    def up(self, cursor: sqlite3.Cursor):
        # Create FTS virtual table
        cursor.execute('''
            CREATE VIRTUAL TABLE IF NOT EXISTS articles_fts USING fts5(
                title, content, summary, author,
                content='articles',
                content_rowid='rowid'
            )
        ''')
        
        # Populate FTS table with existing data
        cursor.execute('''
            INSERT INTO articles_fts(rowid, title, content, summary, author)
            SELECT rowid, title, content, summary, author FROM articles
        ''')
        
        # Create triggers to keep FTS table in sync
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS articles_fts_insert AFTER INSERT ON articles BEGIN
                INSERT INTO articles_fts(rowid, title, content, summary, author)
                VALUES (new.rowid, new.title, new.content, new.summary, new.author);
            END
        ''')
        
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS articles_fts_delete AFTER DELETE ON articles BEGIN
                INSERT INTO articles_fts(articles_fts, rowid, title, content, summary, author)
                VALUES('delete', old.rowid, old.title, old.content, old.summary, old.author);
            END
        ''')
        
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS articles_fts_update AFTER UPDATE ON articles BEGIN
                INSERT INTO articles_fts(articles_fts, rowid, title, content, summary, author)
                VALUES('delete', old.rowid, old.title, old.content, old.summary, old.author);
                INSERT INTO articles_fts(rowid, title, content, summary, author)
                VALUES (new.rowid, new.title, new.content, new.summary, new.author);
            END
        ''')
    
    def down(self, cursor: sqlite3.Cursor):
        cursor.execute('DROP TRIGGER IF EXISTS articles_fts_insert')
        cursor.execute('DROP TRIGGER IF EXISTS articles_fts_delete')
        cursor.execute('DROP TRIGGER IF EXISTS articles_fts_update')
        cursor.execute('DROP TABLE IF EXISTS articles_fts')


# CLI interface for migrations
def main():
    """CLI interface for running migrations"""
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description='Database migration manager')
    parser.add_argument('--db', default='news.db', help='Database path')
    parser.add_argument('command', choices=['up', 'down', 'status', 'reset'], 
                       help='Migration command')
    parser.add_argument('--steps', type=int, default=1, 
                       help='Number of steps for down command')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    manager = MigrationManager(args.db)
    
    if args.command == 'up':
        success = manager.migrate_up()
        sys.exit(0 if success else 1)
    
    elif args.command == 'down':
        success = manager.migrate_down(args.steps)
        sys.exit(0 if success else 1)
    
    elif args.command == 'status':
        applied = manager.get_applied_migrations()
        all_migrations = [m.version for m in manager.migrations]
        pending = [v for v in all_migrations if v not in applied]
        
        print(f"Applied migrations ({len(applied)}):")
        for version in applied:
            print(f"  ✓ {version}")
        
        print(f"\nPending migrations ({len(pending)}):")
        for version in pending:
            migration = next(m for m in manager.migrations if m.version == version)
            print(f"  - {version}: {migration.description}")
    
    elif args.command == 'reset':
        # This is dangerous - only for development
        confirmation = input("This will reset all migrations. Are you sure? (yes/no): ")
        if confirmation.lower() == 'yes':
            applied = manager.get_applied_migrations()
            manager.migrate_down(len(applied))
            print("All migrations rolled back")
        else:
            print("Reset cancelled")


if __name__ == "__main__":
    main()
