from base_scraper import BaseScraper
from bs4 import BeautifulSoup
import hashlib
from datetime import datetime
import re
import json
import requests

class BBCScraper(BaseScraper):
    """Modern BBC News Scraper - Düzeltilmiş URL ve Kategori Sistemi"""
    
    def __init__(self):
        super().__init__(
            base_url="https://www.bbc.com",
            name="BBC News",
            delay_range=(1, 3)
        )
        # BBC için modern headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json,text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
        })

    def determine_category_ultra_strict(self, title, content=""):
        """ULTRA KATI kategori belirleme - sadece başlık bazlı"""
        title_lower = title.lower().strip()
        
        print(f"\n🔍 KATEGORI ANALIZ: '{title}'")
        
        # === KESIN DIŞLAMA - SPOR OLMAYAN İÇERİKLER ===
        
        # 1. Reality TV & Dating Shows -> Entertainment
        reality_keywords = ['love island', 'reality tv', 'reality show', 'dating show', 'tv show']
        if any(keyword in title_lower for keyword in reality_keywords):
            print(f"   ✅ ENTERTAINMENT: Reality TV detected ({[k for k in reality_keywords if k in title_lower]})")
            return "Entertainment"
        
        # 2. Crime & Legal -> General
        crime_keywords = ['paedophile', 'pedophile', 'sexual abuse', 'murder', 'rape', 'convicted', 'sentenced', 'trial', 'court', 'arrest']
        if any(keyword in title_lower for keyword in crime_keywords):
            print(f"   ✅ GENERAL: Crime detected ({[k for k in crime_keywords if k in title_lower]})")
            return "General"
        
        # 3. Protests & Politics -> Politics
        politics_keywords = ['pride', 'protest', 'demonstration', 'anti-government', 'political', 'government', 'supreme court', 'trump', 'biden']
        if any(keyword in title_lower for keyword in politics_keywords):
            print(f"   ✅ POLITICS: Political event detected ({[k for k in politics_keywords if k in title_lower]})")
            return "Politics"
        
        # 4. International News -> World
        world_keywords = ['serbia', 'belgrade', 'budapest', 'hungary', 'iran', 'israel', 'gaza', 'ukraine', 'russia']
        if any(keyword in title_lower for keyword in world_keywords):
            # Double check - not sports related
            sports_check = ['football', 'soccer', 'match', 'game', 'tournament', 'championship']
            if not any(sport in title_lower for sport in sports_check):
                print(f"   ✅ WORLD: International location detected ({[k for k in world_keywords if k in title_lower]})")
                return "World"
        
        # 5. Entertainment & Celebrity -> Entertainment
        entertainment_keywords = ['celebrity', 'disney', 'disneyland', 'entertainment', 'hollywood', 'music', 'concert', 'festival']
        if any(keyword in title_lower for keyword in entertainment_keywords):
            print(f"   ✅ ENTERTAINMENT: Celebrity/Entertainment detected ({[k for k in entertainment_keywords if k in title_lower]})")
            return "Entertainment"
        
        # === ULTRA SPESIFIK SPOR KONTROLÜ ===
        
        # Gerçek spor kelimeleri - çok spesifik
        definite_sports = [
            'f1', 'formula 1', 'formula one', 'grand prix', 'racing', 'motorsport',
            'football', 'soccer', 'premier league', 'champions league', 'fifa', 'uefa',
            'tennis', 'wimbledon', 'cricket', 'rugby', 'basketball', 'nba',
            'olympics', 'olympic', 'athletics', 'championship'
        ]
        
        # Spor bağlamı kelimeleri
        sports_context = [
            'match', 'game', 'tournament', 'team', 'player', 'athlete', 'coach',
            'goal', 'score', 'victory', 'defeat', 'league', 'cup'
        ]
        
        has_definite_sports = any(sport in title_lower for sport in definite_sports)
        has_sports_context = any(context in title_lower for context in sports_context)
        
        # MEGA KATI: Her iki şart da olmalı VE title'da exclusion olmamalı
        if has_definite_sports and has_sports_context:
            # Son kontrol - exclusion kelimeleri
            final_exclusions = ['love', 'island', 'reality', 'disney', 'crime', 'murder', 'court', 'police', 'pride', 'protest']
            if not any(exclusion in title_lower for exclusion in final_exclusions):
                print(f"   ✅ SPORTS: Pure sports detected (Sports: {[s for s in definite_sports if s in title_lower]}, Context: {[c for c in sports_context if c in title_lower]})")
                return "Sports"
            else:
                print(f"   ❌ SPORTS BLOCKED: Exclusion words found ({[e for e in final_exclusions if e in title_lower]})")
        else:
            if has_definite_sports:
                print(f"   ❌ SPORTS PARTIAL: Has sports words but no context")
            elif has_sports_context:
                print(f"   ❌ SPORTS PARTIAL: Has context but no definite sports")
            else:
                print(f"   ❌ SPORTS: No sports indicators")
        
        # === DİĞER KATEGORİLER ===
        
        # Health
        if any(keyword in title_lower for keyword in ['health', 'medical', 'nhs', 'doctor', 'hospital']):
            print(f"   ✅ HEALTH: Health content detected")
            return "Health"
        
        # Business
        if any(keyword in title_lower for keyword in ['business', 'company', 'economy', 'market', 'financial']):
            print(f"   ✅ BUSINESS: Business content detected")
            return "Business"
        
        # Technology
        if any(keyword in title_lower for keyword in ['technology', 'tech', 'ai', 'digital']):
            print(f"   ✅ TECHNOLOGY: Tech content detected")
            return "Technology"
        
        # Science
        if any(keyword in title_lower for keyword in ['science', 'research', 'discovery', 'scientist']):
            print(f"   ✅ SCIENCE: Science content detected")
            return "Science"
        
        # UK
        if any(keyword in title_lower for keyword in ['britain', 'british', 'england', 'scotland', 'uk']):
            print(f"   ✅ UK: UK-specific content detected")
            return "UK"
        
        print(f"   ✅ GENERAL: Default category assigned")
        return "General"

    def get_article_links_modern(self):
        """Modern BBC link extraction - Düzeltilmiş URL'ler"""
        all_links = []
        
        # BBC'nin ÇALIŞAN seksiyonları - 404 veren URL'leri kaldırdık
        sections = [
            "https://www.bbc.com/news",
            "https://www.bbc.com/news/world", 
            "https://www.bbc.com/news/uk",
            "https://www.bbc.com/news/politics",
            "https://www.bbc.com/news/business",
            "https://www.bbc.com/news/technology",
            # Bu URL'ler 404 veriyor - kaldırıldı
            # "https://www.bbc.com/news/science-environment",
            # "https://www.bbc.com/news/entertainment-arts"
            "https://www.bbc.com/news/health"
        ]
        
        for section_url in sections:
            try:
                print(f"🔍 Fetching {section_url}...")
                response = self.get_page(section_url)
                if not response:
                    print(f"   ❌ Failed to fetch {section_url}")
                    continue
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Daha basit fallback scraping - JSON karmaşık
                print(f"   🔄 Using fallback scraping for {section_url}")
                selectors = [
                    'a[href*="/news/"]',
                    'h2 a',
                    'h3 a',
                    '.gs-c-promo-heading a',
                    '[data-testid="internal-link"]'
                ]
                
                page_links = set()
                for selector in selectors:
                    try:
                        elements = soup.select(selector)
                        for element in elements:
                            href = element.get('href', '')
                            if href and '/news/' in href:
                                # Basit filtreleme
                                if not any(x in href.lower() for x in ['live', 'video', 'pictures', 'sport/']):
                                    full_url = self.make_absolute_url(href)
                                    if self._is_valid_article_url(full_url):
                                        page_links.add(full_url)
                                        print(f"   📰 Found: {full_url}")
                    except Exception as e:
                        print(f"   ⚠️ Selector {selector} failed: {e}")
                
                all_links.extend(list(page_links))
                print(f"   ✅ Found {len(page_links)} links from {section_url}")
                
                self.random_delay()
                
            except Exception as e:
                print(f"   ❌ Error fetching {section_url}: {e}")
        
        # Duplicates'i temizle
        unique_links = list(dict.fromkeys(all_links))
        print(f"\n📊 Total unique articles found: {len(unique_links)}")
        
        # Debug: İlk 5 linki göster
        if unique_links:
            print("🔍 First 5 links found:")
            for i, link in enumerate(unique_links[:5]):
                print(f"   {i+1}. {link}")
        
        return unique_links[:50]  # Daha fazla makale

    def _is_valid_article_url(self, url):
        """URL'nin geçerli makale URL'si olup olmadığını kontrol et"""
        if not url or 'bbc.com' not in url:
            return False
        
        # Geçerli BBC makale pattern'leri
        valid_patterns = [
            r'/news/[a-zA-Z-]+-\d{8}',
            r'/news/articles/[a-zA-Z0-9-]+',
            r'/news/world-\d+',
            r'/news/uk-\d+',
            r'/news/business-\d+',
            r'/news/technology-\d+',
            r'/news/health-\d+'
        ]
        
        return any(re.search(pattern, url) for pattern in valid_patterns)

    def scrape_article_modern(self, url):
        """Modern BBC makale scraping"""
        response = self.get_page(url)
        if not response:
            print(f"❌ Failed to fetch: {url}")
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        try:
            # Modern JSON-based extraction
            json_script = soup.find('script', {'id': '__NEXT_DATA__'})
            title = ""
            content = ""
            
            if json_script:
                try:
                    data = json.loads(json_script.text)
                    page_data = data.get('props', {}).get('pageProps', {}).get('page', {})
                    
                    for key, value in page_data.items():
                        if key.startswith('@') and isinstance(value, dict):
                            contents = value.get('contents', [])
                            for content_block in contents:
                                if content_block.get('type') == 'headline':
                                    blocks = content_block.get('model', {}).get('blocks', [])
                                    for block in blocks:
                                        title = block.get('model', {}).get('text', '')
                                        if title:
                                            break
                                elif content_block.get('type') == 'text':
                                    blocks = content_block.get('model', {}).get('blocks', [])
                                    for block in blocks:
                                        text = block.get('model', {}).get('text', '')
                                        if text:
                                            content += text + " "
                except json.JSONDecodeError:
                    pass
            
            # Fallback: Traditional extraction
            if not title:
                title_selectors = [
                    'h1[data-testid="headline"]',
                    'header h1',
                    'h1'
                ]
                for selector in title_selectors:
                    title_elem = soup.select_one(selector)
                    if title_elem:
                        title = self.clean_text(title_elem.get_text())
                        if title and len(title) > 5:
                            break
            
            if not content:
                content_selectors = [
                    '[data-component="text-block"] p',
                    '.story-body__inner p',
                    'article p'
                ]
                content_parts = []
                for selector in content_selectors:
                    paragraphs = soup.select(selector)
                    if paragraphs:
                        for p in paragraphs:
                            text = self.clean_text(p.get_text())
                            if text and len(text) > 20:
                                content_parts.append(text)
                        if content_parts:
                            content = ' '.join(content_parts)
                            break
            
            if not title:
                print(f"❌ No title found for: {url}")
                return None
            
            print(f"\n📰 SCRAPING: {title}")
            
            # KRITIK: Kategori belirleme
            category = self.determine_category_ultra_strict(title, content)
            
            # Yazar, tarih, resim (basit extraction)
            author = ""
            published_date = ""
            image_url = ""
            
            # Yazar
            author_elem = soup.select_one('[data-testid="byline"], .byline__name')
            if author_elem:
                author = self.clean_text(author_elem.get_text()).replace('By ', '')
            
            # Tarih
            date_elem = soup.select_one('[data-testid="timestamp"], time[datetime]')
            if date_elem:
                published_date = date_elem.get('datetime') or self.clean_text(date_elem.get_text())
            
            # Resim
            img_elem = soup.select_one('[data-testid="hero-image"] img, figure img')
            if img_elem:
                src = img_elem.get('src') or img_elem.get('data-src')
                if src and 'bbc' in src:
                    image_url = src if src.startswith('http') else f"https:{src}"
            
            print(f"🎯 FINAL RESULT: {category}")
            print("-" * 80)
            
            article_data = {
                'title': title,
                'content': content,
                'summary': content[:300] if content else "",
                'author': author,
                'published_date': published_date,
                'url': url,
                'category': category,  # BU ÇOK ÖNEMLİ - DOĞRU KATEGORİ
                'image_url': image_url,
                'source': self.name,
                'scraped_at': datetime.utcnow().isoformat(),
                'id': self.generate_article_id(title, url)
            }
            
            return article_data
            
        except Exception as e:
            print(f"❌ Error scraping {url}: {e}")
            return None

    def scrape_all(self, max_articles=30):
        """Ana scraping fonksiyonu"""
        print("🚀 Starting BBC scraping with ULTRA STRICT categorization...")
        
        links = self.get_article_links_modern()
        if not links:
            print("❌ No article links found")
            return []
        
        articles = []
        successful_scrapes = 0
        
        print(f"\n📊 Processing {min(len(links), max_articles)} articles...")
        
        for i, url in enumerate(links[:max_articles]):
            print(f"\n[{i+1}/{min(len(links), max_articles)}] Processing: {url}")
            
            article = self.scrape_article_modern(url)
            if article:
                articles.append(article)
                successful_scrapes += 1
                print(f"✅ SUCCESS: '{article['title'][:50]}...' -> {article['category']}")
                
                # CRITICAL CHECK
                if article['category'] == 'Sports':
                    print(f"🚨 SPORTS ARTICLE DETECTED: {article['title']}")
            else:
                print(f"❌ FAILED: {url}")
            
            self.random_delay()
        
        print(f"\n🎉 BBC scraping completed: {successful_scrapes}/{len(links[:max_articles])} successful")
        
        # Kategori dağılımını göster
        categories = {}
        for article in articles:
            cat = article['category']
            categories[cat] = categories.get(cat, 0) + 1
        
        print(f"\n📊 CATEGORY DISTRIBUTION:")
        for cat, count in categories.items():
            print(f"   {cat}: {count} articles")
        
        return articles

    # Gerekli inherited metodlar
    def get_article_links(self):
        return self.get_article_links_modern()
    
    def scrape_article(self, url):
        return self.scrape_article_modern(url)