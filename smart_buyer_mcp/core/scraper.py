import asyncio
import re
from typing import Optional, Dict
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# Supported e-commerce domains
SUPPORTED_DOMAINS = [
    'amazon.',
    'flipkart.',
    'myntra.'
]

def is_supported_url(url: str) -> bool:
    """Check if the URL belongs to a supported e-commerce site."""
    return any(domain in url for domain in SUPPORTED_DOMAINS)

async def _scrape_amazon(page) -> Dict[str, Optional[str]]:
    """Scrape product info from Amazon product page."""
    await page.wait_for_selector('#productTitle', timeout=8000)
    title = (await page.query_selector('#productTitle')).inner_text()
    price = None
    # Try multiple price selectors
    for selector in ['#priceblock_ourprice', '#priceblock_dealprice', '#priceblock_saleprice', '.a-price .a-offscreen']:
        el = await page.query_selector(selector)
        if el:
            price = await el.inner_text()
            break
    # Try to get rating
    rating = None
    rating_el = await page.query_selector('span[data-asin][data-attrid="average-customer-review"] span.a-icon-alt, .a-icon-star span.a-icon-alt')
    if rating_el:
        rating = await rating_el.inner_text()
    return {
        'title': title.strip() if title else None,
        'price': price.strip() if price else None,
        'rating': rating.strip() if rating else None
    }

async def _scrape_flipkart(page) -> Dict[str, Optional[str]]:
    """Scrape product info from Flipkart product page."""
    await page.wait_for_selector('span.B_NuCI', timeout=8000)
    title = (await page.query_selector('span.B_NuCI')).inner_text()
    price = None
    price_el = await page.query_selector('div._30jeq3._16Jk6d')
    if price_el:
        price = await price_el.inner_text()
    rating = None
    rating_el = await page.query_selector('div._3LWZlK')
    if rating_el:
        rating = await rating_el.inner_text()
    return {
        'title': title.strip() if title else None,
        'price': price.strip() if price else None,
        'rating': rating.strip() if rating else None
    }

async def _scrape_myntra(page) -> Dict[str, Optional[str]]:
    """Scrape product info from Myntra product page."""
    await page.wait_for_selector('h1.pdp-title', timeout=8000)
    title = (await page.query_selector('h1.pdp-title')).inner_text()
    price = None
    price_el = await page.query_selector('span.pdp-price, span.pdp-discounted-price')
    if price_el:
        price = await price_el.inner_text()
    rating = None
    rating_el = await page.query_selector('div.index-overallRating')
    if rating_el:
        rating = await rating_el.inner_text()
    return {
        'title': title.strip() if title else None,
        'price': price.strip() if price else None,
        'rating': rating.strip() if rating else None
    }

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
    Given a product URL from Amazon, Flipkart, or Myntra, scrape the title, price, and rating.
    Returns a dict: {title, price, rating, url}
    Handles errors gracefully.
    """
    if not is_supported_url(url):
        return {'title': None, 'price': None, 'rating': None, 'url': url, 'error': 'Unsupported URL'}
    try:
        return asyncio.run(_scrape_product(url))
    except Exception as e:
        return {'title': None, 'price': None, 'rating': None, 'url': url, 'error': str(e)} 