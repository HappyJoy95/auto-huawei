const { contextBridge, ipcRenderer } = require('electron')

const api = {
  // 任务管理
  task: {
    list: () => ipcRenderer.invoke('task:list'),
    run: (taskId) => ipcRenderer.invoke('task:run', taskId),
    stop: (taskId) => ipcRenderer.invoke('task:stop', taskId),
    start: (taskId) => ipcRenderer.invoke('task:start', taskId),
    onStatus: (callback) => {
      ipcRenderer.on('task:status', (_, status) => callback(status))
    },
    offStatus: () => {
      ipcRenderer.removeAllListeners('task:status')
    }
  },

  // 配置管理
  config: {
    get: (key) => ipcRenderer.invoke('config:get', key),
    set: (key, value) => ipcRenderer.invoke('config:set', key, value),
    reload: () => ipcRenderer.invoke('config:reload')
  },

  // 门店管理
  stores: {
    list: () => ipcRenderer.invoke('stores:list'),
    add: (store) => ipcRenderer.invoke('stores:add', store),
    update: (index, store) => ipcRenderer.invoke('stores:update', index, store),
    delete: (index) => ipcRenderer.invoke('stores:delete', index)
  },

  // 数据
  data: {
    xiaohongshu: () => ipcRenderer.invoke('data:xiaohongshu'),
    douyin: () => ipcRenderer.invoke('data:douyin'),
    inspection: () => ipcRenderer.invoke('data:inspection'),
    orders: () => ipcRenderer.invoke('data:orders')
  }
}

contextBridge.exposeInMainWorld('api', api)
