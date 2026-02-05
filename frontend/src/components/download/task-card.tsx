import {
    AlertCircle,
    CheckCircle2,
    Clock,
    Download,
    Trash2,
    XCircle,
} from 'lucide-react'
import {
    Card,
} from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { cn, formatBytes, formatSpeed, estimateTimeRemaining } from '@/lib/utils'
import { useCancelTask, useDeleteTask } from '@/hooks/use-tasks'
import type { DownloadTask, TaskStatus } from '@/types/api'
import { toast } from 'sonner'

interface TaskCardProps {
    task: DownloadTask
}

export function TaskCard({ task }: TaskCardProps) {
    const cancelTask = useCancelTask()
    const deleteTask = useDeleteTask()

    const isActive = task.status === 'downloading'
    const isCompleted = task.status === 'completed'
    const isFailed = task.status === 'failed'

    const getStatusColor = (status: TaskStatus) => {
        switch (status) {
            case 'downloading':
                return 'text-primary'
            case 'completed':
                return 'text-green-500'
            case 'failed':
                return 'text-destructive'
            case 'pending':
                return 'text-orange-500'
            default:
                return 'text-muted-foreground'
        }
    }

    const getStatusIcon = (status: TaskStatus) => {
        switch (status) {
            case 'downloading':
                return <Download className="h-4 w-4 animate-bounce" />
            case 'completed':
                return <CheckCircle2 className="h-4 w-4" />
            case 'failed':
                return <AlertCircle className="h-4 w-4" />
            case 'pending':
                return <Clock className="h-4 w-4" />
            case 'cancelled':
                return <XCircle className="h-4 w-4" />
            default:
                return <AlertCircle className="h-4 w-4" />
        }
    }

    const handleCancel = () => {
        cancelTask.mutate(task.id, {
            onSuccess: () => toast.success('Task cancelled'),
            onError: () => toast.error('Failed to cancel task')
        })
    }

    const handleDelete = () => {
        deleteTask.mutate(task.id, {
            onSuccess: () => toast.success('Task deleted'),
            onError: () => toast.error('Failed to delete task')
        })
    }

    // Proxy thumbnail
    const proxyImageUrl = task.thumbnail_url
        ? `/api/proxy/image?url=${encodeURIComponent(task.thumbnail_url)}`
        : ''

    return (
        <Card className="overflow-hidden transition-all hover:border-primary/50">
            <div className="flex flex-col sm:flex-row">
                <div className="relative h-32 w-full shrink-0 overflow-hidden bg-muted sm:h-auto sm:w-48">
                    {proxyImageUrl ? (
                        <img
                            src={proxyImageUrl}
                            alt={task.title}
                            className="h-full w-full object-cover transition-transform hover:scale-105"
                        />
                    ) : (
                        <div className="flex h-full w-full items-center justify-center">
                            <Download className="h-8 w-8 text-muted-foreground/50" />
                        </div>
                    )}
                    <div className="absolute left-2 top-2 rounded-md bg-black/60 px-2 py-0.5 text-xs font-medium text-white backdrop-blur-sm">
                        {task.resolution}
                    </div>
                </div>

                <div className="flex min-w-0 flex-1 flex-col justify-between p-4">
                    <div className="flex items-start justify-between gap-4">
                        <div className="space-y-1 truncate">
                            <h3 className="truncate font-medium leading-none" title={task.title}>
                                {task.title}
                            </h3>
                            <p className={cn("flex items-center gap-2 text-xs", getStatusColor(task.status))}>
                                {getStatusIcon(task.status)}
                                <span className="capitalize">{task.status}</span>
                                {isFailed && task.error_message && (
                                    <span className="text-muted-foreground">- {task.error_message}</span>
                                )}
                            </p>
                        </div>

                        <div className="flex items-center gap-1">
                            {isActive && (
                                <Button variant="ghost" size="icon" className="h-8 w-8" onClick={handleCancel} title="Cancel">
                                    <XCircle className="h-4 w-4" />
                                </Button>
                            )}
                            {!isActive && (
                                <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive" onClick={handleDelete} title="Delete">
                                    <Trash2 className="h-4 w-4" />
                                </Button>
                            )}
                        </div>
                    </div>

                    <div className="mt-4 space-y-2">
                        <div className="flex items-center justify-between text-xs text-muted-foreground">
                            <span>{formatBytes(task.downloaded_bytes)} / {formatBytes(task.total_bytes)}</span>
                            <span>{Math.round(task.progress)}%</span>
                        </div>

                        <Progress value={task.progress} className={cn("h-1.5",
                            isFailed ? "bg-red-100" : "",
                            isCompleted ? "bg-green-100" : ""
                        )} />

                        <div className="flex items-center justify-between text-xs text-muted-foreground h-4">
                            {isActive && (
                                <>
                                    <span>{formatSpeed(task.speed)}</span>
                                    <span>ETA: {estimateTimeRemaining(task.downloaded_bytes, task.total_bytes, task.speed)}</span>
                                </>
                            )}
                            {isCompleted && (
                                <span className="text-green-600">Completed at {new Date(task.completed_at).toLocaleString()}</span>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </Card>
    )
}
