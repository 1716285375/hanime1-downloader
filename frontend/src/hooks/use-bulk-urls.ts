import { useMutation } from '@tanstack/react-query'
import { toast } from 'sonner'

const API_BASE = '/api'

// Types
export interface BulkUrlsRequest {
    urls: string[]
    resolution: string
}

export interface BulkUrlsResponse {
    task_ids: string[]
    success_count: number
    failed_count: number
    failed_urls: string[]
}

// API Function
async function bulkUrlsImport(request: BulkUrlsRequest): Promise<BulkUrlsResponse> {
    const response = await fetch(`${API_BASE}/bulk-urls`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
    })

    if (!response.ok) {
        throw new Error(`Bulk URLs import failed: ${response.statusText}`)
    }

    return response.json()
}

// Validation
export function validateVideoUrl(url: string): boolean {
    if (!url || typeof url !== 'string') return false

    const trimmed = url.trim()
    if (!trimmed) return false

    // Check if URL contains hanime1.me/watch or starts with /watch
    return trimmed.includes('hanime1.me/watch') || trimmed.startsWith('/watch')
}

export function parseUrls(text: string): string[] {
    // Split by newlines and filter valid URLs
    return text
        .split('\n')
        .map(line => line.trim())
        .filter(line => line.length > 0)
}

export function parseUrlsFromFile(file: File): Promise<string[]> {
    return new Promise((resolve, reject) => {
        const reader = new FileReader()

        reader.onload = (e) => {
            try {
                const text = e.target?.result as string
                const urls = parseUrls(text)
                resolve(urls)
            } catch (error) {
                reject(error)
            }
        }

        reader.onerror = () => reject(reader.error)
        reader.readAsText(file)
    })
}

// Hook
export function useBulkUrls() {
    return useMutation({
        mutationFn: (request: BulkUrlsRequest) => bulkUrlsImport(request),
        onSuccess: (data) => {
            if (data.failed_count > 0) {
                toast.warning(
                    `Created ${data.success_count} tasks, ${data.failed_count} failed`,
                    {
                        description: data.failed_urls.length > 0
                            ? `Failed URLs: ${data.failed_urls.slice(0, 3).join(', ')}${data.failed_urls.length > 3 ? '...' : ''}`
                            : undefined
                    }
                )
            } else {
                toast.success(`Successfully created ${data.success_count} download tasks`)
            }
        },
        onError: (error: Error) => {
            toast.error(`Bulk import failed: ${error.message}`)
        },
    })
}
