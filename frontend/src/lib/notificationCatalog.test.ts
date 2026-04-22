import { describe, expect, it } from 'vitest'

import {
	createLabelsByCode,
	emptyNotificationCatalog,
	getCategoryLabel,
	getChannelLabel,
	getFirstCategoryCode,
	getLoadedNotificationCatalog,
	hasCategoryCode,
	statusLabelsByCode,
	type MessageCategoryOption,
	type NotificationChannelOption,
} from './notificationCatalog'

const categories: MessageCategoryOption[] = [
	{ code: 'sports', label: 'Sports' },
	{ code: 'finance', label: 'Finance' },
]

const channels: NotificationChannelOption[] = [
	{ code: 'sms', label: 'SMS' },
	{ code: 'email', label: 'E-Mail' },
]

describe('notification catalog helpers', () => {
	it('returns an empty catalog fallback before API data loads', () => {
		expect(getLoadedNotificationCatalog(undefined)).toBe(
			emptyNotificationCatalog,
		)
		expect(getLoadedNotificationCatalog({ categories, channels })).toEqual({
			categories,
			channels,
		})
	})

	it('builds labels and falls back to raw category or channel codes', () => {
		const categoryLabelsByCode = createLabelsByCode(categories)
		const channelLabelsByCode = createLabelsByCode(channels)

		expect(categoryLabelsByCode).toEqual({
			sports: 'Sports',
			finance: 'Finance',
		})
		expect(channelLabelsByCode).toEqual({
			sms: 'SMS',
			email: 'E-Mail',
		})
		expect(getCategoryLabel(categoryLabelsByCode, 'sports')).toBe('Sports')
		expect(getCategoryLabel(categoryLabelsByCode, 'movies')).toBe('movies')
		expect(getChannelLabel(channelLabelsByCode, 'sms')).toBe('SMS')
		expect(getChannelLabel(channelLabelsByCode, 'push')).toBe('push')
	})

	it('selects and validates category codes from loaded options', () => {
		expect(getFirstCategoryCode(categories)).toBe('sports')
		expect(getFirstCategoryCode([])).toBeNull()
		expect(hasCategoryCode(categories, 'finance')).toBe(true)
		expect(hasCategoryCode(categories, 'weather')).toBe(false)
	})

	it('exposes user-facing delivery status labels', () => {
		expect(statusLabelsByCode).toEqual({
			pending: 'Pending',
			sent: 'Sent',
			failed: 'Failed',
		})
	})
})
