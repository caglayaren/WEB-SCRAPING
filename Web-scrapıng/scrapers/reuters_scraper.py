from base_scraper import BaseScraper
from bs4 import BeautifulSoup
import re
from datetime import datetime

class ReutersScraper(BaseScraper):
    """Scraper for Reuters News"""
    
    def __init__(self):
        super().__init__(
            base_url="https://www.reuters.com",
            name="Reuters",
            delay_range=(2, 4)  # Increased delay to avoid being blocked
        )
        # Add Reuters-specific headers
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        })
    
    def get_article_links(self):
        """Get article links from Reuters homepage"""
        # Try multiple Reuters sections to get more diverse articles
        urls_to_try = [
            "https://www.reuters.com",
            "https://www.reuters.com/world/",
            "https://www.reuters.com/business/",
            "https://www.reuters.com/technology/"
        ]
        
        all_links = []
        
        for base_url in urls_to_try:
            response = self.get_page(base_url)
            if not response:
                continue
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find article links with more specific selectors
            selectors = [
                'a[href*="/world/"]',
                'a[href*="/business/"]', 
                'a[href*="/technology/"]',
                'a[href*="/markets/"]',
                'a[href*="/legal/"]',
                'a[href*="/breakingviews/"]',
                # More generic selectors
                'a[data-testid*="Link"]',
                'h3 a[href*="reuters.com"]',
                'h2 a[href*="reuters.com"]'
            ]
            
            for selector in selectors:
                elements = soup.select(selector)
                for element in elements:
                    href = element.get('href', '')
                    if href:
                        # Skip unwanted content types
                        if any(skip in href.lower() for skip in ['/live/', '/tv/', '/video/', '/graphics/', '/picture/', '/audio/']):
                            continue
                            
                        full_url = self.make_absolute_url(href)
                        
                        # Ensure it's a valid Reuters article URL
                        if ('reuters.com' in full_url and 
                            full_url not in all_links and
                            len(full_url.split('/')) >= 5):  # Basic URL structure check
                            all_links.append(full_url)
            
            # Add delay between different sections
            self.random_delay()
        
        # Remove duplicates and limit
        unique_links = list(dict.fromkeys(all_links))
        return unique_links[:25]
    
    def scrape_article(self, url):
        """Scrape individual Reuters article"""
        response = self.get_page(url)
        if not response:
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        try:
            # Title - try multiple selectors
            title_selectors = [
                '[data-testid="ArticleHeader-headline"]',
                '[data-testid="Heading"]',
                'h1[data-testid="Heading"]',
                '.ArticleHeader_headline',
                'h1.text__text',
                'h1'
            ]
            
            title = ""
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    title = self.clean_text(title_elem.get_text())
                    if title and len(title) > 10:  # Ensure it's a meaningful title
                        break
            
            if not title:
                self.logger.warning(f"No title found for {url}")
                return None
            
            # Content - Reuters uses data-testid for paragraphs
            content_paragraphs = []
            
            # Method 1: Try data-testid paragraph approach
            for i in range(30):  # Check up to 30 paragraphs
                paragraph = soup.select_one(f'[data-testid="paragraph-{i}"]')
                if paragraph:
                    text = self.clean_text(paragraph.get_text())
                    if text and len(text) > 15:  # Filter out very short paragraphs
                        content_paragraphs.append(text)
                else:
                    break
            
            # Method 2: If first method doesn't work, try other selectors
            if not content_paragraphs:
                content_selectors = [
                    '.StandardArticleBody_body p',
                    '.ArticleBodyWrapper p',
                    'div[data-module="ArticleBody"] p',
                    '.text__text p',
                    'article p'
                ]
                
                for selector in content_selectors:
                    paragraphs = soup.select(selector)
                    if paragraphs:
                        content_paragraphs = [
                            self.clean_text(p.get_text()) 
                            for p in paragraphs 
                            if p.get_text().strip() and len(p.get_text().strip()) > 20
                        ]
                        if content_paragraphs:  # If we found content, break
                            break
            
            content = ' '.join(content_paragraphs)
            
            # Summary (first paragraph or meta description)
            summary = ""
            if content_paragraphs:
                summary = content_paragraphs[0]
            
            # Try meta description if no summary
            if not summary:
                meta_description = soup.find('meta', {'name': 'description'})
                if meta_description:
                    summary = meta_description.get('content', '')
            
            # Author
            author = ""
            author_selectors = [
                '[data-testid="AuthorBylineCard"]',
                '.AuthorByline_authorName',
                '.author-name',
                '[data-module="BylineCard"] span',
                '.text__text .text__text'  # Sometimes nested
            ]
            
            for selector in author_selectors:
                author_elem = soup.select_one(selector)
                if author_elem:
                    author_text = self.clean_text(author_elem.get_text())
                    # Clean up author text
                    if author_text.lower().startswith('by '):
                        author = author_text[3:]
                    elif author_text and not author_text.lower().startswith('reuters'):
                        author = author_text
                    if author:
                        break
            
            # Published date
            published_date = ""
            date_selectors = [
                '[data-testid="ArticleHeader-date"]',
                'time[datetime]',
                '.ArticleHeader_date',
                '.timestamp',
                'time'
            ]
            
            for selector in date_selectors:
                date_elem = soup.select_one(selector)
                if date_elem:
                    # Try datetime attribute first
                    date_text = date_elem.get('datetime') or date_elem.get_text()
                    if date_text:
                        published_date = self.clean_text(date_text)
                        break
            
            # Image
            image_url = ""
            img_selectors = [
                '[data-testid="Image"] img',
                '.PlaceholderInlineVideo_image img',
                'figure img',
                '.media-object img',
                'img[src*="cloudfront"]'
            ]
            
            for selector in img_selectors:
                img_elem = soup.select_one(selector)
                if img_elem:
                    image_url = img_elem.get('src', '') or img_elem.get('data-src', '')
                    if image_url and ('http' in image_url or image_url.startswith('//')):
                        if image_url.startswith('//'):
                            image_url = 'https:' + image_url
                        elif not image_url.startswith('http'):
                            image_url = self.make_absolute_url(image_url)
                        break
            
            # Category (extract from URL)
            category = "General"
            url_lower = url.lower()
            if '/world/' in url_lower:
                category = "World"
            elif '/business/' in url_lower:
                category = "Business"
            elif '/technology/' in url_lower:
                category = "Technology"
            elif '/markets/' in url_lower:
                category = "Markets"
            elif '/breakingviews/' in url_lower:
                category = "Opinion"
            elif '/sports/' in url_lower:
                category = "Sports"
            elif '/lifestyle/' in url_lower:
                category = "Lifestyle"
            elif '/legal/' in url_lower:
                category = "Legal"
            
            # Use base class method for ID generation
            article_data = {
                'title': title,
                'content': content,
                'summary': summary[:500] if summary else "",
                'author': author,
                'published_date': published_date,
                'url': url,
                'category': category,
                'image_url': image_url,
                'source': self.name,
                'scraped_at': datetime.now().isoformat()
            }
            
            # Generate ID using base class method
            article_data['id'] = self.generate_article_id(title, url)
            
            return article_data
            
        except Exception as e:
            self.logger.error(f"Error scraping Reuters article {url}: {e}")
            return None
    
    def scrape_all(self, max_articles=25):
        """Scrape all articles from Reuters - use base class implementation"""
        return super().scrape_all(max_articles)