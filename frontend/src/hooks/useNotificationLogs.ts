import { useQuery } from '@tanstack/react-query'

import {
	listNotificationLogs,
	type NotificationLogItem,
} from '../services/notificationApi'

export const notificationLogsQueryKey = ['notification-logs']

function fetchNotificationLogs(): Promise<NotificationLogItem[]> {
	return listNotificationLogs()
}

export function useNotificationLogs() {
	return useQuery({
		queryKey: notificationLogsQueryKey,
		queryFn: fetchNotificationLogs,
	})
}
