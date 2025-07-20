import asyncio
from typing import List, Dict
from playwright.async_api import async_playwright
from .scraper import get_product_info
from .live_scraper import LiveDealScraper

class DealFinder:
    def __init__(self):
        self.live_scraper = LiveDealScraper()
        
    async def find_best_deals(self, categories=None, max_deals=50) -> List[Dict]:
        """Find the best deals from live websites with real URLs ONLY."""
        all_deals = []
        
        # Get live deals from all websites
        print("🔍 Scraping live deals from all websites...")
        live_deals = self.live_scraper.find_live_deals_sync(max_deals)
        all_deals.extend(live_deals)
        
        # Get best sellers
        print("🏆 Finding best-selling products...")
        try:
            best_sellers = await self.live_scraper.find_best_sellers(max_deals//4)
            all_deals.extend(best_sellers)
        except Exception as e:
            print(f"Bestseller finding failed: {e}")
        
        # Sort by discount percentage and rating
        all_deals.sort(key=lambda x: (x.get('discount_percent', 0), x.get('rating', 0)), reverse=True)
        
        return all_deals[:max_deals]
    
    def is_good_deal(self, deal: Dict) -> bool:
        """Determine if a deal is worth considering."""
        # Criteria for a good deal
        discount = deal.get('discount_percent', 0)
        rating = deal.get('rating', '0')
        has_timer = deal.get('has_timer', False)
        
        # Extract numeric rating
        try:
            rating_num = float(rating.split()[0]) if rating else 0
        except:
            rating_num = 0
        
        # Good deal criteria:
        # - At least 20% discount OR
        # - At least 10% discount with 4+ star rating OR
        # - Has timer (limited time deal)
        return (discount >= 20) or (discount >= 10 and rating_num >= 4.0) or has_timer
    
    def get_best_deals_sync(self, categories=None, max_deals=50) -> List[Dict]:
        """Synchronous wrapper for finding deals."""
        try:
            return asyncio.run(self.find_best_deals(categories, max_deals))
        except Exception as e:
            print(f"Deal finding failed: {e}")
            return [] 