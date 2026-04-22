import { getAppConfig } from './appConfig'

export type MessageCategoryCode = 'sports' | 'finance' | 'movies'
export type NotificationChannelCode = 'sms' | 'email' | 'push'
export type DeliveryStatus = 'pending' | 'sent' | 'failed'
export type LogPageSize = 10 | 50 | 100

export interface NotificationCatalogOption<TCode extends string> {
	code: TCode
	label: string
}

export type MessageCategoryOption =
	NotificationCatalogOption<MessageCategoryCode>
export type NotificationChannelOption =
	NotificationCatalogOption<NotificationChannelCode>

export interface NotificationCatalogResponse {
	categories: MessageCategoryOption[]
	channels: NotificationChannelOption[]
}

export interface CreateMessagePayload {
	category: MessageCategoryCode
	body: string
	idempotencyKey?: string
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

export interface NotificationLogUser {
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
	user: NotificationLogUser
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

export interface NotificationLogFilters {
	category: MessageCategoryCode | null
	channel: NotificationChannelCode | null
	status: DeliveryStatus | null
	messageId: number | null
	userId: number | null
	search: string
}

export interface NotificationLogListParams {
	limit: LogPageSize
	offset: number
	filters: NotificationLogFilters
}

export interface NotificationLogListResponse {
	items: NotificationLogItem[]
	total: number
	limit: LogPageSize
	offset: number
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
	let detail = 'The request could not be completed.'
	if (isErrorResponsePayload(payload) && typeof payload.detail === 'string') {
		detail = payload.detail
	}

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

async function readNotificationCatalogResponse(
	response: Response,
): Promise<NotificationCatalogResponse> {
	return response.json()
}

export async function getNotificationCatalog(
	fetchImpl: typeof fetch = globalThis.fetch,
): Promise<NotificationCatalogResponse> {
	const response = await fetchImpl(buildApiUrl('/catalog'))
	if (!response.ok) {
		await throwApiError(response)
	}

	return readNotificationCatalogResponse(response)
}

export async function listNotificationLogs(
	params: NotificationLogListParams,
	fetchImpl: typeof fetch = globalThis.fetch,
): Promise<NotificationLogListResponse> {
	const searchParams = new URLSearchParams({
		limit: params.limit.toString(),
		offset: params.offset.toString(),
	})
	if (params.filters.category !== null) {
		searchParams.set('category', params.filters.category)
	}
	if (params.filters.channel !== null) {
		searchParams.set('channel', params.filters.channel)
	}
	if (params.filters.status !== null) {
		searchParams.set('status', params.filters.status)
	}
	if (params.filters.messageId !== null) {
		searchParams.set('message_id', params.filters.messageId.toString())
	}
	if (params.filters.userId !== null) {
		searchParams.set('user_id', params.filters.userId.toString())
	}
	const normalizedSearch = params.filters.search.trim()
	if (normalizedSearch !== '') {
		searchParams.set('q', normalizedSearch)
	}
	const response = await fetchImpl(
		buildApiUrl(`/logs?${searchParams.toString()}`),
	)
	if (!response.ok) {
		await throwApiError(response)
	}

	return readNotificationLogListResponse(response)
}

export async function submitMessage(
	payload: CreateMessagePayload,
	fetchImpl: typeof fetch = globalThis.fetch,
): Promise<CreateMessageResponse> {
	const headers: Record<string, string> = {
		'Content-Type': 'application/json',
	}
	if (payload.idempotencyKey !== undefined) {
		headers['Idempotency-Key'] = payload.idempotencyKey
	}

	const response = await fetchImpl(buildApiUrl('/messages'), {
		method: 'POST',
		headers,
		body: JSON.stringify({
			category: payload.category,
			body: payload.body,
		}),
	})

	if (!response.ok) {
		await throwApiError(response)
	}

	return readCreateMessageResponse(response)
}
