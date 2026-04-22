const DEFAULT_APP_NAME = 'Notification Console'
const DEFAULT_API_BASE_URL = 'http://localhost:8000/v1'

interface AppConfig {
	appName: string
	apiBaseUrl: string
}

export function getAppConfig(): AppConfig {
	return {
		appName: import.meta.env.VITE_APP_NAME ?? DEFAULT_APP_NAME,
		apiBaseUrl: import.meta.env.VITE_API_BASE_URL ?? DEFAULT_API_BASE_URL,
	}
}
