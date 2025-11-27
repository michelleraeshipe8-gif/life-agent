"""
Browser Automation Module - Web interaction capabilities
"""
import asyncio
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from typing import Optional, Dict, Any, List
import logging
import os

logger = logging.getLogger(__name__)


class BrowserAutomation:
    """Browser automation for web interactions"""
    
    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.screenshots_dir = "data/screenshots"
        
        # Create screenshots directory
        os.makedirs(self.screenshots_dir, exist_ok=True)
    
    async def initialize(self, headless: bool = True):
        """Initialize browser"""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=headless)
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            self.page = await self.context.new_page()
            logger.info("Browser initialized")
        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            raise
    
    async def shutdown(self):
        """Close browser"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            logger.info("Browser closed")
        except Exception as e:
            logger.error(f"Error closing browser: {e}")
    
    async def navigate(self, url: str, wait_until: str = 'networkidle') -> bool:
        """
        Navigate to URL
        
        Args:
            url: URL to navigate to
            wait_until: When to consider navigation finished
            
        Returns:
            Success status
        """
        try:
            await self.page.goto(url, wait_until=wait_until, timeout=30000)
            logger.info(f"Navigated to: {url}")
            return True
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            return False
    
    async def screenshot(self, filename: str = None) -> str:
        """
        Take screenshot
        
        Args:
            filename: Optional filename (generates one if not provided)
            
        Returns:
            Path to screenshot
        """
        if not filename:
            from datetime import datetime
            filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        filepath = os.path.join(self.screenshots_dir, filename)
        await self.page.screenshot(path=filepath, full_page=True)
        logger.info(f"Screenshot saved: {filepath}")
        return filepath
    
    async def fill_form(self, selectors: Dict[str, str]):
        """
        Fill form fields
        
        Args:
            selectors: Dict of {selector: value} to fill
        """
        for selector, value in selectors.items():
            try:
                await self.page.fill(selector, value)
                logger.debug(f"Filled {selector}")
            except Exception as e:
                logger.error(f"Failed to fill {selector}: {e}")
    
    async def click(self, selector: str, wait_for_navigation: bool = False):
        """Click element"""
        try:
            if wait_for_navigation:
                async with self.page.expect_navigation():
                    await self.page.click(selector)
            else:
                await self.page.click(selector)
            logger.debug(f"Clicked {selector}")
        except Exception as e:
            logger.error(f"Failed to click {selector}: {e}")
    
    async def get_text(self, selector: str) -> Optional[str]:
        """Get text content of element"""
        try:
            element = await self.page.query_selector(selector)
            if element:
                return await element.text_content()
        except Exception as e:
            logger.error(f"Failed to get text from {selector}: {e}")
        return None
    
    async def extract_data(self, selectors: Dict[str, str]) -> Dict[str, str]:
        """
        Extract data from multiple selectors
        
        Args:
            selectors: Dict of {key: selector}
            
        Returns:
            Dict of {key: extracted_text}
        """
        results = {}
        for key, selector in selectors.items():
            text = await self.get_text(selector)
            results[key] = text
        return results
    
    async def wait_for_selector(self, selector: str, timeout: int = 5000):
        """Wait for element to appear"""
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            return True
        except Exception as e:
            logger.error(f"Timeout waiting for {selector}")
            return False
    
    async def scrape_page(self) -> Dict[str, Any]:
        """
        Scrape current page for common data
        
        Returns:
            Dict with page data
        """
        try:
            data = {
                'url': self.page.url,
                'title': await self.page.title(),
                'html': await self.page.content(),
                'text': await self.page.inner_text('body')
            }
            return data
        except Exception as e:
            logger.error(f"Failed to scrape page: {e}")
            return {}
    
    async def execute_script(self, script: str) -> Any:
        """Execute JavaScript on page"""
        try:
            return await self.page.evaluate(script)
        except Exception as e:
            logger.error(f"Script execution failed: {e}")
            return None
    
    async def search_google(self, query: str) -> List[Dict[str, str]]:
        """
        Search Google and return results
        
        Args:
            query: Search query
            
        Returns:
            List of search result dicts
        """
        try:
            await self.navigate(f"https://www.google.com/search?q={query}")
            await asyncio.sleep(2)  # Wait for results
            
            results = []
            result_elements = await self.page.query_selector_all('.g')
            
            for element in result_elements[:10]:  # Top 10 results
                try:
                    title_elem = await element.query_selector('h3')
                    link_elem = await element.query_selector('a')
                    snippet_elem = await element.query_selector('.VwiC3b')
                    
                    if title_elem and link_elem:
                        title = await title_elem.text_content()
                        url = await link_elem.get_attribute('href')
                        snippet = await snippet_elem.text_content() if snippet_elem else ""
                        
                        results.append({
                            'title': title,
                            'url': url,
                            'snippet': snippet
                        })
                except Exception as e:
                    logger.debug(f"Error parsing result: {e}")
                    continue
            
            return results
            
        except Exception as e:
            logger.error(f"Google search failed: {e}")
            return []
    
    async def download_file(self, url: str, save_path: str) -> bool:
        """Download file from URL"""
        try:
            async with self.page.expect_download() as download_info:
                await self.page.goto(url)
            download = await download_info.value
            await download.save_as(save_path)
            logger.info(f"Downloaded: {save_path}")
            return True
        except Exception as e:
            logger.error(f"Download failed: {e}")
            return False


# Global instance
browser = BrowserAutomation()
