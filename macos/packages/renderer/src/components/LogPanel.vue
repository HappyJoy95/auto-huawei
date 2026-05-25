<template>
  <div class="log-panel">
    <div ref="logContainer" class="log-container">
      <div v-for="(log, i) in logs" :key="log.timestamp || i" class="log-line">
        <span class="log-time">{{ log.time }}</span>
        <span class="log-level" :class="`level-${log.level?.toLowerCase()}`">{{ log.level }}</span>
        <span class="log-msg">{{ log.msg }}</span>
      </div>
      <div v-if="!logs.length" class="log-empty">暂无日志</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, watch } from 'vue'

interface LogEntry {
  time: string
  level: string
  msg: string
  timestamp?: string
}

const props = defineProps<{
  logs: LogEntry[]
}>()

const logContainer = ref<HTMLElement | null>(null)

// 自动滚动到底部
watch(() => props.logs.length, () => {
  nextTick(() => {
    if (logContainer.value) {
      logContainer.value.scrollTop = logContainer.value.scrollHeight
    }
  })
})
</script>

<style scoped>
.log-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.log-container {
  flex: 1;
  overflow-y: auto;
  font-family: monospace;
  font-size: 12px;
  padding: 8px;
  background: var(--color-fill-1);
  border-radius: 4px;
}

.log-line {
  display: flex;
  gap: 8px;
  padding: 2px 0;
  line-height: 1.5;
}

.log-time {
  color: var(--color-text-3);
  flex-shrink: 0;
}

.log-level {
  flex-shrink: 0;
  font-weight: 500;
  min-width: 60px;
}

.level-info { color: var(--color-text-2); }
.level-success { color: rgb(var(--green-6)); }
.level-warning { color: rgb(var(--orange-6)); }
.level-error { color: rgb(var(--red-6)); }

.log-msg {
  color: var(--color-text-1);
  word-break: break-all;
}

.log-empty {
  color: var(--color-text-3);
  text-align: center;
  padding: 20px;
}
</style>
