import { app } from 'electron'
import { PythonShell } from 'python-shell'
import { join } from 'path'

export class PythonManager {
  private process: PythonShell | null = null
  private port: number = 5001

  async start(): Promise<void> {
    const modulePath = app.isPackaged
      ? join(process.resourcesPath, 'module')
      : join(process.cwd(), '../shared/module')

    const pythonPath = app.isPackaged
      ? join(process.resourcesPath, 'python/python.exe')
      : this.getDevPythonPath()

    console.log('[Python] Starting...')
    console.log('[Python] Module path:', modulePath)
    console.log('[Python] Python path:', pythonPath)

    return new Promise((resolve, reject) => {
      this.process = new PythonShell('main.py', {
        mode: 'text',
        pythonPath: pythonPath,
        scriptPath: modulePath,
        env: {
          ...process.env,
          PORT: String(this.port),
          PYTHONIOENCODING: 'utf-8'
        }
      })

      this.process.on('message', (message) => {
        console.log('[Python]', message)
        if (message.includes('Uvicorn running')) {
          resolve()
        }
      })

      this.process.on('stderr', (error) => {
        console.error('[Python Error]', error)
      })

      this.process.on('error', (error) => {
        console.error('[Python Process Error]', error)
        reject(error)
      })

      // 5秒超时
      setTimeout(() => resolve(), 5000)
    })
  }

  async stop(): Promise<void> {
    if (this.process) {
      console.log('[Python] Stopping...')
      this.process.terminate()
      this.process = null
    }
  }

  private getDevPythonPath(): string {
    // 开发环境使用项目虚拟环境
    const venvPath = join(process.cwd(), 'venv')
    if (process.platform === 'win32') {
      return join(venvPath, 'Scripts/python.exe')
    }
    return join(venvPath, 'bin/python')
  }
}
