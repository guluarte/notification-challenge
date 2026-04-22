import { afterEach, describe, expect, it, vi } from 'vitest'

import { listNotificationLogs } from './notificationApi'

afterEach(() => {
	vi.unstubAllEnvs()
})

function jsonResponse(body: unknown): Response {
	return new Response(JSON.stringify(body), {
		status: 200,
		headers: {
			'Content-Type': 'application/json',
		},
	})
}

describe('notification API client', () => {
	it('builds log listing URLs with server-side filters', async () => {
		const fetchMock = vi.fn(() => {
			return Promise.resolve(
				jsonResponse({
					items: [],
					total: 0,
					limit: 50,
					offset: 100,
				}),
			)
		})

		await listNotificationLogs(
			{
				limit: 50,
				offset: 100,
				filters: {
					category: 'sports',
					channel: 'email',
					status: 'failed',
					messageId: 4,
					userId: 1,
					search: ' Alex Morgan ',
				},
			},
			fetchMock,
		)

		expect(fetchMock).toHaveBeenCalledWith(
			'http://localhost:8000/v1/logs?limit=50&offset=100&category=sports&channel=email&status=failed&message_id=4&user_id=1&q=Alex+Morgan',
		)
	})
})
