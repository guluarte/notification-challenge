import { useQuery } from '@tanstack/react-query'

import {
	getNotificationCatalog,
	type NotificationCatalogResponse,
} from '../services/notificationApi'

export const notificationCatalogQueryKey = ['notification-catalog']

function fetchNotificationCatalog(): Promise<NotificationCatalogResponse> {
	return getNotificationCatalog()
}

export function useNotificationCatalog() {
	return useQuery({
		queryKey: notificationCatalogQueryKey,
		queryFn: fetchNotificationCatalog,
	})
}
