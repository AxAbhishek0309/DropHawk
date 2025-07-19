def test_get_product_info():
    from core.scraper import get_product_info
    # Placeholder: Use a mock or a known static product page for testing
    result = get_product_info("https://www.amazon.in/dp/B09G9FPGTN")
    assert "title" in result 