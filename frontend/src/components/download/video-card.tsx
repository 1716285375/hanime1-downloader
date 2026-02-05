import { Card, CardContent } from '@/components/ui/card'
import { Checkbox } from '@/components/ui/checkbox'
import type { VideoInfo } from '@/hooks/use-search'

interface VideoCardProps {
    video: VideoInfo
    selected: boolean
    onSelect: (selected: boolean) => void
}

export function VideoCard({ video, selected, onSelect }: VideoCardProps) {
    const thumbnailUrl = video.thumbnail_url
        ? (video.thumbnail_url.startsWith('/api/') || video.thumbnail_url.startsWith('http') === false
            ? video.thumbnail_url
            : `/api/proxy/image?url=${encodeURIComponent(video.thumbnail_url)}`)
        : '/placeholder.jpg'

    return (
        <Card className="group overflow-hidden hover:shadow-lg transition-shadow">
            <CardContent className="p-0">
                <div className="relative aspect-[2/3] w-full overflow-hidden bg-muted">
                    <img
                        src={thumbnailUrl}
                        alt={video.title}
                        className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
                        loading="lazy"
                        onError={(e) => {
                            e.currentTarget.src = '/placeholder.jpg'
                        }}
                    />
                    <div className="absolute top-2 right-2 flex gap-2">
                        {Object.keys(video.resolutions).length > 0 && (
                            <div className="rounded-md bg-black/60 px-2 py-0.5 text-xs font-medium text-white backdrop-blur-sm">
                                {Object.keys(video.resolutions)[0]}
                            </div>
                        )}
                        <Checkbox
                            checked={selected}
                            onCheckedChange={onSelect}
                            className="bg-background/80 backdrop-blur-sm data-[state=checked]:bg-primary data-[state=checked]:text-primary-foreground"
                        />
                    </div>
                </div>
                <div className="p-3">
                    <h3 className="text-sm font-medium line-clamp-2 min-h-[2.5rem]">
                        {video.title}
                    </h3>
                </div>
            </CardContent>
        </Card>
    )
}
