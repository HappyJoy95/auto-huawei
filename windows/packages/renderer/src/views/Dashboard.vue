<template>
  <div class="dashboard-page">
    <!-- 左侧：控制面板 + 执行池 -->
    <div class="left-panel">
      <!-- 控制按钮 -->
      <div class="control-bar">
        <a-tag :color="schedulerRunning ? 'green' : 'gray'" size="large">
          {{ schedulerRunning ? '调度器运行中' : '调度器已停止' }}
        </a-tag>
        <a-badge :count="runningTaskCount" status="success" />
        <span class="status-hint">运行中</span>
        <a-badge :count="pendingTaskCount" status="warning" />
        <span class="status-hint">排队中</span>
      </div>

      <!-- 执行池摘要 -->
      <div class="pool-tabs">
        <button
          v-for="pool in poolTabs"
          :key="pool.type"
          :class="['pool-tab', { active: activePool === pool.type }]"
          @click="selectPool(pool.type)"
        >
          <div class="pool-tab-title">{{ pool.title }}</div>
          <div class="pool-tab-stats">
            <span>运行 {{ pool.status.running_now.length }}</span>
            <span>排队 {{ pool.status.queue.length }}</span>
            <span>等待 {{ pool.status.waiting.length }}</span>
          </div>
        </button>
      </div>

      <!-- 当前执行池详情 -->
      <div class="pool detail-pool">
        <div class="pool-header">
          <span class="title">{{ activePoolTitle }}</span>
          <span class="pool-limit">并发 {{ activePoolStatus.max_concurrent }}</span>
        </div>
        <div class="pool-content">
          <div class="pool-section">
            <div class="section-header">
              <icon-play-arrow class="icon running-icon" />
              <span>运行中</span>
              <a-badge :count="runningTasks.length" :max-count="99" />
            </div>
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
            <div v-if="runningTasks.length === 0" class="empty compact">
              暂无运行任务
            </div>
          </div>

          <div class="pool-section">
            <div class="section-header">
              <icon-clock-circle class="icon pending-icon" />
              <span>队列中</span>
              <a-badge :count="pendingTasks.length" :max-count="99" />
            </div>
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
            <div v-if="pendingTasks.length === 0" class="empty compact">
              暂无排队任务
            </div>
          </div>

          <div class="pool-section">
            <div class="section-header">
              <icon-check-circle class="icon waiting-icon" />
              <span>等待中</span>
              <a-badge :count="waitingTasks.length" :max-count="99" />
            </div>
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
            <div v-if="waitingTasks.length === 0" class="empty compact">
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
  IconSettings,
  IconClockCircle,
  IconCheckCircle,
  IconFile,
  IconDelete
} from '@arco-design/web-vue/es/icon'

type PoolType = 'simulator' | 'browser' | 'report'
type WaitingTask = { name: string; next_run: string; pool_type?: PoolType }
type PoolStatus = {
  max_concurrent: number
  waiting: WaitingTask[]
  queue: string[]
  running_now: string[]
}

const router = useRouter()
const moduleStore = useModuleStore()
const logContainer = ref<HTMLElement>()

const logs = ref<Array<{ time: string; level: string; msg: string }>>([])

// 调度器状态
const schedulerRunning = ref(false)
const activePool = ref<PoolType>('simulator')
const userSelectedPool = ref(false)
const pools = ref<Record<PoolType, PoolStatus>>({
  simulator: createEmptyPoolStatus(),
  browser: createEmptyPoolStatus(),
  report: createEmptyPoolStatus()
})

function createEmptyPoolStatus(): PoolStatus {
  return { max_concurrent: 1, waiting: [], queue: [], running_now: [] }
}

function normalizePoolStatus(status: any): PoolStatus {
  return {
    max_concurrent: status?.max_concurrent || 1,
    waiting: status?.waiting || [],
    queue: status?.queue || [],
    running_now: status?.running_now || []
  }
}

// 获取模块显示名
function getModuleDisplayName(name: string): string {
  const mod = moduleStore.modules.find((m: any) => m.name === name)
  return mod?.display_name || name
}

