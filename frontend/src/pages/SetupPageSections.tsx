import { ArrowUpRight, RadioTower, Rows3 } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import type {
	CreateMessageResponse,
	NotificationChannelOption,
} from '../services/notificationApi'

interface SetupHeroProps {
	appName: string
	channels: NotificationChannelOption[]
}

interface ActivitySnapshotProps {
	totalLogItems: number
	sentAttempts: number
	failedAttempts: number
	pendingAttempts: number
}

export function SetupHero({ appName, channels }: SetupHeroProps) {
	return (
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
					Submit category-targeted updates, fan them out through the selected
					channels, and inspect the delivery audit trail from the same screen.
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
			<div className="mt-6 rounded-[1.5rem] border border-white/60 bg-white/70 p-4 shadow-sm">
				<p className="text-xs font-semibold uppercase tracking-[0.24em] text-stone-500">
					Channels
				</p>
				<div className="mt-3 flex flex-wrap gap-2">
					{channels.map((channel) => (
						<Badge
							key={channel.code}
							variant="outline"
							className="rounded-full border-stone-300 bg-white/90 px-3 py-1 text-stone-700"
						>
							{channel.label}
						</Badge>
					))}
				</div>
			</div>
		</div>
	)
}

export function ActivitySnapshot({
	totalLogItems,
	sentAttempts,
	failedAttempts,
	pendingAttempts,
}: ActivitySnapshotProps) {
	return (
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
					<SnapshotMetric label="Audit rows" value={totalLogItems} />
					<SnapshotMetric label="Sent" value={sentAttempts} />
					<SnapshotMetric label="Failed" value={failedAttempts} />
					<SnapshotMetric label="Pending" value={pendingAttempts} />
				</div>
			</CardContent>
		</Card>
	)
}

function SnapshotMetric({ label, value }: { label: string; value: number }) {
	return (
		<div className="rounded-[1.4rem] border border-white/10 bg-white/6 p-4">
			<p className="text-xs font-semibold uppercase tracking-[0.24em] text-stone-400">
				{label}
			</p>
			<p className="mt-3 text-4xl font-semibold text-white">{value}</p>
		</div>
	)
}

export function LatestDispatchSummary({
	summary,
}: {
	summary: CreateMessageResponse
}) {
	return (
		<aside className="self-start">
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
							{summary.message_id}
						</p>
					</div>
					<div className="grid gap-3 sm:grid-cols-3 xl:grid-cols-1">
						<SummaryMetric label="Users" value={summary.total_users} />
						<SummaryMetric label="Attempts" value={summary.total_attempts} />
						<SummaryMetric
							label="Sent / Failed"
							value={`${summary.sent} / ${summary.failed}`}
						/>
					</div>
				</CardContent>
			</Card>
		</aside>
	)
}

function SummaryMetric({
	label,
	value,
}: {
	label: string
	value: number | string
}) {
	return (
		<div className="rounded-[1.2rem] border border-stone-200/80 bg-stone-50/90 p-4">
			<p className="text-xs font-semibold uppercase tracking-[0.2em] text-stone-500">
				{label}
			</p>
			<p className="mt-2 font-medium text-stone-900">{value}</p>
		</div>
	)
}
