import { useState } from 'react'
import { Download, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useCreateDownload } from '@/hooks/use-tasks'
import type { VideoInfo } from '@/types/api'
import { toast } from 'sonner'
import { cn } from '@/lib/utils'
import { useLanguage } from '@/contexts/language-context'

interface VideoInfoCardProps {
    videoInfo: VideoInfo
    pageUrl: string
    onClear: () => void
}

export function VideoInfoCard({ videoInfo, pageUrl, onClear }: VideoInfoCardProps) {
    const { t } = useLanguage()
    const [resolution, setResolution] = useState(
        Object.keys(videoInfo.resolutions)[0] || '1080p'
    )
    const createDownload = useCreateDownload()

    const handleDownload = () => {
        createDownload.mutate(
            {
                page_url: pageUrl,
                resolution,
                video_url: videoInfo.resolutions[resolution],
                thumbnail_url: videoInfo.thumbnail_url,
                title: videoInfo.title,
            },
            {
                onSuccess: () => {
                    toast.success(t('download.started'))
                    onClear()
                },
                onError: () => {
                    toast.error(t('download.failed'))
                },
            }
        )
    }

    // Use proxy for image to avoid CORS
    const proxyImageUrl = videoInfo.thumbnail_url
        ? `/api/proxy/image?url=${encodeURIComponent(videoInfo.thumbnail_url)}`
        : ''

    return (
        <div className="mt-4 rounded-lg border bg-muted/40 p-4 transition-all">
            <div className="flex flex-col gap-4 sm:flex-row">
                <div className="relative aspect-video w-full overflow-hidden rounded-md sm:w-48">
                    {proxyImageUrl ? (
                        <img
                            src={proxyImageUrl}
                            alt={videoInfo.title}
                            className="h-full w-full object-cover"
                        />
                    ) : (
                        <div className="flex h-full w-full items-center justify-center bg-muted">
                            <span className="text-muted-foreground">{t('common.noThumbnail')}</span>
                        </div>
                    )}
                </div>

                <div className="flex flex-1 flex-col gap-2">
                    <div className="flex items-start justify-between gap-2">
                        <h3 className="font-semibold leading-tight">{videoInfo.title}</h3>
                        <Button
                            variant="ghost"
                            size="icon"
                            className="h-6 w-6 shrink-0"
                            onClick={onClear}
                        >
                            <X className="h-4 w-4" />
                        </Button>
                    </div>

                    <div className="mt-auto flex flex-wrap items-center gap-2">
                        <select
                            value={resolution}
                            onChange={(e) => setResolution(e.target.value)}
                            className={cn(
                                "h-9 w-[120px] rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors",
                                "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring",
                                "disabled:cursor-not-allowed disabled:opacity-50"
                            )}
                        >
                            {Object.keys(videoInfo.resolutions).map((res) => (
                                <option key={res} value={res}>
                                    {res}
                                </option>
                            ))}
                        </select>

                        <Button onClick={handleDownload} disabled={createDownload.isPending}>
                            <Download className="mr-2 h-4 w-4" />
                            {createDownload.isPending ? t('common.loading') : t('download.downloadBtn')}
                        </Button>
                    </div>
                </div>
            </div>
        </div>
    )
}
