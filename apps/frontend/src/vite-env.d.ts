/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string
  readonly VITE_WS_URL: string
  readonly VITE_ENABLE_AUTH: string
  readonly VITE_ENABLE_FILE_UPLOAD: string
  readonly VITE_ENABLE_PIPELINES: string
  readonly VITE_ENABLE_WEBSOCKETS: string
  readonly VITE_MAX_FILE_SIZE: string
  readonly VITE_MAX_FILES: string
  readonly VITE_APP_NAME: string
  readonly VITE_APP_DESCRIPTION: string
  readonly VITE_VERCEL_ANALYTICS_ID?: string
  readonly VITE_DEBUG: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}