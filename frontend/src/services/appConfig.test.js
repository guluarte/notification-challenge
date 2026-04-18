import { afterEach, describe, expect, it, vi } from 'vitest'

import { getAppConfig } from './appConfig'

afterEach(() => {
	vi.unstubAllEnvs()
})

describe('getAppConfig', () => {
	it('returns defaults when no environment overrides are provided', () => {
		vi.stubEnv('VITE_APP_NAME', undefined)
		vi.stubEnv('VITE_API_BASE_URL', undefined)

		expect(getAppConfig()).toEqual({
			appName: 'Notification Console',
			apiBaseUrl: 'http://localhost:8000/v1',
		})
	})

	it('returns environment overrides when provided', () => {
		vi.stubEnv('VITE_APP_NAME', 'Ops Console')
		vi.stubEnv('VITE_API_BASE_URL', 'https://api.example.test/v1')

		expect(getAppConfig()).toEqual({
			appName: 'Ops Console',
			apiBaseUrl: 'https://api.example.test/v1',
		})
	})
})
