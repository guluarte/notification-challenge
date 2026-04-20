import { QueryClientProvider } from '@tanstack/react-query'
import React from 'react'
import ReactDOM from 'react-dom/client'

import App from './App'
import './index.css'
import { createQueryClient } from './services/queryClient'

const rootElement = document.getElementById('root')
const queryClient = createQueryClient()

if (!rootElement) {
	throw new Error('Root element #root was not found')
}

ReactDOM.createRoot(rootElement).render(
	<React.StrictMode>
		<QueryClientProvider client={queryClient}>
			<App />
		</QueryClientProvider>
	</React.StrictMode>,
)
