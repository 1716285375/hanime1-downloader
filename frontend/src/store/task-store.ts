import { create } from 'zustand'
import type { DownloadTask, ProgressMessage } from '@/types/api'

interface TaskStore {
    tasks: DownloadTask[]
    setTasks: (tasks: DownloadTask[]) => void
    updateTask: (taskId: string, updates: Partial<DownloadTask>) => void
    removeTask: (taskId: string) => void
    updateProgress: (progress: ProgressMessage) => void
}

export const useTaskStore = create<TaskStore>((set) => ({
    tasks: [],

    setTasks: (tasks) => set({ tasks }),

    updateTask: (taskId, updates) => set((state) => ({
        tasks: state.tasks.map((task) =>
            task.id === taskId ? { ...task, ...updates } : task
        ),
    })),

    removeTask: (taskId) => set((state) => ({
        tasks: state.tasks.filter((task) => task.id !== taskId),
    })),

    updateProgress: (progress) => set((state) => ({
        tasks: state.tasks.map((task) =>
            task.id === progress.task_id
                ? {
                    ...task,
                    progress: progress.progress,
                    downloaded_bytes: progress.downloaded,
                    total_bytes: progress.total,
                    speed: progress.speed,
                    status: progress.status as any,
                }
                : task
        ),
    })),
}))
