import { useMutation } from '@tanstack/react-query'

import {
	submitMessage,
	type CreateMessagePayload,
	type CreateMessageResponse,
} from '../services/notificationApi'

function createMessage(
	payload: CreateMessagePayload,
): Promise<CreateMessageResponse> {
	return submitMessage(payload)
}

export function useCreateMessageMutation() {
	return useMutation({
		mutationFn: createMessage,
	})
}
