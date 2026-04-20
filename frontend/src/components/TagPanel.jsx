import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader } from '@/components/ui/card'

/**
 * @param {{ title: string; items: string[] }} props
 */
export function TagPanel({ title, items }) {
	return (
		<Card className="border-0 bg-white/74 shadow-[0_18px_60px_rgba(75,46,16,0.1)] ring-1 ring-stone-950/8 backdrop-blur xl:rounded-[2rem]">
			<CardHeader className="pb-3">
				<h2 className="text-lg font-semibold tracking-tight text-stone-950">
					{title}
				</h2>
			</CardHeader>
			<CardContent className="flex flex-wrap gap-2">
				{items.map((item) => (
					<Badge
						key={item}
						variant="outline"
						className="rounded-full border-stone-300 bg-stone-50/90 px-3 py-1 text-stone-700"
					>
						{item}
					</Badge>
				))}
			</CardContent>
		</Card>
	)
}
