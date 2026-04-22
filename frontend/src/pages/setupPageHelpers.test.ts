import { describe, expect, it } from 'vitest'

import { ApiRequestError } from '../services/notificationApi'
import {
	getApiFieldError,
	getCatalogErrorMessage,
	getCatalogStatusMessage,
	getComposerLayoutClassName,
} from './setupPageHelpers'

describe('setup page helpers', () => {
	it('selects the composer layout from dispatch summary state', () => {
		expect(getComposerLayoutClassName(true)).toBe(
			'grid items-start gap-6 xl:grid-cols-[minmax(0,1.5fr)_360px]',
		)
		expect(getComposerLayoutClassName(false)).toBe('grid gap-6')
	})

	it('normalizes catalog query errors into display messages', () => {
		expect(
			getCatalogErrorMessage(
				new ApiRequestError({ detail: 'Catalog unavailable.' }),
			),
		).toBe('Catalog unavailable.')
		expect(getCatalogErrorMessage(new Error('Network unavailable.'))).toBe(
			'Network unavailable.',
		)
		expect(getCatalogErrorMessage(new Error('   '))).toBeNull()
		expect(getCatalogErrorMessage('failed')).toBeNull()
	})

	it('returns the current catalog status message', () => {
		expect(
			getCatalogStatusMessage({
				isLoading: true,
				errorMessage: null,
				hasCategories: false,
			}),
		).toBe('Loading categories and channels from the API.')
		expect(
			getCatalogStatusMessage({
				isLoading: false,
				errorMessage: 'Catalog unavailable.',
				hasCategories: false,
			}),
		).toBe('Catalog unavailable.')
		expect(
			getCatalogStatusMessage({
				isLoading: false,
				errorMessage: null,
				hasCategories: false,
			}),
		).toBe('No message categories are available.')
		expect(
			getCatalogStatusMessage({
				isLoading: false,
				errorMessage: null,
				hasCategories: true,
			}),
		).toBeNull()
	})

	it('returns API field errors with an empty fallback', () => {
		const error = new ApiRequestError({
			detail: 'Request validation failed.',
			fieldErrors: {
				body: 'Message body must not be blank.',
			},
		})

		expect(getApiFieldError(error, 'body')).toBe(
			'Message body must not be blank.',
		)
		expect(getApiFieldError(error, 'category')).toBe('')
	})
})
