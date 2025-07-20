import asyncio
from typing import List, Dict, Optional
from playwright.async_api import async_playwright
import re
from datetime import datetime
import requests
from bs4 import BeautifulSoup

class LiveDealScraper:
    def __init__(self):
        self.deal_sites = {
            'amazon': {
                'deals_page': 'https://www.amazon.in/deals',
                'best_sellers': 'https://www.amazon.in/gp/bestsellers',
                'today_deals': 'https://www.amazon.in/gp/goldbox'
            },
            'flipkart': {
                'deals_page': 'https://www.flipkart.com/offers-store',
                'best_sellers': 'https://www.flipkart.com/bestsellers',
                'today_deals': 'https://www.flipkart.com/offers-natwest'
            },
            'myntra': {
                'deals_page': 'https://www.myntra.com/sale',
                'best_sellers': 'https://www.myntra.com/bestsellers',
                'today_deals': 'https://www.myntra.com/offers'
            },
            'nykaa': {
                'deals_page': 'https://www.nykaa.com/offers',
                'best_sellers': 'https://www.nykaa.com/bestsellers',
                'today_deals': 'https://www.nykaa.com/sale'
            },
            'ajio': {
                'deals_page': 'https://www.ajio.com/sale',
                'best_sellers': 'https://www.ajio.com/bestsellers',
                'today_deals': 'https://www.ajio.com/offers'
            }
        }
    
    def find_live_deals_sync(self, max_deals=50) -> List[Dict]:
        """Find real deals from live websites with working URLs."""
        try:
            return asyncio.run(self.find_live_deals(max_deals))
        except RuntimeError:
            # If already in event loop, use asyncio.create_task
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're already in an async context
                return self._find_deals_sync_fallback(max_deals)
            else:
                return asyncio.run(self.find_live_deals(max_deals))
        except Exception as e:
            print(f"Live deal finding failed: {e}")
            return self._find_deals_sync_fallback(max_deals)
    
    def _find_deals_sync_fallback(self, max_deals=50) -> List[Dict]:
        """Fallback method when async doesn't work."""
        deals = []
        
        # Try to scrape all sites
        sites = [
            ('amazon', self._scrape_amazon_sync),
            ('flipkart', self._scrape_flipkart_sync),
            ('myntra', self._scrape_myntra_sync),
            ('nykaa', self._scrape_nykaa_sync),
            ('ajio', self._scrape_ajio_sync)
        ]
        
        for site_name, scraper_func in sites:
            try:
                print(f"🔍 Scraping {site_name.title()}...")
                site_deals = scraper_func(max_deals//5)
                deals.extend(site_deals)
                print(f"✅ Found {len(site_deals)} deals from {site_name.title()}")
            except Exception as e:
                print(f"❌ {site_name.title()} scraping failed: {e}")
        
        return deals[:max_deals]
    
    def _scrape_amazon_sync(self, max_deals=10) -> List[Dict]:
        """Synchronous Amazon scraper."""
        deals = []
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get('https://www.amazon.in/deals', headers=headers, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for deal elements
                deal_elements = soup.find_all(['div', 'section'], class_=lambda x: x and any(word in x.lower() for word in ['deal', 'product', 'item']))
                
                for element in deal_elements[:max_deals]:
                    try:
                        # Find product link
                        link = element.find('a', href=re.compile(r'/dp/|/gp/product/'))
                        if not link:
                            continue
                        
                        url = link.get('href')
                        if not url:
                            continue
                        
                        # Make URL absolute
                        if url.startswith('/'):
                            url = f"https://www.amazon.in{url}"
                        
                        # Get title
                        title_el = link.find(['h2', 'h3', 'span'], class_=lambda x: x and 'title' in x.lower())
                        title = title_el.get_text().strip() if title_el else "Amazon Product"
                        
                        # Get price
                        price_el = element.find(['span', 'div'], class_=lambda x: x and 'price' in x.lower())
                        price = price_el.get_text().strip() if price_el else "₹999"
                        
                        # Calculate discount
                        original_price_el = element.find(['span', 'div'], class_=lambda x: x and 'strike' in x.lower())
                        discount_percent = 25  # Default
                        if original_price_el:
                            original_price = original_price_el.get_text().strip()
                            try:
                                original = float(re.sub(r'[₹,.\s]', '', original_price))
                                current = float(re.sub(r'[₹,.\s]', '', price))
                                discount_percent = int(((original - current) / original) * 100)
                            except:
                                pass
                        
                        deals.append({
                            'title': title[:100],
                            'price': price,
                            'url': url,
                            'discount_percent': discount_percent,
                            'rating': '4.0 out of 5',
                            'source': 'Amazon',
                            'has_timer': True,
                            'scraped_at': datetime.now().isoformat()
                        })
                        
                    except Exception as e:
                        continue
                        
        except Exception as e:
            print(f"Amazon sync scraping error: {e}")
        
        return deals
    
    def _scrape_flipkart_sync(self, max_deals=10) -> List[Dict]:
        """Synchronous Flipkart scraper."""
        deals = []
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get('https://www.flipkart.com/offers-store', headers=headers, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for product elements
                product_elements = soup.find_all(['div', 'section'], class_=lambda x: x and any(word in x.lower() for word in ['product', 'item', 'deal']))
                
                for element in product_elements[:max_deals]:
                    try:
                        # Find product link
                        link = element.find('a', href=re.compile(r'/p/|/product/'))
                        if not link:
                            continue
                        
                        url = link.get('href')
                        if not url:
                            continue
                        
                        # Make URL absolute
                        if url.startswith('/'):
                            url = f"https://www.flipkart.com{url}"
                        
                        # Get title
                        title_el = link.find(['h3', 'h4', 'span'], class_=lambda x: x and 'title' in x.lower())
                        title = title_el.get_text().strip() if title_el else "Flipkart Product"
                        
                        # Get price
                        price_el = element.find(['span', 'div'], class_=lambda x: x and 'price' in x.lower())
                        price = price_el.get_text().strip() if price_el else "₹999"
                        
                        # Get discount
                        discount_el = element.find(['span', 'div'], class_=lambda x: x and 'discount' in x.lower())
                        discount_percent = 30  # Default
                        if discount_el:
                            discount_text = discount_el.get_text().strip()
                            try:
                                discount_percent = int(re.sub(r'[%\s]', '', discount_text))
                            except:
                                pass
                        
                        deals.append({
                            'title': title[:100],
                            'price': price,
                            'url': url,
                            'discount_percent': discount_percent,
                            'rating': '4.0 out of 5',
                            'source': 'Flipkart',
                            'has_timer': True,
                            'scraped_at': datetime.now().isoformat()
                        })
                        
                    except Exception as e:
                        continue
                        
        except Exception as e:
            print(f"Flipkart sync scraping error: {e}")
        
        return deals
    
    def _scrape_myntra_sync(self, max_deals=10) -> List[Dict]:
        """Synchronous Myntra scraper."""
        deals = []
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get('https://www.myntra.com/sale', headers=headers, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for product elements
                product_elements = soup.find_all(['div', 'section'], class_=lambda x: x and any(word in x.lower() for word in ['product', 'item', 'deal']))
                
                for element in product_elements[:max_deals]:
                    try:
                        # Find product link
                        link = element.find('a', href=re.compile(r'/buy|/product/'))
                        if not link:
                            continue
                        
                        url = link.get('href')
                        if not url:
                            continue
                        
                        # Make URL absolute
                        if url.startswith('/'):
                            url = f"https://www.myntra.com{url}"
                        
                        # Get title
                        title_el = link.find(['h3', 'h4', 'span'], class_=lambda x: x and 'title' in x.lower())
                        title = title_el.get_text().strip() if title_el else "Myntra Product"
                        
                        # Get price
                        price_el = element.find(['span', 'div'], class_=lambda x: x and 'price' in x.lower())
                        price = price_el.get_text().strip() if price_el else "₹999"
                        
                        # Get discount
                        discount_el = element.find(['span', 'div'], class_=lambda x: x and 'discount' in x.lower())
                        discount_percent = 40  # Default for fashion
                        if discount_el:
                            discount_text = discount_el.get_text().strip()
                            try:
                                discount_percent = int(re.sub(r'[%\s]', '', discount_text))
                            except:
                                pass
                        
                        deals.append({
                            'title': title[:100],
                            'price': price,
                            'url': url,
                            'discount_percent': discount_percent,
                            'rating': '4.2 out of 5',
                            'source': 'Myntra',
                            'has_timer': True,
                            'scraped_at': datetime.now().isoformat()
                        })
                        
                    except Exception as e:
                        continue
                        
        except Exception as e:
            print(f"Myntra sync scraping error: {e}")
        
        return deals
    
    def _scrape_nykaa_sync(self, max_deals=10) -> List[Dict]:
        """Synchronous Nykaa scraper."""
        deals = []
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get('https://www.nykaa.com/offers', headers=headers, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for product elements
                product_elements = soup.find_all(['div', 'section'], class_=lambda x: x and any(word in x.lower() for word in ['product', 'item', 'deal']))
                
                for element in product_elements[:max_deals]:
                    try:
                        # Find product link
                        link = element.find('a', href=re.compile(r'/p/|/product/'))
                        if not link:
                            continue
                        
                        url = link.get('href')
                        if not url:
                            continue
                        
                        # Make URL absolute
                        if url.startswith('/'):
                            url = f"https://www.nykaa.com{url}"
                        
                        # Get title
                        title_el = link.find(['h3', 'h4', 'span'], class_=lambda x: x and 'title' in x.lower())
                        title = title_el.get_text().strip() if title_el else "Nykaa Product"
                        
                        # Get price
                        price_el = element.find(['span', 'div'], class_=lambda x: x and 'price' in x.lower())
                        price = price_el.get_text().strip() if price_el else "₹999"
                        
                        # Get discount
                        discount_el = element.find(['span', 'div'], class_=lambda x: x and 'discount' in x.lower())
                        discount_percent = 50  # Default for beauty
                        if discount_el:
                            discount_text = discount_el.get_text().strip()
                            try:
                                discount_percent = int(re.sub(r'[%\s]', '', discount_text))
                            except:
                                pass
                        
                        deals.append({
                            'title': title[:100],
                            'price': price,
                            'url': url,
                            'discount_percent': discount_percent,
                            'rating': '4.3 out of 5',
                            'source': 'Nykaa',
                            'has_timer': True,
                            'scraped_at': datetime.now().isoformat()
                        })
                        
                    except Exception as e:
                        continue
                        
        except Exception as e:
            print(f"Nykaa sync scraping error: {e}")
        
        return deals
    
    def _scrape_ajio_sync(self, max_deals=10) -> List[Dict]:
        """Synchronous Ajio scraper."""
        deals = []
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get('https://www.ajio.com/sale', headers=headers, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for product elements
                product_elements = soup.find_all(['div', 'section'], class_=lambda x: x and any(word in x.lower() for word in ['product', 'item', 'deal']))
                
                for element in product_elements[:max_deals]:
                    try:
                        # Find product link
                        link = element.find('a', href=re.compile(r'/p/|/product/'))
                        if not link:
                            continue
                        
                        url = link.get('href')
                        if not url:
                            continue
                        
                        # Make URL absolute
                        if url.startswith('/'):
                            url = f"https://www.ajio.com{url}"
                        
                        # Get title
                        title_el = link.find(['h3', 'h4', 'span'], class_=lambda x: x and 'title' in x.lower())
                        title = title_el.get_text().strip() if title_el else "Ajio Product"
                        
                        # Get price
                        price_el = element.find(['span', 'div'], class_=lambda x: x and 'price' in x.lower())
                        price = price_el.get_text().strip() if price_el else "₹999"
                        
                        # Get discount
                        discount_el = element.find(['span', 'div'], class_=lambda x: x and 'discount' in x.lower())
                        discount_percent = 45  # Default for fashion
                        if discount_el:
                            discount_text = discount_el.get_text().strip()
                            try:
                                discount_percent = int(re.sub(r'[%\s]', '', discount_text))
                            except:
                                pass
                        
                        deals.append({
                            'title': title[:100],
                            'price': price,
                            'url': url,
                            'discount_percent': discount_percent,
                            'rating': '4.4 out of 5',
                            'source': 'Ajio',
                            'has_timer': True,
                            'scraped_at': datetime.now().isoformat()
                        })
                        
                    except Exception as e:
                        continue
                        
        except Exception as e:
            print(f"Ajio sync scraping error: {e}")
        
        return deals
    
    async def find_live_deals(self, max_deals=50) -> List[Dict]:
        """Find real deals from live websites with working URLs."""
        all_deals = []
        
        # Scrape from multiple sites
        tasks = [
            self._scrape_amazon_deals(max_deals//5),
            self._scrape_flipkart_deals(max_deals//5),
            self._scrape_myntra_deals(max_deals//5),
            self._scrape_nykaa_deals(max_deals//5),
            self._scrape_ajio_deals(max_deals//5)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, list):
                all_deals.extend(result)
        
        return all_deals[:max_deals]
    
    async def _scrape_amazon_deals(self, max_deals=10) -> List[Dict]:
        """Scrape real deals from Amazon with working URLs."""
        deals = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                # Try Amazon deals page
                await page.goto('https://www.amazon.in/deals', timeout=20000)
                await page.wait_for_load_state('domcontentloaded', timeout=10000)
                
                # Look for deal elements with timers
                deal_elements = await page.query_selector_all('[data-component-type="s-deal-card"], .a-section.a-spacing-base, [class*="deal"]')
                
                for element in deal_elements[:max_deals]:
                    try:
                        # Get real product link
                        link_el = await element.query_selector('a[href*="/dp/"], a[href*="/gp/product/"]')
                        if not link_el:
                            continue
                        
                        url = await link_el.get_attribute('href')
                        if not url:
                            continue
                        
                        # Make URL absolute
                        if url.startswith('/'):
                            url = f"https://www.amazon.in{url}"
                        
                        # Get title
                        title_el = await element.query_selector('h2 a, h3 a, .a-text-normal, [class*="title"]')
                        title = await title_el.inner_text() if title_el else "Amazon Product"
                        
                        # Get price
                        price_el = await element.query_selector('.a-price .a-offscreen, .a-price-whole, [class*="price"]')
                        price = await price_el.inner_text() if price_el else "₹999"
                        
                        # Check for timer/deal badge
                        timer_el = await element.query_selector('[class*="timer"], [class*="countdown"], [class*="deal"]')
                        has_timer = timer_el is not None
                        
                        # Calculate discount
                        original_price_el = await element.query_selector('.a-text-strike, [class*="original"]')
                        discount_percent = 0
                        if original_price_el:
                            original_price = await original_price_el.inner_text()
                            try:
                                original = float(re.sub(r'[₹,.\s]', '', original_price))
                                current = float(re.sub(r'[₹,.\s]', '', price))
                                discount_percent = int(((original - current) / original) * 100)
                            except:
                                discount_percent = 25  # Default
                        
                        # Get rating
                        rating_el = await element.query_selector('.a-icon-alt, [class*="rating"]')
                        rating = await rating_el.inner_text() if rating_el else "4.0 out of 5"
                        
                        deals.append({
                            'title': title.strip()[:100],
                            'price': price.strip(),
                            'url': url,
                            'discount_percent': discount_percent,
                            'rating': rating,
                            'source': 'Amazon',
                            'has_timer': has_timer,
                            'scraped_at': datetime.now().isoformat()
                        })
                        
                    except Exception as e:
                        continue
                        
            except Exception as e:
                print(f"Amazon scraping error: {e}")
            finally:
                await context.close()
                await browser.close()
        
        return deals
    
    async def _scrape_flipkart_deals(self, max_deals=10) -> List[Dict]:
        """Scrape real deals from Flipkart with working URLs."""
        deals = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                # Try Flipkart offers page
                await page.goto('https://www.flipkart.com/offers-store', timeout=20000)
                await page.wait_for_load_state('domcontentloaded', timeout=10000)
                
                # Look for product elements
                product_elements = await page.query_selector_all('[class*="product"], [class*="item"], [class*="deal"]')
                
                for element in product_elements[:max_deals]:
                    try:
                        # Get real product link
                        link_el = await element.query_selector('a[href*="/p/"], a[href*="/product/"]')
                        if not link_el:
                            continue
                        
                        url = await link_el.get_attribute('href')
                        if not url:
                            continue
                        
                        # Make URL absolute
                        if url.startswith('/'):
                            url = f"https://www.flipkart.com{url}"
                        
                        # Get title
                        title_el = await element.query_selector('a[class*="title"], a[class*="name"], [class*="title"]')
                        title = await title_el.inner_text() if title_el else "Flipkart Product"
                        
                        # Get price
                        price_el = await element.query_selector('[class*="price"]')
                        price = await price_el.inner_text() if price_el else "₹999"
                        
                        # Check for timer/deal badge
                        timer_el = await element.query_selector('[class*="timer"], [class*="countdown"], [class*="deal"]')
                        has_timer = timer_el is not None
                        
                        # Calculate discount
                        discount_el = await element.query_selector('[class*="discount"]')
                        discount_percent = 0
                        if discount_el:
                            discount_text = await discount_el.inner_text()
                            try:
                                discount_percent = int(re.sub(r'[%\s]', '', discount_text))
                            except:
                                discount_percent = 30  # Default
                        
                        # Get rating
                        rating_el = await element.query_selector('[class*="rating"]')
                        rating = await rating_el.inner_text() if rating_el else "4.0 out of 5"
                        
                        deals.append({
                            'title': title.strip()[:100],
                            'price': price.strip(),
                            'url': url,
                            'discount_percent': discount_percent,
                            'rating': rating,
                            'source': 'Flipkart',
                            'has_timer': has_timer,
                            'scraped_at': datetime.now().isoformat()
                        })
                        
                    except Exception as e:
                        continue
                        
            except Exception as e:
                print(f"Flipkart scraping error: {e}")
            finally:
                await context.close()
                await browser.close()
        
        return deals
    
    async def _scrape_myntra_deals(self, max_deals=10) -> List[Dict]:
        """Scrape real deals from Myntra with working URLs."""
        deals = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                # Try Myntra sale page
                await page.goto('https://www.myntra.com/sale', timeout=20000)
                await page.wait_for_load_state('domcontentloaded', timeout=10000)
                
                # Look for product elements
                product_elements = await page.query_selector_all('[class*="product"], [class*="item"], [class*="deal"]')
                
                for element in product_elements[:max_deals]:
                    try:
                        # Get real product link
                        link_el = await element.query_selector('a[href*="/buy"], a[href*="/product/"]')
                        if not link_el:
                            continue
                        
                        url = await link_el.get_attribute('href')
                        if not url:
                            continue
                        
                        # Make URL absolute
                        if url.startswith('/'):
                            url = f"https://www.myntra.com{url}"
                        
                        # Get title
                        title_el = await element.query_selector('a[class*="title"], a[class*="name"], [class*="title"]')
                        title = await title_el.inner_text() if title_el else "Myntra Product"
                        
                        # Get price
                        price_el = await element.query_selector('[class*="price"]')
                        price = await price_el.inner_text() if price_el else "₹999"
                        
                        # Check for timer/deal badge
                        timer_el = await element.query_selector('[class*="timer"], [class*="countdown"], [class*="deal"]')
                        has_timer = timer_el is not None
                        
                        # Calculate discount
                        discount_el = await element.query_selector('[class*="discount"]')
                        discount_percent = 0
                        if discount_el:
                            discount_text = await discount_el.inner_text()
                            try:
                                discount_percent = int(re.sub(r'[%\s]', '', discount_text))
                            except:
                                discount_percent = 40  # Default for fashion
                        
                        deals.append({
                            'title': title.strip()[:100],
                            'price': price.strip(),
                            'url': url,
                            'discount_percent': discount_percent,
                            'rating': '4.2 out of 5',  # Default for fashion
                            'source': 'Myntra',
                            'has_timer': has_timer,
                            'scraped_at': datetime.now().isoformat()
                        })
                        
                    except Exception as e:
                        continue
                        
            except Exception as e:
                print(f"Myntra scraping error: {e}")
            finally:
                await context.close()
                await browser.close()
        
        return deals
    
    async def _scrape_nykaa_deals(self, max_deals=10) -> List[Dict]:
        """Scrape real deals from Nykaa with working URLs."""
        deals = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                # Try Nykaa offers page
                await page.goto('https://www.nykaa.com/offers', timeout=20000)
                await page.wait_for_load_state('domcontentloaded', timeout=10000)
                
                # Look for product elements
                product_elements = await page.query_selector_all('[class*="product"], [class*="item"], [class*="deal"]')
                
                for element in product_elements[:max_deals]:
                    try:
                        # Get real product link
                        link_el = await element.query_selector('a[href*="/p/"], a[href*="/product/"]')
                        if not link_el:
                            continue
                        
                        url = await link_el.get_attribute('href')
                        if not url:
                            continue
                        
                        # Make URL absolute
                        if url.startswith('/'):
                            url = f"https://www.nykaa.com{url}"
                        
                        # Get title
                        title_el = await element.query_selector('a[class*="title"], a[class*="name"], [class*="title"]')
                        title = await title_el.inner_text() if title_el else "Nykaa Product"
                        
                        # Get price
                        price_el = await element.query_selector('[class*="price"]')
                        price = await price_el.inner_text() if price_el else "₹999"
                        
                        # Check for timer/deal badge
                        timer_el = await element.query_selector('[class*="timer"], [class*="countdown"], [class*="deal"]')
                        has_timer = timer_el is not None
                        
                        # Calculate discount
                        discount_el = await element.query_selector('[class*="discount"]')
                        discount_percent = 0
                        if discount_el:
                            discount_text = await discount_el.inner_text()
                            try:
                                discount_percent = int(re.sub(r'[%\s]', '', discount_text))
                            except:
                                discount_percent = 50  # Default for beauty
                        
                        deals.append({
                            'title': title.strip()[:100],
                            'price': price.strip(),
                            'url': url,
                            'discount_percent': discount_percent,
                            'rating': '4.3 out of 5',  # Default for beauty
                            'source': 'Nykaa',
                            'has_timer': has_timer,
                            'scraped_at': datetime.now().isoformat()
                        })
                        
                    except Exception as e:
                        continue
                        
            except Exception as e:
                print(f"Nykaa scraping error: {e}")
            finally:
                await context.close()
                await browser.close()
        
        return deals
    
    async def _scrape_ajio_deals(self, max_deals=10) -> List[Dict]:
        """Scrape real deals from Ajio with working URLs."""
        deals = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                # Try Ajio sale page
                await page.goto('https://www.ajio.com/sale', timeout=20000)
                await page.wait_for_load_state('domcontentloaded', timeout=10000)
                
                # Look for product elements
                product_elements = await page.query_selector_all('[class*="product"], [class*="item"], [class*="deal"]')
                
                for element in product_elements[:max_deals]:
                    try:
                        # Get real product link
                        link_el = await element.query_selector('a[href*="/p/"], a[href*="/product/"]')
                        if not link_el:
                            continue
                        
                        url = await link_el.get_attribute('href')
                        if not url:
                            continue
                        
                        # Make URL absolute
                        if url.startswith('/'):
                            url = f"https://www.ajio.com{url}"
                        
                        # Get title
                        title_el = await element.query_selector('a[class*="title"], a[class*="name"], [class*="title"]')
                        title = await title_el.inner_text() if title_el else "Ajio Product"
                        
                        # Get price
                        price_el = await element.query_selector('[class*="price"]')
                        price = await price_el.inner_text() if price_el else "₹999"
                        
                        # Check for timer/deal badge
                        timer_el = await element.query_selector('[class*="timer"], [class*="countdown"], [class*="deal"]')
                        has_timer = timer_el is not None
                        
                        # Calculate discount
                        discount_el = await element.query_selector('[class*="discount"]')
                        discount_percent = 0
                        if discount_el:
                            discount_text = await discount_el.inner_text()
                            try:
                                discount_percent = int(re.sub(r'[%\s]', '', discount_text))
                            except:
                                discount_percent = 45  # Default for fashion
                        
                        deals.append({
                            'title': title.strip()[:100],
                            'price': price.strip(),
                            'url': url,
                            'discount_percent': discount_percent,
                            'rating': '4.4 out of 5',  # Default for fashion
                            'source': 'Ajio',
                            'has_timer': has_timer,
                            'scraped_at': datetime.now().isoformat()
                        })
                        
                    except Exception as e:
                        continue
                        
            except Exception as e:
                print(f"Ajio scraping error: {e}")
            finally:
                await context.close()
                await browser.close()
        
        return deals
    
    async def find_best_sellers(self, max_products=10) -> List[Dict]:
        """Find best-selling products from multiple sites."""
        best_sellers = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                # Amazon bestsellers
                await page.goto('https://www.amazon.in/gp/bestsellers', timeout=15000)
                await page.wait_for_load_state('domcontentloaded', timeout=8000)
                
                bestseller_elements = await page.query_selector_all('[class*="product"], [class*="item"]')
                
                for element in bestseller_elements[:max_products//2]:
                    try:
                        link_el = await element.query_selector('a[href*="/dp/"]')
                        if link_el:
                            url = await link_el.get_attribute('href')
                            if url.startswith('/'):
                                url = f"https://www.amazon.in{url}"
                            
                            title_el = await element.query_selector('h2 a, h3 a, .a-text-normal')
                            title = await title_el.inner_text() if title_el else "Amazon Bestseller"
                            
                            price_el = await element.query_selector('.a-price .a-offscreen')
                            price = await price_el.inner_text() if price_el else "₹999"
                            
                            best_sellers.append({
                                'title': title.strip()[:100],
                                'price': price.strip(),
                                'url': url,
                                'source': 'Amazon Bestseller',
                                'scraped_at': datetime.now().isoformat()
                            })
                    except:
                        continue
                        
            except Exception as e:
                print(f"Bestseller scraping error: {e}")
            finally:
                await context.close()
                await browser.close()
        
        return best_sellers 

class JobListingScraper:
    """Scrapes job/internship/competition listings from various platforms."""
    def __init__(self):
        self.last_run_time = None  # To be set by scheduler

    def fetch_linkedin_jobs(self, keywords, since_time):
        """Fetch jobs from LinkedIn matching keywords, posted after since_time."""
        import requests
        from bs4 import BeautifulSoup
        from datetime import datetime, timedelta
        import re
        listings = []
        base_url = "https://www.linkedin.com/jobs/search/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        for keyword in keywords:
            params = {
                'keywords': keyword,
                'location': 'India',
                'f_TPR': 'r86400',  # posted in last 24 hours
                'f_E': '2,3',  # Entry level, Internship
                'trk': 'public_jobs_jobs-search-bar_search-submit',
            }
            try:
                response = requests.get(base_url, params=params, headers=headers, timeout=15)
                if response.status_code != 200:
                    continue
                soup = BeautifulSoup(response.content, 'html.parser')
                job_cards = soup.find_all('li', class_=re.compile(r'jobs-search-results__list-item'))
                for card in job_cards:
                    try:
                        title_el = card.find('h3')
                        company_el = card.find('h4')
                        location_el = card.find('span', class_=re.compile(r'job-search-card__location'))
                        link_el = card.find('a', href=True)
                        posted_time_el = card.find('time')
                        title = title_el.get_text(strip=True) if title_el else ''
                        company = company_el.get_text(strip=True) if company_el else ''
                        location = location_el.get_text(strip=True) if location_el else ''
                        link = link_el['href'] if link_el else ''
                        posted_time = posted_time_el['datetime'] if posted_time_el and posted_time_el.has_attr('datetime') else ''
                        # Parse posted_time to datetime
                        posted_dt = None
                        if posted_time:
                            try:
                                posted_dt = datetime.fromisoformat(posted_time.replace('Z', '+00:00'))
                            except:
                                posted_dt = None
                        if posted_dt and posted_dt < since_time:
                            continue  # Skip old jobs
                        # Work type (Remote/Onsite/Hybrid) - LinkedIn may have a tag
                        work_type = ''
                        tag_els = card.find_all('span', class_=re.compile(r'job-search-card__job-insight'))
                        tags = [keyword.lower()]
                        for tag_el in tag_els:
                            tag_text = tag_el.get_text(strip=True)
                            if any(x in tag_text.lower() for x in ['remote', 'onsite', 'hybrid']):
                                work_type = tag_text
                            tags.append(tag_text.lower())
                        listings.append({
                            'title': title,
                            'company': company,
                            'location': location,
                            'work_type': work_type,
                            'posted_time': posted_time,
                            'deadline': '',
                            'link': link,
                            'tags': list(set(tags)),
                            'source': 'LinkedIn',
                        })
                    except Exception:
                        continue
            except Exception:
                continue
        print(f"[DEBUG] LinkedIn: {len(listings)} jobs fetched.")
        return listings

    def fetch_unstop_events(self, since_time):
        """Fetch new hackathons, sprints, competitions from Unstop posted after since_time."""
        import requests
        from bs4 import BeautifulSoup
        from datetime import datetime
        import re
        listings = []
        base_url = "https://unstop.com/competitions"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        try:
            response = requests.get(base_url, headers=headers, timeout=15)
            if response.status_code != 200:
                return []
            soup = BeautifulSoup(response.content, 'html.parser')
            event_cards = soup.find_all('div', class_=re.compile(r'event-card|competition-card'))
            for card in event_cards:
                try:
                    title_el = card.find('h3')
                    org_el = card.find('div', class_=re.compile(r'organizer|org-name'))
                    deadline_el = card.find('span', class_=re.compile(r'deadline|end-date'))
                    team_size_el = card.find('span', class_=re.compile(r'team-size|team'))
                    eligibility_el = card.find('span', class_=re.compile(r'eligibility|criteria'))
                    link_el = card.find('a', href=True)
                    title = title_el.get_text(strip=True) if title_el else ''
                    company = org_el.get_text(strip=True) if org_el else ''
                    deadline = deadline_el.get_text(strip=True) if deadline_el else ''
                    team_size = team_size_el.get_text(strip=True) if team_size_el else ''
                    eligibility = eligibility_el.get_text(strip=True) if eligibility_el else ''
                    link = link_el['href'] if link_el else ''
                    # Parse deadline to datetime if possible
                    deadline_dt = None
                    if deadline:
                        try:
                            deadline_dt = datetime.strptime(deadline, '%d %b %Y, %I:%M %p')
                        except:
                            deadline_dt = None
                    # Only include if deadline is after now
                    if deadline_dt and deadline_dt < datetime.now():
                        continue
                    # Only include if posted after since_time (Unstop may not show posted time, so skip if not available)
                    tags = ['hackathon', 'competition', 'unstop']
                    if team_size:
                        tags.append('team')
                    if eligibility:
                        tags.append(eligibility.lower())
                    listings.append({
                        'title': title,
                        'company': company,
                        'location': '',
                        'work_type': '',
                        'posted_time': '',
                        'deadline': deadline,
                        'team_size': team_size,
                        'eligibility': eligibility,
                        'link': link,
                        'tags': list(set(tags)),
                        'source': 'Unstop',
                    })
                except Exception:
                    continue
        except Exception:
            return []
        print(f"[DEBUG] Unstop: {len(listings)} events fetched.")
        return listings

    def fetch_internshala_internships(self, keywords, since_time):
        """Fetch internships from Internshala matching keywords, posted after since_time."""
        import requests
        from bs4 import BeautifulSoup
        from datetime import datetime
        import re
        listings = []
        base_url = "https://internshala.com/internships/keywords-{}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        for keyword in keywords:
            url = base_url.format(keyword.replace(' ', '-').lower())
            try:
                response = requests.get(url, headers=headers, timeout=15)
                if response.status_code != 200:
                    continue
                soup = BeautifulSoup(response.content, 'html.parser')
                cards = soup.find_all('div', class_=re.compile(r'internship_meta'))
                for card in cards:
                    try:
                        # Try to get the parent card for more info
                        parent = card.find_parent('div', class_='individual_internship')
                        title_el = parent.find('div', class_='heading_4_5') if parent else card.find_previous('div', class_='heading_4_5')
                        company_el = parent.find('a', class_='link_display_like_text') if parent else card.find_previous('a', class_='link_display_like_text')
                        location_el = card.find('a', class_='location_link')
                        posted_time_el = card.find('div', class_='status')
                        link_el = parent.find('a', href=True) if parent else card.find_previous('a', href=True)
                        title = title_el.get_text(strip=True) if title_el else ''
                        company = company_el.get_text(strip=True) if company_el else ''
                        location = location_el.get_text(strip=True) if location_el else ''
                        link = 'https://internshala.com' + link_el['href'] if link_el and link_el['href'].startswith('/') else (link_el['href'] if link_el else '')
                        posted_time = posted_time_el.get_text(strip=True) if posted_time_el else ''
                        # Parse posted_time to datetime if possible (e.g., 'Posted 1 day ago')
                        posted_dt = None
                        if posted_time:
                            m = re.search(r'(\d+) day', posted_time)
                            if m:
                                days_ago = int(m.group(1))
                                posted_dt = datetime.now() - timedelta(days=days_ago)
                            elif 'today' in posted_time.lower():
                                posted_dt = datetime.now()
                        if posted_dt and posted_dt < since_time:
                            continue
                        tags = [keyword.lower(), 'internship']
                        listings.append({
                            'title': title,
                            'company': company,
                            'location': location,
                            'work_type': '',
                            'posted_time': posted_time,
                            'deadline': '',
                            'link': link,
                            'tags': list(set(tags)),
                            'source': 'Internshala',
                        })
                    except Exception as e:
                        print(f"[DEBUG] Internshala: Error parsing card: {e}")
                        continue
            except Exception as e:
                print(f"[DEBUG] Internshala: Error fetching {url}: {e}")
                continue
        print(f"[DEBUG] Internshala: {len(listings)} internships fetched.")
        return listings

    def fetch_cuvette_roles(self, keywords, since_time):
        """Fetch internships/junior roles from Cuvette matching keywords, posted after since_time."""
        import requests
        from bs4 import BeautifulSoup
        from datetime import datetime
        import re
        listings = []
        base_url = "https://www.cuvette.tech/jobs?search={}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        for keyword in keywords:
            url = base_url.format(keyword.replace(' ', '%20'))
            try:
                response = requests.get(url, headers=headers, timeout=15)
                if response.status_code != 200:
                    continue
                soup = BeautifulSoup(response.content, 'html.parser')
                cards = soup.find_all('div', class_=re.compile(r'job-card|job-listing'))
                for card in cards:
                    try:
                        title_el = card.find('h3')
                        company_el = card.find('span', class_=re.compile(r'company|org'))
                        location_el = card.find('span', class_=re.compile(r'location'))
                        posted_time_el = card.find('span', class_=re.compile(r'post-time|posted'))
                        link_el = card.find('a', href=True)
                        title = title_el.get_text(strip=True) if title_el else ''
                        company = company_el.get_text(strip=True) if company_el else ''
                        location = location_el.get_text(strip=True) if location_el else ''
                        link = 'https://www.cuvette.tech' + link_el['href'] if link_el and link_el['href'].startswith('/') else (link_el['href'] if link_el else '')
                        posted_time = posted_time_el.get_text(strip=True) if posted_time_el else ''
                        # Parse posted_time to datetime if possible (e.g., '2 days ago')
                        posted_dt = None
                        if posted_time:
                            m = re.search(r'(\d+) day', posted_time)
                            if m:
                                days_ago = int(m.group(1))
                                posted_dt = datetime.now() - timedelta(days=days_ago)
                            elif 'today' in posted_time.lower():
                                posted_dt = datetime.now()
                        if posted_dt and posted_dt < since_time:
                            continue
                        tags = [keyword.lower(), 'cuvette']
                        listings.append({
                            'title': title,
                            'company': company,
                            'location': location,
                            'work_type': '',
                            'posted_time': posted_time,
                            'deadline': '',
                            'link': link,
                            'tags': list(set(tags)),
                            'source': 'Cuvette',
                        })
                    except Exception:
                        continue
            except Exception:
                continue
        print(f"[DEBUG] Cuvette: {len(listings)} roles fetched.")
        return listings

    def fetch_wellfound_roles(self, keywords, since_time):
        """Fetch internships/junior roles from Wellfound matching keywords, posted after since_time."""
        import requests
        from bs4 import BeautifulSoup
        from datetime import datetime
        import re
        listings = []
        base_url = "https://wellfound.com/jobs?keywords={}&remote=true"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        for keyword in keywords:
            url = base_url.format(keyword.replace(' ', '%20'))
            try:
                response = requests.get(url, headers=headers, timeout=15)
                if response.status_code != 200:
                    continue
                soup = BeautifulSoup(response.content, 'html.parser')
                cards = soup.find_all('div', class_=re.compile(r'job-listing|styles_jobListing'))
                for card in cards:
                    try:
                        title_el = card.find('div', class_=re.compile(r'title|styles_title'))
                        company_el = card.find('div', class_=re.compile(r'company|styles_companyName'))
                        location_el = card.find('div', class_=re.compile(r'location|styles_location'))
                        posted_time_el = card.find('div', class_=re.compile(r'posted|styles_postedAt'))
                        link_el = card.find('a', href=True)
                        title = title_el.get_text(strip=True) if title_el else ''
                        company = company_el.get_text(strip=True) if company_el else ''
                        location = location_el.get_text(strip=True) if location_el else ''
                        link = 'https://wellfound.com' + link_el['href'] if link_el and link_el['href'].startswith('/') else (link_el['href'] if link_el else '')
                        posted_time = posted_time_el.get_text(strip=True) if posted_time_el else ''
                        # Parse posted_time to datetime if possible (e.g., '2 days ago')
                        posted_dt = None
                        if posted_time:
                            m = re.search(r'(\d+) day', posted_time)
                            if m:
                                days_ago = int(m.group(1))
                                posted_dt = datetime.now() - timedelta(days=days_ago)
                            elif 'today' in posted_time.lower():
                                posted_dt = datetime.now()
                        if posted_dt and posted_dt < since_time:
                            continue
                        tags = [keyword.lower(), 'wellfound']
                        listings.append({
                            'title': title,
                            'company': company,
                            'location': location,
                            'work_type': '',
                            'posted_time': posted_time,
                            'deadline': '',
                            'link': link,
                            'tags': list(set(tags)),
                            'source': 'Wellfound',
                        })
                    except Exception:
                        continue
            except Exception:
                continue
        print(f"[DEBUG] Wellfound: {len(listings)} roles fetched.")
        return listings

    def fetch_all(self, keywords, since_time):
        """Fetch and combine all relevant listings from all sources."""
        jobs = self.fetch_linkedin_jobs(keywords, since_time)
        events = self.fetch_unstop_events(since_time)
        internships = self.fetch_internshala_internships(keywords, since_time)
        cuvette = self.fetch_cuvette_roles(keywords, since_time)
        wellfound = self.fetch_wellfound_roles(keywords, since_time)
        return jobs + events + internships + cuvette + wellfound 