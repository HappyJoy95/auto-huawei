import { spawn } from 'child_process'
import { createServer } from 'vite'

async function main() {
  // 启动 Vite dev server
  const server = await createServer({
    configFile: 'packages/renderer/vite.config.ts',
    root: process.cwd(),
    server: {
      port: 5173
    }
  })
  await server.listen()
  console.log('[Vite] Dev server running at http://localhost:5173')

  // 构建 main 和 preload
  const buildMain = spawn('npx', ['vite', 'build', '--config', 'packages/main/vite.config.ts', '--watch'], {
    stdio: 'inherit',
    shell: true
  })

  const buildPreload = spawn('npx', ['vite', 'build', '--config', 'packages/preload/vite.config.ts', '--watch'], {
    stdio: 'inherit',
    shell: true
  })

  // 等待初始构建完成
  await new Promise(resolve => setTimeout(resolve, 3000))

  // 启动 Electron
  const electron = spawn('node_modules/electron/dist/electron.exe', ['.'], {
    stdio: 'inherit',
    env: { ...process.env, NODE_ENV: 'development' }
  })

  electron.on('close', () => {
    buildMain.kill()
    buildPreload.kill()
    server.close()
    process.exit()
  })
}

main().catch(console.error)
