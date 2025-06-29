from flask import Flask, render_template, request, jsonify, redirect, url_for
import sqlite3
import json
from datetime import datetime, timedelta
from news_scraper import NewsAggregator
import threading
import time
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Initialize news aggregator
news_aggregator = NewsAggregator()

# Background scraping thread
def background_scraper():
    """Background thread to scrape news every hour"""
    while True:
        try:
            news_aggregator.run_scraping_cycle()
            print(f"Background scraping completed at {datetime.now()}")
        except Exception as e:
            print(f"Background scraping error: {e}")
        
        # Wait for 1 hour
        time.sleep(3600)

# Start background scraper in a daemon thread
scraper_thread = threading.Thread(target=background_scraper, daemon=True)
scraper_thread.start()

@app.route('/')
def dashboard():
    """Main dashboard page"""
    # Get user preferences (default values for demo)
    sources = request.args.getlist('sources') or ['BBC News', 'CNN', 'Reuters']
    categories = request.args.getlist('categories') or []  # Boş array - tüm kategoriler
    keywords = request.args.get('keywords', '').split(',') if request.args.get('keywords') else None
    
    # Debug: Print sources being requested
    print(f"Dashboard sources requested: {sources}")
    
    # Get articles
    articles = news_aggregator.get_articles(
        sources=sources,
        categories=categories if categories else None,  # None = tüm kategoriler
        keywords=keywords,
        limit=100  # Daha fazla makale
    )
    
    # Debug: Print articles found
    print(f"Articles found: {len(articles)}")
    article_sources = [a['source'] for a in articles]
    source_counts = {}
    for source in article_sources:
        source_counts[source] = source_counts.get(source, 0) + 1
    print(f"Articles by source: {source_counts}")
    
    # Group articles by category
    articles_by_category = {}
    for article in articles:
        category = article.get('category', 'General')
        if category not in articles_by_category:
            articles_by_category[category] = []
        articles_by_category[category].append(article)
    
    # Get statistics
    stats = get_dashboard_stats()
    
    return render_template('dashboard.html', 
                         articles_by_category=articles_by_category,
                         stats=stats,
                         selected_sources=sources,
                         selected_categories=categories,
                         keywords=request.args.get('keywords', ''))

@app.route('/api/articles')
def api_articles():
    """API endpoint for articles"""
    sources = request.args.getlist('sources')
    categories = request.args.getlist('categories')
    keywords = request.args.get('keywords', '').split(',') if request.args.get('keywords') else None
    limit = int(request.args.get('limit', 100))
    
    print(f"API sources requested: {sources}")
    
    articles = news_aggregator.get_articles(
        sources=sources if sources else None,
        categories=categories if categories else None,
        keywords=keywords,
        limit=limit
    )
    
    print(f"API articles returned: {len(articles)}")
    
    return jsonify(articles)

@app.route('/api/scrape', methods=['POST'])
def api_scrape():
    """Trigger manual scraping"""
    try:
        print("Manual scraping triggered")
        total_articles, new_articles = news_aggregator.run_scraping_cycle(max_articles_per_source=10)
        print(f"Manual scraping completed: {total_articles} total, {new_articles} new")
        
        return jsonify({
            'success': True,
            'total_articles': total_articles,
            'new_articles': new_articles,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        print(f"Manual scraping error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/refresh', methods=['POST'])  # Eklenen endpoint
def api_refresh():
    """Alternative refresh endpoint"""
    return api_scrape()

@app.route('/api/stats')
def api_stats():
    """Get dashboard statistics"""
    return jsonify(get_dashboard_stats())

@app.route('/api/debug')  # Debug endpoint eklendi
def api_debug():
    """Debug endpoint to check database"""
    conn = sqlite3.connect(news_aggregator.db_path)
    cursor = conn.cursor()
    
    # Get all sources
    cursor.execute('SELECT DISTINCT source FROM articles')
    sources = [row[0] for row in cursor.fetchall()]
    
    # Get count by source
    cursor.execute('SELECT source, COUNT(*) FROM articles GROUP BY source')
    source_counts = dict(cursor.fetchall())
    
    # Get recent articles
    cursor.execute('SELECT title, source, created_at FROM articles ORDER BY created_at DESC LIMIT 10')
    recent_articles = [{'title': row[0], 'source': row[1], 'created_at': row[2]} for row in cursor.fetchall()]
    
    conn.close()
    
    return jsonify({
        'sources': sources,
        'source_counts': source_counts,
        'recent_articles': recent_articles
    })

def get_dashboard_stats():
    """Get dashboard statistics"""
    conn = sqlite3.connect(news_aggregator.db_path)
    cursor = conn.cursor()
    
    # Total articles
    cursor.execute('SELECT COUNT(*) FROM articles')
    total_articles = cursor.fetchone()[0]
    
    # Articles in last 24 hours
    cursor.execute("SELECT COUNT(*) FROM articles WHERE created_at > datetime('now', '-24 hours')")
    recent_articles = cursor.fetchone()[0]
    
    # Articles by source
    cursor.execute('SELECT source, COUNT(*) FROM articles GROUP BY source')
    all_articles_by_source = dict(cursor.fetchall())
    
    # Recent articles by source
    cursor.execute('''
        SELECT source, COUNT(*) as count 
        FROM articles 
        WHERE created_at > datetime('now', '-24 hours')
        GROUP BY source
    ''')
    articles_by_source = dict(cursor.fetchall())
    
    # Articles by category
    cursor.execute('''
        SELECT category, COUNT(*) as count 
        FROM articles 
        WHERE created_at > datetime('now', '-24 hours')
        GROUP BY category
    ''')
    articles_by_category = dict(cursor.fetchall())
    
    # Last update - HER ZAMAN ŞİMDİKİ ZAMANI GÖSTER
    last_updated = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    conn.close()
    
    return {
        'total_articles': total_articles,
        'recent_articles': recent_articles,
        'articles_by_source': articles_by_source,
        'articles_by_category': articles_by_category,
        'all_articles_by_source': all_articles_by_source,  # Eklendi
        'last_updated': last_updated
    }

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    app.run(debug=True, host='0.0.0.0', port=5000)