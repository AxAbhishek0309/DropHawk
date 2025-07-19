import asyncio
import re
from typing import Optional, Dict
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# Supported e-commerce domains
SUPPORTED_DOMAINS = [
    'amazon.',
    'flipkart.',
    'myntra.',
    'nykaa.',
    'ajio.',
    'nike.'
]

def is_supported_url(url: str) -> bool:
    """Check if the URL belongs to a supported e-commerce site."""
    return any(domain in url for domain in SUPPORTED_DOMAINS)

async def _scrape_amazon(page) -> Dict[str, Optional[str]]:
    """Scrape product info from Amazon product page."""
    try:
        # Wait for page to load
        await page.wait_for_load_state('networkidle', timeout=10000)
        
        # Try multiple title selectors
        title = None
        title_selectors = [
            '#productTitle',
            'h1.a-size-large',
            'h1.a-size-base-plus',
            'span#productTitle'
        ]
        for selector in title_selectors:
            try:
                title_el = await page.query_selector(selector)
                if title_el:
                    title = await title_el.inner_text()
                    if title and title.strip():
                        break
            except:
                continue
        
        # Try multiple price selectors
        price = None
        price_selectors = [
            'span.a-price-whole',
            'span.a-price .a-offscreen',
            '#priceblock_ourprice',
            '#priceblock_dealprice',
            '#priceblock_saleprice',
            'span.a-price.a-text-price.a-size-medium.apexPriceToPay .a-offscreen'
        ]
        for selector in price_selectors:
            try:
                price_el = await page.query_selector(selector)
                if price_el:
                    price = await price_el.inner_text()
                    if price and price.strip():
                        break
            except:
                continue
        
        # Try to get rating
        rating = None
        rating_selectors = [
            'span.a-icon-alt',
            'i.a-icon-star .a-icon-alt',
            'span[data-asin][data-attrid="average-customer-review"] span.a-icon-alt'
        ]
        for selector in rating_selectors:
            try:
                rating_el = await page.query_selector(selector)
                if rating_el:
                    rating = await rating_el.inner_text()
                    if rating and rating.strip():
                        break
            except:
                continue
        
        return {
            'title': title.strip() if title else None,
            'price': price.strip() if price else None,
            'rating': rating.strip() if rating else None
        }
    except Exception as e:
        print(f"Amazon scraping error: {e}")
        return {'title': None, 'price': None, 'rating': None}

async def _scrape_flipkart(page) -> Dict[str, Optional[str]]:
    """Scrape product info from Flipkart product page."""
    try:
        # Wait for page to load
        await page.wait_for_load_state('networkidle', timeout=10000)
        
        # Try multiple title selectors
        title = None
        title_selectors = [
            'span.B_NuCI',
            'h1._2E8Pvb',
            'h1[class*="title"]',
            'span[class*="title"]'
        ]
        for selector in title_selectors:
            try:
                title_el = await page.query_selector(selector)
                if title_el:
                    title = await title_el.inner_text()
                    if title and title.strip():
                        break
            except:
                continue
        
        # Try multiple price selectors
        price = None
        price_selectors = [
            'div._30jeq3._16Jk6d',
            'div[class*="price"]',
            'span[class*="price"]',
            'div._1vC4OE._3qQ9m1'
        ]
        for selector in price_selectors:
            try:
                price_el = await page.query_selector(selector)
                if price_el:
                    price = await price_el.inner_text()
                    if price and price.strip():
                        break
            except:
                continue
        
        # Try to get rating
        rating = None
        rating_selectors = [
            'div._3LWZlK',
            'div[class*="rating"]',
            'span[class*="rating"]'
        ]
        for selector in rating_selectors:
            try:
                rating_el = await page.query_selector(selector)
                if rating_el:
                    rating = await rating_el.inner_text()
                    if rating and rating.strip():
                        break
            except:
                continue
        
        return {
            'title': title.strip() if title else None,
            'price': price.strip() if price else None,
            'rating': rating.strip() if rating else None
        }
    except Exception as e:
        print(f"Flipkart scraping error: {e}")
        return {'title': None, 'price': None, 'rating': None}

