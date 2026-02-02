"""
Unit tests for Pydantic models
"""
import pytest
from datetime import datetime
from inference.models import (
    RawNewsArticle,
    NewsSource,
    AnalyzedNewsArticle,
    AnalysisResult,
    SentimentType
)


def test_news_source_normalization():
    """Test NewsSource name normalization"""
    source = NewsSource(name="  Test   Source!@#  ")
    assert source.name == "Test   Source"
    
    source2 = NewsSource(name="Normal Source")
    assert source2.name == "Normal Source"


def test_raw_news_article_validation():
    """Test RawNewsArticle validation"""
    article = RawNewsArticle(
        id="test-001",
        source=NewsSource(name="Test Source"),
        title="  Test  Title  ",
        description="  Some   description  ",
        content="<p>Some content</p>",
        url="https://example.com/news",
        publishedAt="2026-02-02T10:00:00Z"
    )
    
    # Check normalization
    assert article.title == "Test  Title"
    assert "Some content" in article.content
    assert "<p>" not in article.content  # HTML removed


def test_raw_news_article_url_validation():
    """Test URL validation"""
    with pytest.raises(ValueError):
        RawNewsArticle(
            id="test-001",
            source=NewsSource(name="Test"),
            title="Title",
            url="invalid-url",
            publishedAt="2026-02-02T10:00:00Z"
        )


def test_raw_news_article_datetime_validation():
    """Test datetime validation"""
    # Valid datetime
    article = RawNewsArticle(
        id="test-001",
        source=NewsSource(name="Test"),
        title="Title",
        url="https://example.com",
        publishedAt="2026-02-02T10:00:00Z"
    )
    assert article.publishedAt == "2026-02-02T10:00:00Z"
    
    # Invalid datetime
    with pytest.raises(ValueError):
        RawNewsArticle(
            id="test-001",
            source=NewsSource(name="Test"),
            title="Title",
            url="https://example.com",
            publishedAt="invalid-date"
        )


def test_analysis_result():
    """Test AnalysisResult"""
    result = AnalysisResult(
        sentiment=SentimentType.POSITIVE,
        sentiment_score=0.8,
        confidence=0.9,
        keywords=["test", "keyword", "news", "test"]  # duplicate
    )
    
    # Check keyword normalization (deduplication)
    assert len(result.keywords) == 3
    assert "test" in result.keywords
    assert "keyword" in result.keywords


def test_analysis_result_score_validation():
    """Test score validation"""
    # Valid scores
    result = AnalysisResult(
        sentiment_score=0.5,
        confidence=0.8
    )
    assert result.sentiment_score == 0.5
    assert result.confidence == 0.8
    
    # Invalid scores
    with pytest.raises(ValueError):
        AnalysisResult(sentiment_score=1.5)  # > 1.0
    
    with pytest.raises(ValueError):
        AnalysisResult(confidence=-0.1)  # < 0.0


def test_analyzed_news_article():
    """Test AnalyzedNewsArticle"""
    article = AnalyzedNewsArticle(
        id="test-001",
        source=NewsSource(name="Test Source"),
        title="Test Title",
        url="https://example.com",
        publishedAt="2026-02-02T10:00:00Z",
        analysis=AnalysisResult(
            sentiment=SentimentType.POSITIVE,
            sentiment_score=0.8,
            keywords=["test", "news"]
        )
    )
    
    assert article.id == "test-001"
    assert article.analysis.sentiment == SentimentType.POSITIVE
    assert article.analysis.sentiment_score == 0.8


def test_keywords_normalization():
    """Test keywords normalization"""
    result = AnalysisResult(
        keywords=[
            "  UPPER  ",  # uppercase with spaces
            "lower",
            "ab",  # too short (< 3 chars)
            "valid",
            "valid",  # duplicate
            "Valid"   # case-insensitive duplicate
        ]
    )
    
    # Should be normalized: lowercase, stripped, deduplicated, min length 3
    assert "upper" in result.keywords
    assert "lower" in result.keywords
    assert "valid" in result.keywords
    assert "ab" not in result.keywords
    assert len([k for k in result.keywords if k == "valid"]) == 1


def test_model_serialization():
    """Test model serialization to JSON"""
    article = RawNewsArticle(
        id="test-001",
        source=NewsSource(name="Test Source"),
        title="Test Title",
        url="https://example.com",
        publishedAt="2026-02-02T10:00:00Z"
    )
    
    # Serialize to dict
    data = article.model_dump()
    assert data["id"] == "test-001"
    assert data["source"]["name"] == "Test Source"
    
    # Serialize to JSON
    json_str = article.model_dump_json()
    assert "test-001" in json_str
    
    # Deserialize from JSON
    article2 = RawNewsArticle.model_validate_json(json_str)
    assert article2.id == article.id
