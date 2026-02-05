import { useTasks } from '@/hooks/use-tasks'
import { useLanguage } from '@/contexts/language-context'
import { useWebSocket } from '@/hooks/use-websocket'
import { TaskCard } from './task-card'
import { AlertCircle, Inbox } from 'lucide-react'
import { Button } from '@/components/ui/button'

export function TaskList() {
    const { t } = useLanguage()
    // Initialize WebSocket connection
    useWebSocket()

    const { data: tasks, isLoading, isError, refetch } = useTasks()

    if (isLoading && !tasks) {
        return (
            <div className="flex h-32 items-center justify-center rounded-lg border border-dashed text-muted-foreground">
                {t('common.loading')}
            </div>
        )
    }

    if (isError) {
        return (
            <div className="flex h-32 flex-col items-center justify-center gap-2 rounded-lg border border-destructive/20 bg-destructive/5 text-destructive">
                <div className="flex items-center gap-2">
                    <AlertCircle className="h-5 w-5" />
                    <span>{t('common.error')}</span>
                </div>
                <Button variant="outline" size="sm" onClick={() => refetch()}>{t('common.retry')}</Button>
            </div>
        )
    }

    if (!tasks || tasks.length === 0) {
        return (
            <div className="flex h-64 flex-col items-center justify-center gap-2 rounded-lg border border-dashed text-muted-foreground">
                <Inbox className="h-10 w-10 opacity-20" />
                <p>{t('tasks.noDownloads')}</p>
            </div>
        )
    }

    // Sort tasks: downloading first, then by creation date (newest first)
    const sortedTasks = [...tasks].sort((a, b) => {
        // Priority: Downloading > Pending > Others
        const getScore = (status: string) => {
            if (status === 'downloading') return 2;
            if (status === 'pending') return 1;
            return 0;
        }

        const scoreA = getScore(a.status);
        const scoreB = getScore(b.status);

        if (scoreA !== scoreB) return scoreB - scoreA;

        // Determine creation time safely
        const timeA = new Date(a.created_at).getTime();
        const timeB = new Date(b.created_at).getTime();
        return timeB - timeA;
    });

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold tracking-tight">{t('tasks.title')}</h2>
                <span className="text-sm text-muted-foreground">
                    {t('tasks.count', { count: tasks.length })}
                </span>
            </div>
            <div className="grid gap-4">
                {sortedTasks.map((task) => (
                    <TaskCard key={task.id} task={task} />
                ))}
            </div>
        </div>
    )
}
