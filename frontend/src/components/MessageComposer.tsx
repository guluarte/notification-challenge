import { SendHorizontal, Sparkles } from 'lucide-react'
import type { ComponentProps } from 'react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from '@/components/ui/card'
import {
	Select,
	SelectContent,
	SelectItem,
	SelectTrigger,
	SelectValue,
} from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import type {
	MessageCategoryCode,
	MessageCategoryOption,
} from '../services/notificationApi'

type FormSubmitHandler = NonNullable<ComponentProps<'form'>['onSubmit']>

export interface MessageComposerFeedback {
	tone: 'success' | 'error'
	title: string
	detail: string
}

interface MessageComposerProps {
	categories: MessageCategoryOption[]
	selectedCategory: MessageCategoryCode | null
	body: string
	bodyError?: string
	isSubmitting: boolean
	isSubmitDisabled: boolean
	catalogStatusMessage: string | null
	feedback: MessageComposerFeedback | null
	onCategoryChange: (category: string) => void
	onBodyChange: (body: string) => void
	onSubmit: FormSubmitHandler
}

function getFeedbackClassName(
	feedback: MessageComposerFeedback | null,
): string {
	if (feedback !== null && feedback.tone === 'error') {
		return 'border-red-300/70 bg-red-50/90 text-red-900'
	}
	return 'border-emerald-300/70 bg-emerald-50/90 text-emerald-900'
}

function getSelectedCategoryValue(
	selectedCategory: MessageCategoryCode | null,
): MessageCategoryCode | undefined {
	if (selectedCategory === null) {
		return undefined
	}
	return selectedCategory
}

function getBodyErrorDescriptionId(
	bodyError: string | undefined,
): string | undefined {
	if (bodyError === undefined || bodyError === '') {
		return undefined
	}
	return 'message-body-error'
}

function hasBodyError(bodyError: string | undefined): boolean {
	return bodyError !== undefined && bodyError !== ''
}

function getSubmitButtonLabel(isSubmitting: boolean): string {
	if (isSubmitting) {
		return 'Sending...'
	}
	return 'Send message'
}

