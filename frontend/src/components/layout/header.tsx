import { Moon, Sun } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useTheme } from '@/components/theme-provider'
import { useLanguage } from '@/contexts/language-context'
import { LanguageSwitcher } from '@/components/ui/language-switcher'

export function Header() {
    const { t } = useLanguage()
    const { theme, setTheme } = useTheme()

    const toggleTheme = () => {
        setTheme(theme === 'light' ? 'dark' : 'light')
    }

    return (
        <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
            <div className="container max-w-7xl mx-auto flex h-16 items-center justify-between px-4">
                <div className="flex items-center gap-2">
                    <img src="/logo.png" alt="Hanime1 Downloader" className="h-8 w-auto mr-2" />
                    <h1 className="text-xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent hidden sm:block">
                        {t('header.title')}
                    </h1>
                    <span className="text-xs text-muted-foreground self-end mb-1">v1.0</span>
                </div>

                <div className="flex items-center gap-2">
                    <LanguageSwitcher />
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
            </div>
        </header>
    )
}