async def _scrape_myntra(page) -> Dict[str, Optional[str]]:
    """Scrape product info from Myntra product page."""
    try:
        await page.wait_for_load_state('networkidle', timeout=10000)
        
        # Try multiple title selectors
        title = None
        title_selectors = [
            'h1.pdp-title',
            'h1[class*="title"]',
            'span[class*="title"]'
        ]
        for selector in title_selectors:
            try:
                title_el = await page.query_selector(selector)
                if title_el:
                    title = await title_el.inner_text()
                    if title and title.strip():
                        break
            except:
                continue
        
        # Try multiple price selectors
        price = None
        price_selectors = [
            'span.pdp-price',
            'span.pdp-discounted-price',
            'span[class*="price"]',
            'div[class*="price"]'
        ]
        for selector in price_selectors:
            try:
                price_el = await page.query_selector(selector)
                if price_el:
                    price = await price_el.inner_text()
                    if price and price.strip():
                        break
            except:
                continue
        
        # Try to get rating
        rating = None
        rating_selectors = [
            'div.index-overallRating',
            'span[class*="rating"]',
            'div[class*="rating"]'
        ]
        for selector in rating_selectors:
            try:
                rating_el = await page.query_selector(selector)
                if rating_el:
                    rating = await rating_el.inner_text()
                    if rating and rating.strip():
                        break
            except:
                continue
        
        return {
            'title': title.strip() if title else None,
            'price': price.strip() if price else None,
            'rating': rating.strip() if rating else None
        }
    except Exception as e:
        print(f"Myntra scraping error: {e}")
        return {'title': None, 'price': None, 'rating': None}

async def _scrape_nykaa(page) -> Dict[str, Optional[str]]:
    """Scrape product info from Nykaa product page."""
    try:
        await page.wait_for_load_state('networkidle', timeout=10000)
        
        # Try multiple title selectors
        title = None
        title_selectors = [
            'h1[class*="title"]',
            'h1[class*="product"]',
            'span[class*="title"]'
        ]
        for selector in title_selectors:
            try:
                title_el = await page.query_selector(selector)
                if title_el:
                    title = await title_el.inner_text()
                    if title and title.strip():
                        break
            except:
                continue
        
        # Try multiple price selectors
        price = None
        price_selectors = [
            'span[class*="price"]',
            'div[class*="price"]',
            'span[class*="discount"]'
        ]
        for selector in price_selectors:
            try:
                price_el = await page.query_selector(selector)
                if price_el:
                    price = await price_el.inner_text()
                    if price and price.strip():
                        break
            except:
                continue
        
        # Try to get rating
        rating = None
        rating_selectors = [
            'span[class*="rating"]',
            'div[class*="rating"]',
            'span[class*="star"]'
        ]
        for selector in rating_selectors:
            try:
                rating_el = await page.query_selector(selector)
                if rating_el:
                    rating = await rating_el.inner_text()
                    if rating and rating.strip():
                        break
            except:
                continue
        
        return {
            'title': title.strip() if title else None,
            'price': price.strip() if price else None,
            'rating': rating.strip() if rating else None
        }
    except Exception as e:
        print(f"Nykaa scraping error: {e}")
        return {'title': None, 'price': None, 'rating': None}

