import type {
	DeliveryStatus,
	LogPageSize,
	NotificationLogFilters,
} from '../services/notificationApi'

export const ALL_FILTER_VALUE = 'all'
export const DELIVERY_STATUS_OPTIONS: DeliveryStatus[] = [
	'pending',
	'sent',
	'failed',
]

export function parseLogPageSize(
	value: string,
	pageSizeOptions: LogPageSize[],
): LogPageSize | null {
	for (const pageSizeOption of pageSizeOptions) {
		if (pageSizeOption.toString() === value) {
			return pageSizeOption
		}
	}

	return null
}

export function getFilterSelectValue(value: string | null): string {
	if (value === null) {
		return ALL_FILTER_VALUE
	}
	return value
}

export function getDeliveryStatus(value: string): DeliveryStatus | null {
	for (const statusOption of DELIVERY_STATUS_OPTIONS) {
		if (statusOption === value) {
			return statusOption
		}
	}
	return null
}

export function parsePositiveInteger(value: string): number | null {
	const normalized = value.trim()
	if (normalized === '') {
		return null
	}

	const parsed = Number.parseInt(normalized, 10)
	if (!Number.isSafeInteger(parsed) || parsed < 1) {
		return null
	}
	return parsed
}

export function formatOptionalNumber(value: number | null): string {
	if (value === null) {
		return ''
	}
	return value.toString()
}

export function hasActiveFilters(filters: NotificationLogFilters): boolean {
	return (
		filters.category !== null ||
		filters.channel !== null ||
		filters.status !== null ||
		filters.messageId !== null ||
		filters.userId !== null ||
		filters.search.trim() !== ''
	)
}

export function getUpdatedFilters(
	filters: NotificationLogFilters,
	patch: Partial<NotificationLogFilters>,
): NotificationLogFilters {
	return {
		...filters,
		...patch,
	}
}
