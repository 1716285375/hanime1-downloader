"""
Async scraper using Playwright for hanime1.me
"""
import asyncio
import re
import json
import time
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from loguru import logger
import aiohttp
import os

from config import scraper_config, download_config, DATA_DIR

# Cache configuration
CACHE_FILE = DATA_DIR / "search_cache.json"
CACHE_TTL = 86400  # 24 hours


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


class SearchCache:
    """Simple file-based cache for search results"""
    
    def __init__(self):
        self.cache = {}
        self.load()
        
    def load(self):
        """Load cache from file"""
        try:
            if CACHE_FILE.exists():
                with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
            else:
                self.cache = {}
        except Exception as e:
            logger.error(f"Error loading cache: {e}")
            self.cache = {}
            
    def save(self):
        """Save cache to file"""
        try:
            CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving cache: {e}")
            
    def get(self, url: str) -> Optional[List[dict]]:
        """Get cached videos for a URL"""
        key = self._get_key(url)
        if key in self.cache:
            entry = self.cache[key]
            if time.time() - entry.get('timestamp', 0) < CACHE_TTL:
                return entry['data']
            else:
                del self.cache[key]
        return None
        
    def set(self, url: str, videos: List[VideoInfo]):
        """Cache videos for a URL"""
        key = self._get_key(url)
        data = [asdict(v) for v in videos]
        self.cache[key] = {
            'timestamp': time.time(),
            'data': data,
            'url': url
        }
        self.save()
        
    def _get_key(self, url: str) -> str:
        """Generate cache key from URL"""
        return hashlib.md5(url.encode()).hexdigest()


