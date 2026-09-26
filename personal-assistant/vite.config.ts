import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
export default defineConfig({ base: '/assistant/', plugins: [react()], server: { proxy: { '/pipeline/api/assistant': { target: 'http://127.0.0.1:8080', rewrite: path => path.replace(/^\/pipeline/, '') } } } })
