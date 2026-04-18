import React from 'react'
import { render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { SetupPage } from './SetupPage'

afterEach(() => {
	vi.unstubAllEnvs()
})

describe('SetupPage', () => {
	it('renders the configured application and backend values', () => {
		vi.stubEnv('VITE_APP_NAME', 'Notification Control Center')
		vi.stubEnv('VITE_API_BASE_URL', 'http://localhost:9000/v1')

		render(<SetupPage />)

		expect(
			screen.getByRole('heading', {
				level: 1,
				name: 'Notification Control Center',
			}),
		).toBeInTheDocument()
		expect(screen.getByText('http://localhost:9000/v1')).toBeInTheDocument()
	})

	it('renders the expected categories and channels', () => {
		render(<SetupPage />)

		expect(
			screen.getByRole('heading', { level: 2, name: 'Categories' }),
		).toBeInTheDocument()
		expect(screen.getByText('Sports')).toBeInTheDocument()
		expect(screen.getByText('Finance')).toBeInTheDocument()
		expect(screen.getByText('Movies')).toBeInTheDocument()

		expect(
			screen.getByRole('heading', { level: 2, name: 'Channels' }),
		).toBeInTheDocument()
		expect(screen.getByText('SMS')).toBeInTheDocument()
		expect(screen.getByText('E-Mail')).toBeInTheDocument()
		expect(screen.getByText('Push Notification')).toBeInTheDocument()
	})
})
