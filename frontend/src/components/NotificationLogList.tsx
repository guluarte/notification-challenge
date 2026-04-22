import {
	ChevronLeft,
	ChevronRight,
	Clock3,
	RefreshCw,
	Search,
	X,
} from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Separator } from '@/components/ui/separator'
import {
	Select,
	SelectContent,
	SelectItem,
	SelectTrigger,
	SelectValue,
} from '@/components/ui/select'
import {
	createLabelsByCode,
	getCategoryLabel,
	getChannelLabel,
	getLoadedNotificationCatalog,
	hasCategoryCode,
	hasChannelCode,
	statusLabelsByCode,
} from '@/lib/notificationCatalog'
import {
	ALL_FILTER_VALUE,
	DELIVERY_STATUS_OPTIONS,
	formatOptionalNumber,
	getDeliveryStatus,
	getFilterSelectValue,
	getUpdatedFilters,
	hasActiveFilters,
	parseLogPageSize,
	parsePositiveInteger,
} from '@/lib/notificationLogFilters'
import { useNotificationCatalog } from '@/hooks/useNotificationCatalog'
import { useNotificationLogState } from '../providers/NotificationLogProvider'
import type {
	DeliveryStatus,
	NotificationLogItem,
	NotificationLogFilters,
} from '../services/notificationApi'

const dateTimeFormatter = new Intl.DateTimeFormat(undefined, {
	dateStyle: 'medium',
	timeStyle: 'short',
})

function formatTimestamp(value: string | null | undefined): string {
	if (!value) {
		return 'Not processed yet'
	}

	return dateTimeFormatter.format(new Date(value))
}

function getStatusClassName(status: DeliveryStatus): string {
	if (status === 'sent') {
		return 'bg-emerald-100 text-emerald-900 ring-1 ring-emerald-900/10'
	}

	if (status === 'failed') {
		return 'bg-red-100 text-red-900 ring-1 ring-red-900/10'
	}

	return 'bg-amber-100 text-amber-900 ring-1 ring-amber-900/10'
}

function getRefreshIconClassName(isRefreshing: boolean): string {
	if (isRefreshing) {
		return 'size-4 animate-spin'
	}
	return 'size-4'
}

function getRefreshButtonLabel(isRefreshing: boolean): string {
	if (isRefreshing) {
		return 'Refreshing...'
	}
	return 'Refresh logs'
}

function getProcessedTimestamp(item: NotificationLogItem): string | null {
	if (item.processed_at !== null) {
		return item.processed_at
	}
	return item.delivered_at
}

function getProviderReferenceLabel(providerReference: string | null): string {
	if (providerReference === null) {
		return 'Not provided'
	}
	return providerReference
}

interface LogPaginationBarProps {
	placement: 'top' | 'bottom'
}

function LogPaginationBar({ placement }: LogPaginationBarProps) {
	const {
		currentPage,
		totalPages,
		totalItems,
		firstVisibleItem,
		lastVisibleItem,
		hasPreviousPage,
		hasNextPage,
		goToPreviousPage,
		goToNextPage,
	} = useNotificationLogState()

	return (
		<nav
			aria-label={`${placement} notification log pagination`}
			className="flex flex-col gap-3 rounded-[1.4rem] border border-stone-200/80 bg-stone-50/80 px-4 py-3 text-sm text-stone-600 sm:flex-row sm:items-center sm:justify-between"
		>
			<p>
				Showing {firstVisibleItem}-{lastVisibleItem} of {totalItems}
			</p>
			<div className="flex items-center gap-2">
				<Button
					type="button"
					variant="outline"
					onClick={goToPreviousPage}
					disabled={!hasPreviousPage}
					className="h-9 rounded-full border-stone-300 bg-white/90 px-3 text-stone-900 hover:bg-stone-100"
				>
					<ChevronLeft className="size-4" />
					Previous
				</Button>
				<span className="min-w-24 text-center font-medium text-stone-900">
					Page {currentPage} of {totalPages}
				</span>
				<Button
					type="button"
					variant="outline"
					onClick={goToNextPage}
					disabled={!hasNextPage}
					className="h-9 rounded-full border-stone-300 bg-white/90 px-3 text-stone-900 hover:bg-stone-100"
				>
					Next
					<ChevronRight className="size-4" />
				</Button>
			</div>
		</nav>
	)
}

