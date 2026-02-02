"""
News analysis/inference service
Simple sentiment and keyword extraction
"""
import re
import logging
from typing import Dict, Any, List
from collections import Counter

logger = logging.getLogger(__name__)


class NewsAnalyzer:
    """
    Simple news analyzer for demonstration
    In production, you might use ML models, transformers, etc.
    """
    
    # Simple sentiment keywords
    POSITIVE_WORDS = {
        'good', 'great', 'excellent', 'amazing', 'positive', 'success',
        'win', 'growth', 'improve', 'innovative', 'breakthrough', 'gain'
    }
    
    NEGATIVE_WORDS = {
        'bad', 'worst', 'terrible', 'negative', 'fail', 'loss', 'decline',
        'crisis', 'crash', 'collapse', 'drop', 'concern', 'risk'
    }
    
    def analyze(self, news_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze news article and return inference results
        
        Args:
            news_data: Raw news data
        
        Returns:
            Analysis results with sentiment, keywords, etc.
        """
        title = news_data.get('title', '').lower()
        description = news_data.get('description', '').lower()
        content = news_data.get('content', '').lower()
        
        full_text = f"{title} {description} {content}"
        
        # Sentiment analysis
        sentiment = self._analyze_sentiment(full_text)
        
        # Extract keywords
        keywords = self._extract_keywords(full_text)
        
        # Calculate importance score (simple heuristic)
        importance_score = self._calculate_importance(news_data, sentiment)
        
        analysis_result = {
            **news_data,
            "analysis": {
                "sentiment": sentiment,
                "sentiment_score": self._sentiment_to_score(sentiment),
                "keywords": keywords,
                "importance_score": importance_score,
                "analyzed_at": self._get_timestamp()
            }
        }
        
        logger.info(f"Analyzed article: {news_data.get('id')} - Sentiment: {sentiment}")
        return analysis_result
    
    def _analyze_sentiment(self, text: str) -> str:
        """Simple sentiment analysis"""
        words = set(re.findall(r'\b\w+\b', text))
        
        positive_count = len(words & self.POSITIVE_WORDS)
        negative_count = len(words & self.NEGATIVE_WORDS)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"
    
    def _sentiment_to_score(self, sentiment: str) -> float:
        """Convert sentiment to numeric score"""
        scores = {"positive": 1.0, "neutral": 0.0, "negative": -1.0}
        return scores.get(sentiment, 0.0)
    
    def _extract_keywords(self, text: str, top_n: int = 5) -> List[str]:
        """Extract top keywords from text"""
        # Remove common stop words
        stop_words = {
            'the', 'is', 'at', 'which', 'on', 'a', 'an', 'and', 'or', 'but',
            'in', 'with', 'to', 'for', 'of', 'as', 'by', 'that', 'this'
        }
        
        words = re.findall(r'\b\w{4,}\b', text.lower())
        filtered_words = [w for w in words if w not in stop_words]
        
        word_counts = Counter(filtered_words)
        return [word for word, _ in word_counts.most_common(top_n)]
    
    def _calculate_importance(self, news_data: Dict[str, Any], sentiment: str) -> float:
        """Calculate importance score (0-10)"""
        score = 5.0
        
        # Boost score based on sentiment extremity
        if sentiment != "neutral":
            score += 1.0
        
        # Boost if from major sources
        source = news_data.get('source', '').lower()
        major_sources = ['bbc', 'cnn', 'reuters', 'bloomberg', 'wsj']
        if any(major in source for major in major_sources):
            score += 2.0
        
        # Content length bonus
        content_length = len(news_data.get('content', ''))
        if content_length > 500:
            score += 1.0
        
        return min(score, 10.0)
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"
