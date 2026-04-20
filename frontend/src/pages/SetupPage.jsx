import { useQueryClient } from '@tanstack/react-query'
import { ArrowUpRight, RadioTower, Rows3 } from 'lucide-react'
import { useState } from 'react'

import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { MessageComposer } from '../components/MessageComposer'
import { NotificationLogList } from '../components/NotificationLogList'
import { TagPanel } from '../components/TagPanel'
import {
	notificationCategories,
	notificationChannels,
} from '../constants/notificationCatalog'
import { useCreateMessageMutation } from '../hooks/useCreateMessageMutation'
import {
	notificationLogsQueryKey,
	useNotificationLogs,
} from '../hooks/useNotificationLogs'
import { getAppConfig } from '../services/appConfig'
import { ApiRequestError } from '../services/notificationApi'

/**
 * @typedef {import('../services/notificationApi').CreateMessageResponse} CreateMessageResponse
 * @typedef {import('../services/notificationApi').MessageCategoryCode} MessageCategoryCode
 * @typedef {import('../services/notificationApi').NotificationLogItem} NotificationLogItem
 * @typedef {{ tone: 'success' | 'error'; title: string; detail: string }} FeedbackState
 */

/**
 * @returns {FeedbackState | null}
 */
function createInitialFeedback() {
	return null
}

/**
 * @returns {CreateMessageResponse | null}
 */
function createInitialDispatchSummary() {
	return null
}

/**
 * @param {string} value
 * @returns {value is MessageCategoryCode}
 */
function isMessageCategoryCode(value) {
	return notificationCategories.some(
		(categoryOption) => categoryOption.code === value,
	)
}

/**
 * @param {unknown} error
 * @param {string} fallbackMessage
 * @returns {string}
 */
function getErrorMessage(error, fallbackMessage) {
	if (error instanceof ApiRequestError) {
		return error.detail
	}

	if (error instanceof Error && error.message.trim() !== '') {
		return error.message
	}

	return fallbackMessage
}

