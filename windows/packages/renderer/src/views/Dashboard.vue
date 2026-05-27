<template>
  <div class="dashboard-page">
    <!-- 左侧：控制面板 + 模块池 -->
    <div class="left-panel">
      <!-- 控制按钮 -->
      <div class="control-bar">
        <a-tag :color="schedulerRunning ? 'green' : 'gray'" size="large">
          {{ schedulerRunning ? '调度器运行中' : '调度器已停止' }}
        </a-tag>
        <a-badge :count="runningTasks.length" status="success" />
        <span class="status-hint">运行中</span>
        <a-badge :count="pendingTasks.length" status="warning" />
        <span class="status-hint">排队中</span>
      </div>

      <!-- 三个模块池（竖排） -->
      <div class="pools-container">
        <!-- 运行中 -->
        <div class="pool running">
          <div class="pool-header">
            <icon-play-arrow class="icon running-icon" />
            <span class="title">运行中</span>
            <a-badge :count="runningTasks.length" :max-count="99" />
          </div>
          <div class="pool-content">
            <div
              v-for="task in runningTasks"
              :key="task.name"
              class="task-item running"
            >
              <div class="task-info">
                <span class="task-name">{{ task.display_name }}</span>
                <span class="task-status">执行中...</span>
              </div>
              <a-button size="mini" type="text" @click="goToSettings(task.name)">
                <template #icon><icon-settings /></template>
              </a-button>
            </div>
            <div v-if="runningTasks.length === 0" class="empty">
              暂无运行任务
            </div>
          </div>
        </div>

        <!-- 队列中 -->
        <div class="pool pending">
          <div class="pool-header">
            <icon-clock-circle class="icon pending-icon" />
            <span class="title">队列中</span>
            <a-badge :count="pendingTasks.length" :max-count="99" />
          </div>
          <div class="pool-content">
            <div
              v-for="task in pendingTasks"
              :key="task.name"
              class="task-item pending"
            >
              <div class="task-info">
                <span class="task-name">{{ task.display_name }}</span>
                <span class="task-status">等待执行</span>
              </div>
              <a-button size="mini" type="text" @click="goToSettings(task.name)">
                <template #icon><icon-settings /></template>
              </a-button>
            </div>
            <div v-if="pendingTasks.length === 0" class="empty">
              暂无排队任务
            </div>
          </div>
        </div>

        <!-- 等待中 -->
        <div class="pool waiting">
          <div class="pool-header">
            <icon-check-circle class="icon waiting-icon" />
            <span class="title">等待中</span>
            <a-badge :count="waitingTasks.length" :max-count="99" />
          </div>
          <div class="pool-content">
            <div
              v-for="task in waitingTasks"
              :key="task.name"
              class="task-item waiting"
            >
              <div class="task-info">
                <span class="task-name">{{ task.display_name }}</span>
                <span class="task-next">下次运行: {{ getNextRun(task) }}</span>
              </div>
              <a-button size="mini" type="text" @click="goToSettings(task.name)">
                <template #icon><icon-settings /></template>
              </a-button>
            </div>
            <div v-if="waitingTasks.length === 0" class="empty">
              暂无等待任务
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧：日志面板 -->
    <div class="right-panel">
      <div class="log-header">
        <icon-file />
        <span>运行日志</span>
        <a-button size="mini" type="text" @click="clearLogs">
          <template #icon><icon-delete /></template>
        </a-button>
      </div>
      <div class="log-content" ref="logContainer">
        <div
          v-for="(log, i) in logs"
          :key="i"
          class="log-line"
        >
          <span class="log-time">{{ log.time }}</span>
          <span :class="['log-level', log.level.toLowerCase()]">{{ log.level }}</span>
          <span class="log-msg">{{ log.msg }}</span>
        </div>
        <div v-if="logs.length === 0" class="log-empty">
          暂无日志
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useModuleStore } from '@/stores/module'
import * as api from '@/services/api'
import {
  IconPlayArrow,
  IconPause,
  IconSettings,
  IconClockCircle,
  IconCheckCircle,
  IconFile,
  IconDelete
} from '@arco-design/web-vue/es/icon'

const router = useRouter()
const moduleStore = useModuleStore()
const logContainer = ref<HTMLElement>()

const logs = ref<Array<{ time: string; level: string; msg: string }>>([])

// 调度器状态
const schedulerRunning = ref(false)
const waitingList = ref<Array<{ name: string; next_run: string }>>([])
const queueList = ref<string[]>([])
const runningList = ref<string[]>([])

// 获取模块显示名
function getModuleDisplayName(name: string): string {
  const mod = moduleStore.modules.find((m: any) => m.name === name)
  return mod?.display_name || name
}

// 任务列表
const waitingTasks = computed(() => {
  return waitingList.value.map(item => ({
    name: item.name,
    display_name: getModuleDisplayName(item.name),
    next_run: item.next_run
  }))
})

