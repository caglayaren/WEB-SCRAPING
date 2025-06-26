
# 📰 News Scraper

![Python](https://img.shields.io/badge/python-v3.8+-blue.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)

Automated news aggregation and analysis system that collects articles from BBC, CNN, and Reuters, analyzes content, and presents them through a web interface.

## ✨ Features

- **Multi-source scraping** from BBC News, CNN, and Reuters
- **Parallel processing** for fast data collection using ThreadPoolExecutor
- **Sentiment analysis** to determine article tone
- **Web dashboard** built with Flask framework
- **Advanced filtering** by source, category, and keywords
- **Duplicate detection** to avoid redundant articles
- **Real-time statistics** and monitoring

## 🚀 Installation

1. Clone the repository
2. Install dependencies with pip
3. Run setup command
4. Start collecting news

## 🖥️ Usage

### Command Line Interface
- **Collect news**: Run scraping cycle to gather latest articles
- **Start web server**: Launch dashboard interface
- **Check status**: View system health and statistics
- **Test scrapers**: Verify individual source functionality

### Web Dashboard
Access the web interface at `http://localhost:5000` to:
- Browse collected articles
- Filter by source and category
- Search with keywords
- View statistics and analytics

## 📊 Performance

| Metric | Value |
|--------|-------|
| Scraping Speed | ~25 articles/source in 5-10 seconds |
| Success Rate | 95%+ successful extraction |
| Concurrent Processing | 3 sources simultaneously |
| Database Performance | Optimized with indexes |

## 🏗️ System Architecture

```
News Sources → Scraper Engine → Database → Web Interface
(BBC/CNN/Reuters) → (Processing & Analysis) → (SQLite) → (Dashboard)
```

### Project Structure
- **Main Application**: Core scraper and runner
- **Scraper Modules**: Individual source scrapers (BBC, CNN, Reuters)
- **Database Layer**: Article storage and management
- **Web Interface**: Dashboard and API endpoints
- **Configuration**: Settings and source definitions

## 🔧 Technologies

- **Python 3.8+**: Main programming language
- **BeautifulSoup4**: HTML parsing and content extraction
- **Requests**: HTTP requests and web scraping
- **Flask**: Web framework for dashboard
- **SQLite**: Database for article storage
- **Threading**: Concurrent processing
- **Logging**: System monitoring and debugging

## 🎯 Key Capabilities

### Data Collection
- Automatic article discovery from news homepages
- Full article content extraction
- Metadata gathering (author, date, category)
- Error handling and retry mechanisms

### Content Analysis
- Basic sentiment scoring
- Word count and content metrics
- Automatic categorization
- Publication date parsing

### Data Management
- SQLite database with optimized schema
- Article deduplication based on URLs
- Source statistics tracking
- Efficient querying with indexes

## 📈 Results

The system successfully:
- Processes 70+ articles per scraping cycle
- Maintains 95%+ extraction accuracy
- Completes full cycle in under 10 seconds
- Stores articles with comprehensive metadata
- Provides real-time web interface access

## 👨‍💻 Developer

**Çağla Yaren**  
GitHub: [@caglayaren](https://github.com/caglayaren)

