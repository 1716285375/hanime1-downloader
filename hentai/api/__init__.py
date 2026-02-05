"""
API package for hanime1-downloader WebUI
"""
from .models import (
    VideoInfoResponse,
    DownloadRequest,
    TaskResponse,
    ProgressUpdate,
    StatisticsResponse,
    SearchRequest,
    SearchResult,
    ErrorResponse
)
from .websocket import manager, ConnectionManager
from .server import app

__all__ = [
    'VideoInfoResponse',
    'DownloadRequest',
    'TaskResponse',
    'ProgressUpdate',
    'StatisticsResponse',
    'SearchRequest',
    'SearchResult',
    'ErrorResponse',
    'manager',
    'ConnectionManager',
    'app',
]
