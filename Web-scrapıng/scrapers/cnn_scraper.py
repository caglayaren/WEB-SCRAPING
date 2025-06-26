from base_scraper import BaseScraper
from bs4 import BeautifulSoup
import re
from datetime import datetime

class CNNScraper(BaseScraper):
    """Scraper for CNN News"""
    
    def __init__(self):
        super().__init__(
            base_url="https://www.cnn.com",
            name="CNN",
            delay_range=(1, 3)
        )
    
    def get_article_links(self):
        """Get article links from CNN homepage"""
        response = self.get_page("https://www.cnn.com")
        if not response:
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        links = []
        
        # Find article links
        selectors = [
            'a[href*="/2024/"]',
            'a[href*="/2025/"]',
            '.card a',
            'h3 a',
            '.headline a'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                href = element.get('href', '')
                if href and any(year in href for year in ['/2024/', '/2025/']):
                    # Skip live updates, videos, and other non-article content
                    if not any(skip in href.lower() for skip in ['live-updates', '/videos/', '/video/', 'gallery']):
                        full_url = self.make_absolute_url(href)
                        if full_url not in links:
                            links.append(full_url)
        
        return links[:25]
    
    def scrape_article(self, url):
        """Scrape individual CNN article"""
        response = self.get_page(url)
        if not response:
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        try:
            # Title
            title_selectors = [
                'h1.headline__text',
                'h1[data-editable="headlineText"]',
                '.pg-headline',
                'h1'
            ]
            title = ""
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    title = self.clean_text(title_elem.get_text())
                    break
            
            if not title:
                return None
            
            # Content
            content_selectors = [
                '.article__content p',
                '.zn-body__paragraph',
                '.paragraph-inline-video p',
                'div[data-component-name="ArticleBody"] p',
                '.storytext p'
            ]
            
            content_paragraphs = []
            for selector in content_selectors:
                paragraphs = soup.select(selector)
                if paragraphs:
                    content_paragraphs = [self.clean_text(p.get_text()) for p in paragraphs 
                                        if p.get_text().strip() and len(p.get_text().strip()) > 20]
                    break
            
            content = ' '.join(content_paragraphs)
            
            # Summary
            summary = ""
            if content_paragraphs:
                summary = content_paragraphs[0]
            
            # Try meta description if no summary
            meta_description = soup.find('meta', {'name': 'description'})
            if meta_description and not summary:
                summary = meta_description.get('content', '')
            
            # Author
            author = ""
            author_selectors = [
                '.byline__name',
                '.metadata__byline a',
                '.author-name',
                '[rel="author"]'
            ]
            for selector in author_selectors:
                author_elem = soup.select_one(selector)
                if author_elem:
                    author = self.clean_text(author_elem.get_text())
                    break
            
            # Published date
            published_date = ""
            date_selectors = [
                '.timestamp',
                '.update-time',
                'time',
                '.metadata__date'
            ]
            for selector in date_selectors:
                date_elem = soup.select_one(selector)
                if date_elem:
                    date_text = date_elem.get('datetime') or date_elem.get_text()
                    published_date = self.clean_text(date_text)
                    break
            
            # Image
            image_url = ""
            img_selectors = [
                '.media__image img',
                '.image__dam-img',
                'article img',
                '.lead-media img'
            ]
            for selector in img_selectors:
                img_elem = soup.select_one(selector)
                if img_elem:
                    image_url = img_elem.get('src', '') or img_elem.get('data-src', '')
                    if image_url:
                        image_url = self.make_absolute_url(image_url)
                        break
            
            # Category
            category = "General"
            # Try to extract from URL
            if '/politics/' in url:
                category = "Politics"
            elif '/business/' in url:
                category = "Business"
            elif '/health/' in url:
                category = "Health"
            elif '/tech/' in url:
                category = "Technology"
            elif '/sport/' in url:
                category = "Sports"
            elif '/world/' in url:
                category = "World"
            else:
                # Try breadcrumbs
                breadcrumb_selectors = ['.breadcrumb a', '.nav a']
                for selector in breadcrumb_selectors:
                    breadcrumbs = soup.select(selector)
                    if breadcrumbs:
                        for breadcrumb in breadcrumbs:
                            text = breadcrumb.get_text().strip()
                            if text.lower() not in ['home', 'cnn', '']:
                                category = text
                                break
                        break
            
            return {
                'title': title,
                'content': content,
                'summary': summary[:500] if summary else "",
                'author': author,
                'published_date': published_date,
                'url': url,
                'category': category,
                'image_url': image_url
            }
            
        except Exception as e:
            self.logger.error(f"Error scraping CNN article {url}: {e}")
            return None