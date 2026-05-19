<template>
  <div class="modules-page">
    <a-page-header title="模块管理" />
    
    <a-card style="margin-top: 16px">
      <a-row :gutter="16">
        <a-col
          v-for="mod in modules"
          :key="mod.name"
          :span="8"
          style="margin-bottom: 16px"
        >
          <a-card
            hoverable
            class="module-card"
            :class="{ disabled: !mod.enabled }"
          >
            <template #cover>
              <div class="module-icon">
                <icon-apps :size="48" />
              </div>
            </template>
            <a-card-meta
              :title="mod.display_name"
              :description="mod.description"
            >
              <template #title>
                <div class="module-title">
                  <span>{{ mod.display_name }}</span>
                  <a-tag v-if="mod.enabled" color="green">已启用</a-tag>
                  <a-tag v-else color="gray">已禁用</a-tag>
                </div>
              </template>
            </a-card-meta>
            
            <div class="module-actions">
              <a-button
                type="primary"
                size="small"
                @click="openSettings(mod.name)"
              >
                设置
              </a-button>
            </div>
          </a-card>
        </a-col>
      </a-row>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useModuleStore } from '../stores/module'
import { IconApps } from '@arco-design/web-vue/es/icon'

const router = useRouter()
const moduleStore = useModuleStore()
const modules = moduleStore.modules

function openSettings(moduleName: string) {
  router.push({ name: 'module-settings', params: { moduleName } })
}

onMounted(() => {
  moduleStore.loadModules()
})
</script>

<style scoped>
.module-card {
  transition: all 0.3s;
}

.module-card.disabled {
  opacity: 0.6;
}

.module-icon {
  height: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-fill-2);
}

.module-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.module-actions {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--color-border);
}
</style>
