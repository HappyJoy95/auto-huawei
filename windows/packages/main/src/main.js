const { app, BrowserWindow, ipcMain } = require("electron")
const path = require("path")
const axios = require("axios")

let mainWindow = null

const NODE_ENV = process.env.NODE_ENV || "development"
const API_BASE = "http://127.0.0.1:5001/api"

async function createWindow() {
  console.log("正在创建窗口...")
  console.log("模式:", NODE_ENV)
  console.log("__dirname:", __dirname)

  // 计算正确的 preload 路径
  // __dirname 在构建后是 packages/main/dist/
  // preload 在 packages/preload/dist/index.cjs
  const preloadPath = path.join(__dirname, "../../preload/dist/index.cjs")
  console.log("preload 路径:", preloadPath)

  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 900,
    minHeight: 600,
    webPreferences: {
      preload: preloadPath,
      nodeIntegration: false,
      contextIsolation: true
    },
    title: "Auto Controller"
  })

  if (NODE_ENV === 'development') {
    await mainWindow.loadURL('http://localhost:5173')
  } else {
    await mainWindow.loadFile(path.join(__dirname, '../../../renderer/dist/index.html'))
  }

  console.log("窗口已加载")
}

function setupIpc() {
  ipcMain.handle("task:list", async () => {
    const response = await axios.get(`${API_BASE}/tasks/`)
    return response.data
  })

  ipcMain.handle("task:run", async (_, taskId) => {
    const response = await axios.post(`${API_BASE}/tasks/${taskId}/run`)
    return response.data
  })

  ipcMain.handle("task:stop", async (_, taskId) => {
    const response = await axios.post(`${API_BASE}/tasks/${taskId}/stop`)
    return response.data
  })

  ipcMain.handle("config:get", async (_, key) => {
    const url = key ? `${API_BASE}/config/${key}` : `${API_BASE}/config`
    const response = await axios.get(url)
    return response.data
  })

  ipcMain.handle("config:set", async (_, key, value) => {
    const response = await axios.put(`${API_BASE}/config/${key}`, { value })
    return response.data
  })

  ipcMain.handle("module:list", async () => {
    const response = await axios.get(`${API_BASE}/modules`)
    return response.data
  })

  ipcMain.handle("module:config:get", async (_, moduleName) => {
    const response = await axios.get(`${API_BASE}/modules/${moduleName}/configs`)
    return response.data
  })

  ipcMain.handle("module:config:save", async (_, moduleName, config) => {
    try {
      const results = {}

      if (config.scheduler) {
        const res = await axios.put(`${API_BASE}/modules/${moduleName}/scheduler-config`, config.scheduler)
        results.scheduler = res.data
      }

      if (config.module) {
        const res = await axios.put(`${API_BASE}/modules/${moduleName}/module-config`, config.module)
        results.module = res.data
      }

      return { success: true, ...results }
    } catch (error) {
      console.error('Save config error:', error.message)
      return { success: false, error: error.message }
    }
  })
}

app.whenReady().then(async () => {
  try {
    console.log("Electron 已启动，正在初始化...")
    setupIpc()
    await createWindow()
    console.log("初始化完成！")
  } catch (error) {
    console.error("启动失败:", error)
    app.quit()
  }
})

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit()
  }
})

app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow()
  }
})
