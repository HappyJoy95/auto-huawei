import { app, BrowserWindow, ipcMain } from 'electron'
import { join } from 'path'
import { PythonManager } from '@shared-main/python'

let mainWindow: BrowserWindow | null = null
let pythonManager: PythonManager | null = null

const API_BASE = 'http://localhost:5001/api'

async function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 900,
    minHeight: 600,
    webPreferences: {
      preload: join(__dirname, '../../preload/dist/index.cjs'),
      nodeIntegration: false,
      contextIsolation: true
    },
    title: 'Auto Controller',
    show: false
  })

  mainWindow.once('ready-to-show', () => {
    mainWindow?.show()
  })

  // 开发模式加载 dev server，生产模式加载打包文件
  if (process.env.NODE_ENV === 'development') {
    await mainWindow.loadURL('http://localhost:5173')
    mainWindow.webContents.openDevTools()
  } else {
    await mainWindow.loadFile(join(__dirname, '../../renderer/dist/index.html'))
  }
}

async function startPython() {
  pythonManager = new PythonManager()
  await pythonManager.start()
}

function setupIpc() {
  // 任务管理
  ipcMain.handle('task:list', async () => {
    const axios = require('axios')
    const response = await axios.get(`${API_BASE}/tasks`)
    return response.data
  })

  ipcMain.handle('task:run', async (_, taskId: string) => {
    const axios = require('axios')
    const response = await axios.post(`${API_BASE}/tasks/${taskId}/run`)
    return response.data
  })

  ipcMain.handle('task:stop', async (_, taskId: string) => {
    const axios = require('axios')
    const response = await axios.post(`${API_BASE}/tasks/${taskId}/stop`)
    return response.data
  })

  ipcMain.handle('task:start', async (_, taskId: string) => {
    const axios = require('axios')
    const response = await axios.post(`${API_BASE}/tasks/${taskId}/start`)
    return response.data
  })

  // 配置管理
  ipcMain.handle('config:get', async (_, key?: string) => {
    const axios = require('axios')
    const url = key ? `${API_BASE}/config/${key}` : `${API_BASE}/config`
    const response = await axios.get(url)
    return response.data
  })

  ipcMain.handle('config:set', async (_, key: string, value: any) => {
    const axios = require('axios')
    const response = await axios.put(`${API_BASE}/config/${key}`, { value })
    return response.data
  })

  // 数据获取（动态）
  ipcMain.handle('data:get', async (_, moduleName: string, fileName?: string) => {
    const axios = require('axios')
    const url = fileName
      ? `${API_BASE}/data/${moduleName}/${fileName}`
      : `${API_BASE}/data/${moduleName}`
    const response = await axios.get(url)
    return response.data
  })

  // 模块管理
  ipcMain.handle('module:list', async () => {
    const axios = require('axios')
    const response = await axios.get(`${API_BASE}/modules`)
    return response.data
  })

  ipcMain.handle('module:config:get', async (_, moduleName: string) => {
    const axios = require('axios')
    const response = await axios.get(`${API_BASE}/modules/${moduleName}/configs`)
    return response.data
  })

  ipcMain.handle('module:config:save', async (_, moduleName: string, config: any) => {
    const axios = require('axios')
    // 保存调度器配置
    await axios.put(`${API_BASE}/modules/${moduleName}/scheduler-config`, config.scheduler)
    // 保存模块配置
    await axios.put(`${API_BASE}/modules/${moduleName}/module-config`, config.module)
    return { success: true }
  })

  ipcMain.handle('module:style:get', async (_, moduleName: string) => {
    const axios = require('axios')
    const response = await axios.get(`${API_BASE}/modules/${moduleName}/style`)
    return response.data
  })
}

app.whenReady().then(async () => {
  try {
    await startPython()
    setupIpc()
    await createWindow()
  } catch (error) {
    console.error('启动失败:', error)
    app.quit()
  }
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    pythonManager?.stop()
    app.quit()
  }
})

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow()
  }
})
