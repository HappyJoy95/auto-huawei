<template>
  <div class="general-page">
    <div class="page-header">
      <h2>通用设置</h2>
      <span class="subtitle">配置执行器全局参数</span>
    </div>

    <!-- 自动保存悬浮提示 -->
    <Transition name="save-toast">
      <div v-if="saving || lastSaveTime" class="save-toast">
        <span v-if="saving" class="save-toast-text">保存中...</span>
        <span v-else class="save-toast-text success">已自动保存</span>
      </div>
    </Transition>

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
              <a-input-number v-model="config.check_interval" :min="1" :max="60" @change="autoSave">
                <template #suffix>秒</template>
              </a-input-number>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="重试次数">
              <a-input-number v-model="config.retry_count" :min="0" :max="10" @change="autoSave" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-row :gutter="24">
          <a-col :span="12">
            <a-form-item label="任务超时">
              <a-input-number v-model="config.task_timeout" :min="1" :max="120" @change="autoSave">
                <template #suffix>分钟</template>
              </a-input-number>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="并发数">
              <a-input-number v-model="config.concurrency" :min="1" :max="5" @change="autoSave" />
            </a-form-item>
          </a-col>
        </a-row>
      </a-card>

      <!-- 模拟器设置 -->
      <a-card title="模拟器设置" class="config-card">
        <a-row :gutter="24">
          <a-col :span="12">
            <a-form-item label="ADB 地址">
              <a-input v-model="config.adb_address" placeholder="127.0.0.1:16448" @input="autoSave" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="模拟器类型">
              <a-select v-model="config.emulator_type" @change="autoSave">
                <a-option value="mumu">MuMu 模拟器</a-option>
                <a-option value="ldplayer">雷电模拟器</a-option>
                <a-option value="bluestacks">蓝叠模拟器</a-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>
      </a-card>

      <!-- 通知设置 -->
      <a-card title="通知设置" class="config-card">
        <a-form-item label="通知级别">
          <a-select v-model="config.notify_level" style="width: 200px" @change="autoSave">
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
              <a-input v-model="config.smtp_server" placeholder="smtp.qq.com" @input="autoSave" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="SMTP 端口">
              <a-input-number v-model="config.smtp_port" :min="1" :max="65535" style="width: 100%" @change="autoSave" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-row :gutter="24">
          <a-col :span="12">
            <a-form-item label="发件邮箱">
              <a-input v-model="config.smtp_user" placeholder="your@email.com" @input="autoSave" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="授权码">
              <a-input-password v-model="config.smtp_password" placeholder="邮箱授权码" @input="autoSave" />
            </a-form-item>
          </a-col>
        </a-row>
        <div class="form-hint">
          提示：使用QQ邮箱需开启SMTP服务并获取授权码，企业微信通知在模块设置中配置Webhook
        </div>
        <div class="email-test-section">
          <a-button type="outline" @click="testEmail" :loading="testingEmail">
            发送测试邮件
          </a-button>
          <span v-if="testEmailResult" :class="['test-result', testEmailSuccess ? 'success' : 'error']">
            {{ testEmailResult }}
          </span>
        </div>
      </a-card>

      <!-- 企业微信应用配置 -->
      <a-card title="企业微信应用配置" class="config-card">
        <a-row :gutter="24">
          <a-col :span="12">
            <a-form-item label="企业 ID (CorpID)">
              <a-input v-model="config.wechat_corpid" placeholder="ww1234567890" @input="autoSave" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="应用 AgentId">
              <a-input v-model="config.wechat_agentid" placeholder="1000002" @input="autoSave" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-row :gutter="24">
          <a-col :span="12">
            <a-form-item label="应用 Secret">
              <a-input-password v-model="config.wechat_corpsecret" placeholder="应用 Secret" @input="autoSave" />
            </a-form-item>
          </a-col>
        </a-row>
        <div class="form-hint">
          在企业微信管理后台创建自建应用，获取 CorpID、AgentId 和 Secret
        </div>
        <a-divider />
        <a-form-item label="门店→接收人映射">
          <div class="target-mapping">
            <div v-for="(contact, cIdx) in targetContacts" :key="cIdx" class="target-contact">
              <div class="target-contact-header">
                <a-input v-model="contact.userid" placeholder="userid" style="width: 30%" @input="syncTargetContacts" />
                <a-input v-model="contact.name" placeholder="姓名" style="width: 20%" @input="syncTargetContacts" />
                <a-button type="text" status="danger" @click="removeTargetContact(cIdx)">
                  <icon-delete />
                </a-button>
              </div>
              <div class="target-aliases">
                <span class="alias-label">别名：</span>
                <a-tag v-for="(alias, aIdx) in contact.aliases" :key="aIdx" closable @close="removeAlias(cIdx, aIdx)">
                  {{ alias }}
                </a-tag>
                <a-input
                  v-if="contact.addingAlias"
                  size="mini"
                  style="width: 120px"
                  v-model="contact.newAlias"
                  @blur="confirmAlias(cIdx)"
                  @keydown-enter="confirmAlias(cIdx)"
                  autofocus
                />
                <a-button v-else type="dashed" size="mini" @click="startAddAlias(cIdx)">
                  <icon-plus /> 添加别名
                </a-button>
              </div>
            </div>
            <a-button type="dashed" long @click="addTargetContact">
              <icon-plus /> 添加联系人
            </a-button>
          </div>
          <span class="form-hint">同一门店在不同模块可能叫不同名字，添加所有别名即可自动匹配</span>
        </a-form-item>
        <div class="email-test-section">
          <a-button type="outline" @click="testWechatApp" :loading="testingWechatApp">
            发送测试消息
          </a-button>
          <span v-if="testWechatAppResult" :class="['test-result', testWechatAppSuccess ? 'success' : 'error']">
            {{ testWechatAppResult }}
          </span>
        </div>
      </a-card>

      <!-- 日志设置 -->
      <a-card title="日志设置" class="config-card">
        <a-row :gutter="24">
          <a-col :span="12">
            <a-form-item label="日志级别">
              <a-select v-model="config.log_level" @change="autoSave">
                <a-option value="debug">Debug</a-option>
                <a-option value="info">Info</a-option>
                <a-option value="warning">Warning</a-option>
                <a-option value="error">Error</a-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="保留天数">
              <a-input-number v-model="config.log_retention" :min="1" :max="30" @change="autoSave">
                <template #suffix>天</template>
              </a-input-number>
            </a-form-item>
          </a-col>
        </a-row>
      </a-card>
    </a-form>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import * as api from '@/services/api'
