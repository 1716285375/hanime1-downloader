import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Download, Loader2, Search } from 'lucide-react'
import { videoApi } from '@/lib/api'
import { VideoInfoCard } from './video-info-card'
import type { VideoInfo } from '@/types/api'
import { toast } from 'sonner'

export function DownloadSection() {
    const [url, setUrl] = useState('')
    const [videoInfo, setVideoInfo] = useState<VideoInfo | null>(null)
    const [loading, setLoading] = useState(false)

    const handleGetInfo = async () => {
        if (!url.trim()) {
            toast.error('Please enter a video URL')
            return
        }

        setLoading(true)
        try {
            const info = await videoApi.getInfo(url)
            setVideoInfo(info)
            toast.success('Video information loaded')
        } catch (error) {
            console.error('Failed to get video info:', error)
            toast.error('Failed to load video information')
            setVideoInfo(null)
        } finally {
            setLoading(false)
        }
    }

    const handleClear = () => {
        setUrl('')
        setVideoInfo(null)
    }

    return (
        <Card>
            <CardHeader>
                <CardTitle className="flex items-center gap-2">
                    <Download className="h-5 w-5" />
                    New Download
                </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
                <div className="flex gap-2">
                    <Input
                        placeholder="Enter video URL (e.g., https://hanime1.me/watch?v=xxxxx)"
                        value={url}
                        onChange={(e) => setUrl(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleGetInfo()}
                        className="flex-1"
                    />
                    <Button onClick={handleGetInfo} disabled={loading}>
                        {loading ? (
                            <>
                                <Loader2 className="h-4 w-4 animate-spin" />
                                Loading...
                            </>
                        ) : (
                            <>
                                <Search className="h-4 w-4" />
                                Get Info
                            </>
                        )}
                    </Button>
                </div>

                {videoInfo && (
                    <VideoInfoCard
                        videoInfo={videoInfo}
                        pageUrl={url}
                        onClear={handleClear}
                    />
                )}
            </CardContent>
        </Card>
    )
}
