export type Language = 'en' | 'zh'

export const translations = {
    en: {
        common: {
            loading: 'Loading...',
            success: 'Success',
            error: 'Error',
            cancel: 'Cancel',
            confirm: 'Confirm',
            save: 'Save',
            delete: 'Delete',
            all: 'All',
            none: 'None',
            unknown: 'Unknown',
            retry: 'Retry',
            noThumbnail: 'No Thumbnail',
        },
        header: {
            title: 'Hanime1 Downloader',
            tasks: 'Tasks',
            settings: 'Settings',
        },
        tabs: {
            single: 'Single Download',
            search: 'Batch Search',
            bulk: 'Bulk Import',
        },
        download: {
            urlPlaceholder: 'Enter video URL...',
            downloadBtn: 'Download',
            analyzing: 'Analyzing...',
            addToQueue: 'Add to Queue',
            started: 'Download started',
            failed: 'Failed to start download',
        },
        search: {
            placeholder: 'Enter search or browse URL (e.g. https://hanime1.me/search?genre=裏番)',
            analyzeSingle: 'Analyze Page',
            analyzeMulti: 'Analyze Multi-Page',
            detecting: 'Detecting...',
            pageRange: 'Page Range',
            startPage: 'Start',
            endPage: 'End',
            totalVideos: 'Found {{count}} videos',
            fetching: 'Fetching page {{current}}/{{total}}...',
        },
        bulk: {
            title: 'Bulk URL Import',
            description: 'Import multiple video URLs to download at once',
            placeholder: 'Enter video URLs (one per line)',
            uploadFile: 'Upload/Drag .txt File',
            addDownloads: 'Add Downloads',
            clear: 'Clear',
            count: '{{count}} URLs',
            resolution: 'Resolution',
            fromFile: 'From: {{fileName}}',
        },
        grid: {
            selectAll: 'Select All',
            deselectAll: 'Deselect All',
            downloadSelected: 'Download Selected',
            selectedCount: '{{count}} Selected',
        },
        tasks: {
            title: 'Download Tasks',
            clearCompleted: 'Clear Completed',
            noDownloads: 'No downloads yet',
            retry: 'Retry',
            count: '{{count}} tasks',
            eta: 'ETA: ',
            completedAt: 'Completed at ',
            status: {
                pending: 'Pending',
                downloading: 'Downloading',
                completed: 'Completed',
                failed: 'Failed',
                cancelled: 'Cancelled',
            },
        },
    },
    zh: {
        common: {
            loading: '加载中...',
            success: '成功',
            error: '错误',
            cancel: '取消',
            confirm: '确认',
            save: '保存',
            delete: '删除',
            all: '全部',
            none: '无',
            unknown: '未知',
            retry: '重试',
            noThumbnail: '无缩略图',
        },
        header: {
            title: 'Hanime1 下载器',
            tasks: '任务列表',
            settings: '设置',
        },
        tabs: {
            single: '单个下载',
            search: '搜索批量',
            bulk: 'URL导入',
        },
        download: {
            urlPlaceholder: '输入视频链接...',
            downloadBtn: '下载',
            analyzing: '解析中...',
            addToQueue: '加入队列',
            started: '下载已开始',
            failed: '启动下载失败',
        },
        search: {
            placeholder: '输入搜索或浏览页面 URL (如 https://hanime1.me/search?genre=裏番)',
            analyzeSingle: '解析当前页',
            analyzeMulti: '解析多页',
            detecting: '检测中...',
            pageRange: '页面范围',
            startPage: '起始页',
            endPage: '结束页',
            totalVideos: '共找到 {{count}} 个视频',
            fetching: '正在获取第 {{current}}/{{total}} 页...',
        },
        bulk: {
            title: '批量 URL 导入',
            description: '导入多个视频 URL 进行批量下载',
            placeholder: '输入视频链接（每行一个）',
            uploadFile: '上传/拖拽 .txt 文件',
            addDownloads: '批量添加下载',
            clear: '清空',
            count: '{{count}} 个链接',
            resolution: '分辨率',
            fromFile: '来自: {{fileName}}',
        },
        grid: {
            selectAll: '全选',
            deselectAll: '取消全选',
            downloadSelected: '下载选中',
            selectedCount: '已选 {{count}} 个',
        },
        tasks: {
            title: '下载任务',
            clearCompleted: '清除已完成',
            noDownloads: '暂无下载任务',
            retry: '重试',
            count: '{{count}} 个任务',
            eta: '剩余时间: ',
            completedAt: '完成于 ',
            status: {
                pending: '等待中',
                downloading: '下载中',
                completed: '已完成',
                failed: '失败',
                cancelled: '已取消',
            },
        },
    },
} as const

// Helper type to get all keys recursively
type NestedKeyOf<ObjectType extends object> = {
    [Key in keyof ObjectType & (string | number)]: ObjectType[Key] extends object
    ? `${Key}` | `${Key}.${NestedKeyOf<ObjectType[Key]>}`
    : `${Key}`
}[keyof ObjectType & (string | number)]

export type TranslationKey = NestedKeyOf<typeof translations.en>
