import { describe, expect, it } from 'vitest'

import type { NotificationLogFilters } from '../services/notificationApi'
import {
	ALL_FILTER_VALUE,
	DELIVERY_STATUS_OPTIONS,
	formatOptionalNumber,
	getDeliveryStatus,
	getFilterSelectValue,
	getUpdatedFilters,
	hasActiveFilters,
	parseLogPageSize,
	parsePositiveInteger,
} from './notificationLogFilters'

const emptyFilters: NotificationLogFilters = {
	category: null,
	channel: null,
	status: null,
	messageId: null,
	userId: null,
	search: '',
}

describe('notification log filter helpers', () => {
	it('parses configured log page sizes', () => {
		expect(parseLogPageSize('10', [10, 50, 100])).toBe(10)
		expect(parseLogPageSize('25', [10, 50, 100])).toBeNull()
	})

	it('normalizes select values', () => {
		expect(getFilterSelectValue(null)).toBe(ALL_FILTER_VALUE)
		expect(getFilterSelectValue('sports')).toBe('sports')
		expect(DELIVERY_STATUS_OPTIONS).toEqual(['pending', 'sent', 'failed'])
		expect(getDeliveryStatus('failed')).toBe('failed')
		expect(getDeliveryStatus('unknown')).toBeNull()
	})

	it('parses positive integer filters', () => {
		expect(parsePositiveInteger(' 12 ')).toBe(12)
		expect(parsePositiveInteger('')).toBeNull()
		expect(parsePositiveInteger('0')).toBeNull()
		expect(parsePositiveInteger('abc')).toBeNull()
		expect(formatOptionalNumber(null)).toBe('')
		expect(formatOptionalNumber(12)).toBe('12')
	})

	it('detects and updates active filters', () => {
		expect(hasActiveFilters(emptyFilters)).toBe(false)
		expect(hasActiveFilters({ ...emptyFilters, search: ' Alex ' })).toBe(true)
		expect(hasActiveFilters({ ...emptyFilters, category: 'sports' })).toBe(true)
		expect(hasActiveFilters({ ...emptyFilters, channel: 'email' })).toBe(true)
		expect(hasActiveFilters({ ...emptyFilters, status: 'sent' })).toBe(true)
		expect(hasActiveFilters({ ...emptyFilters, messageId: 1 })).toBe(true)
		expect(hasActiveFilters({ ...emptyFilters, userId: 1 })).toBe(true)
		expect(getUpdatedFilters(emptyFilters, { search: 'Alex' })).toEqual({
			...emptyFilters,
			search: 'Alex',
		})
	})
})
