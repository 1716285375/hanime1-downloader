import { useMutation } from '@tanstack/react-query'
import { toast } from 'sonner'

const API_BASE = '/api'

// Types
export interface VideoInfo {
    title: string
    url: string
    thumbnail_url: string
    resolutions: Record<string, string>
}

export interface SearchResult {
    videos: VideoInfo[]
    total: number
}

export interface PaginatedSearchResult {
    videos: VideoInfo[]
    total_pages: number
    total_videos: number
}

export interface BatchDownloadRequest {
    videos: Array<{
        page_url: string
        resolution: string
        title?: string
    }>
}

export interface BatchDownloadResponse {
    task_ids: string[]
    success_count: number
    failed_count: number
    failed_urls: string[]
}

// API Functions
async function searchVideos(url: string): Promise<SearchResult> {
    const response = await fetch(`${API_BASE}/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ search_url: url }),
    })

    if (!response.ok) {
        throw new Error(`Search failed: ${response.statusText}`)
    }

    return response.json()
}

async function searchVideosPaginated(
    url: string,
    startPage: number,
    endPage?: number
): Promise<PaginatedSearchResult> {
    const response = await fetch(`${API_BASE}/search/paginated`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            search_url: url,
            start_page: startPage,
            end_page: endPage,
        }),
    })

    if (!response.ok) {
        throw new Error(`Paginated search failed: ${response.statusText}`)
    }

    return response.json()
}

async function batchDownload(request: BatchDownloadRequest): Promise<BatchDownloadResponse> {
    const response = await fetch(`${API_BASE}/batch-download`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
    })

    if (!response.ok) {
        throw new Error(`Batch download failed: ${response.statusText}`)
    }

    return response.json()
}

// Hooks
export function useSearchVideos() {
    return useMutation({
        mutationFn: (url: string) => searchVideos(url),
        onSuccess: (data) => {
            toast.success(`Found ${data.total} videos`)
        },
        onError: (error: Error) => {
            toast.error(`Search failed: ${error.message}`)
        },
    })
}

export function usePaginatedSearch() {
    return useMutation({
        mutationFn: ({
            url,
            startPage,
            endPage,
        }: {
            url: string
            startPage: number
            endPage?: number
        }) => searchVideosPaginated(url, startPage, endPage),
        onSuccess: (data) => {
            toast.success(
                `Found ${data.total_videos} videos across ${data.total_pages} pages`
            )
        },
        onError: (error: Error) => {
            toast.error(`Paginated search failed: ${error.message}`)
        },
    })
}

export function useBatchDownload() {
    return useMutation({
        mutationFn: (request: BatchDownloadRequest) => batchDownload(request),
        onSuccess: (data) => {
            if (data.failed_count > 0) {
                toast.warning(
                    `Created ${data.success_count} tasks, ${data.failed_count} failed`
                )
            } else {
                toast.success(`Created ${data.success_count} download tasks`)
            }
        },
        onError: (error: Error) => {
            toast.error(`Batch download failed: ${error.message}`)
        },
    })
}
