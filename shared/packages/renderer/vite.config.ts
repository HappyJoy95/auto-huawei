import { createRequire } from 'module'
import { resolve } from 'path'

// 平台根目录：环境变量指定，或使用当前工作目录（npm run 在 windows 目录执行）
const platformRoot = process.env.PLATFORM_ROOT
  ? resolve(process.env.PLATFORM_ROOT)
  : process.cwd()

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