export function MessageComposer({
	categories,
	selectedCategory,
	body,
	bodyError,
	isSubmitting,
	isSubmitDisabled,
	catalogStatusMessage,
	feedback,
	onCategoryChange,
	onBodyChange,
	onSubmit,
}: MessageComposerProps) {
	const feedbackClassName = getFeedbackClassName(feedback)
	const selectValue = getSelectedCategoryValue(selectedCategory)
	const bodyErrorVisible = hasBodyError(bodyError)
	const submitButtonLabel = getSubmitButtonLabel(isSubmitting)
	const submitDisabled = isSubmitting || isSubmitDisabled

	return (
		<Card className="overflow-visible border-0 bg-white/75 shadow-[0_24px_90px_rgba(75,46,16,0.12)] ring-1 ring-stone-950/8 backdrop-blur xl:rounded-[2rem]">
			<CardHeader className="gap-4">
				<div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
					<div className="space-y-2">
						<Badge
							variant="secondary"
							className="bg-amber-100 text-amber-900 ring-1 ring-amber-900/10"
						>
							<Sparkles className="size-3.5" />
							Mutation
						</Badge>
						<CardTitle className="text-2xl tracking-tight text-stone-950 sm:text-3xl">
							Dispatch a category update
						</CardTitle>
						<CardDescription className="max-w-2xl text-[0.96rem] leading-7 text-stone-600">
							Compose the notification, validate it locally, and persist each
							delivery attempt independently so one failure does not block the
							rest.
						</CardDescription>
					</div>
					<div className="rounded-3xl border border-stone-200/70 bg-stone-100/70 px-4 py-3 text-sm text-stone-600">
						<p className="font-medium text-stone-900">Submission rules</p>
						<p className="mt-1">
							Blank bodies are rejected before the mutation runs.
						</p>
					</div>
				</div>
			</CardHeader>

			<CardContent>
				<form className="grid gap-5" onSubmit={onSubmit}>
					<div className="grid gap-5 lg:grid-cols-[220px_minmax(0,1fr)]">
						<div className="grid gap-2">
							<label
								className="text-xs font-semibold uppercase tracking-[0.24em] text-stone-500"
								htmlFor="category-trigger"
							>
								Category
							</label>
							<Select
								value={selectValue}
								onValueChange={onCategoryChange}
								disabled={isSubmitDisabled}
							>
								<SelectTrigger
									id="category-trigger"
									aria-label="Category"
									className="h-12 w-full rounded-2xl border-stone-200 bg-white/90 px-4 text-stone-900 shadow-none"
								>
									<SelectValue placeholder="Select a category" />
								</SelectTrigger>
								<SelectContent className="rounded-2xl border-stone-200 bg-white/95 backdrop-blur">
									{categories.map((category) => (
										<SelectItem key={category.code} value={category.code}>
											{category.label}
										</SelectItem>
									))}
								</SelectContent>
							</Select>
						</div>

						<div className="grid gap-2">
							<div className="flex items-center justify-between gap-3">
								<label
									className="text-xs font-semibold uppercase tracking-[0.24em] text-stone-500"
									htmlFor="message"
								>
									Message
								</label>
								<span className="text-xs text-stone-500">
									{body.trim().length} characters
								</span>
							</div>
							<Textarea
								id="message"
								name="body"
								rows={7}
								value={body}
								onChange={(event) => onBodyChange(event.target.value)}
								aria-invalid={bodyErrorVisible}
								aria-describedby={getBodyErrorDescriptionId(bodyError)}
								className="min-h-44 rounded-[1.6rem] border-stone-200 bg-white/90 px-4 py-3 text-base leading-7 text-stone-900 shadow-none placeholder:text-stone-400 focus-visible:border-amber-500 focus-visible:ring-amber-500/20"
								placeholder="Share the update that subscribers should receive."
							/>
							<div className="flex flex-wrap items-center justify-between gap-3">
								<span className="text-sm text-stone-500">
									The audit stream refreshes automatically after a successful
									dispatch.
								</span>
								{bodyErrorVisible && (
									<span
										className="text-sm font-medium text-red-700"
										id="message-body-error"
										role="alert"
									>
										{bodyError}
									</span>
								)}
							</div>
						</div>
					</div>

					{catalogStatusMessage !== null && (
						<div className="rounded-[1.4rem] border border-amber-300/70 bg-amber-50/90 px-4 py-3 text-amber-950 shadow-sm">
							<p className="font-semibold">Catalog status</p>
							<p className="mt-1 text-sm leading-6">{catalogStatusMessage}</p>
						</div>
					)}

					{feedback !== null && (
						<div
							className={`animate-in fade-in-0 slide-in-from-bottom-2 rounded-[1.4rem] border px-4 py-3 shadow-sm ${feedbackClassName}`}
							role="status"
							aria-live="polite"
						>
							<p className="font-semibold">{feedback.title}</p>
							<p className="mt-1 text-sm leading-6">{feedback.detail}</p>
						</div>
					)}

					<div className="flex flex-wrap items-center justify-between gap-4 rounded-[1.5rem] border border-stone-200/70 bg-stone-100/70 px-4 py-4">
						<div>
							<p className="text-sm font-medium text-stone-900">
								Ready to submit
							</p>
							<p className="mt-1 text-sm text-stone-500">
								The backend will fan out by category and channel, then persist
								every attempt.
							</p>
						</div>
						<Button
							type="submit"
							size="lg"
							disabled={submitDisabled}
							className="h-12 rounded-full bg-stone-950 px-6 text-stone-50 hover:bg-stone-800"
						>
							<SendHorizontal className="size-4" />
							{submitButtonLabel}
						</Button>
					</div>
				</form>
			</CardContent>
		</Card>
	)
}