import { Message } from '@arco-design/web-vue'
import { IconDelete, IconPlus } from '@arco-design/web-vue/es/icon'

const saving = ref(false)
const testingEmail = ref(false)
const testEmailResult = ref('')
const testEmailSuccess = ref(false)
const testingWechatApp = ref(false)
const testWechatAppResult = ref('')
const testWechatAppSuccess = ref(false)
const lastSaveTime = ref(false)

const config = reactive({
  check_interval: 10,
  retry_count: 3,
  task_timeout: 30,
  concurrency: 1,
  adb_address: '127.0.0.1:16448',
  emulator_type: 'mumu',
  notify_level: 'all',
  smtp_server: 'smtp.qq.com',
  smtp_port: 587,
  smtp_user: '',
  smtp_password: '',
  wechat_corpid: '',
  wechat_corpsecret: '',
  wechat_agentid: '',
  wechat_app_targets: {} as Record<string, any>,
  log_level: 'info',
  log_retention: 7
})

let saveTimer: ReturnType<typeof setTimeout> | null = null

// 门店→接收人映射表（UI 用数组，保存时转对象）
interface TargetContact {
  userid: string
  name: string
  aliases: string[]
  addingAlias: boolean
  newAlias: string
}
const targetContacts = ref<TargetContact[]>([])

function initTargetContacts(targets: Record<string, any>) {
  targetContacts.value = Object.entries(targets).map(([userid, info]) => ({
    userid,
    name: typeof info === 'object' ? (info.name || '') : '',
    aliases: typeof info === 'object' ? (info.aliases || []) : [info],
    addingAlias: false,
    newAlias: ''
  }))
}

function syncTargetContacts() {
  const obj: Record<string, any> = {}
  for (const c of targetContacts.value) {
    if (c.userid) {
      obj[c.userid] = { name: c.name || '', aliases: c.aliases.filter(a => a) }
    }
  }
  config.wechat_app_targets = obj
  autoSave()
}

