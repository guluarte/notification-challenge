import type {
	DeliveryStatus,
	MessageCategoryCode,
	MessageCategoryOption,
	NotificationCatalogOption,
	NotificationCatalogResponse,
	NotificationChannelCode,
	NotificationChannelOption,
} from '../services/notificationApi'

export const emptyNotificationCatalog: NotificationCatalogResponse = {
	categories: [],
	channels: [],
}

export function createLabelsByCode<TCode extends string>(
	options: NotificationCatalogOption<TCode>[],
): Record<TCode, string> {
	const labelsByCode = {} as Record<TCode, string>
	for (const option of options) {
		labelsByCode[option.code] = option.label
	}
	return labelsByCode
}

export const statusLabelsByCode: Record<DeliveryStatus, string> = {
	pending: 'Pending',
	sent: 'Sent',
	failed: 'Failed',
}

export function getFirstCategoryCode(
	categories: MessageCategoryOption[],
): MessageCategoryCode | null {
	const firstCategory = categories[0]
	if (firstCategory === undefined) {
		return null
	}
	return firstCategory.code
}

export function hasCategoryCode(
	categories: MessageCategoryOption[],
	value: string,
): value is MessageCategoryCode {
	return categories.some((category) => category.code === value)
}

export function hasChannelCode(
	channels: NotificationChannelOption[],
	value: string,
): value is NotificationChannelCode {
	return channels.some((channel) => channel.code === value)
}

export function getCategoryLabel(
	labelsByCode: Record<MessageCategoryCode, string>,
	code: MessageCategoryCode,
): string {
	const label = labelsByCode[code]
	if (label === undefined) {
		return code
	}
	return label
}

export function getChannelLabel(
	labelsByCode: Record<NotificationChannelCode, string>,
	code: NotificationChannelCode,
): string {
	const label = labelsByCode[code]
	if (label === undefined) {
		return code
	}
	return label
}

export function getLoadedNotificationCatalog(
	catalog: NotificationCatalogResponse | undefined,
): NotificationCatalogResponse {
	if (catalog === undefined) {
		return emptyNotificationCatalog
	}
	return catalog
}

export type { MessageCategoryOption, NotificationChannelOption }
