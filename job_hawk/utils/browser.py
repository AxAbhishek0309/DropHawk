from playwright.async_api import async_playwright

class BrowserContextManager:
    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context()
        return self.context

    async def __aexit__(self, exc_type, exc, tb):
        await self.context.close()
        await self.browser.close()
        await self.playwright.stop() 