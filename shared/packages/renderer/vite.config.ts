import { createRequire } from 'module'
import { resolve } from 'path'

const platformRoot = process.cwd()
const require = createRequire(resolve(platformRoot, 'package.json'))
const vue = require('@vitejs/plugin-vue')

export default {
  plugins: [vue()],
  root: __dirname,
  base: './',
  build: {
    outDir: resolve(platformRoot, 'packages/renderer/dist'),
    emptyOutDir: true,
    rollupOptions: {
      input: resolve(__dirname, 'index.html')
    }
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
      '@platform': resolve(platformRoot, 'packages/renderer/src'),
      'vue': resolve(platformRoot, 'node_modules/vue'),
      'vue-router': resolve(platformRoot, 'node_modules/vue-router'),
      'pinia': resolve(platformRoot, 'node_modules/pinia'),
      '@arco-design/web-vue': resolve(platformRoot, 'node_modules/@arco-design/web-vue'),
      '@arco-design/web-vue/es/icon': resolve(platformRoot, 'node_modules/@arco-design/web-vue/es/icon')
    }
  }
}
