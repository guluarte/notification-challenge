import path from 'node:path'

import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

export default defineConfig({
	plugins: [react()],
	resolve: {
		alias: {
			'@': path.resolve(__dirname, './src'),
		},
	},
	test: {
		coverage: {
			exclude: [
				'src/**/*.test.{ts,tsx}',
				'src/test/**',
				'src/vite-env.d.ts',
				'src/main.tsx',
				'src/components/ui/**',
			],
			include: ['src/**/*.{ts,tsx}'],
			provider: 'v8',
			reporter: ['text'],
			thresholds: {
				branches: 80,
				functions: 80,
				lines: 80,
				statements: 80,
			},
		},
		environment: 'jsdom',
		setupFiles: './src/test/setup.ts',
	},
})
