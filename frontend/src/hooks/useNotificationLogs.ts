import { useQuery } from '@tanstack/react-query'

import {
	listNotificationLogs,
	type NotificationLogListParams,
	type NotificationLogListResponse,
} from '../services/notificationApi'

export const notificationLogsQueryKey = ['notification-logs']

function fetchNotificationLogs(
	params: NotificationLogListParams,
): Promise<NotificationLogListResponse> {
	return listNotificationLogs(params)
}

export function useNotificationLogs(params: NotificationLogListParams) {
	return useQuery({
		queryKey: [...notificationLogsQueryKey, params],
		queryFn: () => fetchNotificationLogs(params),
		placeholderData: (previousData) => previousData,
	})
}
