import react from '@vitejs/plugin-react'
import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vite'

const projectRoot = fileURLToPath(new URL('..', import.meta.url))

// Dev: `npm run dev` proxies the API to serve.py (python run_all.py). Prod: `npm run build` -> dist/, served by serve.py.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: { '/api': 'http://127.0.0.1:8765' },
    fs: { allow: [projectRoot] }, // styles import ../ui-handoff/tokens.css
  },
})
