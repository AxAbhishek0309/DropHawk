from datetime import datetime
import re
import json
from pathlib import Path

class DecisionEngine:
    def __init__(self):
        self.price_history_file = Path("data/price_history.json")
        self._load_price_history()
        
        # Category-specific decision rules
        self.category_rules = {
            'electronics': {
                'min_discount': 15,
                'max_price': 50000,
                'min_rating': 4.0
            },
            'fashion': {
                'min_discount': 30,
                'max_price': 5000,
                'min_rating': 4.0
            },
            'beauty': {
                'min_discount': 40,
                'max_price': 2000,
                'min_rating': 4.0
            },
            'sports': {
                'min_discount': 25,
                'max_price': 15000,
                'min_rating': 4.2
            },
            'home_kitchen': {
                'min_discount': 20,
                'max_price': 50000,
                'min_rating': 4.0
            },
            'books': {
                'min_discount': 50,
                'max_price': 500,
                'min_rating': 4.5
            }
        }
    
    def _load_price_history(self):
        """Load price history from file."""
        if self.price_history_file.exists():
            with open(self.price_history_file, 'r') as f:
                self.price_history = json.load(f)
        else:
            self.price_history = {}
    
    def _save_price_history(self):
        """Save price history to file."""
        with open(self.price_history_file, 'w') as f:
            json.dump(self.price_history, f, indent=2)
    
    def decide(self, product_info):
        """Make a decision based on product info with improved logic."""
        price = product_info.get('price')
        discount = product_info.get('discount_percent', 0)
        rating = product_info.get('rating', '0')
        title = product_info.get('title', '').lower()
        url = product_info.get('url', '')
        
        # Extract numeric rating
        try:
            rating_num = float(rating.split()[0]) if rating else 0
        except:
            rating_num = 0
        
        # Parse price more robustly
        price_num = self._parse_price(price)
        
        # Determine product category
        category = self._determine_category(title)
        
        # Get category-specific rules
        rules = self.category_rules.get(category, {
            'min_discount': 20,
            'max_price': 10000,
            'min_rating': 4.0
        })
        
        # Check price history
        price_trend = self._check_price_trend(url, price_num)
        
        # Decision logic
        verdict = "Wait"
        reason = ""
        confidence = 0
        
        # High confidence scenarios
        if discount >= 50:
            verdict = "Buy"
            reason = f"Excellent discount: {discount}%"
            confidence = 95
        elif discount >= rules['min_discount'] and rating_num >= rules['min_rating'] and price_num <= rules['max_price']:
            verdict = "Buy"
            reason = f"Good deal: {discount}% off, {rating_num}/5 stars, ₹{price_num}"
            confidence = 85
        elif price_trend == "decreasing" and discount >= 15:
            verdict = "Buy"
            reason = f"Price dropping + {discount}% discount"
            confidence = 80
        elif price_num and price_num < 2000 and rating_num >= 4.0:
            verdict = "Buy"
            reason = f"Good price (₹{price_num}) with high rating ({rating_num}/5)"
            confidence = 75
        elif discount >= 40:
            verdict = "Buy"
            reason = f"High discount: {discount}%"
            confidence = 70
        else:
            reason = f"Wait for better deal (Current: {discount}% off, ₹{price_num}, {rating_num}/5)"
            confidence = 30
        
        # Update price history
        if url and price_num:
            self._update_price_history(url, price_num, title)
        
        return {
            "verdict": verdict,
            "reason": reason,
            "confidence": confidence,
            "category": category,
            "price_trend": price_trend,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _parse_price(self, price_str):
        """Parse price string to float, handling various formats."""
        if not price_str:
            return None
        
        try:
            # Remove common currency symbols and extra characters
            cleaned = re.sub(r'[₹$€£,.\s\n]', '', str(price_str))
            
            # Handle cases like "9159\n." -> "9159"
            cleaned = cleaned.replace('\n', '').replace('.', '')
            
            # Extract first number found
            numbers = re.findall(r'\d+', cleaned)
            if numbers:
                return float(numbers[0])
            else:
                return None
        except Exception as e:
            print(f"Price parsing error for '{price_str}': {e}")
            return None
    
    def _determine_category(self, title):
        """Determine product category from title."""
        title_lower = title.lower()
        
        if any(word in title_lower for word in ['laptop', 'computer', 'phone', 'smartphone', 'headphone', 'camera', 'watch']):
            return 'electronics'
        elif any(word in title_lower for word in ['shirt', 'jeans', 'dress', 'shoes', 'nike', 'adidas', 'levis']):
            return 'fashion'
        elif any(word in title_lower for word in ['lipstick', 'foundation', 'makeup', 'beauty', 'cosmetic']):
            return 'beauty'
        elif any(word in title_lower for word in ['running', 'fitness', 'sports', 'gym', 'workout']):
            return 'sports'
        elif any(word in title_lower for word in ['kitchen', 'appliance', 'home', 'washing', 'fryer']):
            return 'home_kitchen'
        elif any(word in title_lower for word in ['book', 'novel', 'author']):
            return 'books'
        else:
            return 'general'
    
    def _check_price_trend(self, url, current_price):
        """Check if price is trending down."""
        if not url or not current_price:
            return "unknown"
        
        if url in self.price_history:
            prices = self.price_history[url]['prices']
            if len(prices) >= 2:
                if prices[-1] < prices[-2]:
                    return "decreasing"
                elif prices[-1] > prices[-2]:
                    return "increasing"
                else:
                    return "stable"
        
        return "unknown"
    
    def _update_price_history(self, url, price, title):
        """Update price history for a product."""
        if url not in self.price_history:
            self.price_history[url] = {
                'title': title,
                'prices': [],
                'first_seen': datetime.now().isoformat()
            }
        
        # Add current price
        self.price_history[url]['prices'].append(price)
        self.price_history[url]['last_updated'] = datetime.now().isoformat()
        
        # Keep only last 10 prices
        if len(self.price_history[url]['prices']) > 10:
            self.price_history[url]['prices'] = self.price_history[url]['prices'][-10:]
        
        self._save_price_history()
    
    def get_price_history(self, url):
        """Get price history for a specific URL."""
        return self.price_history.get(url, {})
    
    def get_best_deals_by_category(self, deals):
        """Get the best deals organized by category."""
        categorized = {}
        for deal in deals:
            category = self._determine_category(deal.get('title', ''))
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(deal)
        
        return categorized 