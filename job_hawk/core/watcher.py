import json
from pathlib import Path

WATCHLIST_PATH = Path("data/watchlist.json")

class Watcher:
    def __init__(self):
        self._load()

    def _load(self):
        if WATCHLIST_PATH.exists():
            with open(WATCHLIST_PATH, "r") as f:
                self.products = json.load(f)
        else:
            self.products = []

    def get_all_products(self):
        return self.products

    def add_product(self, url, threshold=None):
        self.products.append({"url": url, "threshold": threshold})
        self._save()

    def remove_product(self, url):
        self.products = [p for p in self.products if p["url"] != url]
        self._save()

    def _save(self):
        with open(WATCHLIST_PATH, "w") as f:
            json.dump(self.products, f, indent=2) 