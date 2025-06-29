import re
import hashlib
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

class TextCleaner:
    @staticmethod
    def clean_text(text):
        """Clean and normalize text content"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = ' '.join(text.strip().split())
        
        # Remove common unwanted characters
        text = re.sub(r'[^\w\s\.,!?;:\'"-]', '', text)
        
        return text
    
    @staticmethod
    def extract_summary(text, max_length=200):
        """Extract a summary from text"""
        if not text:
            return ""
        
        sentences = re.split(r'[.!?]+', text)
        summary = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            if len(summary + sentence) <= max_length:
                summary += sentence + ". "
            else:
                break
        
        return summary.strip()

class URLHelper:
    @staticmethod
    def normalize_url(url, base_url):
        """Normalize relative URLs to absolute URLs"""
        if not url:
            return ""
        
        if url.startswith('http'):
            return url
        
        return urljoin(base_url, url)
    
    @staticmethod
    def is_valid_url(url):
        """Check if URL is valid"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    @staticmethod
    def generate_url_hash(url):
        """Generate a hash for URL deduplication"""
        return hashlib.md5(url.encode()).hexdigest()

class DateHelper:
    @staticmethod
    def parse_date(date_string):
        """Parse various date formats"""
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%SZ',
            '%d %b %Y',
            '%B %d, %Y',
            '%d/%m/%Y',
            '%m/%d/%Y'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_string, fmt)
            except ValueError:
                continue
        
        return datetime.now()
    
    @staticmethod
    def time_ago(timestamp):
        """Get human-readable time ago string"""
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        
        now = datetime.now(timezone.utc)
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        
        diff = now - timestamp
        
        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        else:
            return "Just now"
