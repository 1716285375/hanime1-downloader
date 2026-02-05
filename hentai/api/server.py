"""
FastAPI server for hanime1-downloader WebUI
"""
import asyncio
import uuid
import re
from pathlib import Path
from typing import List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from config import webui_config, VIDEO_DIR
from core import VideoScraper, SearchScraper, TaskManager, DownloadTask, TaskStatus
from api.models import (
    VideoInfoResponse,
    DownloadRequest,
    TaskResponse,
    StatisticsResponse,
    SearchRequest,
    SearchResult,
    ErrorResponse,
    PaginatedSearchRequest,
    PaginatedSearchResult,
    BatchDownloadRequest,
    BatchDownloadResponse,
    BulkUrlsRequest,
    BulkUrlsResponse
)
from api.websocket import manager


# Create FastAPI app
app = FastAPI(
    title="Hanime1 Downloader API",
    description="Async video downloader with WebUI",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=webui_config.allow_origins,
    allow_credentials=webui_config.allow_credentials,
    allow_methods=webui_config.allow_methods,
    allow_headers=webui_config.allow_headers,
)

# Global task manager instance
task_manager: TaskManager = None


@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    global task_manager
    
    logger.info("Starting Hanime1 Downloader API...")
    
    # Initialize task manager
    task_manager = TaskManager()
    await task_manager.load_tasks()
    
    # Start worker tasks
    await task_manager.start_workers()
    
    # Start statistics broadcaster
    asyncio.create_task(statistics_broadcaster())
    
    logger.success("API initialized successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down API...")
    
    if task_manager:
        await task_manager.stop_workers()
        await task_manager.save_tasks()
        
    logger.info("API shutdown complete")


async def statistics_broadcaster():
    """Broadcast statistics every 2 seconds"""
    while True:
        try:
            if task_manager and manager.connection_count > 0:
                stats = task_manager.get_statistics()
                await manager.broadcast_statistics(stats)
            await asyncio.sleep(2)
        except Exception as e:
            logger.error(f"Error broadcasting statistics: {e}")
            await asyncio.sleep(5)


