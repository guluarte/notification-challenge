import { ApiRequestError } from '../services/notificationApi'

export function getComposerLayoutClassName(
	hasDispatchSummary: boolean,
): string {
	if (hasDispatchSummary) {
		return 'grid items-start gap-6 xl:grid-cols-[minmax(0,1.5fr)_360px]'
	}
	return 'grid gap-6'
}

export function getCatalogErrorMessage(error: unknown): string | null {
	if (error instanceof ApiRequestError) {
		return error.detail
	}

	if (error instanceof Error && error.message.trim() !== '') {
		return error.message
	}

	return null
}

export function getCatalogStatusMessage({
	isLoading,
	errorMessage,
	hasCategories,
}: {
	isLoading: boolean
	errorMessage: string | null
	hasCategories: boolean
}): string | null {
	if (isLoading) {
		return 'Loading categories and channels from the API.'
	}

	if (errorMessage !== null) {
		return errorMessage
	}

	if (!hasCategories) {
		return 'No message categories are available.'
	}

	return null
}

export function getApiFieldError(
	error: ApiRequestError,
	field: string,
): string {
	const fieldError = error.fieldErrors[field]
	if (fieldError === undefined) {
		return ''
	}
	return fieldError
}
