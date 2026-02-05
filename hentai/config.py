"""
Central configuration for hanime1-downloader
"""
from pathlib import Path
from typing import Optional
from dataclasses import dataclass


# Project paths
ROOT_DIR = Path(__file__).resolve().parent
VIDEO_DIR = ROOT_DIR / 'downloads'
LOG_DIR = ROOT_DIR / 'logs'
DATABASE_DIR = ROOT_DIR / 'database'
DATA_DIR = DATABASE_DIR  # Alias for DATA_DIR used in scraper
TASKS_DB = DATABASE_DIR / 'tasks.json'

# Ensure directories exist
for directory in [VIDEO_DIR, LOG_DIR, DATABASE_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


@dataclass
class DownloadConfig:
    """Download configuration"""
    # Concurrent download limits
    max_concurrent_downloads: int = 3
    max_concurrent_scrapers: int = 2
    
    # Download settings
    chunk_size: int = 1024 * 1024  # 1MB chunks
    timeout: int = 300  # 5 minutes
    retry_attempts: int = 3
    retry_delay: int = 5
    
    # Proxy settings
    proxy_http: Optional[str] = "http://127.0.0.1:7897"
    proxy_https: Optional[str] = "http://127.0.0.1:7897"
    use_proxy: bool = False
    
    # Default resolution preference
    preferred_resolution: str = "1080p"  # Options: 360p, 480p, 720p, 1080p
    
    @property
    def proxies(self):
        """Get proxy dict for httpx"""
        if not self.use_proxy:
            return None
        return {
            "http://": self.proxy_http,
            "https://": self.proxy_https,
        }


@dataclass
class WebUIConfig:
    """WebUI server configuration"""
    host: str = "127.0.0.1"
    port: int = 9191
    reload: bool = False
    log_level: str = "info"
    
    # CORS settings
    allow_origins: list = None
    allow_credentials: bool = True
    allow_methods: list = None
    allow_headers: list = None
    
    def __post_init__(self):
        # Override from environment variables
        import os
        
        env_host = os.getenv("HANIME_HOST")
        if env_host:
            self.host = env_host
            
        env_port = os.getenv("HANIME_PORT")
        if env_port:
            try:
                self.port = int(env_port)
            except ValueError:
                pass
                
        env_reload = os.getenv("HANIME_RELOAD")
        if env_reload:
            self.reload = env_reload.lower() in ("true", "1", "yes")
            
        # Mode setting (shortcut for reload/log_level)
        env_mode = os.getenv("HANIME_MODE")
        if env_mode and env_mode.lower() == "dev":
            self.reload = True
            if self.log_level == "info": # Only override if default
                self.log_level = "debug"

        if self.allow_origins is None:
            self.allow_origins = ["*"]
        if self.allow_methods is None:
            self.allow_methods = ["*"]
        if self.allow_headers is None:
            self.allow_headers = ["*"]


@dataclass
class ScraperConfig:
    """Playwright scraper configuration"""
    headless: bool = True
    browser_type: str = "chromium"  # chromium, firefox, webkit
    timeout: int = 60000  # 60 seconds (increased for slow connections)
    wait_for_video: int = 30000  # 30 seconds
    
    # Proxy settings (use same as download_config)
    use_proxy: bool = False
    
    # Browser args
    browser_args: list = None
    
    def __post_init__(self):
        if self.browser_args is None:
            self.browser_args = [
                '--disable-blink-features=AutomationControlled',
            ]


# Global config instances
download_config = DownloadConfig()
webui_config = WebUIConfig()
scraper_config = ScraperConfig()

# Headers for requests
HEADERS = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'cache-control': 'max-age=0',
    'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'none',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
}

# Cookies for hanime1.me (user should update these)
COOKIES = {
    'quality': '1080',
}
