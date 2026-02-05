import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Checkbox } from '@/components/ui/checkbox'
import { VideoCard } from './video-card'
import { useLanguage } from '@/contexts/language-context'
import { useBatchDownload, type VideoInfo } from '@/hooks/use-search'
import { Loader2 } from 'lucide-react'

interface VideoGridProps {
    videos: VideoInfo[]
    onClear?: () => void
}

export function VideoGrid({ videos, onClear }: VideoGridProps) {
    const { t } = useLanguage()
    const [selectedVideos, setSelectedVideos] = useState<Set<string>>(new Set())
    const [resolution, setResolution] = useState('720p')
    const batchDownload = useBatchDownload()

    const toggleVideo = (url: string) => {
        const newSelected = new Set(selectedVideos)
        if (newSelected.has(url)) {
            newSelected.delete(url)
        } else {
            newSelected.add(url)
        }
        setSelectedVideos(newSelected)
    }

    const toggleAll = (checked: boolean) => {
        if (checked) {
            setSelectedVideos(new Set(videos.map(v => v.url)))
        } else {
            setSelectedVideos(new Set())
        }
    }

    const handleBatchDownload = () => {
        const selectedVideoList = videos.filter(v => selectedVideos.has(v.url))

        if (selectedVideoList.length === 0) {
            return
        }

        batchDownload.mutate({
            videos: selectedVideoList.map(v => ({
                page_url: v.url,
                resolution: resolution,
                title: v.title,
            })),
        }, {
            onSuccess: () => {
                setSelectedVideos(new Set())
                onClear?.()
            }
        })
    }

    if (videos.length === 0) {
        return null
    }

    const allSelected = videos.length > 0 && selectedVideos.size === videos.length
    const indeterminate = selectedVideos.size > 0 && selectedVideos.size < videos.length

    return (
        <Card>
            <CardHeader>
                <div className="flex items-center justify-between">
                    <CardTitle>{t('search.totalVideos', { count: videos.length })}</CardTitle>
                    <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2">
                            <Checkbox
                                checked={allSelected}
                                onCheckedChange={toggleAll}
                                className={indeterminate ? 'data-[state=checked]:bg-muted' : ''}
                            />
                            <span className="text-sm text-muted-foreground">
                                {t('grid.selectAll')} ({selectedVideos.size})
                            </span>
                        </div>
                        <Select value={resolution} onValueChange={setResolution}>
                            <SelectTrigger className="w-[120px]">
                                <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="360p">360p</SelectItem>
                                <SelectItem value="480p">480p</SelectItem>
                                <SelectItem value="720p">720p</SelectItem>
                                <SelectItem value="1080p">1080p</SelectItem>
                            </SelectContent>
                        </Select>
                        <Button
                            onClick={handleBatchDownload}
                            disabled={selectedVideos.size === 0 || batchDownload.isPending}
                        >
                            {batchDownload.isPending && (
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            )}
                            {t('grid.downloadSelected')} ({selectedVideos.size})
                        </Button>
                    </div>
                </div>
            </CardHeader>
            <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                    {videos.map((video) => (
                        <VideoCard
                            key={video.url}
                            video={video}
                            selected={selectedVideos.has(video.url)}
                            onSelect={() => toggleVideo(video.url)}
                        />
                    ))}
                </div>
            </CardContent>
        </Card>
    )
}
