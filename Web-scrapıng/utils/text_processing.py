#!/usr/bin/env python3
"""
Advanced text processing utilities for news articles
"""

import re
import string
from typing import List, Dict, Tuple, Optional
from collections import Counter
import hashlib


class TextProcessor:
    """Advanced text processing for news articles"""
    
    def __init__(self):
        # Common stop words for English
        self.stop_words = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
            'to', 'was', 'were', 'will', 'with', 'the', 'this', 'but', 'they',
            'have', 'had', 'what', 'said', 'each', 'which', 'she', 'do', 'how',
            'their', 'if', 'up', 'out', 'many', 'then', 'them', 'these', 'so',
            'some', 'her', 'would', 'make', 'like', 'into', 'him', 'time',
            'has', 'two', 'more', 'go', 'no', 'way', 'could', 'my', 'than',
            'first', 'been', 'call', 'who', 'its', 'now', 'find', 'long',
            'down', 'day', 'did', 'get', 'come', 'made', 'may', 'part'
        }
        
        # Positive and negative sentiment words
        self.positive_words = {
            'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic',
            'positive', 'success', 'win', 'achieve', 'breakthrough', 'progress',
            'growth', 'improve', 'benefit', 'gain', 'rise', 'boost', 'strong',
            'effective', 'efficient', 'innovative', 'outstanding', 'remarkable',
            'impressive', 'brilliant', 'superb', 'magnificent', 'exceptional',
            'victory', 'triumph', 'advance', 'develop', 'enhance', 'upgrade',
            'optimize', 'expand', 'flourish', 'thrive', 'prosper', 'succeed'
        }
        
        self.negative_words = {
            'bad', 'terrible', 'awful', 'horrible', 'negative', 'fail', 'failure',
            'crisis', 'problem', 'issue', 'concern', 'worry', 'decline', 'fall',
            'drop', 'loss', 'damage', 'threat', 'risk', 'danger', 'weak',
            'poor', 'disappointing', 'concerning', 'alarming', 'devastating',
            'tragic', 'disaster', 'collapse', 'crash', 'plunge', 'suffer',
            'struggle', 'conflict', 'war', 'attack', 'violence', 'death',
            'destroy', 'eliminate', 'reduce', 'cut', 'slash', 'decrease'
        }
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = ' '.join(text.strip().split())
        
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        
        # Remove excessive punctuation
        text = re.sub(r'[.]{2,}', '.', text)
        text = re.sub(r'[!]{2,}', '!', text)
        text = re.sub(r'[?]{2,}', '?', text)
        
        # Remove non-ASCII characters (optional, might want to keep for international news)
        # text = ''.join(char for char in text if ord(char) < 128)
        
        return text.strip()
    
    def extract_summary(self, text: str, max_sentences: int = 3, max_length: int = 300) -> str:
        """Extract summary from text using simple sentence ranking"""
        if not text:
            return ""
        
        sentences = self.split_sentences(text)
        if not sentences:
            return ""
        
        if len(sentences) <= max_sentences:
            summary = ' '.join(sentences)
            return summary[:max_length] + ('...' if len(summary) > max_length else '')
        
        # Score sentences based on word frequency and position
        word_freq = self.get_word_frequency(text)
        sentence_scores = []
        
        for i, sentence in enumerate(sentences):
            score = 0
            words = self.tokenize(sentence.lower())
            
            # Score based on word frequency
            for word in words:
                if word in word_freq:
                    score += word_freq[word]
            
            # Boost score for sentences at the beginning
            position_boost = max(0, (len(sentences) - i) / len(sentences))
            score += position_boost * 10
            
            # Penalty for very short sentences
            if len(words) < 5:
                score *= 0.5
            
            sentence_scores.append((score, sentence))
        
        # Sort by score and take top sentences
        sentence_scores.sort(reverse=True, key=lambda x: x[0])
        top_sentences = [sent for _, sent in sentence_scores[:max_sentences]]
        
        # Reorder sentences by their original position
        summary_sentences = []
        for sentence in sentences:
            if sentence in top_sentences:
                summary_sentences.append(sentence)
        
        summary = ' '.join(summary_sentences)
        return summary[:max_length] + ('...' if len(summary) > max_length else '')
    
    def split_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        if not text:
            return []
        
        # Simple sentence splitting using regex
        sentences = re.split(r'[.!?]+', text)
        
        # Clean and filter sentences
        cleaned_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 10:  # Filter very short sentences
                cleaned_sentences.append(sentence)
        
        return cleaned_sentences
    
    def tokenize(self, text: str) -> List[str]:
        """Tokenize text into words"""
        if not text:
            return []
        
        # Convert to lowercase and remove punctuation
        text = text.lower()
        text = text.translate(str.maketrans('', '', string.punctuation))
        
        # Split into words and filter stop words
        words = text.split()
        return [word for word in words if word not in self.stop_words and len(word) > 2]
    
    def get_word_frequency(self, text: str) -> Dict[str, float]:
        """Get word frequency scores"""
        words = self.tokenize(text)
        if not words:
            return {}
        
        word_count = Counter(words)
        total_words = len(words)
        
        # Calculate frequency scores
        word_freq = {}
        for word, count in word_count.items():
            word_freq[word] = count / total_words
        
        return word_freq
    
    def extract_keywords(self, text: str, max_keywords: int = 10) -> List[Tuple[str, float]]:
        """Extract keywords from text with scores"""
        word_freq = self.get_word_frequency(text)
        
        # Sort by frequency and return top keywords
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return sorted_words[:max_keywords]
    
    def calculate_sentiment(self, text: str) -> float:
        """Calculate sentiment score (-1 to 1)"""
        if not text:
            return 0.0
        
        words = self.tokenize(text)
        if not words:
            return 0.0
        
        positive_count = sum(1 for word in words if word in self.positive_words)
        negative_count = sum(1 for word in words if word in self.negative_words)
        
        total_sentiment_words = positive_count + negative_count
        if total_sentiment_words == 0:
            return 0.0
        
        # Calculate sentiment score
        sentiment = (positive_count - negative_count) / total_sentiment_words
        
        # Apply smoothing to avoid extreme scores
        return max(-1.0, min(1.0, sentiment))
    
    def calculate_readability(self, text: str) -> Dict[str, float]:
        """Calculate readability metrics"""
        if not text:
            return {'flesch_score': 0, 'avg_sentence_length': 0, 'avg_word_length': 0}
        
        sentences = self.split_sentences(text)
        words = text.split()
        
        if not sentences or not words:
            return {'flesch_score': 0, 'avg_sentence_length': 0, 'avg_word_length': 0}
        
        # Average sentence length
        avg_sentence_length = len(words) / len(sentences)
        
        # Average word length
        avg_word_length = sum(len(word.strip(string.punctuation)) for word in words) / len(words)
        
        # Simplified Flesch Reading Ease Score
        # Formula: 206.835 - (1.015 × ASL) - (84.6 × ASW)
        # ASL = average sentence length, ASW = average syllables per word
        # For simplicity, we'll estimate syllables as word_length / 2
        avg_syllables = avg_word_length / 2
        flesch_score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables)
        flesch_score = max(0, min(100, flesch_score))  # Clamp to 0-100
        
        return {
            'flesch_score': round(flesch_score, 2),
            'avg_sentence_length': round(avg_sentence_length, 2),
            'avg_word_length': round(avg_word_length, 2)
        }
    
    def detect_language(self, text: str) -> str:
        """Simple language detection (basic implementation)"""
        if not text:
            return 'unknown'
        
        # Very basic language detection based on common words
        text_lower = text.lower()
        
        # English indicators
        english_indicators = ['the', 'and', 'is', 'in', 'to', 'of', 'a', 'that', 'it', 'with']
        english_count = sum(1 for word in english_indicators if word in text_lower)
        
        # Spanish indicators
        spanish_indicators = ['el', 'la', 'de', 'que', 'y', 'en', 'un', 'es', 'se', 'no']
        spanish_count = sum(1 for word in spanish_indicators if word in text_lower)
        
        # French indicators
        french_indicators = ['le', 'de', 'et', 'à', 'un', 'il', 'être', 'et', 'en', 'avoir']
        french_count = sum(1 for word in french_indicators if word in text_lower)
        
        # Determine language based on indicators
        if english_count >= spanish_count and english_count >= french_count:
            return 'english'
        elif spanish_count >= french_count:
            return 'spanish'
        elif french_count > 0:
            return 'french'
        else:
            return 'unknown'
    
    def generate_text_hash(self, text: str) -> str:
        """Generate hash for text deduplication"""
        if not text:
            return ""
        
        # Normalize text for hashing
        normalized = self.clean_text(text.lower())
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def detect_duplicates(self, articles: List[Dict]) -> List[Tuple[int, int]]:
        """Detect duplicate articles based on content similarity"""
        duplicates = []
        text_hashes = {}
        
        for i, article in enumerate(articles):
            content = article.get('content', '') or article.get('title', '')
            if not content:
                continue
            
            text_hash = self.generate_text_hash(content)
            
            if text_hash in text_hashes:
                duplicates.append((text_hashes[text_hash], i))
            else:
                text_hashes[text_hash] = i
        
        return duplicates
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Simple named entity extraction"""
        if not text:
            return {'persons': [], 'organizations': [], 'locations': []}
        
        # Simple patterns for entity extraction
        # This is a basic implementation - for production use spaCy or NLTK
        
        entities = {
            'persons': [],
            'organizations': [],
            'locations': []
        }
        
        # Pattern for potential person names (Title Case words)
        person_pattern = r'\b[A-Z][a-z]+ [A-Z][a-z]+\b'
        potential_persons = re.findall(person_pattern, text)
        
        # Filter out common false positives
        common_false_positives = {
            'United States', 'New York', 'Los Angeles', 'San Francisco',
            'United Kingdom', 'European Union', 'Middle East'
        }
        
        for person in potential_persons:
            if person not in common_false_positives and len(person.split()) == 2:
                entities['persons'].append(person)
        
        # Pattern for organizations (words ending with common org suffixes)
        org_pattern = r'\b[A-Z][a-zA-Z\s]+(Inc|Corp|Ltd|LLC|Company|Corporation|Organization|Agency)\b'
        entities['organizations'] = list(set(re.findall(org_pattern, text)))
        
        # Simple location detection (this would need a proper gazetteer in production)
        location_keywords = [
            'City', 'State', 'Country', 'Province', 'County', 'District',
            'Street', 'Avenue', 'Road', 'Boulevard'
        ]
        
        for keyword in location_keywords:
            pattern = r'\b[A-Z][a-zA-Z\s]+' + keyword + r'\b'
            locations = re.findall(pattern, text)
            entities['locations'].extend(locations)
        
        # Remove duplicates and limit results
        for key in entities:
            entities[key] = list(set(entities[key]))[:10]  # Limit to 10 entities per type
        
        return entities


# Utility functions for common text processing tasks

def process_article_text(article: Dict) -> Dict:
    """Process article text and add computed fields"""
    processor = TextProcessor()
    
    title = article.get('title', '')
    content = article.get('content', '')
    
    # Generate summary if not present
    if not article.get('summary') and content:
        article['summary'] = processor.extract_summary(content)
    
    # Calculate word count
    if content:
        article['word_count'] = len(content.split())
    else:
        article['word_count'] = 0
    
    # Calculate sentiment
    text_for_sentiment = f"{title} {content}"
    article['sentiment_score'] = processor.calculate_sentiment(text_for_sentiment)
    
    # Extract keywords
    if content:
        keywords = processor.extract_keywords(content, max_keywords=5)
        article['keywords'] = [word for word, score in keywords]
    
    # Calculate readability
    if content:
        readability = processor.calculate_readability(content)
        article['readability'] = readability
    
    # Detect language
    article['language'] = processor.detect_language(content or title)
    
    return article


def clean_article_batch(articles: List[Dict]) -> List[Dict]:
    """Clean and process a batch of articles"""
    processor = TextProcessor()
    cleaned_articles = []
    
    for article in articles:
        try:
            # Clean text fields
            if article.get('title'):
                article['title'] = processor.clean_text(article['title'])
            
            if article.get('content'):
                article['content'] = processor.clean_text(article['content'])
            
            if article.get('summary'):
                article['summary'] = processor.clean_text(article['summary'])
            
            # Process additional fields
            article = process_article_text(article)
            
            cleaned_articles.append(article)
            
        except Exception as e:
            print(f"Error processing article: {e}")
            # Include article even if processing fails
            cleaned_articles.append(article)
    
    return cleaned_articles


# Example usage and testing
if __name__ == "__main__":
    processor = TextProcessor()
    
    # Test text
    sample_text = """
    This is a great example of text processing. The new technology 
    breakthrough will improve efficiency and boost performance significantly. 
    However, there are still some concerns about implementation costs.
    """
    
    print("Original text:", sample_text)
    print("\nCleaned text:", processor.clean_text(sample_text))
    print("\nSummary:", processor.extract_summary(sample_text))
    print("\nKeywords:", processor.extract_keywords(sample_text))
    print("\nSentiment:", processor.calculate_sentiment(sample_text))
    print("\nReadability:", processor.calculate_readability(sample_text))
    print("\nLanguage:", processor.detect_language(sample_text))
