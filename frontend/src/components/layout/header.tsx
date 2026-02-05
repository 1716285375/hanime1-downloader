import { Moon, Sun } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useTheme } from '@/components/theme-provider'

export function Header() {
    const { theme, setTheme } = useTheme()

    const toggleTheme = () => {
        setTheme(theme === 'light' ? 'dark' : 'light')
    }

    return (
        <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
            <div className="container max-w-7xl mx-auto flex h-16 items-center justify-between px-4">
                <div className="flex items-center gap-2">
                    <h1 className="text-2xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
                        Hanime1 Downloader
                    </h1>
                    <span className="text-xs text-muted-foreground">v1.0</span>
                </div>

                <Button
                    variant="ghost"
                    size="icon"
                    onClick={toggleTheme}
                    className="rounded-full"
                >
                    {theme === 'light' ? (
                        <Moon className="h-5 w-5" />
                    ) : (
                        <Sun className="h-5 w-5" />
                    )}
                    <span className="sr-only">Toggle theme</span>
                </Button>
            </div>
        </header>
    )
}
