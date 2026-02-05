import { useEffect, useRef } from 'react'
import { useTaskStore } from '@/store/task-store'
import type { ProgressMessage } from '@/types/api'

export function useWebSocket() {
    const updateProgress = useTaskStore((state) => state.updateProgress)
    const wsRef = useRef<WebSocket | null>(null)

    useEffect(() => {
        // Only run in browser environment
        if (typeof window === 'undefined') return

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
        const host = window.location.host
        const wsUrl = `${protocol}//${host}/api/ws`

        const connect = () => {
            console.log('Connecting to WebSocket:', wsUrl)
            const ws = new WebSocket(wsUrl)
            wsRef.current = ws

            ws.onopen = () => {
                console.log('WebSocket connected')
            }

            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data)
                    // Assume the message is a ProgressMessage or contains one
                    // Adjust this based on actual backend format
                    if (data.task_id && typeof data.progress === 'number') {
                        updateProgress(data as ProgressMessage)
                    }
                } catch (error) {
                    console.error('Failed to parse WebSocket message:', error)
                }
            }

            ws.onclose = () => {
                console.log('WebSocket disconnected')
                // Optional: Reconnect logic
                setTimeout(connect, 3000)
            }

            ws.onerror = (error) => {
                console.error('WebSocket error:', error)
            }
        }

        connect()

        return () => {
            if (wsRef.current) {
                wsRef.current.close()
            }
        }
    }, [updateProgress])
}
