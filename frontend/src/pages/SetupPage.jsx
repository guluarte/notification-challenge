import { TagPanel } from '../components/TagPanel'
import { getAppConfig } from '../services/appConfig'

const categories = ['Sports', 'Finance', 'Movies']
const channels = ['SMS', 'E-Mail', 'Push Notification']

export function SetupPage() {
	const { apiBaseUrl, appName } = getAppConfig()

	return (
		<main className="shell">
			<section className="hero">
				<p className="eyebrow">Project Setup</p>
				<h1>{appName}</h1>
				<p className="lede">
					The frontend and backend scaffolds are in place. The next steps can
					build the actual submission form, notification flow, and audit log on
					top of this baseline.
				</p>
			</section>

			<section className="panel">
				<h2>Environment</h2>
				<dl className="facts">
					<div>
						<dt>Frontend</dt>
						<dd>React + Vite</dd>
					</div>
					<div>
						<dt>Backend API</dt>
						<dd>{apiBaseUrl}</dd>
					</div>
				</dl>
			</section>

			<section className="grid">
				<TagPanel items={categories} title="Categories" />
				<TagPanel items={channels} title="Channels" />
			</section>
		</main>
	)
}
