import { Clock3, RefreshCw } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import {
	categoryLabelsByCode,
	channelLabelsByCode,
	statusLabelsByCode,
} from '@/constants/notificationCatalog'

const dateTimeFormatter = new Intl.DateTimeFormat(undefined, {
	dateStyle: 'medium',
	timeStyle: 'short',
})

/**
 * @typedef {import('../services/notificationApi').NotificationLogItem} NotificationLogItem
 */

/**
 * @param {string | null | undefined} value
 * @returns {string}
 */
function formatTimestamp(value) {
	if (!value) {
		return 'Not processed yet'
	}

	return dateTimeFormatter.format(new Date(value))
}

/**
 * @param {'pending' | 'sent' | 'failed'} status
 * @returns {string}
 */
function getStatusClassName(status) {
	if (status === 'sent') {
		return 'bg-emerald-100 text-emerald-900 ring-1 ring-emerald-900/10'
	}

	if (status === 'failed') {
		return 'bg-red-100 text-red-900 ring-1 ring-red-900/10'
	}

	return 'bg-amber-100 text-amber-900 ring-1 ring-amber-900/10'
}

/**
 * @param {{
 *   items: NotificationLogItem[]
 *   isLoading: boolean
 *   errorMessage: string | null
 *   isRefreshing: boolean
 *   onRefresh: () => void
 * }} props
 */
export function NotificationLogList({
	items,
	isLoading,
	errorMessage,
	isRefreshing,
	onRefresh,
}) {
	return (
		<Card className="border-0 bg-white/78 shadow-[0_24px_90px_rgba(75,46,16,0.12)] ring-1 ring-stone-950/8 backdrop-blur xl:rounded-[2rem]">
			<CardHeader className="gap-4">
				<div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
					<div className="space-y-2">
						<Badge
							variant="secondary"
							className="bg-teal-100 text-teal-900 ring-1 ring-teal-900/10"
						>
							Queries
						</Badge>
						<CardTitle className="text-2xl tracking-tight text-stone-950 sm:text-3xl">
							Notification attempts
						</CardTitle>
						<CardDescription className="max-w-2xl text-[0.96rem] leading-7 text-stone-600">
							Reads are backed by a TanStack Query that keeps the audit history
							sorted from newest to oldest.
						</CardDescription>
					</div>
					<Button
						type="button"
						variant="outline"
						onClick={onRefresh}
						disabled={isRefreshing}
						className="h-11 rounded-full border-stone-300 bg-white/90 px-5 text-stone-900 hover:bg-stone-100"
					>
						<RefreshCw
							className={isRefreshing ? 'size-4 animate-spin' : 'size-4'}
						/>
						{isRefreshing ? 'Refreshing...' : 'Refresh logs'}
					</Button>
				</div>
			</CardHeader>

			<CardContent className="grid gap-4">
				{errorMessage ? (
					<div
						className="animate-in fade-in-0 slide-in-from-bottom-2 rounded-[1.4rem] border border-red-300/70 bg-red-50/90 px-4 py-3 text-red-900 shadow-sm"
						role="alert"
					>
						<p className="font-semibold">Log history unavailable</p>
						<p className="mt-1 text-sm leading-6">{errorMessage}</p>
					</div>
				) : null}

				{isLoading && items.length === 0 ? (
					<div className="rounded-[1.6rem] border border-dashed border-stone-300 bg-stone-100/70 px-6 py-8 text-center">
						<p className="font-medium text-stone-900">Loading activity</p>
						<p className="mt-2 text-sm leading-6 text-stone-500">
							The latest notification attempts are being loaded.
						</p>
					</div>
				) : null}

				{!isLoading && items.length === 0 ? (
					<div className="rounded-[1.6rem] border border-dashed border-stone-300 bg-stone-100/70 px-6 py-8 text-center">
						<p className="font-medium text-stone-900">
							No delivery attempts yet
						</p>
						<p className="mt-2 text-sm leading-6 text-stone-500">
							Submit the first message to populate the audit history.
						</p>
					</div>
				) : null}

				{items.length > 0 ? (
					<ol className="grid gap-4">
						{items.map((item) => (
							<li
								className="animate-in fade-in-0 slide-in-from-bottom-2 rounded-[1.8rem] border border-stone-200/80 bg-stone-50/85 p-5 shadow-sm"
								key={item.attempt_id}
							>
								<div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
									<div className="space-y-3">
										<div className="flex flex-wrap items-center gap-2">
											<Badge
												variant="outline"
												className="border-stone-300 bg-white/90 text-stone-700"
											>
												{categoryLabelsByCode[item.category]}
											</Badge>
											<Badge
												variant="outline"
												className="border-stone-300 bg-white/90 text-stone-700"
											>
												{channelLabelsByCode[item.channel]}
											</Badge>
											<Badge className={getStatusClassName(item.status)}>
												{statusLabelsByCode[item.status]}
											</Badge>
										</div>
										<div>
											<h3 className="text-xl font-semibold tracking-tight text-stone-950">
												{item.body}
											</h3>
											<p className="mt-1 text-sm text-stone-500">
												Attempt {item.attempt_number} for message #
												{item.message_id}
											</p>
										</div>
									</div>
									<div className="inline-flex items-center gap-2 rounded-full bg-white/80 px-3 py-2 text-sm text-stone-600 ring-1 ring-stone-950/8">
										<Clock3 className="size-4 text-stone-500" />
										{formatTimestamp(item.attempted_at)}
									</div>
								</div>

								<Separator className="my-4 bg-stone-200/80" />

								<dl className="grid gap-4 text-sm md:grid-cols-2 xl:grid-cols-5">
									<div className="space-y-1">
										<dt className="text-[0.72rem] font-semibold uppercase tracking-[0.2em] text-stone-500">
											Recipient
										</dt>
										<dd className="space-y-1">
											<p className="font-medium text-stone-900">
												{item.user.name}
											</p>
											<p className="text-stone-500">
												Recipient #{item.user.id}
											</p>
										</dd>
									</div>
									<div className="space-y-1">
										<dt className="text-[0.72rem] font-semibold uppercase tracking-[0.2em] text-stone-500">
											Email
										</dt>
										<dd className="break-all text-stone-700">
											{item.user.email}
										</dd>
									</div>
									<div className="space-y-1">
										<dt className="text-[0.72rem] font-semibold uppercase tracking-[0.2em] text-stone-500">
											Phone
										</dt>
										<dd className="text-stone-700">{item.user.phone_number}</dd>
									</div>
									<div className="space-y-1">
										<dt className="text-[0.72rem] font-semibold uppercase tracking-[0.2em] text-stone-500">
											Processed
										</dt>
										<dd className="text-stone-700">
											{formatTimestamp(item.processed_at ?? item.delivered_at)}
										</dd>
									</div>
									<div className="space-y-1">
										<dt className="text-[0.72rem] font-semibold uppercase tracking-[0.2em] text-stone-500">
											Provider ref
										</dt>
										<dd className="text-stone-700">
											{item.provider_reference ?? 'Not provided'}
										</dd>
									</div>
								</dl>

								{item.failure_reason ? (
									<div className="mt-4 rounded-2xl border border-red-200/80 bg-red-50/80 px-4 py-3 text-sm text-red-900">
										<p className="font-medium">Failure reason</p>
										<p className="mt-1 leading-6">{item.failure_reason}</p>
									</div>
								) : null}
							</li>
						))}
					</ol>
				) : null}
			</CardContent>
		</Card>
	)
}
