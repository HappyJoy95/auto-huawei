<template>
  <div class="tasks-page">
    <a-page-header title="任务管理" subtitle="管理和调度自动化任务" :show-back="false" />

    <a-space direction="vertical" :size="16" style="width: 100%">
      <a-card v-for="task in tasks" :key="task.id" class="task-card">
        <template #title>
          <a-space>
            <a-typography-text strong>{{ task.name }}</a-typography-text>
            <a-tag :color="getStatusColor(task.status)">
              {{ getStatusText(task.status) }}
            </a-tag>
          </a-space>
        </template>

        <template #extra>
          <a-space>
            <a-switch v-model="task.enabled" @change="toggleTask(task.id, $event as boolean)" />
            <a-button
              type="primary"
              size="small"
              :loading="task.status === 'running'"
              @click="runTask(task.id)"
            >
              {{ task.status === 'running' ? '执行中' : '立即执行' }}
            </a-button>
            <a-button
              v-if="task.status === 'running'"
              status="danger"
              size="small"
              @click="stopTask(task.id)"
            >
              停止
            </a-button>
          </a-space>
        </template>

        <!-- 进度条 -->
        <a-progress
          v-if="task.status === 'running'"
          :percent="task.progress"
          :status="task.status === 'error' ? 'danger' : 'normal'"
          style="margin-bottom: 16px"
        />

        <!-- 任务信息 -->
        <a-descriptions :column="4" size="small">
          <a-descriptions-item label="状态">{{ task.message || '-' }}</a-descriptions-item>
          <a-descriptions-item label="上次执行">{{ task.last_run || '-' }}</a-descriptions-item>
          <a-descriptions-item label="下次执行">{{ task.next_run || '-' }}</a-descriptions-item>
        </a-descriptions>
      </a-card>
    </a-space>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

interface Task {
  id: string
  name: string
  status: string
  progress: number
  message: string
  last_run?: string
  next_run?: string
  enabled: boolean
}

const tasks = ref<Task[]>([])

onMounted(async () => {
  await fetchTasks()
})

async function fetchTasks() {
  try {
    const result = await window.api.task.list()
    tasks.value = result
  } catch (e) {
    console.error('获取任务列表失败:', e)
  }
}

async function runTask(taskId: string) {
  try {
    await window.api.task.run(taskId)
    await fetchTasks()
  } catch (e) {
    console.error('运行任务失败:', e)
  }
}

async function stopTask(taskId: string) {
  try {
    await window.api.task.stop(taskId)
    await fetchTasks()
  } catch (e) {
    console.error('停止任务失败:', e)
  }
}

async function toggleTask(taskId: string, enabled: boolean) {
  try {
    if (enabled) {
      await window.api.task.start(taskId)
    } else {
      await window.api.task.stop(taskId)
    }
    await fetchTasks()
  } catch (e) {
    console.error('切换任务状态失败:', e)
  }
}

function getStatusColor(status: string) {
  const colors: Record<string, string> = {
    idle: 'gray',
    running: 'blue',
    paused: 'orange',
    stopped: 'red',
    error: 'red',
    completed: 'green'
  }
  return colors[status] || 'gray'
}

function getStatusText(status: string) {
  const texts: Record<string, string> = {
    idle: '空闲',
    running: '运行中',
    paused: '已暂停',
    stopped: '已停止',
    error: '错误',
    completed: '已完成'
  }
  return texts[status] || status
}
</script>

<style scoped>
.task-card {
  margin-bottom: 0;
}
</style>
