"""
Async downloader using httpx and aiohttp
"""
import asyncio
from pathlib import Path
from typing import Optional, Callable, Dict
import httpx
import aiofiles
from loguru import logger

from config import download_config, HEADERS, COOKIES


class DownloadProgress:
    """Track download progress"""
    
    def __init__(self, total_size: int = 0):
        self.total_size = total_size
        self.downloaded = 0
        self.speed = 0.0
        self.percentage = 0.0
        
    def update(self, chunk_size: int, elapsed_time: float = 0):
        """Update progress"""
        self.downloaded += chunk_size
        if self.total_size > 0:
            self.percentage = (self.downloaded / self.total_size) * 100
        if elapsed_time > 0:
            self.speed = chunk_size / elapsed_time  # bytes per second
            
    @property
    def speed_mbps(self) -> float:
        """Speed in MB/s"""
        return self.speed / (1024 * 1024)
        
    def __repr__(self):
        return f"Progress({self.percentage:.1f}%, {self.downloaded}/{self.total_size} bytes, {self.speed_mbps:.2f} MB/s)"


class AsyncDownloader:
    """Async file downloader with progress tracking"""
    
    def __init__(self):
        self.client: Optional[httpx.AsyncClient] = None
        self._downloads: Dict[str, DownloadProgress] = {}
        
    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
        
    async def start(self):
        """Initialize HTTP client"""
        logger.debug("AsyncDownloader.start() called, creating httpx client...")
        
        # Create client without proxy to avoid blocking
        # Proxy can be configured via environment variables if needed
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(download_config.timeout),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=50),
            follow_redirects=True,
            # Removed proxies parameter - was causing blocking issue
        )
        logger.info("AsyncDownloader initialized")
        
    async def close(self):
        """Close HTTP client"""
        if self.client:
            await self.client.aclose()
        logger.info("AsyncDownloader closed")
        
    async def download_file(
        self,
        url: str,
        save_path: Path,
        progress_callback: Optional[Callable[[DownloadProgress], None]] = None,
        task_id: Optional[str] = None
    ) -> bool:
        """
        Download a file with progress tracking
        
        Args:
            url: URL to download
            save_path: Path to save file
            progress_callback: Optional callback for progress updates
            task_id: Optional task ID for tracking
            
        Returns:
            True if download successful, False otherwise
        """
        if not self.client:
            await self.start()
            
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Check if file already exists
        if save_path.exists():
            logger.info(f"File already exists: {save_path}")
            return True
            
        retry_count = 0
        download_id = task_id or url
        
        while retry_count < download_config.retry_attempts:
            try:
                logger.info(f"Downloading: {url} -> {save_path}")
                
                # Make HEAD request to get file size
                head_response = await self.client.head(url, headers=HEADERS)
                total_size = int(head_response.headers.get('content-length', 0))
                
                # Initialize progress
                progress = DownloadProgress(total_size)
                self._downloads[download_id] = progress
                
                # Start download with streaming
                async with self.client.stream('GET', url, headers=HEADERS) as response:
                    response.raise_for_status()
                    
                    # Open file for writing
                    async with aiofiles.open(save_path, 'wb') as f:
                        start_time = asyncio.get_event_loop().time()
                        
                        async for chunk in response.aiter_bytes(chunk_size=download_config.chunk_size):
                            if chunk:
                                await f.write(chunk)
                                
                                # Update progress
                                elapsed = asyncio.get_event_loop().time() - start_time
                                progress.update(len(chunk), elapsed)
                                start_time = asyncio.get_event_loop().time()
                                
                                # Call progress callback
                                if progress_callback:
                                    progress_callback(progress)
                                    
                logger.success(f"Download completed: {save_path} ({progress.downloaded} bytes)")
                del self._downloads[download_id]
                return True
                
            except httpx.HTTPError as e:
                retry_count += 1
                logger.warning(f"Download error (attempt {retry_count}/{download_config.retry_attempts}): {e}")
                
                if retry_count < download_config.retry_attempts:
                    await asyncio.sleep(download_config.retry_delay)
                else:
                    logger.error(f"Download failed after {download_config.retry_attempts} attempts: {url}")
                    # Clean up partial file
                    if save_path.exists():
                        save_path.unlink()
                    if download_id in self._downloads:
                        del self._downloads[download_id]
                    return False
                    
            except Exception as e:
                logger.error(f"Unexpected error downloading {url}: {e}")
                if save_path.exists():
                    save_path.unlink()
                if download_id in self._downloads:
                    del self._downloads[download_id]
                return False
                
        return False
        
    async def download_image(
        self,
        url: str,
        save_path: Path,
        task_id: Optional[str] = None
    ) -> bool:
        """
        Download an image file
        
        Args:
            url: Image URL
            save_path: Path to save image
            task_id: Optional task ID
            
        Returns:
            True if successful
        """
        if not self.client:
            await self.start()
            
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        if save_path.exists():
            logger.debug(f"Image already exists: {save_path}")
            return True
            
        try:
            logger.debug(f"Downloading image: {url}")
            response = await self.client.get(url, headers=HEADERS)
            response.raise_for_status()
            
            async with aiofiles.open(save_path, 'wb') as f:
                await f.write(response.content)
                
            logger.success(f"Image downloaded: {save_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error downloading image {url}: {e}")
            if save_path.exists():
                save_path.unlink()
            return False
            
    def get_progress(self, download_id: str) -> Optional[DownloadProgress]:
        """Get progress for a download"""
        return self._downloads.get(download_id)
        
    @property
    def active_downloads(self) -> int:
        """Number of active downloads"""
        return len(self._downloads)
