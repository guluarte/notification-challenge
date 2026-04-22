import { QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
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

function jsonResponse(body: unknown, init: ResponseInit = {}): Response {
	return new Response(JSON.stringify(body), {
		status: 200,
		headers: {
			'Content-Type': 'application/json',
		},
		...init,
	})
}

const catalogPayload = {
	categories: [
		{ code: 'sports', label: 'Sports' },
		{ code: 'finance', label: 'Finance' },
		{ code: 'movies', label: 'Movies' },
	],
	channels: [
		{ code: 'sms', label: 'SMS' },
		{ code: 'email', label: 'E-Mail' },
		{ code: 'push', label: 'Push Notification' },
	],
}

function isRequestInit(value: unknown): value is RequestInit {
	return value !== null && typeof value === 'object'
}

function getRequestUrl(input: unknown): string {
	if (typeof input === 'string') {
		return input
	}

	if (input instanceof Request) {
		return input.url
	}

	throw new Error('Expected fetch call to include a request URL')
}

function getIdempotencyKeyFromCall(call: ReadonlyArray<unknown>): string {
	const requestInit = call[1]
	if (!isRequestInit(requestInit)) {
		throw new Error('Expected fetch call to include request options')
	}

	const idempotencyKey = new Headers(requestInit.headers).get('Idempotency-Key')
	if (idempotencyKey === null) {
		throw new Error('Expected request to include an idempotency key')
	}

	return idempotencyKey
}

describe('SetupPage', () => {
	it('renders the configured application, pagination controls, and audit items', async () => {
		vi.stubEnv('VITE_APP_NAME', 'Notification Control Center')
		vi.stubEnv('VITE_API_BASE_URL', 'http://localhost:9000/v1')
		const logsPayload = {
			items: [
				{
					attempt_id: 18,
					message_id: 4,
					category: 'sports',
					body: 'Team A won the championship',
					user: {
						id: 1,
						name: 'Alex Morgan',
						email: 'alex.morgan@example.com',
						phone_number: '+15550000001',
					},
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
			total: 1,
			limit: 10,
			offset: 0,
		}
		const fetchMock = vi.fn((input: RequestInfo | URL) => {
			const url = getRequestUrl(input)
			if (url === 'http://localhost:9000/v1/catalog') {
				return Promise.resolve(jsonResponse(catalogPayload))
			}
			return Promise.resolve(jsonResponse(logsPayload))
		})
		vi.stubGlobal('fetch', fetchMock)

		renderSetupPage()

		expect(
			screen.getByRole('heading', {
				level: 1,
				name: 'Notification Control Center',
			}),
		).toBeInTheDocument()
		expect(await screen.findAllByText('Showing 1-1 of 1')).toHaveLength(2)
		expect(screen.getAllByText('Page 1 of 1')).toHaveLength(2)
		expect(
			screen.getAllByRole('navigation', {
				name: /notification log pagination/,
			}),
		).toHaveLength(2)
		expect(
			screen.getByRole('combobox', { name: 'Rows per page' }),
		).toHaveTextContent('10')
		expect(screen.getByRole('combobox', { name: 'Rows per page' })).toHaveClass(
			'cursor-pointer',
		)
		expect(screen.getByRole('button', { name: 'Refresh logs' })).toHaveClass(
			'cursor-pointer',
		)
		expect(screen.getByRole('button', { name: 'Send message' })).toHaveClass(
			'cursor-pointer',
		)
		expect(fetchMock).toHaveBeenCalledWith('http://localhost:9000/v1/catalog')
		expect(fetchMock).toHaveBeenCalledWith(
			'http://localhost:9000/v1/logs?limit=10&offset=0',
		)

		expect(screen.getByText('Channels')).toBeInTheDocument()
		expect(
			screen.queryByRole('heading', { level: 2, name: 'Categories' }),
		).not.toBeInTheDocument()
		expect(screen.queryByText('Runtime')).not.toBeInTheDocument()
		expect(screen.getAllByText('SMS').length).toBeGreaterThan(0)
		expect(screen.getAllByText('E-Mail').length).toBeGreaterThan(0)
		expect(screen.getAllByText('Push Notification').length).toBeGreaterThan(0)

		expect(
			await screen.findByRole('heading', {
				level: 3,
				name: 'Team A won the championship',
			}),
		).toBeInTheDocument()
		expect(screen.getByText('Alex Morgan')).toBeInTheDocument()
		expect(screen.getByText('ID #1')).toBeInTheDocument()
		expect(screen.getByText('alex.morgan@example.com')).toBeInTheDocument()
		expect(screen.getByText('+15550000001')).toBeInTheDocument()
		expect(screen.getByText('email-4-1')).toBeInTheDocument()
	})

	it('validates blank messages before running the mutation', async () => {
		const fetchMock = vi.fn((input: RequestInfo | URL) => {
			const url = getRequestUrl(input)
			if (url === 'http://localhost:8000/v1/catalog') {
				return Promise.resolve(jsonResponse(catalogPayload))
			}
			return Promise.resolve(
				jsonResponse({
					items: [],
					total: 0,
					limit: 10,
					offset: 0,
				}),
			)
		})
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
		expect(fetchMock).toHaveBeenCalledTimes(2)
	})

	it('submits a message through a mutation and refreshes the logs query', async () => {
		const logResponses = [
			{
				items: [],
				total: 0,
				limit: 10,
				offset: 0,
			},
			{
				items: [
					{
						attempt_id: 22,
						message_id: 12,
						category: 'sports',
						body: 'Team A won',
						user: {
							id: 3,
							name: 'Sam Rivera',
							email: 'sam.rivera@example.com',
							phone_number: '+15550001003',
						},
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
				total: 1,
				limit: 10,
				offset: 0,
			},
		]
		const fetchMock = vi.fn((input: RequestInfo | URL) => {
			const url = getRequestUrl(input)
			if (url === 'http://localhost:8000/v1/catalog') {
				return Promise.resolve(jsonResponse(catalogPayload))
			}
			if (url === 'http://localhost:8000/v1/messages') {
				return Promise.resolve(
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
			}

			const logResponse = logResponses.shift()
			if (logResponse === undefined) {
				throw new Error('Expected queued log response')
			}
			return Promise.resolve(jsonResponse(logResponse))
		})
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
		expect(await screen.findByText('Sam Rivera')).toBeInTheDocument()
		expect(await screen.findByText('push-12-1')).toBeInTheDocument()
		await waitFor(() => {
			expect(fetchMock).toHaveBeenCalledTimes(4)
		})
		expect(fetchMock).toHaveBeenNthCalledWith(
			1,
			'http://localhost:8000/v1/catalog',
		)
		expect(fetchMock).toHaveBeenNthCalledWith(
			2,
			'http://localhost:8000/v1/logs?limit=10&offset=0',
		)

		expect(fetchMock).toHaveBeenNthCalledWith(
			3,
			'http://localhost:8000/v1/messages',
			{
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					'Idempotency-Key': expect.any(String),
				},
				body: JSON.stringify({
					category: 'sports',
					body: 'Team A won',
				}),
			},
		)
		expect(fetchMock).toHaveBeenNthCalledWith(
			4,
			'http://localhost:8000/v1/logs?limit=10&offset=0',
		)
	})

	it('reuses the idempotency key when retrying the same failed submission', async () => {
		let messageAttemptCount = 0
		const fetchMock = vi.fn((input: RequestInfo | URL) => {
			const url = getRequestUrl(input)
			if (url === 'http://localhost:8000/v1/catalog') {
				return Promise.resolve(jsonResponse(catalogPayload))
			}
			if (url === 'http://localhost:8000/v1/messages') {
				messageAttemptCount += 1
				if (messageAttemptCount === 1) {
					return Promise.reject(new Error('network unavailable'))
				}
				return Promise.resolve(
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
			}
			return Promise.resolve(
				jsonResponse({
					items: [],
					total: 0,
					limit: 10,
					offset: 0,
				}),
			)
		})
		vi.stubGlobal('fetch', fetchMock)

		renderSetupPage()

		await screen.findByText('No delivery attempts yet')

		fireEvent.change(screen.getByLabelText('Message'), {
			target: { value: 'Team A won' },
		})
		fireEvent.submit(screen.getByRole('button', { name: 'Send message' }))

		expect(
			await screen.findByText('The message could not be submitted.'),
		).toBeInTheDocument()

		fireEvent.submit(screen.getByRole('button', { name: 'Send message' }))

		await screen.findByText(
			'Delivered 2 of 3 attempts across 2 subscribed users.',
		)
		await waitFor(() => {
			expect(fetchMock).toHaveBeenCalledTimes(5)
		})

		const submitCalls = fetchMock.mock.calls.filter((call) => {
			return getRequestUrl(call[0]) === 'http://localhost:8000/v1/messages'
		})
		const firstSubmitCall = submitCalls[0]
		const secondSubmitCall = submitCalls[1]
		if (firstSubmitCall === undefined || secondSubmitCall === undefined) {
			throw new Error('Expected two submit requests')
		}

		expect(getIdempotencyKeyFromCall(firstSubmitCall)).toBe(
			getIdempotencyKeyFromCall(secondSubmitCall),
		)
	})

	it('shows API errors from the mutation response', async () => {
		const fetchMock = vi.fn((input: RequestInfo | URL) => {
			const url = getRequestUrl(input)
			if (url === 'http://localhost:8000/v1/catalog') {
				return Promise.resolve(jsonResponse(catalogPayload))
			}
			if (url === 'http://localhost:8000/v1/messages') {
				return Promise.resolve(
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
			}
			return Promise.resolve(
				jsonResponse({
					items: [],
					total: 0,
					limit: 10,
					offset: 0,
				}),
			)
		})
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
			vi.fn((input: RequestInfo | URL) => {
				const url = getRequestUrl(input)
				if (url === 'http://localhost:8000/v1/catalog') {
					return Promise.resolve(jsonResponse(catalogPayload))
				}
				return Promise.resolve(
					jsonResponse(
						{
							detail: 'The notification logs could not be loaded.',
						},
						{ status: 500 },
					),
				)
			}),
		)

		renderSetupPage()

		const alert = await screen.findByRole('alert')
		expect(alert).toHaveTextContent(
			'The notification logs could not be loaded.',
		)
		expect(
			screen.queryByText('No delivery attempts yet'),
		).not.toBeInTheDocument()
	})
})
