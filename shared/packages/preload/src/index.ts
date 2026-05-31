import { contextBridge, ipcRenderer } from 'electron'

contextBridge.exposeInMainWorld('api', {
  // 任务 API
  task: {
    list: () => ipcRenderer.invoke('task:list'),
    run: (taskId: string) => ipcRenderer.invoke('task:run', taskId),
    stop: (taskId: string) => ipcRenderer.invoke('task:stop', taskId),
    start: (taskId: string) => ipcRenderer.invoke('task:start', taskId),
  },

  // 配置 API
  config: {
    get: (key?: string) => ipcRenderer.invoke('config:get', key),
    set: (key: string, value: any) => ipcRenderer.invoke('config:set', key, value),
  },

  // 门店 API
  stores: {
    get: () => ipcRenderer.invoke('stores:get'),
    save: (data: any) => ipcRenderer.invoke('stores:save', data),
  },

  // 模块 API
  module: {
    list: () => ipcRenderer.invoke('module:list'),
    getConfig: (moduleName: string) => ipcRenderer.invoke('module:config:get', moduleName),
    saveConfig: (moduleName: string, config: any) => ipcRenderer.invoke('module:config:save', moduleName, config),
    getStyle: (moduleName: string) => ipcRenderer.invoke('module:style:get', moduleName),
    getData: (moduleName: string, fileName?: string) => ipcRenderer.invoke('data:get', moduleName, fileName),
  },

  // 数据 API
  data: {
    get: (moduleName: string, fileName?: string) => ipcRenderer.invoke('data:get', moduleName, fileName),
  },
})

// 兼容旧的 electronAPI 名称
contextBridge.exposeInMainWorld('electronAPI', {
  getTasks: () => ipcRenderer.invoke('task:list'),
  runTask: (taskId: string) => ipcRenderer.invoke('task:run', taskId),
  stopTask: (taskId: string) => ipcRenderer.invoke('task:stop', taskId),
  getConfig: (key?: string) => ipcRenderer.invoke('config:get', key),
  setConfig: (key: string, value: any) => ipcRenderer.invoke('config:set', key, value),
  getGeneralConfig: () => ipcRenderer.invoke('config:get', 'general'),
  saveGeneralConfig: (config: any) => ipcRenderer.invoke('config:set', 'general', config),
  getModules: () => ipcRenderer.invoke('module:list'),
  getModuleConfig: (moduleName: string) => ipcRenderer.invoke('module:config:get', moduleName),
  saveModuleConfig: (moduleName: string, config: any) => ipcRenderer.invoke('module:config:save', moduleName, config),
  getModuleStyle: (moduleName: string) => ipcRenderer.invoke('module:style:get', moduleName),
  getModuleData: (moduleName: string, fileName?: string) => ipcRenderer.invoke('data:get', moduleName, fileName),
})
