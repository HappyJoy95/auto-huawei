import { spawn } from 'child_process'
import { createServer } from 'vite'
import { join } from 'path'

const electronPath = process.platform === 'darwin'
  ? join('node_modules', 'electron', 'dist', 'Electron.app', 'Contents', 'MacOS', 'Electron')
  : join('node_modules', 'electron', 'dist', 'electron.exe')

async function main() {
  const server = await createServer({
    configFile: '../shared/packages/renderer/vite.config.ts',
    root: process.cwd(),
    server: {
      port: 5173
    }
  })
  await server.listen()
  console.log('[Vite] Dev server running at http://localhost:5173')

  const buildMain = spawn('npx', ['vite', 'build', '--config', '../shared/packages/main/vite.config.ts', '--watch'], {
    stdio: 'inherit',
    shell: true
  })

  const buildPreload = spawn('npx', ['vite', 'build', '--config', '../shared/packages/preload/vite.config.ts', '--watch'], {
    stdio: 'inherit',
    shell: true
  })

  // 等待初始构建完成
  await new Promise(resolve => setTimeout(resolve, 3000))

  const electron = spawn(electronPath, ['.'], {
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
