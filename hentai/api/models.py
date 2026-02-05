"""
API models using Pydantic
"""
from typing import Optional, Dict, List
from pydantic import BaseModel, Field


class VideoInfoResponse(BaseModel):
    """Video information response"""
    title: str
    url: str
    thumbnail_url: str
    resolutions: Dict[str, str] = Field(default_factory=dict)


class DownloadRequest(BaseModel):
    """Request to download a video"""
    page_url: str = Field(..., description="Video page URL")
    resolution: Optional[str] = Field("1080p", description="Video resolution (360p, 720p, 1080p)")
    custom_title: Optional[str] = Field(None, description="Custom title for the video")
    # Optional: if provided, skip scraping
    video_url: Optional[str] = Field(None, description="Direct video URL (avoids re-scraping)")
    thumbnail_url: Optional[str] = Field(None, description="Thumbnail URL")
    title: Optional[str] = Field(None, description="Video title")


class TaskResponse(BaseModel):
    """Task information response"""
    id: str
    title: str
    page_url: str
    video_url: str
    thumbnail_url: str
    resolution: str
    status: str
    progress: float
    downloaded_bytes: int
    total_bytes: int
    speed: float
    error_message: str
    created_at: str
    completed_at: str
    save_dir: str


class ProgressUpdate(BaseModel):
    """Real-time progress update"""
    task_id: str
    progress: float
    downloaded_bytes: int
    total_bytes: int
    speed: float
    status: str


class StatisticsResponse(BaseModel):
    """Download statistics"""
    total_tasks: int
    completed: int
    failed: int
    downloading: int
    pending: int
    total_size_bytes: int
    downloaded_size_bytes: int
    average_speed_mbps: float


class SearchRequest(BaseModel):
    """Search videos request"""
    search_url: str = Field(..., description="Search or browse page URL")


class SearchResult(BaseModel):
    """Search results"""
    videos: List[VideoInfoResponse]
    total: int


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None
