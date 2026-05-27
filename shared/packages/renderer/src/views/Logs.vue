<template>
  <div class="logs-page">
    <a-page-header title="日志" subtitle="查看运行日志" :show-back="false" />

    <a-card>
      <template #extra>
        <a-space>
          <a-select v-model="selectedTask" placeholder="选择任务" style="width: 200px">
            <a-option value="all">全部</a-option>
            <a-option value="weekly_media">社媒周报</a-option>
            <a-option value="inspection">点检采集</a-option>
            <a-option value="jddj_orders">京东订单</a-option>
          </a-select>
          <a-button @click="clearLogs">清空</a-button>
          <a-button @click="refreshLogs">刷新</a-button>
        </a-space>
      </template>

      <div class="log-container" ref="logContainer">
        <pre class="log-content">{{ logContent }}</pre>
      </div>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const selectedTask = ref('all')
const logContent = ref('')
const logContainer = ref<HTMLElement | null>(null)

onMounted(async () => {
  await refreshLogs()
})

async function refreshLogs() {
  // TODO: 从后端获取日志
  logContent.value = `[${new Date().toISOString()}] 系统启动\n[${new Date().toISOString()}] Python 后端已启动\n`
}

function clearLogs() {
  logContent.value = ''
}
</script>

<style scoped>
.log-container {
  background: #1e1e1e;
  border-radius: 4px;
  padding: 16px;
  height: 500px;
  overflow: auto;
}

.log-content {
  color: #d4d4d4;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
