import { contextBridge, ipcRenderer } from 'electron'

contextBridge.exposeInMainWorld('electronAPI', {
  // 任务 API
  getTasks: () => ipcRenderer.invoke('task:list'),
  runTask: (taskId: string) => ipcRenderer.invoke('task:run', taskId),
  stopTask: (taskId: string) => ipcRenderer.invoke('task:stop', taskId),

  // 配置 API
  getConfig: (key?: string) => ipcRenderer.invoke('config:get', key),
  setConfig: (key: string, value: any) => ipcRenderer.invoke('config:set', key, value),

  // 通用设置 API
  getGeneralConfig: () => ipcRenderer.invoke('config:get', 'general'),
  saveGeneralConfig: (config: any) => ipcRenderer.invoke('config:set', 'general', config),

  // 模块 API
  getModules: () => ipcRenderer.invoke('module:list'),
  getModuleConfig: (moduleName: string) => ipcRenderer.invoke('module:config:get', moduleName),
  saveModuleConfig: (moduleName: string, config: any) => ipcRenderer.invoke('module:config:save', moduleName, config),
  getModuleStyle: (moduleName: string) => ipcRenderer.invoke('module:style:get', moduleName),

  // 数据 API（动态）
  getModuleData: (moduleName: string, fileName?: string) => ipcRenderer.invoke('data:get', moduleName, fileName)
})
