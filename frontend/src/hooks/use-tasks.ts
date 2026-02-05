import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { taskApi } from '@/lib/api'
import { useTaskStore } from '@/store/task-store'
import type { DownloadRequest } from '@/types/api'

export function useTasks() {
    const setTasks = useTaskStore((state) => state.setTasks)

    return useQuery({
        queryKey: ['tasks'],
        queryFn: async () => {
            const tasks = await taskApi.list()
            setTasks(tasks)
            return tasks
        },
        refetchInterval: 5000, // Fallback polling every 5 seconds
    })
}

export function useCreateDownload() {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: (request: DownloadRequest) => taskApi.create(request),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['tasks'] })
        },
    })
}

export function useCancelTask() {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: (taskId: string) => taskApi.cancel(taskId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['tasks'] })
        },
    })
}

export function useDeleteTask() {
    const queryClient = useQueryClient()
    const removeTask = useTaskStore((state) => state.removeTask)

    return useMutation({
        mutationFn: (taskId: string) => taskApi.delete(taskId),
        onSuccess: (_, taskId) => {
            removeTask(taskId)
            queryClient.invalidateQueries({ queryKey: ['tasks'] })
        },
    })
}
