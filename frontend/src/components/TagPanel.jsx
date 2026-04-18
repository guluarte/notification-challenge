import React from 'react'

/**
 * @param {{ title: string; items: string[] }} props
 */
export function TagPanel({ title, items }) {
	return (
		<article className="panel">
			<h2>{title}</h2>
			<div className="tag-list">
				{items.map((item) => (
					<span key={item} className="tag">
						{item}
					</span>
				))}
			</div>
		</article>
	)
}
