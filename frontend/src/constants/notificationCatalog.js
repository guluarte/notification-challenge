/**
 * @typedef {import('../services/notificationApi').DeliveryStatus} DeliveryStatus
 * @typedef {import('../services/notificationApi').MessageCategoryCode} MessageCategoryCode
 * @typedef {import('../services/notificationApi').NotificationChannelCode} NotificationChannelCode
 */

/** @type {{ code: MessageCategoryCode; label: string }[]} */
export const notificationCategories = [
	{ code: 'sports', label: 'Sports' },
	{ code: 'finance', label: 'Finance' },
	{ code: 'movies', label: 'Movies' },
]

/** @type {{ code: NotificationChannelCode; label: string }[]} */
export const notificationChannels = [
	{ code: 'sms', label: 'SMS' },
	{ code: 'email', label: 'E-Mail' },
	{ code: 'push', label: 'Push Notification' },
]

/** @type {Record<MessageCategoryCode, string>} */
export const categoryLabelsByCode = {
	sports: 'Sports',
	finance: 'Finance',
	movies: 'Movies',
}

/** @type {Record<NotificationChannelCode, string>} */
export const channelLabelsByCode = {
	sms: 'SMS',
	email: 'E-Mail',
	push: 'Push Notification',
}

/** @type {Record<DeliveryStatus, string>} */
export const statusLabelsByCode = {
	pending: 'Pending',
	sent: 'Sent',
	failed: 'Failed',
}
