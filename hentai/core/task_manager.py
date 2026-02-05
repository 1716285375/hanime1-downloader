"""
Download task manager with queue and state management
"""
import asyncio
import json
from pathlib import Path
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime
from loguru import logger

from config import TASKS_DB, download_config


class TaskStatus(str, Enum):
    """Task status enum"""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


@dataclass
class DownloadTask:
    """Download task data structure"""
    id: str
    title: str
    page_url: str
    video_url: str
    thumbnail_url: str
    resolution: str
    status: TaskStatus
    save_dir: Path
    progress: float = 0.0
    downloaded_bytes: int = 0
    total_bytes: int = 0
    speed: float = 0.0  # MB/s
    error_message: str = ""
    created_at: str = ""
    completed_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if isinstance(self.save_dir, str):
            self.save_dir = Path(self.save_dir)
        if isinstance(self.status, str):
            self.status = TaskStatus(self.status)
            
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['save_dir'] = str(self.save_dir)
        data['status'] = self.status.value
        return data
        
    @classmethod
    def from_dict(cls, data: dict) -> 'DownloadTask':
        """Create from dictionary"""
        return cls(**data)


class TaskManager:
    """Manage download tasks with queue and persistence"""
    
    def __init__(self):
        self.tasks: Dict[str, DownloadTask] = {}
        self.queue: asyncio.Queue = asyncio.Queue()
        self._active_downloads: Set[str] = set()
        self._lock = asyncio.Lock()
        self._running = False
        self._workers: List[asyncio.Task] = []
        
    async def load_tasks(self):
        """Load tasks from database"""
        if TASKS_DB.exists():
            try:
                with open(TASKS_DB, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for task_data in data:
                        task = DownloadTask.from_dict(task_data)
                        self.tasks[task.id] = task
                        
                        # Re-queue pending tasks
                        if task.status == TaskStatus.PENDING:
                            await self.queue.put(task.id)
                            
                logger.info(f"Loaded {len(self.tasks)} tasks from database")
            except Exception as e:
                logger.error(f"Error loading tasks: {e}")
        else:
            logger.info("No existing task database found")
            
    async def save_tasks(self):
        """Save tasks to database"""
        try:
            async with self._lock:
                data = [task.to_dict() for task in self.tasks.values()]
                
            with open(TASKS_DB, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            logger.debug("Tasks saved to database")
        except Exception as e:
            logger.error(f"Error saving tasks: {e}")
            
    async def add_task(self, task: DownloadTask) -> str:
        """Add a new task"""
        async with self._lock:
            self.tasks[task.id] = task
            await self.queue.put(task.id)
            
        await self.save_tasks()
        logger.info(f"Task added: {task.id} - {task.title}")
        logger.debug(f"Queue size after add: {self.queue.qsize()}")
        return task.id
        
    async def get_task(self, task_id: str) -> Optional[DownloadTask]:
        """Get a task by ID"""
        return self.tasks.get(task_id)
        
    async def update_task(self, task_id: str, **kwargs):
        """Update task properties"""
        async with self._lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                for key, value in kwargs.items():
                    if hasattr(task, key):
                        setattr(task, key, value)
                        
        await self.save_tasks()
        
    async def delete_task(self, task_id: str) -> bool:
        """Delete a task"""
        async with self._lock:
            if task_id in self.tasks:
                del self.tasks[task_id]
                await self.save_tasks()
                logger.info(f"Task deleted: {task_id}")
                return True
        return False
        
    async def pause_task(self, task_id: str):
        """Pause a task"""
        await self.update_task(task_id, status=TaskStatus.PAUSED)
        if task_id in self._active_downloads:
            self._active_downloads.remove(task_id)
        logger.info(f"Task paused: {task_id}")
        
    async def resume_task(self, task_id: str):
        """Resume a paused task"""
        task = await self.get_task(task_id)
        if task and task.status == TaskStatus.PAUSED:
            await self.update_task(task_id, status=TaskStatus.PENDING)
            await self.queue.put(task_id)
            logger.info(f"Task resumed: {task_id}")
            
    async def cancel_task(self, task_id: str):
        """Cancel a task"""
        await self.update_task(task_id, status=TaskStatus.CANCELLED)
        if task_id in self._active_downloads:
            self._active_downloads.remove(task_id)
        logger.info(f"Task cancelled: {task_id}")
        
    async def retry_task(self, task_id: str):
        """Retry a failed task"""
        task = await self.get_task(task_id)
        if task and task.status == TaskStatus.FAILED:
            await self.update_task(
                task_id,
                status=TaskStatus.PENDING,
                progress=0.0,
                downloaded_bytes=0,
                error_message=""
            )
            await self.queue.put(task_id)
            logger.info(f"Task retrying: {task_id}")
            
    def get_all_tasks(self) -> List[DownloadTask]:
        """Get all tasks"""
        return list(self.tasks.values())
        
    def get_tasks_by_status(self, status: TaskStatus) -> List[DownloadTask]:
        """Get tasks by status"""
        return [task for task in self.tasks.values() if task.status == status]
        
    def get_statistics(self) -> Dict:
        """Get download statistics"""
        total = len(self.tasks)
        completed = len(self.get_tasks_by_status(TaskStatus.COMPLETED))
        failed = len(self.get_tasks_by_status(TaskStatus.FAILED))
        downloading = len(self._active_downloads)
        pending = self.queue.qsize()
        
        total_size = sum(task.total_bytes for task in self.tasks.values())
        downloaded_size = sum(task.downloaded_bytes for task in self.tasks.values())
        
        avg_speed = 0.0
        active_tasks = [task for task in self.tasks.values() if task.id in self._active_downloads]
        if active_tasks:
            avg_speed = sum(task.speed for task in active_tasks) / len(active_tasks)
        
        return {
            "total_tasks": total,
            "completed": completed,
            "failed": failed,
            "downloading": downloading,
            "pending": pending,
            "total_size_bytes": total_size,
            "downloaded_size_bytes": downloaded_size,
            "average_speed_mbps": avg_speed,
        }
        
    async def start_workers(self, num_workers: int = None):
        """Start download worker tasks"""
        if num_workers is None:
            num_workers = download_config.max_concurrent_downloads
            
        self._running = True
        
        for i in range(num_workers):
            worker = asyncio.create_task(self._worker(i))
            self._workers.append(worker)
            
        logger.info(f"Started {num_workers} download workers")
        
    async def stop_workers(self):
        """Stop all workers"""
        self._running = False
        
        # Cancel all workers
        for worker in self._workers:
            worker.cancel()
            
        # Wait for workers to finish
        await asyncio.gather(*self._workers, return_exceptions=True)
        
        self._workers.clear()
        logger.info("All workers stopped")
        
    async def _worker(self, worker_id: int):
        """Worker coroutine to process download queue"""
        from core.downloader import AsyncDownloader
        from core.scraper import VideoScraper
        
        logger.debug(f"Worker {worker_id} ENTRY POINT")
        logger.info(f"Worker {worker_id} started")
        logger.debug(f"Worker {worker_id} creating AsyncDownloader instance...")
        
        # Create downloader without context manager to avoid blocking
        downloader = AsyncDownloader()
        logger.debug(f"Worker {worker_id} calling downloader.start()...")
        await downloader.start()
        logger.debug(f"Worker {worker_id} AsyncDownloader ready, entering main loop")
        
        try:
            loop_count = 0
            while self._running:
                try:
                    # Log queue status every 30 seconds
                    loop_count += 1
                    if loop_count % 30 == 0:
                        logger.debug(f"Worker {worker_id} alive - Queue size: {self.queue.qsize()}, Active downloads: {len(self._active_downloads)}")
                    
                    # Get task from queue with timeout
                    try:
                        task_id = await asyncio.wait_for(self.queue.get(), timeout=1.0)
                        logger.debug(f"Worker {worker_id} got task from queue: {task_id}")
                    except asyncio.TimeoutError:
                        continue
                        
                    task = await self.get_task(task_id)
                    
                    if not task:
                        logger.warning(f"Task {task_id} not found")
                        continue
                        
                    # Skip if task is not pending
                    if task.status != TaskStatus.PENDING:
                        continue
                        
                    # Check concurrent limit
                    while len(self._active_downloads) >= download_config.max_concurrent_downloads:
                        await asyncio.sleep(1)
                        
                    # Mark as downloading
                    self._active_downloads.add(task_id)
                    await self.update_task(task_id, status=TaskStatus.DOWNLOADING)
                    
                    logger.info(f"Worker {worker_id} processing: {task.title}")
                    
                    # Create save directory
                    task.save_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Download thumbnail
                    if task.thumbnail_url:
                        thumbnail_path = task.save_dir / "thumbnail.jpg"
                        await downloader.download_image(task.thumbnail_url, thumbnail_path)
                        
                    # Download video
                    video_filename = f"{task.title}_{task.resolution}.mp4"
                    video_path = task.save_dir / video_filename
                    
                    def progress_callback(progress):
                        """Update task progress"""
                        asyncio.create_task(self.update_task(
                            task_id,
                            progress=progress.percentage,
                            downloaded_bytes=progress.downloaded,
                            total_bytes=progress.total_size,
                            speed=progress.speed_mbps
                        ))
                        
                    success = await downloader.download_file(
                        task.video_url,
                        video_path,
                        progress_callback=progress_callback,
                        task_id=task_id
                    )
                    
                    if success:
                        await self.update_task(
                            task_id,
                            status=TaskStatus.COMPLETED,
                            completed_at=datetime.now().isoformat(),
                            progress=100.0
                        )
                        logger.success(f"Task completed: {task.title}")
                        
                        # Broadcast completion
                        from api.websocket import manager as ws_manager
                        await ws_manager.broadcast_task_update(
                            task_id, "completed", f"Download completed: {task.title}"
                        )
                    else:
                        await self.update_task(
                            task_id,
                            status=TaskStatus.FAILED,
                            error_message="Download failed"
                        )
                        logger.error(f"Task failed: {task.title}")
                        
                        # Broadcast failure
                        from api.websocket import manager as ws_manager
                        await ws_manager.broadcast_task_update(
                            task_id, "failed", f"Download failed: {task.title}"
                        )
                        
                    # Remove from active downloads
                    self._active_downloads.discard(task_id)
                    self.queue.task_done()
                    
                except asyncio.CancelledError:
                    logger.info(f"Worker {worker_id} cancelled")
                    break
                except Exception as e:
                    logger.error(f"Worker {worker_id} error: {e}")
                    if task_id:
                        self._active_downloads.discard(task_id)
                    await asyncio.sleep(5)
        finally:
            # Clean up downloader
            logger.debug(f"Worker {worker_id} shutting down, closing downloader...")
            await downloader.close()
            logger.info(f"Worker {worker_id} stopped")
