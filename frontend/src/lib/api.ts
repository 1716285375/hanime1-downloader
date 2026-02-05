import axios from 'axios'
import type { VideoInfo, DownloadTask, DownloadRequest } from '@/types/api'

const api = axios.create({
    baseURL: '/api',
    headers: {
        'Content-Type': 'application/json',
    },
})

export const videoApi = {
    getInfo: async (url: string): Promise<VideoInfo> => {
        const { data } = await api.get('/video-info', { params: { url } })
        return data
    },
}

export const taskApi = {
    list: async (): Promise<DownloadTask[]> => {
        const { data } = await api.get('/tasks')
        return data
    },

    create: async (request: DownloadRequest): Promise<DownloadTask> => {
        const { data } = await api.post('/download', request)
        return data
    },

    cancel: async (id: string): Promise<void> => {
        await api.post(`/tasks/${id}/cancel`)
    },

    delete: async (id: string): Promise<void> => {
        await api.delete(`/tasks/${id}`)
    },
}
