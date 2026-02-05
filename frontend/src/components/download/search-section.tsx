import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useLanguage } from '@/contexts/language-context'
import { useSearchVideos, usePaginatedSearch, type VideoInfo } from '@/hooks/use-search'
import { VideoGrid } from './video-grid'
import { Loader2 } from 'lucide-react'

export function SearchSection() {
    const { t } = useLanguage()
    const [searchUrl, setSearchUrl] = useState('')
    const [startPage, setStartPage] = useState(1)
    const [endPage, setEndPage] = useState<number | undefined>(undefined)
    const [videos, setVideos] = useState<VideoInfo[]>([])

    const searchSingle = useSearchVideos()
    const searchPaginated = usePaginatedSearch()

    const handleSearchSingle = () => {
        if (!searchUrl.trim()) return

        searchSingle.mutate(searchUrl, {
            onSuccess: (data) => {
                setVideos(data.videos)
            },
        })
    }

    const handleSearchPaginated = () => {
        if (!searchUrl.trim()) return

        searchPaginated.mutate(
            {
                url: searchUrl,
                startPage,
                endPage,
            },
            {
                onSuccess: (data) => {
                    setVideos(data.videos)
                },
            }
        )
    }

    const handleClear = () => {
        setVideos([])
        setSearchUrl('')
    }

    const isLoading = searchSingle.isPending || searchPaginated.isPending

    return (
        <div className="space-y-6">
            <Card>
                <CardHeader>
                    <CardTitle>{t('tabs.search')}</CardTitle>
                    <CardDescription>
                        {t('search.placeholder')}
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="space-y-2">
                        <Label htmlFor="search-url">Search URL</Label>
                        <Input
                            id="search-url"
                            placeholder="https://hanime1.me/search?genre=裏番"
                            value={searchUrl}
                            onChange={(e) => setSearchUrl(e.target.value)}
                            disabled={isLoading}
                        />
                        <p className="text-xs text-muted-foreground">
                            Example genres: 裏番, 泡麵番, Motion Anime, 3DCG, 2.5D, 2D動畫, AI生成, MMD, Cosplay
                        </p>
                    </div>

                    <div className="flex gap-4">
                        <Button
                            onClick={handleSearchSingle}
                            disabled={isLoading || !searchUrl.trim()}
                            className="flex-1"
                        >
                            {searchSingle.isPending && (
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            )}
                            {t('search.analyzeSingle')}
                        </Button>
                        <Button
                            onClick={handleSearchPaginated}
                            disabled={isLoading || !searchUrl.trim()}
                            variant="secondary"
                            className="flex-1"
                        >
                            {searchPaginated.isPending && (
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            )}
                            {t('search.analyzeMulti')}
                        </Button>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <Label htmlFor="start-page">{t('search.startPage')}</Label>
                            <Input
                                id="start-page"
                                type="number"
                                min="1"
                                value={startPage}
                                onChange={(e) => setStartPage(parseInt(e.target.value) || 1)}
                                disabled={isLoading}
                            />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="end-page">{t('search.endPage')}</Label>
                            <Input
                                id="end-page"
                                type="number"
                                min="1"
                                placeholder="Auto-detect"
                                value={endPage || ''}
                                onChange={(e) =>
                                    setEndPage(e.target.value ? parseInt(e.target.value) : undefined)
                                }
                                disabled={isLoading}
                            />
                        </div>
                    </div>

                    {isLoading && (
                        <div className="flex items-center justify-center py-8">
                            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                            <span className="ml-2 text-muted-foreground">
                                {t('search.detecting')}
                            </span>
                        </div>
                    )}
                </CardContent>
            </Card>


            {videos.length > 0 && <VideoGrid videos={videos} onClear={handleClear} />}
        </div>
    )
}
