#!/usr/bin/env python3
"""
Tests for news scrapers
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path to import scrapers
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '../scrapers'))

from scrapers.base_scraper import BaseScraper
from scrapers.bbc_scraper import BBCScraper
from scrapers.cnn_scraper import CNNScraper
from scrapers.reuters_scraper import ReutersScraper


class TestBaseScraper(unittest.TestCase):
    """Test base scraper functionality"""
    
    def setUp(self):
        # Create a concrete implementation for testing
        class TestScraper(BaseScraper):
            def get_article_links(self):
                return ['https://example.com/article1', 'https://example.com/article2']
            
            def scrape_article(self, url):
                return {
                    'title': 'Test Article',
                    'content': 'Test content',
                    'url': url
                }
        
        self.scraper = TestScraper('https://example.com', 'Test Source')
    
    def test_clean_text(self):
        """Test text cleaning functionality"""
        text = "  This   is    messy   text  "
        cleaned = self.scraper.clean_text(text)
        self.assertEqual(cleaned, "This is messy text")
    
    def test_generate_article_id(self):
        """Test article ID generation"""
        title = "Test Article"
        url = "https://example.com/test"
        article_id = self.scraper.generate_article_id(title, url)
        
        self.assertIsInstance(article_id, str)
        self.assertEqual(len(article_id), 32)  # MD5 hash length
    
    def test_is_valid_url(self):
        """Test URL validation"""
        self.assertTrue(self.scraper.is_valid_url('https://example.com'))
        self.assertTrue(self.scraper.is_valid_url('http://example.com'))
        self.assertFalse(self.scraper.is_valid_url('not-a-url'))
        self.assertFalse(self.scraper.is_valid_url(''))
    
    def test_make_absolute_url(self):
        """Test URL absolutization"""
        relative_url = '/article/test'
        absolute_url = self.scraper.make_absolute_url(relative_url)
        self.assertEqual(absolute_url, 'https://example.com/article/test')
    
    @patch('scrapers.base_scraper.requests.Session.get')
    def test_get_page_success(self, mock_get):
        """Test successful page retrieval"""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        response = self.scraper.get_page('https://example.com')
        self.assertEqual(response, mock_response)
    
    @patch('scrapers.base_scraper.requests.Session.get')
    def test_get_page_failure(self, mock_get):
        """Test failed page retrieval"""
        mock_get.side_effect = Exception("Network error")
        
        response = self.scraper.get_page('https://example.com')
        self.assertIsNone(response)


class TestBBCScraper(unittest.TestCase):
    """Test BBC scraper"""
    
    def setUp(self):
        self.scraper = BBCScraper()
    
    def test_initialization(self):
        """Test scraper initialization"""
        self.assertEqual(self.scraper.name, "BBC News")
        self.assertEqual(self.scraper.base_url, "https://www.bbc.com")
    
    @patch('scrapers.bbc_scraper.BBCScraper.get_page')
    def test_get_article_links(self, mock_get_page):
        """Test article link extraction"""
        # Mock HTML response
        mock_response = Mock()
        mock_response.content = b'''
        <html>
            <body>
                <a href="/news/world-12345">World News Article</a>
                <a href="/news/technology-67890">Tech Article</a>
                <a href="/news/live-updates">Live Updates</a>
                <a href="/sport/football">Football News</a>
            </body>
        </html>
        '''
        mock_get_page.return_value = mock_response
        
        links = self.scraper.get_article_links()
        
        # Should get news links but not live updates
        self.assertGreater(len(links), 0)
        self.assertTrue(any('/news/world-12345' in link for link in links))
        self.assertTrue(any('/news/technology-67890' in link for link in links))
        self.assertFalse(any('live' in link.lower() for link in links))
    
    @patch('scrapers.bbc_scraper.BBCScraper.get_page')
    def test_scrape_article(self, mock_get_page):
        """Test individual article scraping"""
        # Mock article HTML
        mock_response = Mock()
        mock_response.content = b'''
        <html>
            <head>
                <meta name="description" content="Test article description">
            </head>
            <body>
                <h1 data-testid="headline">Test BBC Article Title</h1>
                <div data-component="text-block">
                    <p>This is the first paragraph of the article.</p>
                    <p>This is the second paragraph with more content.</p>
                </div>
                <time data-testid="timestamp" datetime="2024-01-01T12:00:00Z">Jan 1, 2024</time>
                <div data-testid="byline-name">John Reporter</div>
                <img data-testid="hero-image" src="/image.jpg" alt="Article image">
            </body>
        </html>
        '''
        mock_get_page.return_value = mock_response
        
        article = self.scraper.scrape_article('https://www.bbc.com/news/test-article')
        
        self.assertIsNotNone(article)
        self.assertEqual(article['title'], 'Test BBC Article Title')
        self.assertIn('first paragraph', article['content'])
        self.assertIn('second paragraph', article['content'])
        self.assertEqual(article['author'], 'John Reporter')
        self.assertEqual(article['url'], 'https://www.bbc.com/news/test-article')


class TestCNNScraper(unittest.TestCase):
    """Test CNN scraper"""
    
    def setUp(self):
        self.scraper = CNNScraper()
    
    def test_initialization(self):
        """Test scraper initialization"""
        self.assertEqual(self.scraper.name, "CNN")
        self.assertEqual(self.scraper.base_url, "https://www.cnn.com")
    
    @patch('scrapers.cnn_scraper.CNNScraper.get_page')
    def test_get_article_links(self, mock_get_page):
        """Test CNN article link extraction"""
        mock_response = Mock()
        mock_response.content = b'''
        <html>
            <body>
                <a href="/2024/01/01/politics/test-article/index.html">Politics Article</a>
                <a href="/2024/01/02/world/news-story/index.html">World News</a>
                <a href="/live-updates/something">Live Updates</a>
                <a href="/videos/test-video">Video Content</a>
            </body>
        </html>
        '''
        mock_get_page.return_value = mock_response
        
        links = self.scraper.get_article_links()
        
        self.assertGreater(len(links), 0)
        # Should include 2024 articles but not live updates or videos
        self.assertTrue(any('2024' in link and 'politics' in link for link in links))
        self.assertTrue(any('2024' in link and 'world' in link for link in links))
        self.assertFalse(any('live-updates' in link for link in links))
        self.assertFalse(any('videos' in link for link in links))


class TestReutersScraper(unittest.TestCase):
    """Test Reuters scraper"""
    
    def setUp(self):
        self.scraper = ReutersScraper()
    
    def test_initialization(self):
        """Test scraper initialization"""
        self.assertEqual(self.scraper.name, "Reuters")
        self.assertEqual(self.scraper.base_url, "https://www.reuters.com")
    
    @patch('scrapers.reuters_scraper.ReutersScraper.get_page')
    def test_scrape_article(self, mock_get_page):
        """Test Reuters article scraping"""
        mock_response = Mock()
        mock_response.content = b'''
        <html>
            <body>
                <h1 data-testid="ArticleHeader-headline">Reuters Test Article</h1>
                <div data-testid="paragraph-0">First paragraph content here.</div>
                <div data-testid="paragraph-1">Second paragraph with more details.</div>
                <div data-testid="AuthorBylineCard">Reuters Reporter</div>
                <time data-testid="ArticleHeader-date">2024-01-01T10:00:00Z</time>
            </body>
        </html>
        '''
        mock_get_page.return_value = mock_response
        
        article = self.scraper.scrape_article('https://www.reuters.com/world/test-article/')
        
        self.assertIsNotNone(article)
        self.assertEqual(article['title'], 'Reuters Test Article')
        self.assertIn('First paragraph', article['content'])
        self.assertIn('Second paragraph', article['content'])
        self.assertEqual(article['category'], 'World')  # Extracted from URL
    
    def test_category_extraction(self):
        """Test category extraction from URL"""
        test_urls = {
            'https://www.reuters.com/world/test': 'World',
            'https://www.reuters.com/business/test': 'Business',
            'https://www.reuters.com/technology/test': 'Technology',
            'https://www.reuters.com/markets/test': 'Markets',
            'https://www.reuters.com/other/test': 'General'
        }
        
        for url, expected_category in test_urls.items():
            # Mock the scraping to test category extraction logic
            with patch.object(self.scraper, 'get_page') as mock_get_page:
                mock_response = Mock()
                mock_response.content = b'<h1 data-testid="ArticleHeader-headline">Test</h1>'
                mock_get_page.return_value = mock_response
                
                article = self.scraper.scrape_article(url)
                if article:
                    self.assertEqual(article['category'], expected_category)


class TestScraperIntegration(unittest.TestCase):
    """Integration tests for scrapers"""
    
    def test_scraper_consistency(self):
        """Test that all scrapers return consistent article structure"""
        scrapers = [BBCScraper(), CNNScraper(), ReutersScraper()]
        
        required_fields = ['title', 'content', 'summary', 'author', 'published_date', 
                          'url', 'category', 'image_url']
        
        for scraper in scrapers:
            # Mock a basic article response
            with patch.object(scraper, 'get_page') as mock_get_page:
                mock_response = Mock()
                mock_response.content = b'''
                <html>
                    <body>
                        <h1>Test Title</h1>
                        <p>Test content</p>
                    </body>
                </html>
                '''
                mock_get_page.return_value = mock_response
                
                article = scraper.scrape_article('https://example.com/test')
                
                if article:  # Some scrapers might return None for malformed HTML
                    for field in required_fields:
                        self.assertIn(field, article, 
                                    f"Scraper {scraper.name} missing field {field}")
    
    def test_error_handling(self):
        """Test scraper error handling"""
        scrapers = [BBCScraper(), CNNScraper(), ReutersScraper()]
        
        for scraper in scrapers:
            # Test with invalid URL
            with patch.object(scraper, 'get_page', return_value=None):
                article = scraper.scrape_article('https://invalid-url.com')
                self.assertIsNone(article)
            
            # Test with empty response
            with patch.object(scraper, 'get_page') as mock_get_page:
                mock_response = Mock()
                mock_response.content = b''
                mock_get_page.return_value = mock_response
                
                article = scraper.scrape_article('https://example.com/empty')
                # Should either return None or handle gracefully
                if article:
                    self.assertIsInstance(article, dict)


if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestBaseScraper,
        TestBBCScraper, 
        TestCNNScraper,
        TestReutersScraper,
        TestScraperIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success: {result.wasSuccessful()}")
    print(f"{'='*50}")