const pendingTasks = computed(() => {
  return queueList.value.map(name => ({
    name,
    display_name: getModuleDisplayName(name)
  }))
})

const runningTasks = computed(() => {
  return runningList.value.map(name => ({
    name,
    display_name: getModuleDisplayName(name)
  }))
})

function getNextRun(task: any): string {
  if (!task.next_run) {
    return '未设置'
  }

  const next = new Date(task.next_run)
  const month = String(next.getMonth() + 1).padStart(2, '0')
  const day = String(next.getDate()).padStart(2, '0')
  const hour = String(next.getHours()).padStart(2, '0')
  const min = String(next.getMinutes()).padStart(2, '0')
  const sec = String(next.getSeconds()).padStart(2, '0')
  return `${month}-${day} ${hour}:${min}:${sec}`
}

async function fetchSchedulerStatus() {
  try {
    const [statusData, logsData] = await Promise.all([
      api.getSchedulerStatus(),
      api.getLogs(100)
    ])

    schedulerRunning.value = statusData.running
    waitingList.value = statusData.waiting || []
    queueList.value = statusData.queue || []
    runningList.value = statusData.running_now || []

    // 更新日志
    if (logsData.logs) {
      const newLogs = logsData.logs.map((log: any) => ({
        time: log.time,
        level: log.level,
        msg: log.msg
      }))

      // 检查是否有新日志（比较最后一条的时间戳）
      const lastNewLog = newLogs[newLogs.length - 1]
      const lastOldLog = logs.value[logs.value.length - 1]
      const hasNewLogs = !lastOldLog ||
        (lastNewLog && (
          lastNewLog.time !== lastOldLog.time ||
          lastNewLog.msg !== lastOldLog.msg
        ))

      if (hasNewLogs) {
        logs.value = newLogs
        nextTick(() => {
          if (logContainer.value) {
            logContainer.value.scrollTop = logContainer.value.scrollHeight
          }
        })
      }
    }
  } catch (e) {
    console.error('Failed to fetch:', e)
  }
}

let pollTimer: number | null = null

function startPolling() {
  fetchSchedulerStatus()
  pollTimer = window.setInterval(fetchSchedulerStatus, 1000)
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

function goToSettings(name: string) {
  router.push({ name: 'module-settings', params: { moduleName: name } })
}

function clearLogs() {
  logs.value = []
}

onMounted(() => {
  moduleStore.loadModules()
  startPolling()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.dashboard-page {
  display: flex;
  height: 100%;
  gap: 0;
}

/* 左侧面板 */
.left-panel {
  width: 320px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  padding: 16px;
  overflow: hidden;
}

/* 控制栏 */
.control-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}

.status-hint {
  font-size: 12px;
  color: var(--color-text-3);
}

/* 模块池容器 */
.pools-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow: hidden;
}

.pool {
  background: var(--color-bg-2);
  border-radius: 8px;
  border: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  flex: none;
}

.pool-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-bottom: 1px solid var(--color-border);
  font-weight: 500;
}

.pool-header .icon {
  font-size: 18px;
}

.pool-header .title {
  flex: 1;
}

.pool-content {
  flex: 1;
  padding: 8px;
  overflow-y: auto;
}

/* 任务项 - 竖排展示 */
.task-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  background: var(--color-fill-1);
  border-radius: 6px;
  margin-bottom: 6px;
}

.task-item:last-child {
  margin-bottom: 0;
}

.task-item.running {
  background: rgb(var(--success-1));
  border-left: 3px solid rgb(var(--success-6));
}

.task-item.pending {
  background: rgb(var(--warning-1));
  border-left: 3px solid rgb(var(--warning-6));
}

.task-item.waiting {
  background: var(--color-fill-1);
  border-left: 3px solid rgb(var(--primary-6));
}

.task-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.task-name {
  font-size: 13px;
  font-weight: 500;
}

.task-status,
.task-next {
  font-size: 11px;
  color: var(--color-text-3);
}

.empty {
  color: var(--color-text-3);
  font-size: 12px;
  text-align: center;
  padding: 16px;
}

/* 图标颜色 */
.running-icon {
  color: rgb(var(--success-6));
}

.pending-icon {
  color: rgb(var(--warning-6));
}

.waiting-icon {
  color: rgb(var(--primary-6));
}

/* 右侧日志面板 */
.right-panel {
  flex: 1;
  background: var(--color-bg-2);
  border-left: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.log-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--color-border);
  font-weight: 500;
}

.log-header .arco-btn {
  margin-left: auto;
}

.log-content {
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
  flex-shrink: 0;
}

.log-level {
  flex-shrink: 0;
  width: 50px;
  font-weight: 600;
}

.log-level.info {
  color: #569cd6;
}

.log-level.success {
  color: #4ec9b0;
}

.log-level.warning {
  color: #dcdcaa;
}

.log-level.error {
  color: #f14c4c;
}

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
