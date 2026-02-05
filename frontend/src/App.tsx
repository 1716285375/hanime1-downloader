import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ThemeProvider } from '@/components/theme-provider'
import { Header } from '@/components/layout/header'
import { DownloadSection } from '@/components/download/download-section'
import { TaskList } from '@/components/download/task-list'
import { Toaster } from '@/components/ui/sonner'

const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            refetchOnWindowFocus: false,
            retry: 1,
        },
    },
})

function App() {
    return (
        <QueryClientProvider client={queryClient}>
            <ThemeProvider defaultTheme="system" storageKey="hanime-theme">
                <div className="min-h-screen bg-background">
                    <Header />
                    <main className="container max-w-7xl mx-auto px-4 py-8 space-y-8">
                        <DownloadSection />
                        <TaskList />
                    </main>
                    <Toaster />
                </div>
            </ThemeProvider>
        </QueryClientProvider>
    )
}

export default App
