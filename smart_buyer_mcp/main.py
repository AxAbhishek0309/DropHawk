import sys
from core.watcher import Watcher
from core.tracker import PriceTracker
from core.decision_engine import DecisionEngine
from core.notion_exporter import NotionExporter
from config.settings import settings

def main():
    # Example CLI entry point for Smart Buyer MCP
    print("Smart Buyer MCP started.")
    watcher = Watcher()
    tracker = PriceTracker(watcher)
    decision_engine = DecisionEngine()
    notion_exporter = NotionExporter()

    # Example: Run a single price check and decision export for all products
    products = watcher.get_all_products()
    for product in products:
        info = tracker.check_price(product['url'])
        verdict = decision_engine.decide(info)
        notion_exporter.export_decision({**info, 'verdict': verdict})

if __name__ == "__main__":
    main() 