import { ref } from 'vue'
import { defineStore } from 'pinia'

export interface ModuleConfig {
  name: string
  display_name: string
  description: string
  icon: string
  enabled: boolean
  has_settings: boolean
  has_task: boolean
  next_run?: string
}

export const useModuleStore = defineStore('module', () => {
  const modules = ref<ModuleConfig[]>([])
  const loading = ref(false)

  async function loadModules() {
    loading.value = true
    try {
      const result = await window.electronAPI.getModules()
      if (result.modules) {
        modules.value = result.modules
      }
    } catch (e) {
      console.error('Failed to load modules:', e)
    } finally {
      loading.value = false
    }
  }

  async function getModuleConfig(moduleName: string) {
    try {
      return await window.electronAPI.getModuleConfig(moduleName)
    } catch (e) {
      console.error('Failed to get module config:', e)
      return {}
    }
  }

  async function saveModuleConfig(moduleName: string, config: any) {
    try {
      return await window.electronAPI.saveModuleConfig(moduleName, config)
    } catch (e) {
      console.error('Failed to save module config:', e)
      return { success: false }
    }
  }

  async function getModuleStyle(moduleName: string) {
    try {
      return await window.electronAPI.getModuleStyle(moduleName)
    } catch (e) {
      console.error('Failed to get module style:', e)
      return { style: null, has_style: false }
    }
  }

  return {
    modules,
    loading,
    loadModules,
    getModuleConfig,
    saveModuleConfig,
    getModuleStyle
  }
})
