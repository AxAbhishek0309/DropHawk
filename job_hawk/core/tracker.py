from apscheduler.schedulers.background import BackgroundScheduler
from .scraper import get_product_info

class PriceTracker:
    def __init__(self, watcher):
        self.watcher = watcher
        self.scheduler = BackgroundScheduler()
        self.scheduler.add_job(self.check_all_prices, 'interval', minutes=60)
        self.scheduler.start()

    def check_price(self, url):
        return get_product_info(url)

    def check_all_prices(self):
        for product in self.watcher.get_all_products():
            info = self.check_price(product['url'])
            # Here you would log or process the info 