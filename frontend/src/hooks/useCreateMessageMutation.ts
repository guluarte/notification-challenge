import { useMutation } from '@tanstack/react-query'
import { useRef } from 'react'

import {
	submitMessage,
	type CreateMessagePayload,
} from '../services/notificationApi'

interface PendingIdempotencyKey {
	payloadSignature: string
	idempotencyKey: string
}

function createIdempotencyKey(): string {
	if (typeof globalThis.crypto?.randomUUID === 'function') {
		return globalThis.crypto.randomUUID()
	}

	return `message-${Date.now()}-${Math.random().toString(36).slice(2)}`
}

function payloadSignature(payload: CreateMessagePayload): string {
	return `${payload.category}\u0000${payload.body}`
}

export function useCreateMessageMutation() {
	const pendingIdempotencyKey = useRef<PendingIdempotencyKey | null>(null)

	return useMutation({
		mutationFn: (payload: CreateMessagePayload) => {
			const signature = payloadSignature(payload)
			let keyEntry = pendingIdempotencyKey.current

			if (keyEntry?.payloadSignature !== signature) {
				keyEntry = {
					payloadSignature: signature,
					idempotencyKey: payload.idempotencyKey ?? createIdempotencyKey(),
				}
				pendingIdempotencyKey.current = keyEntry
			}

			return submitMessage({
				...payload,
				idempotencyKey: payload.idempotencyKey ?? keyEntry.idempotencyKey,
			})
		},
		onSuccess: () => {
			pendingIdempotencyKey.current = null
		},
	})
}