async def _scrape_ajio(page) -> Dict[str, Optional[str]]:
    """Scrape product info from Ajio product page."""
    try:
        await page.wait_for_load_state('networkidle', timeout=10000)
        
        # Try multiple title selectors
        title = None
        title_selectors = [
            'h1[class*="title"]',
            'h1[class*="product"]',
            'span[class*="title"]'
        ]
        for selector in title_selectors:
            try:
                title_el = await page.query_selector(selector)
                if title_el:
                    title = await title_el.inner_text()
                    if title and title.strip():
                        break
            except:
                continue
        
        # Try multiple price selectors
        price = None
        price_selectors = [
            'span[class*="price"]',
            'div[class*="price"]',
            'span[class*="discount"]'
        ]
        for selector in price_selectors:
            try:
                price_el = await page.query_selector(selector)
                if price_el:
                    price = await price_el.inner_text()
                    if price and price.strip():
                        break
            except:
                continue
        
        # Try to get rating
        rating = None
        rating_selectors = [
            'span[class*="rating"]',
            'div[class*="rating"]',
            'span[class*="star"]'
        ]
        for selector in rating_selectors:
            try:
                rating_el = await page.query_selector(selector)
                if rating_el:
                    rating = await rating_el.inner_text()
                    if rating and rating.strip():
                        break
            except:
                continue
        
        return {
            'title': title.strip() if title else None,
            'price': price.strip() if price else None,
            'rating': rating.strip() if rating else None
        }
    except Exception as e:
        print(f"Ajio scraping error: {e}")
        return {'title': None, 'price': None, 'rating': None}

async def _scrape_nike(page) -> Dict[str, Optional[str]]:
    """Scrape product info from Nike product page."""
    try:
        await page.wait_for_load_state('networkidle', timeout=10000)
        
        # Try multiple title selectors
        title = None
        title_selectors = [
            'h1[class*="title"]',
            'h1[class*="product"]',
            'span[class*="title"]'
        ]
        for selector in title_selectors:
            try:
                title_el = await page.query_selector(selector)
                if title_el:
                    title = await title_el.inner_text()
                    if title and title.strip():
                        break
            except:
                continue
        
        # Try multiple price selectors
        price = None
        price_selectors = [
            'span[class*="price"]',
            'div[class*="price"]',
            'span[class*="discount"]'
        ]
        for selector in price_selectors:
            try:
                price_el = await page.query_selector(selector)
                if price_el:
                    price = await price_el.inner_text()
                    if price and price.strip():
                        break
            except:
                continue
        
        # Try to get rating
        rating = None
        rating_selectors = [
            'span[class*="rating"]',
            'div[class*="rating"]',
            'span[class*="star"]'
        ]
        for selector in rating_selectors:
            try:
                rating_el = await page.query_selector(selector)
                if rating_el:
                    rating = await rating_el.inner_text()
                    if rating and rating.strip():
                        break
            except:
                continue
        
        return {
            'title': title.strip() if title else None,
            'price': price.strip() if price else None,
            'rating': rating.strip() if rating else None
        }
    except Exception as e:
        print(f"Nike scraping error: {e}")
        return {'title': None, 'price': None, 'rating': None}

async def _scrape_product(url: str) -> Dict[str, Optional[str]]:
    """Dispatch to the correct scraper based on URL."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        try:
            await page.goto(url, timeout=20000)
            if 'amazon.' in url:
                data = await _scrape_amazon(page)
            elif 'flipkart.' in url:
                data = await _scrape_flipkart(page)
            elif 'myntra.' in url:
                data = await _scrape_myntra(page)
            elif 'nykaa.' in url:
                data = await _scrape_nykaa(page)
            elif 'ajio.' in url:
                data = await _scrape_ajio(page)
            elif 'nike.' in url:
                data = await _scrape_nike(page)
            else:
                raise ValueError('Unsupported URL/domain')
            data['url'] = url
            return data
        except PlaywrightTimeoutError:
            return {'title': None, 'price': None, 'rating': None, 'url': url, 'error': 'Timeout while loading page'}
        except Exception as e:
            return {'title': None, 'price': None, 'rating': None, 'url': url, 'error': str(e)}
        finally:
            await context.close()
            await browser.close()

def get_product_info(url: str) -> dict:
    """
    Given a product URL from Amazon, Flipkart, Myntra, Nykaa, Ajio, or Nike, scrape the title, price, and rating.
    Returns a dict: {title, price, rating, url}
    Handles errors gracefully.
    """
    if not is_supported_url(url):
        return {'title': None, 'price': None, 'rating': None, 'url': url, 'error': 'Unsupported URL'}
    try:
        return asyncio.run(_scrape_product(url))
    except Exception as e:
        return {'title': None, 'price': None, 'rating': None, 'url': url, 'error': str(e)} 