def test_price_tracker():
    from core.tracker import PriceTracker
    class DummyWatcher:
        def get_all_products(self):
            return [{"url": "https://www.amazon.in/dp/B09G9FPGTN"}]
    tracker = PriceTracker(DummyWatcher())
    # Placeholder: Should not raise
    tracker.check_all_prices() 