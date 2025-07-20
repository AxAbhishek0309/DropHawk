import requests
import os
from typing import Dict
from dotenv import load_dotenv

class TelegramExporter:
    def __init__(self):
        load_dotenv()
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        print(f"[DEBUG] TELEGRAM_BOT_TOKEN: {self.bot_token}")
        print(f"[DEBUG] TELEGRAM_CHAT_ID: {self.chat_id}")
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
    
    def export_decision(self, deal: Dict):
        """Export deal decision to Telegram with enhanced formatting."""
        title = deal.get('title', 'Unknown Product')
        price = deal.get('price', 'N/A')
        url = deal.get('url', '#')
        discount = deal.get('discount_percent', 0)
        rating = deal.get('rating', 'N/A')
        source = deal.get('source', 'Unknown')
        has_timer = deal.get('has_timer', False)
        verdict = deal.get('verdict', {})
        
        # Format the message
        message = f"🎯 **{title}**\n\n"
        message += f"💰 **Price:** {price}\n"
        message += f"🏷️ **Discount:** {discount}% off\n"
        message += f"⭐ **Rating:** {rating}\n"
        message += f"🏪 **Source:** {source}\n"
        
        # Add timer indicator
        if has_timer:
            message += f"⏰ **Limited Time Deal!**\n"
        
        # Add verdict
        if isinstance(verdict, dict):
            verdict_text = verdict.get('verdict', 'Wait')
            reason = verdict.get('reason', 'No specific reason')
            confidence = verdict.get('confidence', 0)
            category = verdict.get('category', 'general')
            
            message += f"\n🎯 **Verdict:** {verdict_text}\n"
            message += f"📊 **Confidence:** {confidence}%\n"
            message += f"📝 **Reason:** {reason}\n"
            message += f"🏷️ **Category:** {category.title()}\n"
        else:
            message += f"\n🎯 **Verdict:** {verdict}\n"
        
        # Add URL
        message += f"\n🔗 [View Product]({url})"
        
        # Send to Telegram
        self._send_message(message)
        print(f"Sent to Telegram: {title}")
    
    def send_alert(self, message: str):
        """Send alert message to Telegram."""
        self._send_message(f"🚨 **Smart Buyer Alert:**\n\n{message}")
        print(f"Alert sent to Telegram: {message}")
    
    def send_timer_alert(self, deal: Dict):
        """Send special alert for deals with timers."""
        title = deal.get('title', 'Unknown Product')
        price = deal.get('price', 'N/A')
        discount = deal.get('discount_percent', 0)
        url = deal.get('url', '#')
        
        message = f"⏰ **TIMER DEAL ALERT!** ⏰\n\n"
        message += f"🎯 **{title}**\n"
        message += f"💰 **Price:** {price}\n"
        message += f"🏷️ **Discount:** {discount}% off\n"
        message += f"⏰ **Limited Time Only!**\n"
        message += f"\n🔗 [Buy Now]({url})"
        
        self._send_message(message)
        print(f"Timer alert sent: {title}")
    
    def send_bestseller_alert(self, deal: Dict):
        """Send alert for best-selling products."""
        title = deal.get('title', 'Unknown Product')
        price = deal.get('price', 'N/A')
        source = deal.get('source', 'Unknown')
        url = deal.get('url', '#')
        
        message = f"🏆 **BESTSELLER ALERT!** 🏆\n\n"
        message += f"🎯 **{title}**\n"
        message += f"💰 **Price:** {price}\n"
        message += f"🏪 **Source:** {source}\n"
        message += f"⭐ **Popular Choice!**\n"
        message += f"\n🔗 [View Product]({url})"
        
        self._send_message(message)
        print(f"Bestseller alert sent: {title}")
    
    def send_summary(self, deals: list):
        """Send summary of all deals found."""
        if not deals:
            return
        
        message = "📊 **DEAL SUMMARY** 📊\n\n"
        
        # Count by source
        sources = {}
        timers = 0
        total_discount = 0
        
        for deal in deals:
            source = deal.get('source', 'Unknown')
            sources[source] = sources.get(source, 0) + 1
            
            if deal.get('has_timer', False):
                timers += 1
            
            total_discount += deal.get('discount_percent', 0)
        
        message += f"🎯 **Total Deals:** {len(deals)}\n"
        message += f"⏰ **Timer Deals:** {timers}\n"
        message += f"💰 **Avg Discount:** {total_discount//len(deals)}%\n\n"
        
        message += "📈 **By Source:**\n"
        for source, count in sources.items():
            message += f"  • {source}: {count} deals\n"
        
        self._send_message(message)
        print(f"Summary sent: {len(deals)} deals")
    
    def _send_message(self, message: str):
        """Send message to Telegram."""
        if not self.bot_token or not self.chat_id:
            print("Telegram bot token or chat ID not set.")
            return
            
        try:
            url = f"{self.base_url}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'Markdown',
                'disable_web_page_preview': True
            }
            
            response = requests.post(url, data=data, timeout=10)
            if response.status_code != 200:
                print(f"Telegram API error: {response.text}")
                
        except Exception as e:
            print(f"Failed to send Telegram message: {e}")
    
    def send_error(self, error_message: str):
        """Send error message to Telegram."""
        message = f"❌ **Error:** {error_message}"
        self._send_message(message)
        print(f"Error sent to Telegram: {error_message}") 