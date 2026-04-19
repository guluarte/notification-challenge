import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

export default defineConfig({
	plugins: [react()],
	esbuild: {
		jsx: 'automatic',
		jsxImportSource: 'react',
	},
	test: {
		environment: 'jsdom',
		setupFiles: './src/test/setup.js',
	},
})
