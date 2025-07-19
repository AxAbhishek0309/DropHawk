import sys
import argparse
from core.scheduler import DealScheduler
from core.deal_finder import DealFinder
from core.decision_engine import DecisionEngine
from core.telegram_exporter import TelegramExporter

def main():
    parser = argparse.ArgumentParser(description='Smart Buyer MCP - Automated Deal Hunter')
    parser.add_argument('--mode', choices=['manual', 'auto', 'auto15', 'test'], default='manual',
                       help='Run mode: manual (one-time), auto (hourly), auto15 (15-min), test (test deals)')
    parser.add_argument('--add-deal', nargs=3, metavar=('URL', 'TITLE', 'PRICE'),
                       help='Add a custom deal for tracking')
    
    args = parser.parse_args()
    
    if args.add_deal:
        # Add custom deal
        url, title, price = args.add_deal
        scheduler = DealScheduler()
        deal = scheduler.add_custom_deal(url, title, price)
        print(f"✅ Added custom deal: {title}")
        return
    
    if args.mode == 'auto':
        # Start automated scheduler (hourly)
        scheduler = DealScheduler()
        scheduler.start_scheduler()
    elif args.mode == 'auto15':
        # Start automated scheduler (15 minutes)
        scheduler = DealScheduler()
        scheduler.start_scheduler()
    elif args.mode == 'test':
        # Test mode - run once with live data
        print("🧪 Smart Buyer MCP - Test Mode (Live Data Only)")
        deal_finder = DealFinder()
        decision_engine = DecisionEngine()
        telegram_exporter = TelegramExporter()
        
        # Find live deals
        deals = deal_finder.get_best_deals_sync(max_deals=20)
        
        if deals:
            print(f"🎯 Found {len(deals)} live deals for testing")
            for deal in deals[:5]:  # Test with first 5 deals
                verdict = decision_engine.decide(deal)
                deal['verdict'] = verdict
                telegram_exporter.export_decision(deal)
            
            # Test categorization
            categorized = decision_engine.get_best_deals_by_category(deals)
            print("\n📊 Deals by Category:")
            for category, category_deals in categorized.items():
                print(f"  {category}: {len(category_deals)} deals")
        else:
            print("❌ No live deals found for testing")
    else:
        # Manual mode - run once
        print("🛒 Smart Buyer MCP - Manual Mode (Live Data Only)")
        deal_finder = DealFinder()
        decision_engine = DecisionEngine()
        telegram_exporter = TelegramExporter()
        
        # Find real deals from live websites
        print("Searching for real deals from all websites...")
        deals = deal_finder.get_best_deals_sync(max_deals=50)
        
        if not deals:
            print("No real deals found. Will try again later...")
            telegram_exporter.send_alert("🔍 No real deals found right now. Will check again later!")
            return
        
        # Filter and process good deals
        good_deals = []
        for deal in deals:
            if deal_finder.is_good_deal(deal):
                # Get detailed product info for real deals
                detailed_info = get_product_info(deal['url'])
                if detailed_info.get('title'):
                    deal.update(detailed_info)
                good_deals.append(deal)
        
        if not good_deals:
            print("No good real deals found.")
            telegram_exporter.send_alert("🔍 No good real deals found right now. Will check again later!")
            return
        
        # Send real deals to Telegram
        print(f"Found {len(good_deals)} real good deals! Sending to Telegram...")
        
        for deal in good_deals:
            # Make decision
            verdict = decision_engine.decide(deal)
            deal['verdict'] = verdict
            
            # Send to Telegram
            telegram_exporter.export_decision(deal)
        
        # Send summary of real deals
        summary = f"🎯 Found {len(good_deals)} real deals!\n"
        summary += f"💰 Best discount: {max([d.get('discount_percent', 0) for d in good_deals])}%\n"
        summary += f"⭐ Average rating: {sum([float(d.get('rating', '0').split()[0]) for d in good_deals if d.get('rating')])/len(good_deals):.1f}/5"
        
        telegram_exporter.send_alert(summary)
        print("Real deal hunt complete! Check your Telegram for details.")

def get_product_info(url):
    """Get detailed product info using existing scraper."""
    from core.scraper import get_product_info as scrape_product
    return scrape_product(url)

if __name__ == "__main__":
    main() 