const poolTabs = computed(() => [
  { type: 'simulator' as PoolType, title: '模拟器池', status: pools.value.simulator },
  { type: 'browser' as PoolType, title: '浏览器池', status: pools.value.browser },
  { type: 'report' as PoolType, title: '报表池', status: pools.value.report }
])

const activePoolStatus = computed(() => pools.value[activePool.value])

const activePoolTitle = computed(() =>
  poolTabs.value.find(pool => pool.type === activePool.value)?.title || '模拟器池'
)

const runningTaskCount = computed(() =>
  poolTabs.value.reduce((total, pool) => total + pool.status.running_now.length, 0)
)

const pendingTaskCount = computed(() =>
  poolTabs.value.reduce((total, pool) => total + pool.status.queue.length, 0)
)

const runningTasks = computed(() =>
  activePoolStatus.value.running_now.map(name => ({
    name,
    display_name: getModuleDisplayName(name)
  }))
)

const pendingTasks = computed(() =>
  activePoolStatus.value.queue.map(name => ({
    name,
    display_name: getModuleDisplayName(name)
  }))
)

const waitingTasks = computed(() =>
  activePoolStatus.value.waiting.map(item => ({
    name: item.name,
    display_name: getModuleDisplayName(item.name),
    next_run: item.next_run
  }))
)

function selectPool(pool: PoolType) {
  activePool.value = pool
  userSelectedPool.value = true
}

function updateActivePool() {
  // 用户手动选择过池子后，不再自动切换
  if (userSelectedPool.value) {
    return
  }

  const current = pools.value[activePool.value]
  if (current.running_now.length > 0 || current.queue.length > 0) {
    return
  }

  const runningPool = poolTabs.value.find(pool => pool.status.running_now.length > 0)
  if (runningPool) {
    activePool.value = runningPool.type
    return
  }

  const queuedPool = poolTabs.value.find(pool => pool.status.queue.length > 0)
  if (queuedPool) {
    activePool.value = queuedPool.type
  }
}

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
    if (statusData.pools) {
      pools.value = {
        simulator: normalizePoolStatus(statusData.pools.simulator),
        browser: normalizePoolStatus(statusData.pools.browser),
        report: normalizePoolStatus(statusData.pools.report)
      }
    } else {
      pools.value = {
        simulator: normalizePoolStatus({
          waiting: statusData.waiting || [],
          queue: statusData.queue || [],
          running_now: statusData.running_now || []
        }),
        browser: createEmptyPoolStatus(),
        report: createEmptyPoolStatus()
      }
    }
    updateActivePool()

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

.pool-tabs {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
}

.pool-tab {
  border: 1px solid var(--color-border);
  background: var(--color-bg-2);
  border-radius: 8px;
  padding: 8px 10px;
  text-align: left;
  cursor: pointer;
  color: var(--color-text-1);
}

.pool-tab.active {
  border-color: rgb(var(--primary-6));
  background: rgb(var(--primary-1));
}

.pool-tab-title {
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 4px;
}

.pool-tab-stats {
  display: flex;
  gap: 8px;
  color: var(--color-text-3);
  font-size: 11px;
}

.pool {
  background: var(--color-bg-2);
  border-radius: 8px;
  border: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.detail-pool {
  flex: 1;
}

.pool-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-bottom: 1px solid var(--color-border);
  font-weight: 500;
}

.pool-header .title {
  flex: 1;
}

.pool-limit {
  color: var(--color-text-3);
  font-size: 12px;
  font-weight: 400;
}

.pool-content {
  flex: 1;
  padding: 8px;
  overflow-y: auto;
}

.pool-section {
  margin-bottom: 10px;
}

.pool-section:last-child {
  margin-bottom: 0;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--color-text-2);
  font-size: 12px;
  font-weight: 500;
  margin-bottom: 6px;
}

.section-header .icon {
  font-size: 16px;
}

/* 任务项 - 竖排展示 */
.task-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 10px;
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

.empty.compact {
  padding: 6px 0;
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
