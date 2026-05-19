<template>
  <a-config-provider>
    <div class="app-container">
      <!-- 左侧标签栏 -->
      <div class="sidebar">
        <div class="logo">
          <icon-apps />
        </div>

        <div class="nav-items">
          <!-- 总览 -->
          <div
            class="nav-item"
            :class="{ active: currentRoute === 'dashboard' }"
            @click="navigate('dashboard')"
          >
            <icon-home />
            <span>总览</span>
          </div>

          <!-- 通用设置 -->
          <div
            class="nav-item"
            :class="{ active: currentRoute === 'general' }"
            @click="navigate('general')"
          >
            <icon-settings />
            <span>通用设置</span>
          </div>

          <!-- 分隔线 -->
          <div class="nav-divider" />

          <!-- 模块设置列表 -->
          <div
            v-for="mod in moduleStore.modules"
            :key="mod.name"
            class="nav-item"
            :class="{ active: currentRoute === `module-${mod.name}` }"
            @click="navigate(`module-${mod.name}`)"
          >
            <component :is="getModuleIcon(mod.icon)" />
            <span>{{ mod.display_name }}</span>
          </div>
        </div>
      </div>

      <!-- 主内容区 -->
      <div class="main-content">
        <router-view />
      </div>
    </div>
  </a-config-provider>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useModuleStore } from './stores/module'
import {
  IconApps,
  IconHome,
  IconSettings,
  IconUser,
  IconVideoCamera,
  IconBook,
  IconStorage
} from '@arco-design/web-vue/es/icon'

const router = useRouter()
const route = useRoute()
const moduleStore = useModuleStore()

const currentRoute = computed(() => {
  if (route.name === 'module-settings') {
    return `module-${route.params.moduleName}`
  }
  return route.name as string
})

function navigate(key: string) {
  if (key.startsWith('module-')) {
    const moduleName = key.replace('module-', '')
    router.push({ name: 'module-settings', params: { moduleName } })
  } else {
    router.push({ name: key })
  }
}

function getModuleIcon(iconName: string) {
  const iconMap: Record<string, any> = {
    'xiaohongshu': IconBook,
    'douyin': IconVideoCamera,
    'jddj_orders': IconStorage,
    'default': IconUser
  }
  return iconMap[iconName] || iconMap['default']
}

onMounted(() => {
  moduleStore.loadModules()
})
</script>

<style>
html, body, #app {
  height: 100%;
  margin: 0;
  overflow: hidden;
}

.app-container {
  display: flex;
  height: 100%;
  background: var(--color-fill-2);
}

.sidebar {
  width: 80px;
  background: var(--color-bg-2);
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.logo {
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: rgb(var(--primary-6));
  border-bottom: 1px solid var(--color-border);
}

.nav-items {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
}

.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px 8px;
  cursor: pointer;
  color: var(--color-text-2);
  transition: all 0.2s;
  font-size: 12px;
  gap: 4px;
}

.nav-item:hover {
  background: var(--color-fill-2);
  color: var(--color-text-1);
}

.nav-item.active {
  background: rgb(var(--primary-1));
  color: rgb(var(--primary-6));
  border-right: 2px solid rgb(var(--primary-6));
}

.nav-item svg {
  font-size: 20px;
}

.nav-divider {
  height: 1px;
  background: var(--color-border);
  margin: 8px 16px;
}

.main-content {
  flex: 1;
  overflow: hidden;
}
</style>