# WebSocket endpoint
@app.websocket("/api/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket connection for real-time updates"""
    await manager.connect(websocket)
    
    try:
        while True:
            # Keep connection alive and handle client messages
            data = await websocket.receive_text()
            
            # Echo for heartbeat
            if data == "ping":
                await websocket.send_text("pong")
                
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await manager.disconnect(websocket)


# API Routes

# Mount static files (Frontend)
# In production, serve from ../frontend/dist
# In development, this might not be used if using Vite proxy
# Static file mounting moved to the end of file to prevent shadowing API routes


# Mount thumbnails directory
THUMBNAILS_DIR = VIDEO_DIR.parent / "database" / "thumbnails"
THUMBNAILS_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/api/thumbnails", StaticFiles(directory=str(THUMBNAILS_DIR)), name="thumbnails")


@app.get("/api/video-info")
async def get_video_info(url: str) -> VideoInfoResponse:
    """
    Get video information from URL
    
    Args:
        url: Video page URL
        
    Returns:
        Video information including available resolutions
    """
    try:
        async with VideoScraper() as scraper:
            # Get video metadata
            metadata = await scraper.get_video_url(url)
            
            if not metadata:
                raise HTTPException(status_code=404, detail="Video not found or could not be scraped")
                
            # Get available resolutions
            resolutions = await scraper.get_available_resolutions(url)
            
            # If no resolutions found, use the one from metadata
            if not resolutions and metadata.video_url:
                resolutions[metadata.resolution] = metadata.video_url
                
            return VideoInfoResponse(
                title=metadata.title,
                url=url,
                thumbnail_url=metadata.thumbnail_url,
                resolutions=resolutions
            )
            
    except Exception as e:
        logger.error(f"Error getting video info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/download")
async def create_download(request: DownloadRequest) -> TaskResponse:
    """
    Create a new download task
    
    Args:
        request: Download request with URL and resolution
        
    Returns:
        Created task information
    """
    try:
        # Only scrape if video_url not provided (avoid redundant scraping)
        if request.video_url:
            # Use provided information (from frontend)
            video_url = request.video_url
            thumbnail_url = request.thumbnail_url or ""
            title = request.title or request.custom_title or "Unknown"
            logger.info(f"Using provided video URL, skipping scrape for {title}")
        else:
            # Get video information via scraping
            async with VideoScraper() as scraper:
                metadata = await scraper.get_video_url(request.page_url, request.resolution)
                
                if not metadata:
                    raise HTTPException(status_code=404, detail="Could not extract video information")
                    
            video_url = metadata.video_url
            thumbnail_url = metadata.thumbnail_url
            title = request.custom_title or metadata.title
                
        # Generate task ID
        task_id = str(uuid.uuid4())
        
        # Clean title
        title = re.sub(r'[<>\\.:~@#$%^&_\-()"/\\|?*]', '', title).strip()
        
        # Create save directory
        save_dir = VIDEO_DIR / title
        
        # Create download task
        task = DownloadTask(
            id=task_id,
            title=title,
            page_url=request.page_url,
            video_url=video_url,
            thumbnail_url=thumbnail_url,
            resolution=request.resolution,
            status=TaskStatus.PENDING,
            save_dir=save_dir
        )
        
        # Add to task manager
        await task_manager.add_task(task)
        
        # Broadcast task creation
        await manager.broadcast_task_update(task_id, "pending", f"Task created: {title}")
        
        logger.info(f"Download task created: {task_id} - {title}")
        
        return TaskResponse(**task.to_dict())
        
    except Exception as e:
        logger.error(f"Error creating download: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tasks")
async def get_all_tasks() -> List[TaskResponse]:
    """Get all download tasks"""
    tasks = task_manager.get_all_tasks()
    return [TaskResponse(**task.to_dict()) for task in tasks]


@app.get("/api/tasks/{task_id}")
async def get_task(task_id: str) -> TaskResponse:
    """Get a specific task by ID"""
    task = await task_manager.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    return TaskResponse(**task.to_dict())


@app.post("/api/tasks/{task_id}/pause")
async def pause_task(task_id: str):
    """Pause a download task"""
    task = await task_manager.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    await task_manager.pause_task(task_id)
    await manager.broadcast_task_update(task_id, "paused", "Task paused")
    
    return {"message": "Task paused"}


@app.post("/api/tasks/{task_id}/resume")
async def resume_task(task_id: str):
    """Resume a paused task"""
    task = await task_manager.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    await task_manager.resume_task(task_id)
    await manager.broadcast_task_update(task_id, "pending", "Task resumed")
    
    return {"message": "Task resumed"}


@app.post("/api/tasks/{task_id}/cancel")
async def cancel_task(task_id: str):
    """Cancel a download task"""
    task = await task_manager.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    await task_manager.cancel_task(task_id)
    await manager.broadcast_task_update(task_id, "cancelled", "Task cancelled")
    
    return {"message": "Task cancelled"}


@app.post("/api/tasks/{task_id}/retry")
async def retry_task(task_id: str):
    """Retry a failed task"""
    task = await task_manager.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    await task_manager.retry_task(task_id)
    await manager.broadcast_task_update(task_id, "pending", "Task retrying")
    
    return {"message": "Task retrying"}


@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: str):
    """Delete a task"""
    success = await task_manager.delete_task(task_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
        
    await manager.broadcast_task_update(task_id, "deleted", "Task deleted")
    
    return {"message": "Task deleted"}


@app.get("/api/statistics")
async def get_statistics() -> StatisticsResponse:
    """Get download statistics"""
    stats = task_manager.get_statistics()
    return StatisticsResponse(**stats)


@app.post("/api/search")
async def search_videos(request: SearchRequest) -> SearchResult:
    """
    Search for videos on a browse/search page
    
    Args:
        request: Search request with URL
        
    Returns:
        List of found videos
    """
    try:
        async with SearchScraper() as scraper:
            videos = await scraper.search_videos(request.search_url)
            
            results = [
                VideoInfoResponse(
                    title=video.title,
                    url=video.url,
                    thumbnail_url=video.thumbnail_url,
                    resolutions=video.resolutions
                )
                for video in videos
            ]
            
            return SearchResult(
                videos=results,
                total=len(results)
            )
            
    except Exception as e:
        logger.exception(f"Error searching videos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/proxy/image")
async def proxy_image(url: str):
    """
    Proxy external images to bypass CORS and referrer restrictions
    
    Args:
        url: URL of the image to proxy
        
    Returns:
        Image content with proper headers
    """
    try:
        import httpx
        from fastapi.responses import Response
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Referer': 'https://hanime1.me/'
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                return Response(
                    content=response.content,
                    media_type=response.headers.get('content-type', 'image/jpeg'),
                    headers={
                        'Cache-Control': 'public, max-age=86400',  # Cache for 1 day
                    }
                )
            else:
                raise HTTPException(status_code=response.status_code, detail="Failed to fetch image")
                
    except Exception as e:
        logger.error(f"Error proxying image: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/search/paginated")
async def search_videos_paginated(request: PaginatedSearchRequest) -> PaginatedSearchResult:
    """
    Search for videos across multiple pages
    
    Args:
        request: Paginated search request with URL and page range
        
    Returns:
        List of found videos and pagination info
    """
    try:
        async with SearchScraper() as scraper:
            videos, total_pages = await scraper.search_videos_paginated(
                request.search_url,
                request.start_page,
                request.end_page
            )
            
            results = [
                VideoInfoResponse(
                    title=video.title,
                    url=video.url,
                    thumbnail_url=video.thumbnail_url,
                    resolutions=video.resolutions
                )
                for video in videos
            ]
            
            return PaginatedSearchResult(
                videos=results,
                total_pages=total_pages,
                total_videos=len(results)
            )
            
    except Exception as e:
        logger.error(f"Error in paginated search: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/batch-download")
async def batch_download(request: BatchDownloadRequest) -> BatchDownloadResponse:
    """
    Create multiple download tasks at once
    
    Args:
        request: Batch download request with list of videos
        
    Returns:
        Batch download response with task IDs and success/failure counts
    """
    task_ids = []
    failed_urls = []
    success_count = 0
    failed_count = 0
    
    for video_request in request.videos:
        try:
            # Create download task (reusing existing logic)
            task_response = await create_download(video_request)
            task_ids.append(task_response.id)
            success_count += 1
            
        except Exception as e:
            logger.error(f"Error creating batch download task for {video_request.page_url}: {e}")
            failed_urls.append(video_request.page_url)
            failed_count += 1
    
    logger.info(f"Batch download: {success_count} succeeded, {failed_count} failed")
    
    return BatchDownloadResponse(
        task_ids=task_ids,
        success_count=success_count,
        failed_count=failed_count,
        failed_urls=failed_urls
    )


@app.post("/api/bulk-urls")
async def bulk_urls_import(request: BulkUrlsRequest) -> BulkUrlsResponse:
    """
    Import and download from a list of video URLs
    
    Args:
        request: Bulk URLs request with list of video URLs and resolution
        
    Returns:
        Bulk URLs response with task IDs and success/failure counts
    """
    task_ids = []
    failed_urls = []
    success_count = 0
    failed_count = 0
    
    for url in request.urls:
        try:
            # Validate URL format
            if 'hanime1.me/watch' not in url and not url.startswith('/watch'):
                logger.warning(f"Invalid video URL: {url}")
                failed_urls.append(url)
                failed_count += 1
                continue
            
            # Create download request
            download_request = DownloadRequest(
                page_url=url,
                resolution=request.resolution
            )
            
            # Create download task
            task_response = await create_download(download_request)
            task_ids.append(task_response.id)
            success_count += 1
            
        except Exception as e:
            logger.error(f"Error creating task for URL {url}: {e}")
            failed_urls.append(url)
            failed_count += 1
    
    logger.info(f"Bulk URLs import: {success_count} succeeded, {failed_count} failed")
    
    return BulkUrlsResponse(
        task_ids=task_ids,
        success_count=success_count,
        failed_count=failed_count,
        failed_urls=failed_urls
    )




# Mount static files (Frontend)
# In production, serve from ../frontend/dist
frontend_dir = Path(__file__).parent.parent.parent / "frontend" / "dist"

if frontend_dir.exists():
    # Mount assets directory (built by Vite)
    # Important: Mount assets first so they are not caught by the catch-all route
    if (frontend_dir / "assets").exists():
        app.mount("/assets", StaticFiles(directory=str(frontend_dir / "assets")), name="assets")
        logger.info(f"Serving frontend assets from {frontend_dir / 'assets'}")
    
    # Serve index.html for root and all client-side routes
    # This must be the LAST route defined to avoid shadowing API routes
    @app.get("/{full_path:path}")
    async def serve_app(full_path: str):
        # Explicit check to prevent recursing or shadowing API if something went wrong
        if full_path.startswith("api/") or full_path.startswith("ws"):
            raise HTTPException(status_code=404, detail="Not Found")
            
        # Check if the file exists in frontend_dir (e.g. logo.png, favicon.ico)
        possible_file = frontend_dir / full_path
        if possible_file is not None and possible_file.is_file():
            return FileResponse(str(possible_file))

        # Serve index.html for all other routes (SPA fallback)
        return FileResponse(str(frontend_dir / "index.html"))
    
    logger.info(f"Serving frontend from {frontend_dir}")
else:
    logger.warning(f"Frontend directory not found at {frontend_dir}")
    @app.get("/")
    async def root():
        return {"message": "Frontend not found. Please run 'npm run build' in the frontend directory."}
