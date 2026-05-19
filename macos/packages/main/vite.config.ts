import { defineConfig } from 'vite'
import { resolve } from 'path'

export default defineConfig({
  build: {
    outDir: 'dist',
    lib: {
      entry: resolve(__dirname, 'src/main.ts'),
      formats: ['cjs'],
      fileName: () => 'main.cjs'
    },
    rollupOptions: {
      external: [
        'electron',
        'axios',
        'python-shell',
        'assert', 'buffer', 'child_process', 'cluster', 'console', 'constants',
        'crypto', 'dgram', 'dns', 'domain', 'events', 'fs', 'http', 'https',
        'module', 'net', 'os', 'path', 'perf_hooks', 'process', 'punycode',
        'querystring', 'readline', 'repl', 'stream', 'string_decoder', 'sys',
        'timers', 'tls', 'tty', 'url', 'util', 'v8', 'vm', 'worker_threads', 'zlib'
      ],
      output: {
        entryFileNames: 'main.cjs',
        format: 'cjs',
        interop: 'auto'
      }
    },
    target: 'node18',
    minify: false,
    commonjsOptions: {
      transformMixedEsModules: true
    }
  }
})