function addTargetContact() {
  targetContacts.value.push({ userid: '', name: '', aliases: [], addingAlias: false, newAlias: '' })
}

function removeTargetContact(index: number) {
  targetContacts.value.splice(index, 1)
  syncTargetContacts()
}

function startAddAlias(cIdx: number) {
  targetContacts.value[cIdx].addingAlias = true
  targetContacts.value[cIdx].newAlias = ''
}

function confirmAlias(cIdx: number) {
  const contact = targetContacts.value[cIdx]
  if (contact.newAlias && !contact.aliases.includes(contact.newAlias)) {
    contact.aliases.push(contact.newAlias)
  }
  contact.addingAlias = false
  contact.newAlias = ''
  syncTargetContacts()
}

function removeAlias(cIdx: number, aIdx: number) {
  targetContacts.value[cIdx].aliases.splice(aIdx, 1)
  syncTargetContacts()
}

async function loadConfig() {
  try {
    const result = await api.getGeneralConfig()
    if (result?.success && result.config) {
      Object.assign(config, result.config)
      initTargetContacts(config.wechat_app_targets || {})
    }
  } catch (e) {
    console.error('加载配置失败:', e)
  }
}

async function saveConfig() {
  saving.value = true
  try {
    const result = await api.saveGeneralConfig(config)
    if (result?.success) {
      lastSaveTime.value = true
      setTimeout(() => { lastSaveTime.value = false }, 2000)
    }
  } catch (e) {
    Message.error('保存失败')
  } finally {
    saving.value = false
  }
}

function autoSave() {
  if (saveTimer) {
    clearTimeout(saveTimer)
  }
  saveTimer = setTimeout(() => {
    saveConfig()
  }, 500)
}

async function testEmail() {
  testingEmail.value = true
  testEmailResult.value = ''
  try {
    const result = await api.testEmail()
    if (result?.success) {
      testEmailSuccess.value = true
      testEmailResult.value = result.message || '测试邮件发送成功'
      Message.success(testEmailResult.value)
    } else {
      testEmailSuccess.value = false
      testEmailResult.value = result?.detail || '发送失败'
      Message.error(testEmailResult.value)
    }
  } catch (e) {
    testEmailSuccess.value = false
    testEmailResult.value = '请求失败，请检查后端服务'
    Message.error(testEmailResult.value)
  } finally {
    testingEmail.value = false
  }
}

async function testWechatApp() {
  testingWechatApp.value = true
  testWechatAppResult.value = ''
  try {
    const result = await api.testNotify('wechat_app', 'test', true)
    if (result?.success || result?.mock) {
      testWechatAppSuccess.value = true
      testWechatAppResult.value = result.message || '测试消息发送成功'
      Message.success(testWechatAppResult.value)
    } else {
      testWechatAppSuccess.value = false
      testWechatAppResult.value = result?.detail || '发送失败'
      Message.error(testWechatAppResult.value)
    }
  } catch (e) {
    testWechatAppSuccess.value = false
    testWechatAppResult.value = '请求失败，请检查后端服务'
    Message.error(testWechatAppResult.value)
  } finally {
    testingWechatApp.value = false
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
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-header h2 {
  margin: 0;
  font-size: 20px;
}

.subtitle {
  color: var(--color-text-3);
  font-size: 14px;
}

.save-toast {
  position: fixed;
  top: 16px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 999;
  background: var(--color-bg-3);
  border-radius: 6px;
  padding: 8px 16px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  pointer-events: none;
}

.save-toast-text {
  font-size: 13px;
  color: var(--color-text-2);
}

.save-toast-text.success {
  color: rgb(var(--green-6));
}

.save-toast-enter-active,
.save-toast-leave-active {
  transition: all 0.3s ease;
}

.save-toast-enter-from,
.save-toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(-10px);
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

.email-test-section {
  margin-top: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.test-result {
  font-size: 14px;
}

.test-result.success {
  color: var(--color-success-6);
}

.test-result.error {
  color: var(--color-danger-6);
}

.target-mapping {
  width: 100%;
}

.target-contact {
  margin-bottom: 12px;
  padding: 8px;
  border: 1px solid var(--color-border-2);
  border-radius: 4px;
}

.target-contact-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.target-aliases {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.alias-label {
  color: var(--color-text-3);
  font-size: 12px;
}
</style>