export function SetupPage() {
	const { apiBaseUrl, appName } = getAppConfig()
	const queryClient = useQueryClient()
	const logsQuery = useNotificationLogs()
	const createMessageMutation = useCreateMessageMutation()
	/** @type {[MessageCategoryCode, import('react').Dispatch<import('react').SetStateAction<MessageCategoryCode>>]} */
	const [category, setCategory] = useState(notificationCategories[0].code)
	const [body, setBody] = useState('')
	const [bodyError, setBodyError] = useState('')
	const [feedback, setFeedback] = useState(createInitialFeedback)
	const [lastDispatchSummary, setLastDispatchSummary] = useState(
		createInitialDispatchSummary,
	)

	/** @type {NotificationLogItem[]} */
	const logItems = logsQuery.data ?? []
	const sentAttempts = logItems.filter((item) => item.status === 'sent').length
	const failedAttempts = logItems.filter(
		(item) => item.status === 'failed',
	).length
	const pendingAttempts = logItems.filter(
		(item) => item.status === 'pending',
	).length
	const logErrorMessage = logsQuery.isError
		? getErrorMessage(logsQuery.error, 'The log history could not be loaded.')
		: null

	/**
	 * @param {import('react').FormEvent<HTMLFormElement>} event
	 * @returns {Promise<void>}
	 */
	async function handleSubmit(event) {
		event.preventDefault()

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
				setBodyError(error.fieldErrors.body ?? '')
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

	return (
		<main className="relative min-h-screen overflow-hidden bg-[linear-gradient(145deg,#f8f1e6_0%,#dcc09c_52%,#f7f4ef_100%)]">
			<div className="pointer-events-none absolute inset-0 overflow-hidden">
				<div className="animate-float-slow absolute left-[-8rem] top-[-6rem] h-64 w-64 rounded-full bg-amber-200/50 blur-3xl" />
				<div className="animate-float-slow animation-delay-strong absolute right-[-5rem] top-24 h-72 w-72 rounded-full bg-teal-200/45 blur-3xl" />
				<div className="animate-float-slow animation-delay-soft absolute bottom-10 left-1/3 h-80 w-80 rounded-full bg-rose-100/60 blur-3xl" />
			</div>

			<div className="relative mx-auto flex w-full max-w-7xl flex-col gap-6 px-4 py-8 sm:px-6 lg:px-8">
				<section className="grid gap-6 xl:grid-cols-[minmax(0,1.45fr)_380px]">
					<div className="animate-in fade-in-0 slide-in-from-top-4 rounded-[2rem] border border-white/55 bg-white/38 p-6 shadow-[0_28px_100px_rgba(84,52,20,0.14)] backdrop-blur md:p-8">
						<div className="flex flex-wrap items-center gap-3">
							<Badge className="rounded-full bg-stone-950 text-stone-50 shadow-sm">
								Operations console
							</Badge>
							<Badge
								variant="outline"
								className="rounded-full border-stone-300 bg-white/70 text-stone-700"
							>
								Newest first
							</Badge>
							<Badge
								variant="outline"
								className="rounded-full border-stone-300 bg-white/70 text-stone-700"
							>
								Query + Mutation
							</Badge>
						</div>
						<div className="mt-6 space-y-4">
							<h1 className="max-w-3xl text-4xl font-semibold tracking-tight text-stone-950 sm:text-5xl lg:text-6xl">
								{appName}
							</h1>
							<p className="max-w-3xl text-base leading-8 text-stone-700 sm:text-lg">
								Submit category-targeted updates, fan them out through the
								selected channels, and inspect the delivery audit trail from the
								same screen.
							</p>
						</div>
						<div className="mt-8 grid gap-3 sm:grid-cols-3">
							<div className="rounded-[1.5rem] border border-white/60 bg-white/70 p-4 shadow-sm">
								<p className="text-xs font-semibold uppercase tracking-[0.24em] text-stone-500">
									Reads
								</p>
								<p className="mt-3 flex items-center gap-2 text-lg font-semibold text-stone-950">
									<Rows3 className="size-4 text-teal-700" />
									Log history query
								</p>
							</div>
							<div className="rounded-[1.5rem] border border-white/60 bg-white/70 p-4 shadow-sm">
								<p className="text-xs font-semibold uppercase tracking-[0.24em] text-stone-500">
									Writes
								</p>
								<p className="mt-3 flex items-center gap-2 text-lg font-semibold text-stone-950">
									<ArrowUpRight className="size-4 text-amber-700" />
									Message mutation
								</p>
							</div>
							<div className="rounded-[1.5rem] border border-white/60 bg-white/70 p-4 shadow-sm">
								<p className="text-xs font-semibold uppercase tracking-[0.24em] text-stone-500">
									Delivery
								</p>
								<p className="mt-3 flex items-center gap-2 text-lg font-semibold text-stone-950">
									<RadioTower className="size-4 text-rose-700" />
									Per-channel audit
								</p>
							</div>
						</div>
					</div>

					<Card className="animate-in fade-in-0 slide-in-from-top-4 border-0 bg-stone-950 text-stone-50 shadow-[0_28px_100px_rgba(35,20,9,0.2)] xl:rounded-[2rem]">
						<CardHeader className="gap-3">
							<Badge className="w-fit rounded-full bg-white/12 text-stone-50">
								Live snapshot
							</Badge>
							<CardTitle className="text-2xl tracking-tight text-white">
								Current activity
							</CardTitle>
						</CardHeader>
						<CardContent className="grid gap-4">
							<div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
								<div className="rounded-[1.4rem] border border-white/10 bg-white/6 p-4">
									<p className="text-xs font-semibold uppercase tracking-[0.24em] text-stone-400">
										Audit rows
									</p>
									<p className="mt-3 text-4xl font-semibold text-white">
										{logItems.length}
									</p>
								</div>
								<div className="rounded-[1.4rem] border border-white/10 bg-white/6 p-4">
									<p className="text-xs font-semibold uppercase tracking-[0.24em] text-stone-400">
										Sent
									</p>
									<p className="mt-3 text-4xl font-semibold text-white">
										{sentAttempts}
									</p>
								</div>
								<div className="rounded-[1.4rem] border border-white/10 bg-white/6 p-4">
									<p className="text-xs font-semibold uppercase tracking-[0.24em] text-stone-400">
										Failed
									</p>
									<p className="mt-3 text-4xl font-semibold text-white">
										{failedAttempts}
									</p>
								</div>
								<div className="rounded-[1.4rem] border border-white/10 bg-white/6 p-4">
									<p className="text-xs font-semibold uppercase tracking-[0.24em] text-stone-400">
										Pending
									</p>
									<p className="mt-3 text-4xl font-semibold text-white">
										{pendingAttempts}
									</p>
								</div>
							</div>
						</CardContent>
					</Card>
				</section>

				<section className="grid gap-6 xl:grid-cols-[minmax(0,1.5fr)_360px]">
					<div className="grid gap-6">
						<MessageComposer
							categories={notificationCategories}
							selectedCategory={category}
							body={body}
							bodyError={bodyError}
							isSubmitting={createMessageMutation.isPending}
							feedback={feedback}
							onCategoryChange={(nextCategory) => {
								if (isMessageCategoryCode(nextCategory)) {
									setCategory(nextCategory)
								}
							}}
							onBodyChange={(nextBody) => {
								setBody(nextBody)
								if (bodyError !== '') {
									setBodyError('')
								}
							}}
							onSubmit={handleSubmit}
						/>

						<NotificationLogList
							items={logItems}
							isLoading={logsQuery.isPending}
							errorMessage={logErrorMessage}
							isRefreshing={logsQuery.isFetching}
							onRefresh={() => {
								void logsQuery.refetch()
							}}
						/>
					</div>

					<aside className="grid gap-6">
						<Card className="border-0 bg-white/74 shadow-[0_18px_60px_rgba(75,46,16,0.1)] ring-1 ring-stone-950/8 backdrop-blur xl:rounded-[2rem]">
							<CardHeader className="gap-3">
								<Badge
									variant="outline"
									className="w-fit rounded-full border-stone-300 bg-stone-50/90 text-stone-700"
								>
									Runtime
								</Badge>
								<CardTitle className="text-xl tracking-tight text-stone-950">
									Environment
								</CardTitle>
							</CardHeader>
							<CardContent className="grid gap-4 text-sm">
								<div className="rounded-[1.2rem] border border-stone-200/80 bg-stone-50/90 p-4">
									<p className="text-xs font-semibold uppercase tracking-[0.2em] text-stone-500">
										Frontend
									</p>
									<p className="mt-2 font-medium text-stone-900">
										React + Vite + Tailwind + shadcn/ui
									</p>
								</div>
								<div className="rounded-[1.2rem] border border-stone-200/80 bg-stone-50/90 p-4">
									<p className="text-xs font-semibold uppercase tracking-[0.2em] text-stone-500">
										Server state
									</p>
									<p className="mt-2 font-medium text-stone-900">
										TanStack Query
									</p>
								</div>
								<div className="rounded-[1.2rem] border border-stone-200/80 bg-stone-50/90 p-4">
									<p className="text-xs font-semibold uppercase tracking-[0.2em] text-stone-500">
										Backend API
									</p>
									<p className="mt-2 break-all font-medium text-stone-900">
										{apiBaseUrl}
									</p>
								</div>
							</CardContent>
						</Card>

						{lastDispatchSummary ? (
							<Card className="border-0 bg-white/74 shadow-[0_18px_60px_rgba(75,46,16,0.1)] ring-1 ring-stone-950/8 backdrop-blur xl:rounded-[2rem]">
								<CardHeader className="gap-3">
									<Badge className="w-fit rounded-full bg-emerald-100 text-emerald-900">
										Latest dispatch
									</Badge>
									<CardTitle className="text-xl tracking-tight text-stone-950">
										Result summary
									</CardTitle>
								</CardHeader>
								<CardContent className="grid gap-3 text-sm">
									<div className="rounded-[1.2rem] border border-stone-200/80 bg-stone-50/90 p-4">
										<p className="text-xs font-semibold uppercase tracking-[0.2em] text-stone-500">
											Message ID
										</p>
										<p className="mt-2 text-2xl font-semibold text-stone-950">
											{lastDispatchSummary.message_id}
										</p>
									</div>
									<div className="grid gap-3 sm:grid-cols-3 xl:grid-cols-1">
										<div className="rounded-[1.2rem] border border-stone-200/80 bg-stone-50/90 p-4">
											<p className="text-xs font-semibold uppercase tracking-[0.2em] text-stone-500">
												Users
											</p>
											<p className="mt-2 font-medium text-stone-900">
												{lastDispatchSummary.total_users}
											</p>
										</div>
										<div className="rounded-[1.2rem] border border-stone-200/80 bg-stone-50/90 p-4">
											<p className="text-xs font-semibold uppercase tracking-[0.2em] text-stone-500">
												Attempts
											</p>
											<p className="mt-2 font-medium text-stone-900">
												{lastDispatchSummary.total_attempts}
											</p>
										</div>
										<div className="rounded-[1.2rem] border border-stone-200/80 bg-stone-50/90 p-4">
											<p className="text-xs font-semibold uppercase tracking-[0.2em] text-stone-500">
												Sent / Failed
											</p>
											<p className="mt-2 font-medium text-stone-900">
												{lastDispatchSummary.sent} /{' '}
												{lastDispatchSummary.failed}
											</p>
										</div>
									</div>
								</CardContent>
							</Card>
						) : null}

						<div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-1">
							<TagPanel
								items={notificationCategories.map(
									(categoryOption) => categoryOption.label,
								)}
								title="Categories"
							/>
							<TagPanel
								items={notificationChannels.map((channel) => channel.label)}
								title="Channels"
							/>
						</div>
					</aside>
				</section>
			</div>
		</main>
	)
}
