from base_scraper import BaseScraper
from bs4 import BeautifulSoup
import hashlib
from datetime import datetime
import re

class BBCScraper(BaseScraper):
    """Güncellenmiş BBC News Scraper - 2025 HTML yapısına uyumlu"""
    
    def __init__(self):
        super().__init__(
            base_url="https://www.bbc.com",
            name="BBC News",
            delay_range=(1, 3)
        )
        
        # BBC için daha güçlü headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,tr;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        })
    
    def get_article_links(self):
        """BBC News ana sayfasından makale linklerini çıkar"""
        # Birden fazla BBC sayfasını dene
        urls_to_try = [
            "https://www.bbc.com/news",
            "https://www.bbc.com/news/world",
            "https://www.bbc.com/news/uk", 
            "https://www.bbc.com/news/technology",
            "https://www.bbc.com/news/business"
        ]
        
        all_links = []
        
        for base_url in urls_to_try:
            response = self.get_page(base_url)
            if not response:
                self.logger.warning(f"Failed to fetch {base_url}")
                continue
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Güncel BBC link selector'ları (2025)
            selectors = [
                # Yeni BBC yapısı
                'a[data-testid="internal-link"]',
                'h2[data-testid="card-headline"] a',
                'h3[data-testid="card-headline"] a', 
                '[data-testid="topic-page"] a',
                
                # Geleneksel selector'lar
                'a[href*="/news/"]',
                '.gs-c-promo-heading a',
                '.media__link',
                'h2 a[href*="/news/"]',
                'h3 a[href*="/news/"]',
                
                # Yeni promo yapıları
                '[data-testid="promo-text"] a',
                '.gel-layout a[href*="/news/"]'
            ]
            
            page_links = set()
            for selector in selectors:
                elements = soup.select(selector)
                for element in elements:
                    href = element.get('href', '')
                    if href and '/news/' in href:
                        # Gereksiz linkleri filtrele
                        if not any(x in href.lower() for x in [
                            'live', 'topics', 'av/', 'video', 'pictures', 
                            'in_pictures', 'entertainment', 'newsbeat', 'reality_check'
                        ]):
                            full_url = self.make_absolute_url(href)
                            # URL'nin makale formatında olduğunu kontrol et
                            if self._is_article_url(full_url):
                                page_links.add(full_url)
            
            all_links.extend(list(page_links))
            self.logger.info(f"Found {len(page_links)} links from {base_url}")
            
            # Sayfalar arası gecikme
            self.random_delay()
        
        # Duplicates'i temizle ve sınırla
        unique_links = list(dict.fromkeys(all_links))
        self.logger.info(f"Total unique links found: {len(unique_links)}")
        
        return unique_links[:30]
    
    def _is_article_url(self, url):
        """URL'nin makale URL'si olup olmadığını kontrol et"""
        if not url or 'bbc.com' not in url:
            return False
        
        # BBC makale URL pattern'i: /news/category-12345678 veya /news/articles/
        patterns = [
            r'/news/[a-zA-Z-]+-\d{8}$',  # /news/world-12345678
            r'/news/articles/[a-zA-Z0-9-]+$',  # /news/articles/article-id
            r'/news/[a-zA-Z-]+-\d{8}\?',  # Query parameters ile
            r'/news/uk-\d{8}$',
            r'/news/world-\d{8}$',
            r'/news/business-\d{8}$',
            r'/news/technology-\d{8}$'
        ]
        
        return any(re.search(pattern, url) for pattern in patterns)
    
    def scrape_article(self, url):
        """BBC makalesini scrape et - 2025 yapısına uyumlu"""
        response = self.get_page(url)
        if not response:
            self.logger.warning(f"Failed to fetch article: {url}")
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        try:
            # Başlık - Güncellenmiş selector'lar
            title = ""
            title_selectors = [
                # BBC'nin yeni yapısı
                'h1[data-testid="headline"]',
                'header h1',
                '[data-testid="headline"]',
                
                # Eski yapı fallback'leri
                'h1.story-body__h1',
                '.story-headline h1',
                'h1#main-heading',
                'h1'
            ]
            
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    title = self.clean_text(title_elem.get_text())
                    if title and len(title) > 5:  # Meaningful title kontrolü
                        break
            
            if not title:
                self.logger.warning(f"No title found for: {url}")
                return None
            
            # İçerik - BBC'nin yeni data-component yapısı
            content_paragraphs = []
            
            # Method 1: Yeni BBC yapısı - data-component="text-block"
            text_blocks = soup.select('[data-component="text-block"]')
            if text_blocks:
                for block in text_blocks:
                    # text-block içindeki tüm p tag'lerini al
                    paragraphs = block.find_all('p')
                    for p in paragraphs:
                        text = self.clean_text(p.get_text())
                        if text and len(text) > 20:  # Çok kısa paragrafları filtrele
                            content_paragraphs.append(text)
            
            # Method 2: Eğer yeni yapı çalışmazsa, fallback selector'lar
            if not content_paragraphs:
                content_selectors = [
                    # Farklı BBC content yapıları
                    '[data-component="text-block"] p',
                    '.story-body__inner p',
                    '.story-body div p',
                    '[data-testid="bodyText"] p',
                    'article p',
                    '#story-body p',
                    '.article-body p',
                    'main p'
                ]
                
                for selector in content_selectors:
                    paragraphs = soup.select(selector)
                    if paragraphs:
                        content_paragraphs = [
                            self.clean_text(p.get_text()) 
                            for p in paragraphs 
                            if p.get_text().strip() and len(p.get_text().strip()) > 20
                        ]
                        if content_paragraphs:  # İçerik bulundu
                            break
            
            # Method 3: Son çare - tüm p tag'lerini topla
            if not content_paragraphs:
                all_p = soup.find_all('p')
                potential_content = []
                for p in all_p:
                    text = self.clean_text(p.get_text())
                    if (text and len(text) > 30 and 
                        not any(skip in text.lower() for skip in [
                            'cookie', 'javascript', 'browser', 'subscribe', 
                            'follow us', 'share this', 'related topics'
                        ])):
                        potential_content.append(text)
                
                if potential_content:
                    content_paragraphs = potential_content
            
            content = ' '.join(content_paragraphs)
            
            if not content:
                self.logger.warning(f"No content found for: {url}")
                # Title varsa ama content yoksa, makaleyi yine de kaydet
                # return None  # Bu satırı comment out ettik
            
            # Özet
            summary = ""
            if content_paragraphs:
                summary = content_paragraphs[0]
            
            # Meta description fallback
            if not summary:
                meta_description = soup.find('meta', {'name': 'description'})
                if meta_description:
                    summary = meta_description.get('content', '')
            
            # Yazar
            author = ""
            author_selectors = [
                '[data-testid="byline"]',
                '[data-testid="byline-name"]',
                '.author-name',
                '.byline__name',
                '.story-body .byline',
                'span[data-testid="byline"]'
            ]
            
            for selector in author_selectors:
                author_elem = soup.select_one(selector)
                if author_elem:
                    author_text = self.clean_text(author_elem.get_text())
                    # "By " prefix'ini temizle
                    if author_text.lower().startswith('by '):
                        author = author_text[3:]
                    else:
                        author = author_text
                    if author:
                        break
            
            # Yayın tarihi
            published_date = ""
            date_selectors = [
                '[data-testid="timestamp"]',
                'time[datetime]',
                '.story-body .date',
                '.date-stamp',
                'time'
            ]
            
            for selector in date_selectors:
                date_elem = soup.select_one(selector)
                if date_elem:
                    date_text = date_elem.get('datetime') or date_elem.get_text()
                    if date_text:
                        published_date = self.clean_text(date_text)
                        break
            
            # Resim
            image_url = ""
            img_selectors = [
                '[data-testid="hero-image"] img',
                '[data-testid="image-block"] img',
                'figure img[src*="ichef.bbci.co.uk"]',
                '.story-body img',
                'article img',
                'main img'
            ]
            
            for selector in img_selectors:
                img_elem = soup.select_one(selector)
                if img_elem:
                    src = img_elem.get('src', '') or img_elem.get('data-src', '')
                    if src and ('ichef.bbci.co.uk' in src or 'bbc.co.uk' in src):
                        image_url = src if src.startswith('http') else f"https:{src}"
                        break
            
            # Kategori belirleme
            category = "General"
            
            # URL'den kategori çıkarma
            url_lower = url.lower()
            if 'world' in url_lower:
                category = "World"
            elif 'uk' in url_lower or 'england' in url_lower or 'scotland' in url_lower:
                category = "UK"
            elif 'business' in url_lower:
                category = "Business"
            elif 'technology' in url_lower or 'tech' in url_lower:
                category = "Technology"
            elif 'science' in url_lower:
                category = "Science"
            elif 'health' in url_lower:
                category = "Health"
            elif 'politics' in url_lower:
                category = "Politics"
            elif 'entertainment' in url_lower:
                category = "Entertainment"
            elif 'sport' in url_lower:
                category = "Sports"
            else:
                # Breadcrumb'lardan kategori çıkarma
                breadcrumbs = soup.select('nav a, .breadcrumb a, [data-testid="breadcrumb"] a')
                for breadcrumb in breadcrumbs:
                    text = breadcrumb.get_text().strip().title()
                    if text and text.lower() not in ['home', 'news', 'bbc', '']:
                        category = text
                        break
            
            article_data = {
                'title': title,
                'content': content,
                'summary': summary[:500] if summary else "",  # 500 karakter limit
                'author': author,
                'published_date': published_date,
                'url': url,
                'category': category,
                'image_url': image_url,
                'source': self.name,
                'scraped_at': datetime.utcnow().isoformat(),
                'id': self.generate_article_id(title, url)
            }
            
            self.logger.info(f"Successfully scraped article: {title[:50]}...")
            return article_data
            
        except Exception as e:
            self.logger.error(f"Error scraping BBC article {url}: {e}")
            return None
    
    def scrape_all(self, max_articles=25):
        """Tüm makaleleri scrape et"""
        self.logger.info(f"Starting BBC scraping for max {max_articles} articles")
        
        links = self.get_article_links()
        if not links:
            self.logger.warning("No article links found")
            return []
        
        articles = []
        successful_scrapes = 0
        
        for i, url in enumerate(links[:max_articles]):
            self.logger.info(f"Scraping article {i+1}/{min(len(links), max_articles)}: {url}")
            
            article = self.scrape_article(url)
            if article:
                articles.append(article)
                successful_scrapes += 1
            else:
                self.logger.warning(f"Failed to scrape: {url}")
            
            # Rate limiting
            self.random_delay()
        
        self.logger.info(f"BBC scraping completed: {successful_scrapes}/{len(links[:max_articles])} articles successful")
        return articles