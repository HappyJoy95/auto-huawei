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
        <div class="email-test-section">
          <a-button type="outline" @click="testWechatApp" :loading="testingWechatApp">
            发送测试消息
          </a-button>
          <span v-if="testWechatAppResult" :class="['test-result', testWechatAppSuccess ? 'success' : 'error']">
            {{ testWechatAppResult }}
          </span>
        </div>
      </a-card>

      <!-- 门店信息管理 -->
      <a-card class="config-card">
        <template #title>
          <a-space>
            <span>门店信息管理</span>
            <a-tag color="blue">{{ stores.length }} 个门店</a-tag>
          </a-space>
        </template>
        <template #extra>
          <a-space>
            <a-button type="primary" @click="showAddStore">
              <template #icon><icon-plus /></template>
              添加门店
            </a-button>
            <a-button @click="saveStores" :loading="savingStores">保存门店</a-button>
          </a-space>
        </template>

        <a-table :data="stores" :pagination="{ pageSize: 10 }" :scroll="{ x: 900 }">
          <template #columns>
            <a-table-column title="门店名称" data-index="name" :width="220" />
            <a-table-column title="简称" data-index="short_name" :width="120" />
            <a-table-column title="门店代码" data-index="code" :width="120" />
            <a-table-column title="企微接收人" data-index="wechat_userids" :width="180">
              <template #cell="{ record }">
                <span v-if="record.wechat_userids?.length">{{ record.wechat_userids.join(', ') }}</span>
                <span v-else class="empty-text">-</span>
              </template>
            </a-table-column>
            <a-table-column title="别称" data-index="aliases" :width="180">
              <template #cell="{ record }">
                <span v-if="record.aliases?.length">{{ record.aliases.join(', ') }}</span>
                <span v-else class="empty-text">-</span>
              </template>
            </a-table-column>
            <a-table-column title="操作" :width="140" fixed="right">
              <template #cell="{ rowIndex }">
                <a-space>
                  <a-button size="small" @click="editStore(rowIndex)">编辑</a-button>
                  <a-popconfirm content="确定删除？" @ok="deleteStore(rowIndex)">
                    <a-button size="small" status="danger">删除</a-button>
                  </a-popconfirm>
                </a-space>
              </template>
            </a-table-column>
          </template>
        </a-table>
        <div class="form-hint store-hint">
          门店代码供巡检模块使用；企微接收人和别称供企业微信应用按门店匹配推送使用。
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

    <a-modal v-model:visible="storeModalVisible" :title="editingStoreIndex >= 0 ? '编辑门店' : '添加门店'" @ok="saveStore" @cancel="closeStoreModal" :width="520">
      <a-form :model="editingStore" layout="vertical">
        <a-form-item label="门店名称" required>
          <a-input v-model="editingStore.name" placeholder="杭州萧山机场华为授权体验店" />
        </a-form-item>
        <a-form-item label="简称">
          <a-input v-model="editingStore.short_name" placeholder="萧山机场店" />
        </a-form-item>
        <a-form-item label="门店代码">
          <a-input v-model="editingStore.code" placeholder="SCN123456" />
        </a-form-item>
        <a-form-item label="企微接收人">
          <a-input-tag v-model="editingStore.wechat_userids" placeholder="输入 userid 后回车添加" />
          <template #extra>
            <span class="form-hint">企业微信应用推送时的接收人 userid</span>
          </template>
        </a-form-item>
        <a-form-item label="别称">
          <a-input-tag v-model="editingStore.aliases" placeholder="输入别称后回车添加" />
          <template #extra>
            <span class="form-hint">用于匹配订单、巡检、月报等模块中的门店名</span>
          </template>
        </a-form-item>
      </a-form>
    </a-modal>
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
  log_level: 'info',
  log_retention: 7
})

let saveTimer: ReturnType<typeof setTimeout> | null = null

interface StoreInfo {
  name: string
  short_name: string
  code: string
  wechat_userids: string[]
  aliases: string[]
}

const stores = ref<StoreInfo[]>([])
const savingStores = ref(false)
const storeModalVisible = ref(false)
const editingStoreIndex = ref(-1)
const editingStore = reactive<StoreInfo>({
  name: '',
  short_name: '',
  code: '',
  wechat_userids: [],
  aliases: []
})

function resetEditingStore() {
  Object.assign(editingStore, { name: '', short_name: '', code: '', wechat_userids: [], aliases: [] })
}

async function loadStores() {
  try {
    const result = await api.getStores()
    stores.value = (result?.stores || []).map((store: Partial<StoreInfo>) => ({
      name: store.name || '',
      short_name: store.short_name || '',
      code: store.code || '',
      wechat_userids: Array.isArray(store.wechat_userids) ? store.wechat_userids : [],
      aliases: Array.isArray(store.aliases) ? store.aliases : []
    }))
  } catch (e) {
    console.error('加载门店失败:', e)
  }
}

function showAddStore() {
  editingStoreIndex.value = -1
  resetEditingStore()
  storeModalVisible.value = true
}

function editStore(index: number) {
  editingStoreIndex.value = index
  Object.assign(editingStore, JSON.parse(JSON.stringify(stores.value[index])))
  storeModalVisible.value = true
}

function closeStoreModal() {
  storeModalVisible.value = false
}

function saveStore() {
  if (!editingStore.name.trim()) {
    Message.warning('请输入门店名称')
    return
  }

  const store = JSON.parse(JSON.stringify(editingStore))
  if (editingStoreIndex.value >= 0) {
    stores.value[editingStoreIndex.value] = store
  } else {
    stores.value.push(store)
  }
  storeModalVisible.value = false
}

function deleteStore(index: number) {
  stores.value.splice(index, 1)
}

async function saveStores() {
  savingStores.value = true
  try {
    const result = await api.saveStores({ stores: stores.value })
    if (result?.success) {
      Message.success('门店信息已保存')
    }
  } catch (e) {
    Message.error('门店信息保存失败')
  } finally {
    savingStores.value = false
  }
}

async function loadConfig() {
  try {
    const result = await api.getGeneralConfig()
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
  loadStores()
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

.store-hint {
  margin-top: 12px;
  margin-left: 0;
}

.empty-text {
  color: var(--color-text-4);
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
