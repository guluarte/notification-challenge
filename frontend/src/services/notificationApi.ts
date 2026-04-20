import { getAppConfig } from './appConfig'

export type MessageCategoryCode = 'sports' | 'finance' | 'movies'
export type NotificationChannelCode = 'sms' | 'email' | 'push'
export type DeliveryStatus = 'pending' | 'sent' | 'failed'

export interface CreateMessagePayload {
	category: MessageCategoryCode
	body: string
}

export interface CreateMessageResponse {
	message_id: number
	category: MessageCategoryCode
	body: string
	total_users: number
	total_attempts: number
	sent: number
	failed: number
	created_at: string
}

export interface NotificationRecipient {
	id: number
	name: string
	email: string
	phone_number: string
}

export interface NotificationLogItem {
	attempt_id: number
	message_id: number
	category: MessageCategoryCode
	body: string
	user: NotificationRecipient
	channel: NotificationChannelCode
	status: DeliveryStatus
	attempt_number: number
	attempted_at: string
	processing_started_at: string | null
	processed_at: string | null
	delivered_at: string | null
	last_error_at: string | null
	next_retry_at: string | null
	failure_reason: string | null
	provider_reference: string | null
}

interface NotificationLogListResponse {
	items: NotificationLogItem[]
}

interface ValidationIssue {
	field: string
	message: string
}

interface ErrorResponsePayload {
	detail?: string
	errors?: ValidationIssue[]
}

export class ApiRequestError extends Error {
	detail: string
	fieldErrors: Record<string, string>

	constructor({
		detail,
		fieldErrors = {},
	}: {
		detail: string
		fieldErrors?: Record<string, string>
	}) {
		super(detail)
		this.name = 'ApiRequestError'
		this.detail = detail
		this.fieldErrors = fieldErrors
	}
}

function buildApiUrl(path: string): string {
	const { apiBaseUrl } = getAppConfig()
	return `${apiBaseUrl}${path}`
}

async function parseResponseBody(response: Response): Promise<unknown | null> {
	const contentType = response.headers.get('content-type') ?? ''
	if (!contentType.includes('application/json')) {
		return null
	}

	return response.json()
}

function isValidationIssue(value: unknown): value is ValidationIssue {
	if (value === null || typeof value !== 'object') {
		return false
	}

	return (
		'field' in value &&
		typeof value.field === 'string' &&
		'message' in value &&
		typeof value.message === 'string'
	)
}

function isErrorResponsePayload(value: unknown): value is ErrorResponsePayload {
	if (value === null || typeof value !== 'object') {
		return false
	}

	if (
		'detail' in value &&
		value.detail !== undefined &&
		typeof value.detail !== 'string'
	) {
		return false
	}

	if ('errors' in value && value.errors !== undefined) {
		if (!Array.isArray(value.errors)) {
			return false
		}

		return value.errors.every(isValidationIssue)
	}

	return true
}

async function throwApiError(response: Response): Promise<never> {
	const payload = await parseResponseBody(response)
	const detail =
		isErrorResponsePayload(payload) && typeof payload.detail === 'string'
			? payload.detail
			: 'The request could not be completed.'
	const fieldErrors: Record<string, string> = {}

	if (isErrorResponsePayload(payload) && Array.isArray(payload.errors)) {
		for (const issue of payload.errors) {
			fieldErrors[issue.field] = issue.message
		}
	}

	throw new ApiRequestError({ detail, fieldErrors })
}

async function readNotificationLogListResponse(
	response: Response,
): Promise<NotificationLogListResponse> {
	return response.json()
}

async function readCreateMessageResponse(
	response: Response,
): Promise<CreateMessageResponse> {
	return response.json()
}

export async function listNotificationLogs(
	fetchImpl: typeof fetch = globalThis.fetch,
): Promise<NotificationLogItem[]> {
	const response = await fetchImpl(buildApiUrl('/logs'))
	if (!response.ok) {
		await throwApiError(response)
	}

	const payload = await readNotificationLogListResponse(response)

	return payload.items
		.slice()
		.sort(
			(left, right) =>
				Date.parse(right.attempted_at) - Date.parse(left.attempted_at),
		)
}

export async function submitMessage(
	payload: CreateMessagePayload,
	fetchImpl: typeof fetch = globalThis.fetch,
): Promise<CreateMessageResponse> {
	const response = await fetchImpl(buildApiUrl('/messages'), {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
		},
		body: JSON.stringify(payload),
	})

	if (!response.ok) {
		await throwApiError(response)
	}

	return readCreateMessageResponse(response)
}
