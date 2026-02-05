"""
Async scraper using Playwright for hanime1.me
"""
import asyncio
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from loguru import logger

from config import scraper_config, download_config


@dataclass
class VideoInfo:
    """Video information"""
    title: str
    url: str
    thumbnail_url: str
    resolutions: Dict[str, str]  # {"720p": "url", "1080p": "url"}


@dataclass  
class VideoMetadata:
    """Detailed video metadata"""
    title: str
    page_url: str
    thumbnail_url: str
    video_url: str
    resolution: str


class VideoScraper:
    """Scraper for individual video pages"""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
        
    async def start(self):
        """Start the browser"""
        self.playwright = await async_playwright().start()
        
        # Select browser type
        if scraper_config.browser_type == "chromium":
            browser_type = self.playwright.chromium
        elif scraper_config.browser_type == "firefox":
            browser_type = self.playwright.firefox
        else:
            browser_type = self.playwright.webkit
            
        self.browser = await browser_type.launch(
            headless=scraper_config.headless,
            args=scraper_config.browser_args
        )
        
        # Generate fake user agent
        try:
            from fake_useragent import UserAgent
            ua = UserAgent(browsers=['chrome', 'edge']).random
        except ImportError:
            ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
            
        # Prepare context options
        context_options = {
            'viewport': {'width': 1920, 'height': 1080},
            'user_agent': ua,
            'locale': 'en-US',
            'timezone_id': 'America/New_York',
            'permissions': ['geolocation'],
            'java_script_enabled': True,
        }
        
        # Add proxy if enabled
        if scraper_config.use_proxy and download_config.use_proxy:
            proxy_server = download_config.proxy_http or download_config.proxy_https
            if proxy_server:
                context_options['proxy'] = {'server': proxy_server}
                logger.info(f"Using proxy for browser: {proxy_server}")
        
        self.context = await self.browser.new_context(**context_options)
        
        # Inject stealth scripts to bypass bot detection
        await self.context.add_init_script("""
            // Webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // Languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
            
            // Plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });

            // Chrome runtime
            window.chrome = { runtime: {} };
            
            // Notification permission
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
            );
        """)
        
        logger.info(f"Browser started: {scraper_config.browser_type}, headless={scraper_config.headless}, ua={ua}")
        
    async def close(self):
        """Close the browser"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()
        logger.info("Browser closed")
        
    async def get_video_url(self, page_url: str, resolution: str = "1080p") -> Optional[VideoMetadata]:
        """
        Extract video download URL from a video page
        
        Args:
            page_url: URL of the video page
            resolution: Preferred resolution (360p, 720p, 1080p)
            
        Returns:
            VideoMetadata object or None if extraction fails
        """
        if not self.context:
            await self.start()
            
        page = await self.context.new_page()
        
        try:
            logger.info(f"Navigating to: {page_url}")
            await page.goto(page_url, wait_until='domcontentloaded', timeout=scraper_config.timeout)
            
            # Check for "Enter" or "I am human" or "Age Verification" buttons
            # Also check for Cloudflare "Just a moment..."
            try:
                page_title = await page.title()
                if "Just a moment" in page_title or "Attention Required" in page_title:
                    if not scraper_config.headless:
                        logger.warning("\n\n!!! CLOUDFLARE CHALLENGE DETECTED !!!")
                        logger.warning("Please solve the CAPTCHA in the open browser window.")
                        logger.warning("The scraper will wait until you pass the challenge...\n")
                    else:
                        logger.info("Cloudflare challenge detected. Waiting for stealth bypass...")
                    
                    # Wait for title to change (success)
                    # We wait longer in headless mode to give stealth scripts time
                    wait_time = 60 if scraper_config.headless else 120
                    
                    for _ in range(wait_time // 2): 
                        await asyncio.sleep(2)
                        current_title = await page.title()
                        if "Just a moment" not in current_title and "Attention Required" not in current_title:
                            logger.info("Cloudflare challenge passed!")
                            break
                        
                        # In headless mode, try to find and click the verify checkbox if possible
                        if scraper_config.headless:
                             try:
                                 # Try generic checkbox search
                                 cb = await page.query_selector("iframe[src*='turnstile']")
                                 if cb:
                                     # We can't easily click inside cross-origin iframe without frame object
                                     # But maybe we can find the wrapper
                                     pass
                             except:
                                 pass
                    else:
                        if scraper_config.headless:
                             logger.error("Timeout waiting for Cloudflare bypass in headless mode.")
                             logger.error("Try running with headless=False in config.py or import cookies.")
                        else:
                             logger.error("Timeout waiting for Cloudflare challenge solution")

                # Common selectors for "Enter" buttons on hanime1
                # Note: We separate text selector because it cannot be mixed with CSS in a single query string easily
                enter_button = await page.query_selector('div#home-enter, button#enter, .enter-button')
                if not enter_button:
                     enter_button = await page.query_selector('text="Enter"')
                
                if not enter_button:
                     enter_button = await page.query_selector('text="I am human"')

                if enter_button:
                    logger.info("Found Enter/Verify button, clicking...")
                    if await enter_button.is_visible():
                        await enter_button.click()
                        await asyncio.sleep(2)
            except Exception as e:
                logger.warning(f"Error checking for enter button: {e}")

            # Wait for video player to load
            try:
                # Target the specific Plyr video element
                await page.wait_for_selector('video#player', timeout=scraper_config.wait_for_video)
            except Exception:
                logger.warning("Timeout waiting for video#player, checking generic video")
            
            # Scroll to ensure video loads (trigger lazy load)
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight/4)")
            await asyncio.sleep(1)
            
            # Extract video element
            video_element = await page.query_selector('video#player')
            if not video_element:
                video_element = await page.query_selector('video')
                
            if not video_element:
                logger.error(f"No video element found on {page_url}")
                await page.screenshot(path="debug_scraper_fail.png")
                return None
                
            # Get video source URL
            # First try specific quality from source tags
            resolutions = {}
            sources = await video_element.query_selector_all('source')
            
            for source in sources:
                src = await source.get_attribute('src')
                size = await source.get_attribute('size') # e.g. "1080"
                if src and size:
                    resolutions[f"{size}p"] = src
                elif src:
                    # Fallback regex
                    res_match = re.search(r'(\d+p)', src)
                    if res_match:
                        resolutions[res_match.group(1)] = src
                        
            # Determine best video url based on requested resolution
            video_url = None
            actual_resolution = resolution
            
            if resolutions:
                # Try to find exact match
                if resolution in resolutions:
                    video_url = resolutions[resolution]
                else:
                    # Find closest or highest
                    # Sort resolutions
                    sorted_res = sorted(resolutions.keys(), key=lambda x: int(x.replace('p', '')), reverse=True)
                    video_url = resolutions[sorted_res[0]]
                    actual_resolution = sorted_res[0]
            else:
                 # Fallback to video src
                 video_url = await video_element.get_attribute('src')
            
            if not video_url or video_url.startswith('blob:'):
                logger.error(f"Could not extract valid video URL from {page_url}")
                return None
            
            # Extract title
            title = "Unknown"
            title_element = await page.query_selector('#shareBtn-title')
            if not title_element:
                title_element = await page.query_selector('h1, .video-title')
            
            if title_element:
                title = await title_element.inner_text()
            
            title = re.sub(r'[<>\\.:~@#$%^&_\-()"/\\|?*]', '', title).strip()
            
            # Extract thumbnail
            thumbnail_url = await video_element.get_attribute('poster') or ""
            
            logger.success(f"Successfully extracted video: {title} ({actual_resolution})")
            
            return VideoMetadata(
                title=title,
                page_url=page_url,
                thumbnail_url=thumbnail_url,
                video_url=video_url,
                resolution=actual_resolution
            )
            
        except Exception as e:
            logger.error(f"Error scraping {page_url}: {e}")
            return None
        finally:
            await page.close()
            
    async def get_available_resolutions(self, page_url: str) -> Dict[str, str]:
        """
        Get all available resolutions for a video
        
        Returns:
            Dict mapping resolution to video URL
        """
        if not self.context:
            await self.start()
            
        page = await self.context.new_page()
        resolutions = {}
        
        try:
            await page.goto(page_url, wait_until='domcontentloaded', timeout=scraper_config.timeout)
            
            # Check for Cloudflare (basic bypass attempt)
            try:
                if "Just a moment" in await page.title():
                     await asyncio.sleep(5)
            except:
                pass

            try:
                await page.wait_for_selector('video#player', timeout=scraper_config.wait_for_video)
            except:
                pass
            
            video = await page.query_selector('video#player')
            if not video:
                video = await page.query_selector('video')
                
            if video:
                # Extract from source tags (best method for Hanime1)
                sources = await video.query_selector_all('source')
                for source in sources:
                    src = await source.get_attribute('src')
                    size = await source.get_attribute('size')
                    
                    if src and size:
                        resolutions[f"{size}p"] = src
                    elif src:
                        res = re.search(r'(\d+p)', src)
                        if res:
                            resolutions[res.group(1)] = src
                            
            if not resolutions and video:
                 # Fallback
                 src = await video.get_attribute('src')
                 if src:
                     resolutions['default'] = src
                            
            return resolutions
            
        except Exception as e:
            logger.error(f"Error getting resolutions for {page_url}: {e}")
            return {}
        finally:
            await page.close()


class SearchScraper:
    """Scraper for search/browse pages"""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        
    async def __aenter__(self):
        await self.start()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
        
    async def start(self):
        """Start the browser"""
        self.playwright = await async_playwright().start()
        
        if scraper_config.browser_type == "chromium":
            browser_type = self.playwright.chromium
        elif scraper_config.browser_type == "firefox":
            browser_type = self.playwright.firefox
        else:
            browser_type = self.playwright.webkit
            
        self.browser = await browser_type.launch(
            headless=scraper_config.headless,
            args=scraper_config.browser_args
        )
        
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        
    async def close(self):
        """Close the browser"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()
            
    async def search_videos(self, search_url: str) -> List[VideoInfo]:
        """
        Search for videos on a browse/search page
        
        Args:
            search_url: URL of search or browse page
            
        Returns:
            List of VideoInfo objects
        """
        if not self.context:
            await self.start()
            
        page = await self.context.new_page()
        videos = []
        
        try:
            logger.info(f"Searching: {search_url}")
            await page.goto(search_url, wait_until='domcontentloaded', timeout=scraper_config.timeout)
            
            # Scroll to load lazy images
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1)
            
            # Find video container
            container = await page.query_selector('div.home-rows-videos-wrapper, div[class*="video-list"], div[class*="videos"]')
            if not container:
                logger.error("Could not find video container")
                return videos
                
            # Find all video links
            video_links = await container.query_selector_all('a[href*="/watch/"], a[href*="video"]')
            
            for i, link in enumerate(video_links):
                if i == 0:
                    # Skip first element (often ad)
                    continue
                    
                try:
                    href = await link.get_attribute('href')
                    if not href:
                        continue
                        
                    # Make absolute URL
                    if href.startswith('/'):
                        href = f"https://hanime1.me{href}"
                        
                    # Get thumbnail
                    img = await link.query_selector('img')
                    thumbnail_url = await img.get_attribute('src') if img else ""
                    
                    # Get title
                    title_elem = await link.query_selector('div, span, p')
                    title = await title_elem.inner_text() if title_elem else f"Video {i}"
                    title = title.strip()
                    
                    videos.append(VideoInfo(
                        title=title,
                        url=href,
                        thumbnail_url=thumbnail_url,
                        resolutions={}  # Will be populated when needed
                    ))
                    
                except Exception as e:
                    logger.warning(f"Error parsing video element {i}: {e}")
                    continue
                    
            logger.success(f"Found {len(videos)} videos")
            return videos
            
        except Exception as e:
            logger.error(f"Error searching {search_url}: {e}")
            return videos
        finally:
            await page.close()