export function NotificationLogList() {
	const catalogQuery = useNotificationCatalog()
	const catalog = getLoadedNotificationCatalog(catalogQuery.data)
	const categoryLabelsByCode = createLabelsByCode(catalog.categories)
	const channelLabelsByCode = createLabelsByCode(catalog.channels)
	const {
		items,
		isLoading,
		errorMessage,
		isRefreshing,
		pageSize,
		pageSizeOptions,
		setPageSize,
		filters,
		setFilters,
		clearFilters,
		refresh,
	} = useNotificationLogState()
	const filtersAreActive = hasActiveFilters(filters)

	function updateFilters(patch: Partial<NotificationLogFilters>): void {
		setFilters(getUpdatedFilters(filters, patch))
	}

	function handleCategoryFilterChange(value: string): void {
		if (value === ALL_FILTER_VALUE) {
			updateFilters({ category: null })
			return
		}

		if (hasCategoryCode(catalog.categories, value)) {
			updateFilters({ category: value })
		}
	}

	function handleChannelFilterChange(value: string): void {
		if (value === ALL_FILTER_VALUE) {
			updateFilters({ channel: null })
			return
		}

		if (hasChannelCode(catalog.channels, value)) {
			updateFilters({ channel: value })
		}
	}

	function handleStatusFilterChange(value: string): void {
		if (value === ALL_FILTER_VALUE) {
			updateFilters({ status: null })
			return
		}

		const nextStatus = getDeliveryStatus(value)
		if (nextStatus !== null) {
			updateFilters({ status: nextStatus })
		}
	}

	function handleSearchChange(value: string): void {
		updateFilters({ search: value })
	}

	function handleMessageIdChange(value: string): void {
		updateFilters({ messageId: parsePositiveInteger(value) })
	}

	function handleUserIdChange(value: string): void {
		updateFilters({ userId: parsePositiveInteger(value) })
	}

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
							Reads are backed by a TanStack Query with server-side filters and
							newest-first ordering.
						</CardDescription>
					</div>
					<div className="flex flex-col gap-3 sm:flex-row sm:items-center">
						<div className="flex h-11 items-center gap-2 rounded-full border border-stone-300 bg-white/90 px-3">
							<span className="text-xs font-semibold uppercase text-stone-500">
								Rows
							</span>
							<Select
								value={pageSize.toString()}
								onValueChange={(value) => {
									const nextPageSize = parseLogPageSize(value, pageSizeOptions)
									if (nextPageSize !== null) {
										setPageSize(nextPageSize)
									}
								}}
							>
								<SelectTrigger
									aria-label="Rows per page"
									className="h-8 w-20 rounded-full border-stone-200 bg-stone-50 px-3 text-stone-900 shadow-none"
								>
									<SelectValue />
								</SelectTrigger>
								<SelectContent className="rounded-2xl border-stone-200 bg-white/95 backdrop-blur">
									{pageSizeOptions.map((pageSizeOption) => (
										<SelectItem
											key={pageSizeOption}
											value={pageSizeOption.toString()}
										>
											{pageSizeOption}
										</SelectItem>
									))}
								</SelectContent>
							</Select>
						</div>
						<Button
							type="button"
							variant="outline"
							onClick={refresh}
							disabled={isRefreshing}
							className="h-11 rounded-full border-stone-300 bg-white/90 px-5 text-stone-900 hover:bg-stone-100"
						>
							<RefreshCw className={getRefreshIconClassName(isRefreshing)} />
							{getRefreshButtonLabel(isRefreshing)}
						</Button>
					</div>
				</div>
			</CardHeader>

			<CardContent className="grid gap-4">
				<div className="grid gap-3 rounded-[1.4rem] border border-stone-200/80 bg-white/70 p-4 lg:grid-cols-[minmax(0,1.35fr)_repeat(5,minmax(0,1fr))_auto] lg:items-end">
					<div className="grid gap-2">
						<span className="text-xs font-semibold uppercase text-stone-500">
							Search
						</span>
						<div className="relative">
							<Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-stone-500" />
							<Input
								aria-label="Search logs"
								value={filters.search}
								onChange={(event) => {
									handleSearchChange(event.target.value)
								}}
								className="h-11 rounded-full border-stone-300 bg-white/90 pl-9 text-stone-900 shadow-none"
								placeholder="Message, recipient, provider"
							/>
						</div>
					</div>
					<div className="grid gap-2">
						<span className="text-xs font-semibold uppercase text-stone-500">
							Category
						</span>
						<Select
							value={getFilterSelectValue(filters.category)}
							onValueChange={handleCategoryFilterChange}
						>
							<SelectTrigger
								aria-label="Filter by category"
								className="h-11 rounded-full border-stone-300 bg-white/90 px-3 text-stone-900 shadow-none"
							>
								<SelectValue />
							</SelectTrigger>
							<SelectContent className="rounded-2xl border-stone-200 bg-white/95 backdrop-blur">
								<SelectItem value={ALL_FILTER_VALUE}>All categories</SelectItem>
								{catalog.categories.map((category) => (
									<SelectItem key={category.code} value={category.code}>
										{category.label}
									</SelectItem>
								))}
							</SelectContent>
						</Select>
					</div>
					<div className="grid gap-2">
						<span className="text-xs font-semibold uppercase text-stone-500">
							Channel
						</span>
						<Select
							value={getFilterSelectValue(filters.channel)}
							onValueChange={handleChannelFilterChange}
						>
							<SelectTrigger
								aria-label="Filter by channel"
								className="h-11 rounded-full border-stone-300 bg-white/90 px-3 text-stone-900 shadow-none"
							>
								<SelectValue />
							</SelectTrigger>
							<SelectContent className="rounded-2xl border-stone-200 bg-white/95 backdrop-blur">
								<SelectItem value={ALL_FILTER_VALUE}>All channels</SelectItem>
								{catalog.channels.map((channel) => (
									<SelectItem key={channel.code} value={channel.code}>
										{channel.label}
									</SelectItem>
								))}
							</SelectContent>
						</Select>
					</div>
					<div className="grid gap-2">
						<span className="text-xs font-semibold uppercase text-stone-500">
							Status
						</span>
						<Select
							value={getFilterSelectValue(filters.status)}
							onValueChange={handleStatusFilterChange}
						>
							<SelectTrigger
								aria-label="Filter by status"
								className="h-11 rounded-full border-stone-300 bg-white/90 px-3 text-stone-900 shadow-none"
							>
								<SelectValue />
							</SelectTrigger>
							<SelectContent className="rounded-2xl border-stone-200 bg-white/95 backdrop-blur">
								<SelectItem value={ALL_FILTER_VALUE}>All statuses</SelectItem>
								{DELIVERY_STATUS_OPTIONS.map((status) => (
									<SelectItem key={status} value={status}>
										{statusLabelsByCode[status]}
									</SelectItem>
								))}
							</SelectContent>
						</Select>
					</div>
					<div className="grid gap-2">
						<span className="text-xs font-semibold uppercase text-stone-500">
							Message ID
						</span>
						<Input
							aria-label="Filter by message id"
							type="number"
							min={1}
							value={formatOptionalNumber(filters.messageId)}
							onChange={(event) => {
								handleMessageIdChange(event.target.value)
							}}
							className="h-11 rounded-full border-stone-300 bg-white/90 text-stone-900 shadow-none"
						/>
					</div>
					<div className="grid gap-2">
						<span className="text-xs font-semibold uppercase text-stone-500">
							User ID
						</span>
						<Input
							aria-label="Filter by user id"
							type="number"
							min={1}
							value={formatOptionalNumber(filters.userId)}
							onChange={(event) => {
								handleUserIdChange(event.target.value)
							}}
							className="h-11 rounded-full border-stone-300 bg-white/90 text-stone-900 shadow-none"
						/>
					</div>
					<Button
						type="button"
						variant="outline"
						onClick={clearFilters}
						disabled={!filtersAreActive}
						className="h-11 rounded-full border-stone-300 bg-white/90 px-4 text-stone-900 hover:bg-stone-100"
					>
						<X className="size-4" />
						Clear
					</Button>
				</div>

				<LogPaginationBar placement="top" />

				{errorMessage !== null && (
					<div
						className="animate-in fade-in-0 slide-in-from-bottom-2 rounded-[1.4rem] border border-red-300/70 bg-red-50/90 px-4 py-3 text-red-900 shadow-sm"
						role="alert"
					>
						<p className="font-semibold">Log history unavailable</p>
						<p className="mt-1 text-sm leading-6">{errorMessage}</p>
					</div>
				)}

				{isLoading && items.length === 0 && (
					<div className="rounded-[1.6rem] border border-dashed border-stone-300 bg-stone-100/70 px-6 py-8 text-center">
						<p className="font-medium text-stone-900">Loading activity</p>
						<p className="mt-2 text-sm leading-6 text-stone-500">
							The latest notification attempts are being loaded.
						</p>
					</div>
				)}

				{!isLoading && errorMessage === null && items.length === 0 && (
					<div className="rounded-[1.6rem] border border-dashed border-stone-300 bg-stone-100/70 px-6 py-8 text-center">
						<p className="font-medium text-stone-900">
							No delivery attempts yet
						</p>
						<p className="mt-2 text-sm leading-6 text-stone-500">
							Submit the first message to populate the audit history.
						</p>
					</div>
				)}

				{items.length > 0 && (
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
												{getCategoryLabel(categoryLabelsByCode, item.category)}
											</Badge>
											<Badge
												variant="outline"
												className="border-stone-300 bg-white/90 text-stone-700"
											>
												{getChannelLabel(channelLabelsByCode, item.channel)}
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

								<dl className="grid gap-4 text-sm md:grid-cols-2 xl:grid-cols-4">
									<div className="space-y-1">
										<dt className="text-[0.72rem] font-semibold uppercase tracking-[0.2em] text-stone-500">
											Recipient
										</dt>
										<dd className="space-y-1 text-stone-700">
											<p className="font-medium text-stone-900">
												{item.user.name}
											</p>
											<p className="text-stone-500">ID #{item.user.id}</p>
											<p className="break-all text-stone-500">
												{item.user.email}
											</p>
											<p className="text-stone-500">{item.user.phone_number}</p>
										</dd>
									</div>
									<div className="space-y-1">
										<dt className="text-[0.72rem] font-semibold uppercase tracking-[0.2em] text-stone-500">
											Attempt
										</dt>
										<dd className="text-stone-700">#{item.attempt_id}</dd>
									</div>
									<div className="space-y-1">
										<dt className="text-[0.72rem] font-semibold uppercase tracking-[0.2em] text-stone-500">
											Processed
										</dt>
										<dd className="text-stone-700">
											{formatTimestamp(getProcessedTimestamp(item))}
										</dd>
									</div>
									<div className="space-y-1">
										<dt className="text-[0.72rem] font-semibold uppercase tracking-[0.2em] text-stone-500">
											Provider ref
										</dt>
										<dd className="text-stone-700">
											{getProviderReferenceLabel(item.provider_reference)}
										</dd>
									</div>
								</dl>

								{item.failure_reason !== null && (
									<div className="mt-4 rounded-2xl border border-red-200/80 bg-red-50/80 px-4 py-3 text-sm text-red-900">
										<p className="font-medium">Failure reason</p>
										<p className="mt-1 leading-6">{item.failure_reason}</p>
									</div>
								)}
							</li>
						))}
					</ol>
				)}

				<LogPaginationBar placement="bottom" />
			</CardContent>
		</Card>
	)
}
