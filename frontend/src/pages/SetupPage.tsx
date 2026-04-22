import { useQueryClient } from '@tanstack/react-query'
import type { ComponentProps } from 'react'
import { useEffect, useState } from 'react'

import type { MessageComposerFeedback } from '../components/MessageComposer'
import { MessageComposer } from '../components/MessageComposer'
import { NotificationLogList } from '../components/NotificationLogList'
import {
	getFirstCategoryCode,
	getLoadedNotificationCatalog,
	hasCategoryCode,
} from '../lib/notificationCatalog'
import { useCreateMessageMutation } from '../hooks/useCreateMessageMutation'
import { useNotificationCatalog } from '../hooks/useNotificationCatalog'
import { notificationLogsQueryKey } from '../hooks/useNotificationLogs'
import {
	NotificationLogProvider,
	useNotificationLogState,
} from '../providers/NotificationLogProvider'
import { getAppConfig } from '../services/appConfig'
import {
	ApiRequestError,
	type CreateMessageResponse,
	type MessageCategoryCode,
} from '../services/notificationApi'
import {
	ActivitySnapshot,
	LatestDispatchSummary,
	SetupHero,
} from './SetupPageSections'
import {
	getApiFieldError,
	getCatalogErrorMessage,
	getCatalogStatusMessage,
	getComposerLayoutClassName,
} from './setupPageHelpers'

type FormSubmitEvent = Parameters<
	NonNullable<ComponentProps<'form'>['onSubmit']>
>[0]

export function SetupPage() {
	return (
		<NotificationLogProvider>
			<SetupPageContent />
		</NotificationLogProvider>
	)
}

function SetupPageContent() {
	const { appName } = getAppConfig()
	const queryClient = useQueryClient()
	const createMessageMutation = useCreateMessageMutation()
	const catalogQuery = useNotificationCatalog()
	const {
		totalItems: totalLogItems,
		sentAttempts,
		failedAttempts,
		pendingAttempts,
		resetToFirstPage,
	} = useNotificationLogState()
	const catalog = getLoadedNotificationCatalog(catalogQuery.data)
	const firstCategoryCode = getFirstCategoryCode(catalog.categories)
	const hasCategories = catalog.categories.length > 0
	const catalogErrorMessage = getCatalogErrorMessage(catalogQuery.error)
	const catalogStatusMessage = getCatalogStatusMessage({
		isLoading: catalogQuery.isPending,
		errorMessage: catalogErrorMessage,
		hasCategories,
	})
	const [category, setCategory] = useState<MessageCategoryCode | null>(null)
	const [body, setBody] = useState('')
	const [bodyError, setBodyError] = useState('')
	const [feedback, setFeedback] = useState<MessageComposerFeedback | null>(null)
	const [lastDispatchSummary, setLastDispatchSummary] =
		useState<CreateMessageResponse | null>(null)

	useEffect(() => {
		if (category === null) {
			if (firstCategoryCode === null) {
				return
			}
			setCategory(firstCategoryCode)
			return
		}

		if (hasCategoryCode(catalog.categories, category)) {
			return
		}

		setCategory(firstCategoryCode)
	}, [catalog.categories, category, firstCategoryCode])

	async function handleSubmit(event: FormSubmitEvent): Promise<void> {
		event.preventDefault()

		if (category === null) {
			setFeedback({
				tone: 'error',
				title: 'Submission unavailable',
				detail: 'Message categories are still loading.',
			})
			return
		}

		const normalizedBody = body.trim()
		if (normalizedBody === '') {
			setBodyError('Message body must not be blank.')
			setFeedback(null)
			return
		}

		setBodyError('')
		setFeedback(null)

		try {
			const result = await createMessageMutation.mutateAsync({
				category,
				body: normalizedBody,
			})

			setBody('')
			resetToFirstPage()
			setLastDispatchSummary(result)
			setFeedback({
				tone: 'success',
				title: 'Dispatch recorded',
				detail: `Delivered ${result.sent} of ${result.total_attempts} attempts across ${result.total_users} subscribed users.`,
			})
			await queryClient.invalidateQueries({
				queryKey: notificationLogsQueryKey,
			})
		} catch (error) {
			if (error instanceof ApiRequestError) {
				setBodyError(getApiFieldError(error, 'body'))
				setFeedback({
					tone: 'error',
					title: 'Submission failed',
					detail: error.detail,
				})
				return
			}

			setFeedback({
				tone: 'error',
				title: 'Submission failed',
				detail: 'The message could not be submitted.',
			})
		}
	}

	function handleBodyChange(nextBody: string): void {
		setBody(nextBody)
		if (bodyError !== '') {
			setBodyError('')
		}
	}

	function handleCategoryChange(nextCategory: string): void {
		if (hasCategoryCode(catalog.categories, nextCategory)) {
			setCategory(nextCategory)
		}
	}

	return (
		<main className="relative min-h-screen overflow-hidden bg-[linear-gradient(145deg,#f8f1e6_0%,#dcc09c_52%,#f7f4ef_100%)]">
			<div className="pointer-events-none absolute inset-0 overflow-hidden">
				<div className="animate-float-slow absolute -left-32 -top-24 h-64 w-64 rounded-full bg-amber-200/50 blur-3xl" />
				<div className="animate-float-slow animation-delay-strong absolute -right-20 top-24 h-72 w-72 rounded-full bg-teal-200/45 blur-3xl" />
				<div className="animate-float-slow animation-delay-soft absolute bottom-10 left-1/3 h-80 w-80 rounded-full bg-rose-100/60 blur-3xl" />
			</div>

			<div className="relative mx-auto flex w-full max-w-7xl flex-col gap-6 px-4 py-8 sm:px-6 lg:px-8">
				<section className="grid gap-6 xl:grid-cols-[minmax(0,1.45fr)_380px]">
					<SetupHero appName={appName} channels={catalog.channels} />
					<ActivitySnapshot
						totalLogItems={totalLogItems}
						sentAttempts={sentAttempts}
						failedAttempts={failedAttempts}
						pendingAttempts={pendingAttempts}
					/>
				</section>

				<section className="grid gap-6">
					<div
						className={getComposerLayoutClassName(lastDispatchSummary !== null)}
					>
						<MessageComposer
							categories={catalog.categories}
							selectedCategory={category}
							body={body}
							bodyError={bodyError}
							isSubmitting={createMessageMutation.isPending}
							isSubmitDisabled={!hasCategories}
							catalogStatusMessage={catalogStatusMessage}
							feedback={feedback}
							onCategoryChange={handleCategoryChange}
							onBodyChange={handleBodyChange}
							onSubmit={handleSubmit}
						/>

						{lastDispatchSummary !== null && (
							<LatestDispatchSummary summary={lastDispatchSummary} />
						)}
					</div>

					<NotificationLogList />
				</section>
			</div>
		</main>
	)
}
