"""
WebSocket manager for real-time updates
"""
import asyncio
import json
from typing import Set
from fastapi import WebSocket
from loguru import logger


class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()
        
    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        async with self._lock:
            self.active_connections.add(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
        
    async def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        async with self._lock:
            self.active_connections.discard(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
        
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to a specific client"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            await self.disconnect(websocket)
            
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        if not self.active_connections:
            return
            
        async with self._lock:
            connections = list(self.active_connections)
            
        # Send to all connections
        disconnected = []
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Error broadcasting to client: {e}")
                disconnected.append(connection)
                
        # Clean up disconnected clients
        if disconnected:
            async with self._lock:
                for conn in disconnected:
                    self.active_connections.discard(conn)
                    
    async def broadcast_progress(self, task_id: str, progress: float, downloaded: int, total: int, speed: float, status: str):
        """Broadcast download progress update"""
        await self.broadcast({
            "type": "progress",
            "data": {
                "task_id": task_id,
                "progress": progress,
                "downloaded_bytes": downloaded,
                "total_bytes": total,
                "speed": speed,
                "status": status
            }
        })
        
    async def broadcast_task_update(self, task_id: str, status: str, message: str = ""):
        """Broadcast task status update"""
        await self.broadcast({
            "type": "task_update",
            "data": {
                "task_id": task_id,
                "status": status,
                "message": message
            }
        })
        
    async def broadcast_statistics(self, stats: dict):
        """Broadcast statistics update"""
        await self.broadcast({
            "type": "statistics",
            "data": stats
        })
        
    @property
    def connection_count(self) -> int:
        """Get number of active connections"""
        return len(self.active_connections)


# Global connection manager instance
manager = ConnectionManager()
