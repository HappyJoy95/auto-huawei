/**
 * 统一 API 服务层
 * 所有后端 API 调用统一通过此模块，走 Electron IPC 通道
 */

const API_BASE = 'http://127.0.0.1:5001/api'

/** 通用请求封装 */
async function request<T = any>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${url}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail || `请求失败: ${response.status}`)
  }
  return response.json()
}

// ===== 调度器 API =====

export async function getSchedulerStatus() {
  return request('/scheduler/status')
}

export async function getTaskStatus(moduleName: string) {
  return request(`/scheduler/task/${moduleName}`)
}

export async function runTaskNow(moduleName: string, mode: string = 'normal') {
  return request(`/scheduler/task/${moduleName}/run-now?mode=${mode}`)
}

export async function setManualTime(moduleName: string, time: string) {
  return request(`/scheduler/task/${moduleName}/manual-time`, {
    method: 'POST',
    body: JSON.stringify({ time })
  })
}

// ===== 任务 API =====

export async function getTasks() {
  return request('/tasks')
}

export async function runTask(taskId: string) {
  return request(`/tasks/${taskId}/run`, { method: 'POST' })
}

export async function stopTask(taskId: string) {
  return request(`/tasks/${taskId}/stop`, { method: 'POST' })
}

// ===== 配置 API =====

export async function getGeneralConfig() {
  return request('/config/general')
}

export async function saveGeneralConfig(config: Record<string, any>) {
  return request('/config/general', {
    method: 'PUT',
    body: JSON.stringify(config)
  })
}

export async function testEmail() {
  return request('/config/test-email', { method: 'POST' })
}

// ===== 日志 API =====

export async function getLogs(limit: number = 100) {
  return request(`/logs?limit=${limit}`)
}

// ===== 模块 API（通过 IPC） =====

export const modules = {
  async list() {
    return window.electronAPI.getModules()
  },

  async getConfig(moduleName: string) {
    return window.electronAPI.getModuleConfig(moduleName)
  },

  async saveConfig(moduleName: string, config: any) {
    return window.electronAPI.saveModuleConfig(moduleName, config)
  },

  async getStyle(moduleName: string) {
    return window.electronAPI.getModuleStyle(moduleName)
  },

  async getData(moduleName: string, fileName?: string) {
    return window.electronAPI.getModuleData(moduleName, fileName)
  }
}
