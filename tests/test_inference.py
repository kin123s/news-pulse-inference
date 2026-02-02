"""
Integration tests for Async Inference Engine
"""
import pytest
import asyncio
from inference.async_inference_engine import AsyncInferenceEngine
from inference.models import RawNewsArticle, NewsSource


@pytest.fixture
def sample_article():
    """Sample news article for testing"""
    return RawNewsArticle(
        id="test-001",
        source=NewsSource(name="Test Source"),
        title="Amazing breakthrough in AI technology brings hope to millions",
        description="Scientists achieve remarkable success",
        content="This is groundbreaking research...",
        url="https://example.com/news",
        publishedAt="2026-02-02T10:00:00Z"
    )


@pytest.fixture
def sample_articles():
    """Multiple sample articles for batch testing"""
    return [
        RawNewsArticle(
            id=f"test-{i:03d}",
            source=NewsSource(name="Test Source"),
            title=f"News article {i} with {'positive' if i % 2 == 0 else 'negative'} sentiment",
            url=f"https://example.com/news/{i}",
            publishedAt="2026-02-02T10:00:00Z"
        )
        for i in range(10)
    ]


@pytest.mark.asyncio
async def test_analyze_single(sample_article):
    """Test single article analysis"""
    engine = AsyncInferenceEngine(max_concurrent_requests=5)
    
    result = await engine.analyze_single(sample_article, use_external_api=False)
    
    # Check result structure
    assert result.id == sample_article.id
    assert result.title == sample_article.title
    assert result.analysis is not None
    assert result.analysis.sentiment is not None
    assert result.analysis.keywords is not None
    assert len(result.analysis.keywords) > 0
    
    # Check sentiment detection (positive words in title)
    assert result.analysis.sentiment in ["positive", "neutral"]
    
    await engine.close()


@pytest.mark.asyncio
async def test_analyze_batch(sample_articles):
    """Test batch article analysis"""
    engine = AsyncInferenceEngine(max_concurrent_requests=10)
    
    results = await engine.analyze_batch(sample_articles, use_external_api=False)
    
    # All articles should be analyzed
    assert len(results) == len(sample_articles)
    
    # Check each result
    for result in results:
        assert result.id.startswith("test-")
        assert result.analysis is not None
        assert result.analysis.sentiment is not None
    
    await engine.close()


@pytest.mark.asyncio
async def test_concurrent_processing(sample_articles):
    """Test concurrent processing with semaphore"""
    max_concurrent = 5
    engine = AsyncInferenceEngine(max_concurrent_requests=max_concurrent)
    
    # Process batch
    results = await engine.analyze_batch(sample_articles, use_external_api=False)
    
    # Should complete successfully
    assert len(results) == len(sample_articles)
    
    await engine.close()


@pytest.mark.asyncio
async def test_sentiment_detection():
    """Test sentiment detection accuracy"""
    engine = AsyncInferenceEngine()
    
    # Positive article
    positive_article = RawNewsArticle(
        id="pos-001",
        source=NewsSource(name="Test"),
        title="Great success and amazing achievement brings positive growth",
        url="https://example.com",
        publishedAt="2026-02-02T10:00:00Z"
    )
    
    result = await engine.analyze_single(positive_article, use_external_api=False)
    assert result.analysis.sentiment == "positive"
    assert result.analysis.sentiment_score > 0
    
    # Negative article
    negative_article = RawNewsArticle(
        id="neg-001",
        source=NewsSource(name="Test"),
        title="Terrible crisis and worst failure causes negative decline",
        url="https://example.com",
        publishedAt="2026-02-02T10:00:00Z"
    )
    
    result = await engine.analyze_single(negative_article, use_external_api=False)
    assert result.analysis.sentiment == "negative"
    assert result.analysis.sentiment_score < 0
    
    await engine.close()


@pytest.mark.asyncio
async def test_keyword_extraction():
    """Test keyword extraction"""
    engine = AsyncInferenceEngine()
    
    article = RawNewsArticle(
        id="kw-001",
        source=NewsSource(name="Test"),
        title="Machine learning artificial intelligence neural networks deep learning",
        description="Technology innovation machine learning models",
        url="https://example.com",
        publishedAt="2026-02-02T10:00:00Z"
    )
    
    result = await engine.analyze_single(article, use_external_api=False)
    
    # Should extract relevant keywords
    assert len(result.analysis.keywords) > 0
    # Common words like "machine" or "learning" should appear
    keywords_text = " ".join(result.analysis.keywords).lower()
    assert any(word in keywords_text for word in ["machine", "learning", "intelligence", "neural"])
    
    await engine.close()


@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling for invalid input"""
    engine = AsyncInferenceEngine()
    
    # Invalid article (should still handle gracefully)
    try:
        article = RawNewsArticle(
            id="err-001",
            source=NewsSource(name="Test"),
            title="",  # Empty title might cause issues
            url="https://example.com",
            publishedAt="2026-02-02T10:00:00Z"
        )
        # This should raise validation error
        assert False, "Should have raised validation error"
    except ValueError:
        pass  # Expected
    
    await engine.close()


@pytest.mark.asyncio
async def test_performance():
    """Test performance metrics"""
    engine = AsyncInferenceEngine(max_concurrent_requests=20)
    
    # Create 50 articles
    articles = [
        RawNewsArticle(
            id=f"perf-{i:03d}",
            source=NewsSource(name="Test"),
            title=f"Performance test article {i}",
            url=f"https://example.com/{i}",
            publishedAt="2026-02-02T10:00:00Z"
        )
        for i in range(50)
    ]
    
    import time
    start = time.time()
    results = await engine.analyze_batch(articles, use_external_api=False)
    elapsed = time.time() - start
    
    # Should complete all 50 articles
    assert len(results) == 50
    
    # Should be reasonably fast (< 5 seconds for 50 articles)
    assert elapsed < 5.0, f"Too slow: {elapsed:.2f}s"
    
    # Calculate avg time per article
    avg_time = elapsed / len(results)
    print(f"Performance: {avg_time*1000:.2f}ms per article")
    
    await engine.close()
