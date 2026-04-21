import { QueryClientProvider } from '@tanstack/react-query'
import {
	fireEvent,
	render,
	screen,
	waitFor,
	within,
} from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { createQueryClient } from '../services/queryClient'
import { SetupPage } from './SetupPage'

afterEach(() => {
	vi.unstubAllEnvs()
	vi.unstubAllGlobals()
})

function renderSetupPage() {
	const queryClient = createQueryClient()

	return render(
		<QueryClientProvider client={queryClient}>
			<SetupPage />
		</QueryClientProvider>,
	)
}

/**
 * @param {unknown} body
 * @param {ResponseInit} [init]
 * @returns {Response}
 */
function jsonResponse(body, init = {}) {
	return new Response(JSON.stringify(body), {
		status: 200,
		headers: {
			'Content-Type': 'application/json',
		},
		...init,
	})
}

describe('SetupPage', () => {
	it('renders the configured application, backend values, and audit items', async () => {
		vi.stubEnv('VITE_APP_NAME', 'Notification Control Center')
		vi.stubEnv('VITE_API_BASE_URL', 'http://localhost:9000/v1')
		vi.stubGlobal(
			'fetch',
			vi.fn(() =>
				Promise.resolve(
					jsonResponse({
						items: [
							{
								attempt_id: 18,
								message_id: 4,
								category: 'sports',
								body: 'Team A won the championship',
								channel: 'email',
								status: 'sent',
								attempt_number: 1,
								attempted_at: '2026-04-20T17:05:00Z',
								processing_started_at: '2026-04-20T17:05:01Z',
								processed_at: '2026-04-20T17:05:02Z',
								delivered_at: '2026-04-20T17:05:02Z',
								last_error_at: null,
								next_retry_at: null,
								failure_reason: null,
								provider_reference: 'email-4-1',
							},
						],
					}),
				),
			),
		)

		renderSetupPage()

		expect(
			screen.getByRole('heading', {
				level: 1,
				name: 'Notification Control Center',
			}),
		).toBeInTheDocument()
		expect(screen.getByText('http://localhost:9000/v1')).toBeInTheDocument()

		const categoriesPanel = screen
			.getByRole('heading', { level: 2, name: 'Categories' })
			.closest('[data-slot="card"]')
		const channelsPanel = screen
			.getByRole('heading', { level: 2, name: 'Channels' })
			.closest('[data-slot="card"]')

		if (!categoriesPanel || !channelsPanel) {
			throw new Error('Expected categories and channels panels to be rendered.')
		}
		if (
			!(categoriesPanel instanceof HTMLElement) ||
			!(channelsPanel instanceof HTMLElement)
		) {
			throw new Error('Expected panel containers to be HTML elements.')
		}
		expect(within(categoriesPanel).getByText('Sports')).toBeInTheDocument()
		expect(within(categoriesPanel).getByText('Finance')).toBeInTheDocument()
		expect(within(categoriesPanel).getByText('Movies')).toBeInTheDocument()
		expect(within(channelsPanel).getByText('SMS')).toBeInTheDocument()
		expect(within(channelsPanel).getByText('E-Mail')).toBeInTheDocument()
		expect(
			within(channelsPanel).getByText('Push Notification'),
		).toBeInTheDocument()

		expect(
			await screen.findByRole('heading', {
				level: 3,
				name: 'Team A won the championship',
			}),
		).toBeInTheDocument()
		expect(screen.getByText('Details withheld')).toBeInTheDocument()
		expect(
			screen.getByText('PII is kept server-side in the audit record.'),
		).toBeInTheDocument()
		expect(screen.getByText('email-4-1')).toBeInTheDocument()
	})

	it('validates blank messages before running the mutation', async () => {
		const fetchMock = vi.fn(() =>
			Promise.resolve(
				jsonResponse({
					items: [],
				}),
			),
		)
		vi.stubGlobal('fetch', fetchMock)

		renderSetupPage()

		await screen.findByText('No delivery attempts yet')

		fireEvent.change(screen.getByLabelText('Message'), {
			target: { value: '   ' },
		})
		fireEvent.submit(screen.getByRole('button', { name: 'Send message' }))

		expect(
			screen.getByText('Message body must not be blank.'),
		).toBeInTheDocument()
		expect(fetchMock).toHaveBeenCalledTimes(1)
	})

	it('submits a message through a mutation and refreshes the logs query', async () => {
		const fetchMock = vi
			.fn()
			.mockResolvedValueOnce(jsonResponse({ items: [] }))
			.mockResolvedValueOnce(
				jsonResponse(
					{
						message_id: 12,
						category: 'sports',
						body: 'Team A won',
						total_users: 2,
						total_attempts: 3,
						sent: 2,
						failed: 1,
						created_at: '2026-04-20T17:10:00Z',
					},
					{ status: 201 },
				),
			)
			.mockResolvedValueOnce(
				jsonResponse({
					items: [
						{
							attempt_id: 22,
							message_id: 12,
							category: 'sports',
							body: 'Team A won',
							channel: 'push',
							status: 'sent',
							attempt_number: 1,
							attempted_at: '2026-04-20T17:10:02Z',
							processing_started_at: '2026-04-20T17:10:03Z',
							processed_at: '2026-04-20T17:10:04Z',
							delivered_at: '2026-04-20T17:10:04Z',
							last_error_at: null,
							next_retry_at: null,
							failure_reason: null,
							provider_reference: 'push-12-1',
						},
					],
				}),
			)
		vi.stubGlobal('fetch', fetchMock)

		renderSetupPage()

		await screen.findByText('No delivery attempts yet')

		fireEvent.change(screen.getByLabelText('Message'), {
			target: { value: '  Team A won  ' },
		})
		fireEvent.submit(screen.getByRole('button', { name: 'Send message' }))

		await screen.findByText(
			'Delivered 2 of 3 attempts across 2 subscribed users.',
		)
		expect(await screen.findByText('Details withheld')).toBeInTheDocument()
		expect(await screen.findByText('push-12-1')).toBeInTheDocument()
		await waitFor(() => {
			expect(fetchMock).toHaveBeenCalledTimes(3)
		})

		expect(fetchMock).toHaveBeenNthCalledWith(
			2,
			'http://localhost:8000/v1/messages',
			{
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
				},
				body: JSON.stringify({
					category: 'sports',
					body: 'Team A won',
				}),
			},
		)
	})

	it('shows API errors from the mutation response', async () => {
		const fetchMock = vi
			.fn()
			.mockResolvedValueOnce(jsonResponse({ items: [] }))
			.mockResolvedValueOnce(
				jsonResponse(
					{
						detail: 'Request validation failed.',
						errors: [
							{
								field: 'body',
								message: 'Value error, Message body must not be blank.',
							},
						],
					},
					{ status: 422 },
				),
			)
		vi.stubGlobal('fetch', fetchMock)

		renderSetupPage()

		await screen.findByText('No delivery attempts yet')

		fireEvent.change(screen.getByLabelText('Message'), {
			target: { value: 'Quarterly update' },
		})
		fireEvent.submit(screen.getByRole('button', { name: 'Send message' }))

		expect(await screen.findByText('Submission failed')).toBeInTheDocument()
		expect(screen.getByText('Request validation failed.')).toBeInTheDocument()
		expect(
			screen.getByText('Value error, Message body must not be blank.'),
		).toBeInTheDocument()
	})

	it('shows query errors when the audit log cannot be loaded', async () => {
		vi.stubGlobal(
			'fetch',
			vi.fn(() =>
				Promise.resolve(
					jsonResponse(
						{
							detail: 'The notification logs could not be loaded.',
						},
						{ status: 500 },
					),
				),
			),
		)

		renderSetupPage()

		const alert = await screen.findByRole('alert')
		expect(alert).toHaveTextContent(
			'The notification logs could not be loaded.',
		)
	})
})
