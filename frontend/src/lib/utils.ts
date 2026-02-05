import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs))
}

export function formatBytes(bytes: number): string {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`
}

export function formatSpeed(mbps: number): string {
    return `${mbps.toFixed(2)} MB/s`
}

export function formatDuration(seconds: number): string {
    if (seconds < 60) return `${Math.floor(seconds)}s`
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${Math.floor(seconds % 60)}s`
    return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`
}

export function estimateTimeRemaining(downloaded: number, total: number, speed: number): string {
    if (speed === 0 || downloaded === 0) return 'Calculating...'
    const remaining = total - downloaded
    const secondsRemaining = remaining / (speed * 1024 * 1024) // Convert MB/s to bytes/s
    return formatDuration(secondsRemaining)
}