class SearchScraper:
    """Scraper for search/browse pages"""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.cache = SearchCache()
        self.thumbnails_dir = DATA_DIR / "thumbnails"
        self.thumbnails_dir.mkdir(parents=True, exist_ok=True)

    async def _download_thumbnail(self, session: aiohttp.ClientSession, url: str) -> str:
        """
        Download thumbnail and return local API path.
        If download fails, return original URL.
        """
        if not url or not url.startswith('http'):
            return url
            
        try:
            # Generate filename from hash
            ext = os.path.splitext(url.split('?')[0])[1] or '.jpg'
            if len(ext) > 5: ext = '.jpg'
            
            filename = hashlib.md5(url.encode()).hexdigest() + ext
            local_path = self.thumbnails_dir / filename
            
            # Check if already exists
            if local_path.exists():
                return f"/api/thumbnails/{filename}"
                
            # Download
            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.read()
                    with open(local_path, 'wb') as f:
                        f.write(content)
                    return f"/api/thumbnails/{filename}"
                return url
        except Exception as e:
            logger.warning(f"Failed to download thumbnail {url}: {e}")
            return url
        
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
        # Check cache first
        cached_data = self.cache.get(search_url)
        if cached_data:
            return [VideoInfo(**d) for d in cached_data]
            
        if not self.context:
            await self.start()
            
        page = await self.context.new_page()
        videos = []
        
        try:
            logger.info(f"Searching: {search_url}")
            await page.goto(search_url, wait_until='domcontentloaded', timeout=scraper_config.timeout)
            
            # Wait for video container to load
            await asyncio.sleep(2)
            
            # Scroll to load lazy images
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1)
            
            # Find all video links in the content container
            # Use a more generic selector to support all layouts (Grid, List, etc.)
            # Target links inside #home-rows-wrapper containing /watch?v=
            selector = '#home-rows-wrapper a[href*="/watch?v="]'
            video_links = await page.query_selector_all(selector)
            
            logger.info(f"Found {len(video_links)} video link elements using {selector}")
            
            for link in video_links:
                try:
                    href = await link.get_attribute('href')
                    if not href:
                        continue
                    
                    # Filter out ads and non-content links
                    if 'hanime1.me/watch' not in href and not href.startswith('/watch'):
                        continue
                        
                    # Make absolute URL
                    if href.startswith('/'):
                        href = f"https://hanime1.me{href}"
                        
                    # Get thumbnail from img tag
                    img = await link.query_selector('img')
                    thumbnail_url = await img.get_attribute('src') if img else ""
                    
                    # Get title
                    # Try common title classes
                    title = "Unknown"
                    title_elem = await link.query_selector('.home-rows-videos-title') # Grid
                    if not title_elem:
                        title_elem = await link.query_selector('.title') # List/Horizontal
                    if not title_elem:
                        title_elem = await link.query_selector('.video-title') # Generic fallback
                        
                    if title_elem:
                        title = await title_elem.inner_text()
                        title = title.strip()
                    else:
                        # Extract video ID from URL as fallback
                        match = re.search(r'v=(\d+)', href)
                        title = f"Video {match.group(1)}" if match else "Unknown"
                    
                    # Avoid duplicates if any
                    if any(v.url == href for v in videos):
                        continue
                        
                    videos.append(VideoInfo(
                        title=title,
                        url=href,
                        thumbnail_url=thumbnail_url,
                        resolutions={}
                    ))
                    
                except Exception as e:
                    logger.warning(f"Error parsing video element: {e}")
                    continue
            
            logger.success(f"Found {len(videos)} valid videos on page")
            
            # Download thumbnails in parallel
            if videos:
                logger.info("Caching thumbnails...")
                async with aiohttp.ClientSession() as session:
                    tasks = []
                    for video in videos:
                        if video.thumbnail_url and video.thumbnail_url.startswith('http'):
                            tasks.append(self._download_thumbnail(session, video.thumbnail_url))
                        else:
                            tasks.append(asyncio.sleep(0, result=video.thumbnail_url))
                    
                    cached_urls = await asyncio.gather(*tasks)
                    
                    # Update video objects
                    for i, cached_url in enumerate(cached_urls):
                        videos[i].thumbnail_url = cached_url

            # Save to cache
            if videos:
                self.cache.set(search_url, videos)
                
            return videos
            
        except Exception as e:
            logger.error(f"Error searching {search_url}: {e}")
            return videos
        finally:
            await page.close()
    
    async def search_videos_paginated(
        self, 
        base_url: str, 
        start_page: int = 1, 
        end_page: Optional[int] = None
    ) -> Tuple[List[VideoInfo], int]:
        """
        Search for videos across multiple pages
        
        Args:
            base_url: Base search URL (e.g., https://hanime1.me/search?genre=裏番)
            start_page: Starting page number (default: 1)
            end_page: Ending page number (default: None, will auto-detect)
            
        Returns:
            Tuple of (List of VideoInfo objects, total_pages)
        """
        if not self.context:
            await self.start()
            
        all_videos = []
        total_pages = 0
        
        # First, detect total pages if not provided
        if end_page is None:
            page = await self.context.new_page()
            try:
                logger.info(f"Detecting total pages from: {base_url}")
                await page.goto(base_url, wait_until='domcontentloaded', timeout=scraper_config.timeout)
                await asyncio.sleep(2)
                
                # Find pagination elements
                # Look for the last page number link
                pagination_links = await page.query_selector_all('ul.pagination li.page-item a.page-link')
                
                max_page = 1
                for link in pagination_links:
                    text = await link.inner_text()
                    text = text.strip()
                    if text.isdigit():
                        max_page = max(max_page, int(text))
                
                total_pages = max_page
                end_page = max_page
                logger.info(f"Detected {total_pages} total pages")
                
            except Exception as e:
                logger.error(f"Error detecting total pages: {e}")
                end_page = start_page  # Fallback to single page
                total_pages = 1
            finally:
                await page.close()
        else:
            total_pages = end_page
        
        # Now fetch videos from each page
        for page_num in range(start_page, end_page + 1):
            # Construct page URL
            separator = '&' if '?' in base_url else '?'
            page_url = f"{base_url}{separator}page={page_num}"
            
            logger.info(f"Fetching page {page_num}/{end_page}")
            
            try:
                page_videos = await self.search_videos(page_url)
                all_videos.extend(page_videos)
                
                # Small delay between pages to be polite
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error fetching page {page_num}: {e}")
                continue
        
        logger.success(f"Fetched {len(all_videos)} total videos from {end_page - start_page + 1} pages")
        return all_videos, total_pages
