<template>
  <div class="module-detail-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h2>{{ moduleName }}</h2>
        <a-tag v-if="moduleData" :color="moduleData.enabled ? 'green' : 'gray'">
          {{ moduleData.enabled ? '已启用' : '已禁用' }}
        </a-tag>
      </div>
      <div class="header-right">
        <a-button type="outline" @click="goToSettings">
          <template #icon><icon-settings /></template>
          设置
        </a-button>
        <a-button type="primary" @click="runTask" :loading="running">
          <template #icon><icon-play-arrow /></template>
          立即运行
        </a-button>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="content-area">
      <!-- 左侧：模块信息 -->
      <div class="info-panel">
        <div class="panel-header">模块信息</div>
        <div class="panel-body">
          <a-descriptions :column="1" bordered>
            <a-descriptions-item label="名称">{{ moduleData?.display_name || '-' }}</a-descriptions-item>
            <a-descriptions-item label="描述">{{ moduleData?.description || '-' }}</a-descriptions-item>
            <a-descriptions-item label="状态">
              <a-tag :color="taskStatus?.status === 'running' ? 'blue' : 'gray'">
                {{ taskStatus?.status === 'running' ? '运行中' : '空闲' }}
              </a-tag>
            </a-descriptions-item>
            <a-descriptions-item label="进度">
              <a-progress v-if="taskStatus?.progress > 0" :percent="taskStatus.progress" size="small" />
              <span v-else>-</span>
            </a-descriptions-item>
          </a-descriptions>
        </div>
      </div>

      <!-- 右侧：运行日志 -->
      <div class="log-panel">
        <div class="panel-header">运行日志</div>
        <div class="module-log-content">
          <div v-for="(log, i) in moduleLogs" :key="i" class="log-line">
            <span class="log-time">{{ log.time }}</span>
            <span :class="['log-level', log.level.toLowerCase()]">{{ log.level }}</span>
            <span class="log-msg">{{ log.msg }}</span>
          </div>
          <div v-if="moduleLogs.length === 0" class="log-empty">暂无日志</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useModuleStore } from '@/stores/module'
import * as api from '@/services/api'
import { Message } from '@arco-design/web-vue'
import { IconPlayArrow, IconSettings } from '@arco-design/web-vue/es/icon'

const route = useRoute()
const router = useRouter()
const moduleStore = useModuleStore()

const moduleName = computed(() => route.params.moduleName as string)
const moduleData = computed(() => moduleStore.modules.find((m: any) => m.name === moduleName.value))

const running = ref(false)
const taskStatus = ref<any>(null)
const moduleLogs = ref<Array<{ time: string; level: string; msg: string }>>([])

function goToSettings() {
  router.push({ name: 'module-settings', params: { moduleName: moduleName.value } })
}

async function runTask() {
  running.value = true
  addLog('INFO', '任务开始执行...')

  try {
    const result = await api.runTask(moduleName.value)

    if (result.success) {
      Message.success('任务已启动')
      addLog('INFO', '任务已加入队列')
    } else {
      Message.warning(result.message || '启动失败')
      addLog('WARNING', result.message || '启动失败')
    }
  } catch (e) {
    Message.error('启动失败')
    addLog('ERROR', '启动失败: ' + (e instanceof Error ? e.message : String(e)))
  } finally {
    running.value = false
  }
}

function addLog(level: string, msg: string) {
  const now = new Date()
  const time = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`
  moduleLogs.value.push({ time, level, msg })
}

onMounted(async () => {
  await moduleStore.loadModules()

  // 获取任务状态
  try {
    const tasks = await api.getTasks()
    taskStatus.value = tasks.find((t: any) => t.id === moduleName.value)
  } catch (e) {
    console.error('Failed to fetch task status:', e)
  }

  addLog('INFO', '模块已加载')
})
</script>

<style scoped>
.module-detail-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: var(--color-bg-2);
  border-bottom: 1px solid var(--color-border);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-left h2 {
  margin: 0;
  font-size: 18px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.content-area {
  flex: 1;
  display: flex;
  gap: 0;
  overflow: hidden;
}

.info-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--color-bg-2);
  border-right: 1px solid var(--color-border);
}

.log-panel {
  width: 400px;
  display: flex;
  flex-direction: column;
  background: var(--color-bg-2);
}

.panel-header {
  padding: 12px 16px;
  font-weight: 500;
  border-bottom: 1px solid var(--color-border);
}

.panel-body {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
}

.module-log-content {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  background: #1a1a1a;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 12px;
}

.log-line {
  display: flex;
  gap: 8px;
  line-height: 1.8;
}

.log-time {
  color: #6a6a6a;
  min-width: 65px;
  flex-shrink: 0;
}

.log-level {
  min-width: 50px;
  font-weight: 600;
  flex-shrink: 0;
}

.log-level.info { color: #569cd6; }
.log-level.success { color: #4ec9b0; }
.log-level.warning { color: #dcdcaa; }
.log-level.error { color: #f14c4c; }

.log-msg {
  color: #d4d4d4;
  flex: 1;
  word-break: break-all;
}

.log-empty {
  color: #555;
  text-align: center;
  padding: 20px;
}
</style>
