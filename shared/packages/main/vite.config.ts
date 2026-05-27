import { resolve } from 'path'

const platformRoot = process.cwd()

export default {
  resolve: {
    alias: {
      '@shared-main': resolve(__dirname, 'src')
    }
  },
  build: {
    outDir: resolve(platformRoot, 'packages/main/dist'),
    emptyOutDir: true,
    lib: {
      entry: resolve(platformRoot, 'packages/main/src/main.ts'),
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
}