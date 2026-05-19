<template>
  <div class="general-page">
    <div class="page-header">
      <h2>通用设置</h2>
      <span class="subtitle">配置执行器全局参数</span>
    </div>

    <a-form
      :model="config"
      layout="vertical"
      class="config-form"
    >
      <!-- 调度器设置 -->
      <a-card title="调度器设置" class="config-card">
        <a-row :gutter="24">
          <a-col :span="12">
            <a-form-item label="检查间隔">
              <a-input-number v-model="config.checkInterval" :min="1" :max="60">
                <template #suffix>秒</template>
              </a-input-number>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="重试次数">
              <a-input-number v-model="config.retryCount" :min="0" :max="10" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-row :gutter="24">
          <a-col :span="12">
            <a-form-item label="任务超时">
              <a-input-number v-model="config.taskTimeout" :min="1" :max="120">
                <template #suffix>分钟</template>
              </a-input-number>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="并发数">
              <a-input-number v-model="config.concurrency" :min="1" :max="5" />
            </a-form-item>
          </a-col>
        </a-row>
      </a-card>

      <!-- 模拟器设置 -->
      <a-card title="模拟器设置" class="config-card">
        <a-row :gutter="24">
          <a-col :span="12">
            <a-form-item label="ADB 地址">
              <a-input v-model="config.adbAddress" placeholder="127.0.0.1:16448" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="模拟器类型">
              <a-select v-model="config.emulatorType">
                <a-option value="mumu">MuMu 模拟器</a-option>
                <a-option value="ldplayer">雷电模拟器</a-option>
                <a-option value="bluestacks">蓝叠模拟器</a-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="无头模式">
          <a-switch v-model="config.headless" />
          <span class="form-hint">开启后模拟器窗口不显示</span>
        </a-form-item>
      </a-card>

      <!-- 通知设置 -->
      <a-card title="通知设置" class="config-card">
        <a-form-item label="通知级别">
          <a-select v-model="config.notifyLevel" style="width: 200px">
            <a-option value="all">全部通知</a-option>
            <a-option value="error">仅错误</a-option>
            <a-option value="none">不通知</a-option>
          </a-select>
          <span class="form-hint">控制模块执行完成时是否发送通知</span>
        </a-form-item>
      </a-card>

      <!-- 邮箱配置 -->
      <a-card title="邮箱配置" class="config-card">
        <a-row :gutter="24">
          <a-col :span="12">
            <a-form-item label="SMTP 服务器">
              <a-input v-model="config.smtpServer" placeholder="smtp.qq.com" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="SMTP 端口">
              <a-input-number v-model="config.smtpPort" :min="1" :max="65535" style="width: 100%" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-row :gutter="24">
          <a-col :span="12">
            <a-form-item label="发件邮箱">
              <a-input v-model="config.smtpUser" placeholder="your@email.com" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="授权码">
              <a-input-password v-model="config.smtpPassword" placeholder="邮箱授权码" />
            </a-form-item>
          </a-col>
        </a-row>
        <div class="form-hint">
          提示：使用QQ邮箱需开启SMTP服务并获取授权码，企业微信通知在模块设置中配置Webhook
        </div>
      </a-card>

      <!-- 日志设置 -->
      <a-card title="日志设置" class="config-card">
        <a-row :gutter="24">
          <a-col :span="12">
            <a-form-item label="日志级别">
              <a-select v-model="config.logLevel">
                <a-option value="debug">Debug</a-option>
                <a-option value="info">Info</a-option>
                <a-option value="warning">Warning</a-option>
                <a-option value="error">Error</a-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="保留天数">
              <a-input-number v-model="config.logRetention" :min="1" :max="30">
                <template #suffix>天</template>
              </a-input-number>
            </a-form-item>
          </a-col>
        </a-row>
      </a-card>

      <!-- 保存按钮 -->
      <div class="form-actions">
        <a-button type="primary" size="large" @click="saveConfig" :loading="saving">
          保存设置
        </a-button>
      </div>
    </a-form>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { Message } from '@arco-design/web-vue'

const saving = ref(false)

const config = reactive({
  checkInterval: 10,
  retryCount: 3,
  taskTimeout: 30,
  concurrency: 1,
  adbAddress: '127.0.0.1:16448',
  emulatorType: 'mumu',
  headless: true,
  notifyLevel: 'all',
  smtpServer: 'smtp.qq.com',
  smtpPort: 465,
  smtpUser: '',
  smtpPassword: '',
  logLevel: 'info',
  logRetention: 7
})

async function loadConfig() {
  try {
    const response = await fetch('http://127.0.0.1:5001/api/config/general')
    const result = await response.json()
    if (result?.success && result.config) {
      Object.assign(config, result.config)
    }
  } catch (e) {
    console.error('加载配置失败:', e)
  }
}

async function saveConfig() {
  saving.value = true
  try {
    const response = await fetch('http://127.0.0.1:5001/api/config/general', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    })
    const result = await response.json()
    if (result?.success) {
      Message.success('保存成功')
    } else {
      Message.error('保存失败')
    }
  } catch (e) {
    Message.error('保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadConfig()
})
</script>

<style scoped>
.general-page {
  height: 100%;
  overflow-y: auto;
  padding: 24px;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0;
  font-size: 20px;
}

.subtitle {
  color: var(--color-text-3);
  font-size: 14px;
}

.config-form {
  max-width: 800px;
}

.config-card {
  margin-bottom: 16px;
}

.form-hint {
  margin-left: 12px;
  color: var(--color-text-3);
  font-size: 12px;
}

.form-actions {
  margin-top: 24px;
}
</style>
