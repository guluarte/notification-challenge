import {
	createContext,
	type ReactNode,
	useCallback,
	useContext,
	useEffect,
	useMemo,
	useState,
} from 'react'

import { useNotificationLogs } from '../hooks/useNotificationLogs'
import {
	ApiRequestError,
	type LogPageSize,
	type NotificationLogItem,
} from '../services/notificationApi'

const LOG_PAGE_SIZE_OPTIONS: LogPageSize[] = [10, 50, 100]

interface NotificationLogProviderProps {
	children: ReactNode
}

interface NotificationLogContextValue {
	items: NotificationLogItem[]
	isLoading: boolean
	errorMessage: string | null
	isRefreshing: boolean
	pageSize: LogPageSize
	pageSizeOptions: LogPageSize[]
	currentPage: number
	totalPages: number
	totalItems: number
	offset: number
	firstVisibleItem: number
	lastVisibleItem: number
	hasPreviousPage: boolean
	hasNextPage: boolean
	sentAttempts: number
	failedAttempts: number
	pendingAttempts: number
	setPageSize: (pageSize: LogPageSize) => void
	goToPreviousPage: () => void
	goToNextPage: () => void
	refresh: () => void
	resetToFirstPage: () => void
}

const NotificationLogContext =
	createContext<NotificationLogContextValue | null>(null)

function getNotificationLogErrorMessage(error: unknown): string {
	if (error instanceof ApiRequestError) {
		return error.detail
	}

	if (error instanceof Error && error.message.trim() !== '') {
		return error.message
	}

	return 'The log history could not be loaded.'
}

export function NotificationLogProvider({
	children,
}: NotificationLogProviderProps) {
	const [pageSize, setPageSizeState] = useState<LogPageSize>(10)
	const [currentPage, setCurrentPage] = useState(1)
	const offset = (currentPage - 1) * pageSize
	const logsQuery = useNotificationLogs({
		limit: pageSize,
		offset,
	})

	const items: NotificationLogItem[] = logsQuery.data?.items ?? []
	const totalItems = logsQuery.data?.total ?? 0
	const totalPages = Math.max(1, Math.ceil(totalItems / pageSize))
	const firstVisibleItem = totalItems === 0 ? 0 : offset + 1
	const lastVisibleItem = Math.min(offset + items.length, totalItems)
	const hasPreviousPage = currentPage > 1
	const hasNextPage = currentPage < totalPages
	const sentAttempts = items.filter((item) => item.status === 'sent').length
	const failedAttempts = items.filter((item) => item.status === 'failed').length
	const pendingAttempts = items.filter(
		(item) => item.status === 'pending',
	).length
	const errorMessage = logsQuery.isError
		? getNotificationLogErrorMessage(logsQuery.error)
		: null

	useEffect(() => {
		if (currentPage > totalPages) {
			setCurrentPage(totalPages)
		}
	}, [currentPage, totalPages])

	const setPageSize = useCallback((nextPageSize: LogPageSize) => {
		setPageSizeState(nextPageSize)
		setCurrentPage(1)
	}, [])

	const goToPreviousPage = useCallback(() => {
		setCurrentPage((previousPage) => Math.max(1, previousPage - 1))
	}, [])

	const goToNextPage = useCallback(() => {
		setCurrentPage((previousPage) => Math.min(totalPages, previousPage + 1))
	}, [totalPages])

	const refresh = useCallback(() => {
		void logsQuery.refetch()
	}, [logsQuery.refetch])

	const resetToFirstPage = useCallback(() => {
		setCurrentPage(1)
	}, [])

	const value = useMemo<NotificationLogContextValue>(
		() => ({
			items,
			isLoading: logsQuery.isPending,
			errorMessage,
			isRefreshing: logsQuery.isFetching,
			pageSize,
			pageSizeOptions: LOG_PAGE_SIZE_OPTIONS,
			currentPage,
			totalPages,
			totalItems,
			offset,
			firstVisibleItem,
			lastVisibleItem,
			hasPreviousPage,
			hasNextPage,
			sentAttempts,
			failedAttempts,
			pendingAttempts,
			setPageSize,
			goToPreviousPage,
			goToNextPage,
			refresh,
			resetToFirstPage,
		}),
		[
			items,
			logsQuery.isPending,
			logsQuery.isFetching,
			errorMessage,
			pageSize,
			currentPage,
			totalPages,
			totalItems,
			offset,
			firstVisibleItem,
			lastVisibleItem,
			hasPreviousPage,
			hasNextPage,
			sentAttempts,
			failedAttempts,
			pendingAttempts,
			setPageSize,
			goToPreviousPage,
			goToNextPage,
			refresh,
			resetToFirstPage,
		],
	)

	return (
		<NotificationLogContext.Provider value={value}>
			{children}
		</NotificationLogContext.Provider>
	)
}

export function useNotificationLogState(): NotificationLogContextValue {
	const context = useContext(NotificationLogContext)

	if (context === null) {
		throw new Error(
			'useNotificationLogState must be used within NotificationLogProvider.',
		)
	}

	return context
}
