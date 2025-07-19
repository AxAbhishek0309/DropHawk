import schedule
import time
import json
from datetime import datetime, timedelta
from pathlib import Path
from core.deal_finder import DealFinder
from core.decision_engine import DecisionEngine
from core.telegram_exporter import TelegramExporter
import re

class DealScheduler:
    def __init__(self):
        self.deal_finder = DealFinder()
        self.decision_engine = DecisionEngine()
        self.telegram_exporter = TelegramExporter()
        self.deals_file = Path("data/active_deals.json")
        self.expired_deals_file = Path("data/expired_deals.json")
        self.price_history_file = Path("data/price_history.json")
        self._load_deals()
        self._load_price_history()
    
    def _load_deals(self):
        """Load active deals from file."""
        if self.deals_file.exists():
            with open(self.deals_file, 'r') as f:
                self.active_deals = json.load(f)
        else:
            self.active_deals = []
        
        if self.expired_deals_file.exists():
            with open(self.expired_deals_file, 'r') as f:
                self.expired_deals = json.load(f)
        else:
            self.expired_deals = []
    
    def _load_price_history(self):
        """Load price history from file."""
        if self.price_history_file.exists():
            with open(self.price_history_file, 'r') as f:
                self.price_history = json.load(f)
        else:
            self.price_history = {}
    
    def _save_deals(self):
        """Save active deals to file."""
        with open(self.deals_file, 'w') as f:
            json.dump(self.active_deals, f, indent=2)
        
        with open(self.expired_deals_file, 'w') as f:
            json.dump(self.expired_deals, f, indent=2)
    
    def _save_price_history(self):
        """Save price history to file."""
        with open(self.price_history_file, 'w') as f:
            json.dump(self.price_history, f, indent=2)
    
    def run_deal_hunt(self):
        """Main function to hunt for deals and manage them."""
        print(f"🕐 Running deal hunt at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Find new deals
        new_deals = self.deal_finder.get_best_deals_sync(max_deals=100)
        
        # Check for expired deals
        self._check_expired_deals()
        
        # Track price changes for existing deals
        self._track_price_changes()
        
        # Process new deals
        good_deals = []
        for deal in new_deals:
            if self.deal_finder.is_good_deal(deal):
                # Add timestamp and expiration
                deal['found_at'] = datetime.now().isoformat()
                deal['expires_at'] = (datetime.now() + timedelta(hours=24)).isoformat()  # 24 hour expiration
                
                # Make decision
                verdict = self.decision_engine.decide(deal)
                deal['verdict'] = verdict
                
                # Track price
                self._track_deal_price(deal)
                
                good_deals.append(deal)
        
        # Send new deals to Telegram
        if good_deals:
            print(f"🎯 Found {len(good_deals)} new good deals!")
            for deal in good_deals:
                self.telegram_exporter.export_decision(deal)
                self.active_deals.append(deal)
            
            # Send summary
            summary = f"🎯 Found {len(good_deals)} new deals!\n"
            summary += f"💰 Best discount: {max([d.get('discount_percent', 0) for d in good_deals])}%\n"
            summary += f"⭐ Average rating: {sum([float(d.get('rating', '0').split()[0]) for d in good_deals if d.get('rating')])/len(good_deals):.1f}/5"
            self.telegram_exporter.send_alert(summary)
        else:
            print("🔍 No new good deals found.")
            self.telegram_exporter.send_alert("🔍 No new good deals found. Will check again in 15 minutes!")
        
        # Send price change alerts
        self._send_price_alerts()
        
        # Save updated deals
        self._save_deals()
        self._save_price_history()
        print("✅ Deal hunt complete!")
    
    def _track_deal_price(self, deal):
        """Track price for a deal."""
        url = deal.get('url', '')
        price = deal.get('price', '')
        title = deal.get('title', '')
        
        if not url or not price:
            return
        
        # Parse price
        try:
            price_num = float(re.sub(r'[₹,.\s]', '', price))
        except:
            return
        
        if url not in self.price_history:
            self.price_history[url] = {
                'title': title,
                'prices': [],
                'first_seen': datetime.now().isoformat(),
                'source': deal.get('source', 'Unknown')
            }
        
        # Add current price
        self.price_history[url]['prices'].append({
            'price': price_num,
            'timestamp': datetime.now().isoformat(),
            'discount': deal.get('discount_percent', 0)
        })
        
        # Keep only last 20 price points
        if len(self.price_history[url]['prices']) > 20:
            self.price_history[url]['prices'] = self.price_history[url]['prices'][-20:]
        
        self.price_history[url]['last_updated'] = datetime.now().isoformat()
    
    def _track_price_changes(self):
        """Track price changes for existing deals."""
        for deal in self.active_deals:
            url = deal.get('url', '')
            if url in self.price_history:
                # Check if price has changed significantly
                prices = self.price_history[url]['prices']
                if len(prices) >= 2:
                    current_price = prices[-1]['price']
                    previous_price = prices[-2]['price']
                    
                    # Calculate price change percentage
                    if previous_price > 0:
                        price_change = ((current_price - previous_price) / previous_price) * 100
                        
                        # Alert if significant price change
                        if abs(price_change) >= 10:  # 10% change
                            change_type = "increased" if price_change > 0 else "decreased"
                            alert_msg = f"💰 **Price Alert:** {deal.get('title', 'Product')}\n"
                            alert_msg += f"📈 Price {change_type} by {abs(price_change):.1f}%\n"
                            alert_msg += f"💵 New Price: ₹{current_price}\n"
                            alert_msg += f"🔗 [View Product]({url})"
                            self.telegram_exporter.send_alert(alert_msg)
    
    def _send_price_alerts(self):
        """Send price alerts for deals with significant changes."""
        alerts_sent = 0
        for url, history in self.price_history.items():
            prices = history['prices']
            if len(prices) >= 2:
                current_price = prices[-1]['price']
                previous_price = prices[-2]['price']
                
                # Calculate price change
                if previous_price > 0:
                    price_change = ((current_price - previous_price) / previous_price) * 100
                    
                    # Alert for significant drops (good for buyers)
                    if price_change <= -15:  # 15% drop
                        alert_msg = f"📉 **PRICE DROP ALERT!** 📉\n\n"
                        alert_msg += f"🎯 **{history['title']}**\n"
                        alert_msg += f"💰 Price dropped by {abs(price_change):.1f}%\n"
                        alert_msg += f"💵 New Price: ₹{current_price}\n"
                        alert_msg += f"🏪 Source: {history['source']}\n"
                        alert_msg += f"🔗 [Buy Now]({url})"
                        self.telegram_exporter.send_alert(alert_msg)
                        alerts_sent += 1
        
        if alerts_sent > 0:
            print(f"📢 Sent {alerts_sent} price alerts")
    
    def _check_expired_deals(self):
        """Check and remove expired deals."""
        current_time = datetime.now()
        expired_count = 0
        
        # Check each active deal
        for deal in self.active_deals[:]:  # Copy list to avoid modification during iteration
            expires_at = datetime.fromisoformat(deal.get('expires_at', '2024-01-01T00:00:00'))
            
            if current_time > expires_at:
                # Deal has expired
                self.active_deals.remove(deal)
                self.expired_deals.append(deal)
                expired_count += 1
                
                # Send expiration notification
                expired_msg = f"⏰ Deal Expired: {deal.get('title', 'Unknown Product')}\n"
                expired_msg += f"💰 Price: {deal.get('price', 'N/A')}\n"
                expired_msg += f"🎯 Verdict: {deal.get('verdict', {}).get('verdict', 'Unknown')}"
                self.telegram_exporter.send_alert(expired_msg)
        
        if expired_count > 0:
            print(f"🗑️ Removed {expired_count} expired deals")
            self.telegram_exporter.send_alert(f"🗑️ {expired_count} deals have expired and been removed from tracking.")
    
    def start_scheduler(self):
        """Start the automated scheduler."""
        print("🚀 Starting Smart Buyer MCP Scheduler...")
        print("⏰ Will run every 15 minutes")
        print("📱 Sending updates to Telegram")
        print("🗑️ Auto-removing expired deals")
        print("💰 Tracking price changes")
        print("📊 Monitoring 5 websites: Amazon, Flipkart, Myntra, Nykaa, Ajio")
        
        # Schedule deal hunt every 15 minutes
        schedule.every(15).minutes.do(self.run_deal_hunt)
        
        # Run initial deal hunt
        self.run_deal_hunt()
        
        # Keep running
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def get_active_deals(self):
        """Get list of currently active deals."""
        return self.active_deals
    
    def get_expired_deals(self):
        """Get list of expired deals."""
        return self.expired_deals
    
    def get_price_history(self, url):
        """Get price history for a specific URL."""
        return self.price_history.get(url, {})
    
    def add_custom_deal(self, url, title, price, discount_percent=20):
        """Add a custom deal for tracking."""
        deal = {
            'title': title,
            'price': price,
            'url': url,
            'discount_percent': discount_percent,
            'rating': '4.0 out of 5',
            'source': 'Custom',
            'found_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(hours=24)).isoformat(),
            'verdict': self.decision_engine.decide({'price': price, 'discount_percent': discount_percent})
        }
        
        self.active_deals.append(deal)
        self._track_deal_price(deal)
        self._save_deals()
        self._save_price_history()
        
        # Send notification
        self.telegram_exporter.export_decision(deal)
        self.telegram_exporter.send_alert(f"➕ Added custom deal: {title}")
        
        return deal 