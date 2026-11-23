import { fileURLToPath } from 'node:url'
import { defineConfig } from '@playwright/test'

const root = fileURLToPath(new URL('../', import.meta.url))
const localChrome = process.env.DBMS_TEST_CHROME

export default defineConfig({
  testDir: './e2e',
  use: {
    baseURL: 'http://127.0.0.1:5173',
    channel: localChrome ? 'chrome' : undefined,
  },
  workers: 1,
  webServer: [
    {
      command: 'PYTHONPATH=backend backend/.venv/bin/python -m tests.browser_server',
      cwd: root,
      url: 'http://127.0.0.1:8000/api/v1/health',
      reuseExistingServer: false,
    },
    {
      command: 'npm run dev -- --port 5173 --strictPort',
      url: 'http://127.0.0.1:5173/',
      reuseExistingServer: false,
    },
  ],
})
