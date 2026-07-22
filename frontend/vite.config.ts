import type { IncomingMessage } from 'node:http'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// '/meetings', '/tasks', '/decisions' i '/briefing' są jednocześnie ścieżkami
// API (proxy do backendu) i client-side route'ami frontendu (np. /meetings/:id).
// Bez tego `bypass` pełne przeładowanie strony (wpisanie adresu, F5) trafiało
// w proxy i backend zwracał surowy JSON zamiast wczytać aplikację React —
// zamiast tego proxy powinno przepuścić tylko wywołania fetch() z już
// wczytanej aplikacji (Accept: */*), a nawigację przeglądarki (Accept:
// text/html) oddać Vite'owi, żeby serwował index.html.
function bypassBrowserNavigation(req: IncomingMessage) {
  if (req.headers.accept?.includes('text/html')) {
    return '/index.html'
  }
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/health': 'http://127.0.0.1:8000',
      '/auth': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/people': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/topics': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/meetings': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        bypass: bypassBrowserNavigation,
      },
      '/tasks': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        bypass: bypassBrowserNavigation,
      },
      '/decisions': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        bypass: bypassBrowserNavigation,
      },
      '/briefing': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        bypass: bypassBrowserNavigation,
      },
    },
  },
})
