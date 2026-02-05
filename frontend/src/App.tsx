import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ThemeProvider } from '@/components/theme-provider'
import { LanguageProvider, useLanguage } from '@/contexts/language-context'
import { Header } from '@/components/layout/header'
import { DownloadSection } from '@/components/download/download-section'
import { SearchSection } from '@/components/download/search-section'
import { BulkUrlsSection } from '@/components/download/bulk-urls-section'
import { TaskList } from '@/components/download/task-list'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Toaster } from '@/components/ui/sonner'

const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            refetchOnWindowFocus: false,
            retry: 1,
        },
    },
})

function AppContent() {
    const { t } = useLanguage()

    return (
        <div className="min-h-screen bg-background">
            <Header />
            <main className="container max-w-7xl mx-auto px-4 py-8 space-y-8">
                <Tabs defaultValue="single" className="w-full">
                    <TabsList className="grid w-full grid-cols-3">
                        <TabsTrigger value="single">{t('tabs.single')}</TabsTrigger>
                        <TabsTrigger value="search">{t('tabs.search')}</TabsTrigger>
                        <TabsTrigger value="bulk">{t('tabs.bulk')}</TabsTrigger>
                    </TabsList>
                    <TabsContent value="single" className="space-y-4" forceMount>
                        <DownloadSection />
                    </TabsContent>
                    <TabsContent value="search" className="space-y-4" forceMount>
                        <SearchSection />
                    </TabsContent>
                    <TabsContent value="bulk" className="space-y-4" forceMount>
                        <BulkUrlsSection />
                    </TabsContent>
                </Tabs>
                <TaskList />
            </main>
            <Toaster />
        </div>
    )
}

function App() {
    return (
        <QueryClientProvider client={queryClient}>
            <LanguageProvider>
                <ThemeProvider defaultTheme="system" storageKey="hanime-theme">
                    <AppContent />
                </ThemeProvider>
            </LanguageProvider>
        </QueryClientProvider>
    )
}

export default App
