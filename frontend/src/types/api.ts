export interface VideoInfo {
    title: string
    url: string
    thumbnail_url: string
    resolutions: Record<string, string>
}

export interface DownloadTask {
    id: string
    title: string
    page_url: string
    video_url: string
    thumbnail_url: string
    resolution: string
    status: TaskStatus
    progress: number
    downloaded_bytes: number
    total_bytes: number
    speed: number
    error_message: string
    created_at: string
    completed_at: string
    save_dir: string
}

export type TaskStatus = 'pending' | 'downloading' | 'completed' | 'failed' | 'cancelled'

export interface DownloadRequest {
    page_url: string
    resolution: string
    video_url?: string
    thumbnail_url?: string
    title?: string
}

export interface WebSocketMessage {
    type: 'task_update' | 'progress' | 'statistics'
    data: any
}

export interface ProgressMessage {
    task_id: string
    progress: number
    downloaded: number
    total: number
    speed: number
    status: string
}

export interface TaskUpdateMessage {
    task_id: string
    status: string
    message: string
}
