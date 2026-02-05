import { useState, useRef } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useLanguage } from '@/contexts/language-context'
import { useBulkUrls, validateVideoUrl, parseUrls, parseUrlsFromFile } from '@/hooks/use-bulk-urls'
import { Loader2, Upload, X } from 'lucide-react'
import { toast } from 'sonner'

export function BulkUrlsSection() {
    const { t } = useLanguage()
    const [urlsText, setUrlsText] = useState('')
    const [resolution, setResolution] = useState('720p')
    const [fileName, setFileName] = useState<string | null>(null)
    const fileInputRef = useRef<HTMLInputElement>(null)

    const bulkUrls = useBulkUrls()

    const urls = parseUrls(urlsText)
    const validUrls = urls.filter(validateVideoUrl)
    const invalidUrls = urls.filter(url => !validateVideoUrl(url))

    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0]
        if (!file) return

        try {
            const parsedUrls = await parseUrlsFromFile(file)
            setUrlsText(parsedUrls.join('\n'))
            setFileName(file.name)
            toast.success(t('bulk.count', { count: parsedUrls.length }))
        } catch (error) {
            toast.error(t('common.error'))
            console.error(error)
        }
    }

    const handleClearFile = () => {
        setFileName(null)
        if (fileInputRef.current) {
            fileInputRef.current.value = ''
        }
    }

    const handleBulkDownload = () => {
        if (validUrls.length === 0) {
            toast.error(t('common.error'))
            return
        }

        bulkUrls.mutate(
            {
                urls: validUrls,
                resolution,
            },
            {
                onSuccess: () => {
                    setUrlsText('')
                    setFileName(null)
                },
            }
        )
    }

    const handleClear = () => {
        setUrlsText('')
        setFileName(null)
        if (fileInputRef.current) {
            fileInputRef.current.value = ''
        }
    }

    return (
        <Card>
            <CardHeader>
                <CardTitle>{t('tabs.bulk')}</CardTitle>
                <CardDescription>
                    {t('bulk.placeholder')}
                </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
                <div className="space-y-2">
                    <Label htmlFor="urls-textarea">{t('bulk.placeholder')}</Label>
                    <Textarea
                        id="urls-textarea"
                        placeholder="https://hanime1.me/watch?v=404444&#10;https://hanime1.me/watch?v=166752&#10;https://hanime1.me/watch?v=166751"
                        value={urlsText}
                        onChange={(e) => setUrlsText(e.target.value)}
                        rows={10}
                        className="font-mono text-sm"
                        disabled={bulkUrls.isPending}
                    />
                    <div className="flex items-center justify-between text-sm">
                        <div className="space-x-4">
                            <span className="text-muted-foreground">
                                {t('common.all')}: {urls.length}
                            </span>
                            <span className="text-green-600 dark:text-green-400">
                                {t('common.success')}: {validUrls.length}
                            </span>
                            {invalidUrls.length > 0 && (
                                <span className="text-destructive">
                                    {t('common.error')}: {invalidUrls.length}
                                </span>
                            )}
                        </div>
                        {fileName && (
                            <div className="flex items-center gap-2 text-muted-foreground">
                                <span>File: {fileName}</span>
                                <button
                                    onClick={handleClearFile}
                                    className="hover:text-foreground"
                                >
                                    <X className="h-4 w-4" />
                                </button>
                            </div>
                        )}
                    </div>
                </div>

                <div className="flex items-center gap-2">
                    <input
                        ref={fileInputRef}
                        type="file"
                        accept=".txt"
                        onChange={handleFileUpload}
                        className="hidden"
                        id="file-upload"
                    />
                    <Button
                        variant="outline"
                        onClick={() => fileInputRef.current?.click()}
                        disabled={bulkUrls.isPending}
                    >
                        <Upload className="mr-2 h-4 w-4" />
                        {t('bulk.uploadFile')}
                    </Button>
                    <span className="text-sm text-muted-foreground">{t('bulk.placeholder')}</span>
                </div>

                <div className="flex items-center gap-4">
                    <div className="flex-1 space-y-2">
                        <Label htmlFor="bulk-resolution">{t('bulk.resolution')}</Label>
                        <Select value={resolution} onValueChange={setResolution}>
                            <SelectTrigger id="bulk-resolution">
                                <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="360p">360p</SelectItem>
                                <SelectItem value="480p">480p</SelectItem>
                                <SelectItem value="720p">720p</SelectItem>
                                <SelectItem value="1080p">1080p</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>
                </div>

                <div className="flex gap-2">
                    <Button
                        onClick={handleBulkDownload}
                        disabled={validUrls.length === 0 || bulkUrls.isPending}
                        className="flex-1"
                    >
                        {bulkUrls.isPending && (
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        )}
                        {t('bulk.addDownloads')} ({validUrls.length})
                    </Button>
                    <Button
                        variant="outline"
                        onClick={handleClear}
                        disabled={bulkUrls.isPending || !urlsText}
                    >
                        {t('bulk.clear')}
                    </Button>
                </div>

                {invalidUrls.length > 0 && (
                    <div className="rounded-md bg-destructive/10 p-3">
                        <p className="text-sm font-medium text-destructive">
                            {t('common.error')}:
                        </p>
                        <ul className="mt-2 space-y-1 text-xs text-muted-foreground font-mono">
                            {invalidUrls.slice(0, 5).map((url, i) => (
                                <li key={i} className="truncate">
                                    {url}
                                </li>
                            ))}
                            {invalidUrls.length > 5 && (
                                <li>... and {invalidUrls.length - 5} more</li>
                            )}
                        </ul>
                    </div>
                )}
            </CardContent>
        </Card>
    )
}
