<template>
  <div class="config-page">
    <a-page-header title="配置管理" subtitle="编辑任务和系统配置" :show-back="false" />

    <a-tabs v-model:active-key="activeTab">
      <!-- 门店配置 -->
      <a-tab-pane key="stores" title="门店管理">
        <a-card>
          <template #title>
            <a-space>
              <span>门店列表</span>
              <a-tag color="blue">{{ stores.length }} 个门店</a-tag>
            </a-space>
          </template>
          <template #extra>
            <a-space>
              <a-button type="primary" @click="showAddStore">
                <template #icon><icon-plus /></template>
                添加门店
              </a-button>
              <a-button @click="saveStores" :loading="saving">
                保存配置
              </a-button>
            </a-space>
          </template>

          <a-table :data="stores" :pagination="{ pageSize: 10 }" :scroll="{ x: 800 }">
            <template #columns>
              <a-table-column title="门店名称" data-index="name" :width="180" />
              <a-table-column title="简称" data-index="short_name" :width="100" />
              <a-table-column title="编码" data-index="code" :width="100" />
              <a-table-column title="抖音链接" data-index="douyin_url" :width="300" ellipsis />
              <a-table-column title="操作" :width="120" fixed="right">
                <template #cell="{ record, rowIndex }">
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
        </a-card>
      </a-tab-pane>

      <!-- 京东账号配置 -->
      <a-tab-pane key="jddj" title="京东到家">
        <a-card title="京东到家账号配置">
          <a-form :model="jddjConfig" layout="horizontal" :label-col-props="{ span: 4 }" :wrapper-col-props="{ span: 16 }">
            <a-form-item label="用户名">
              <a-input v-model="jddjConfig.username" placeholder="京东到家用户名" />
            </a-form-item>
            <a-form-item label="密码">
              <a-input-password v-model="jddjConfig.password" placeholder="京东到家密码" />
            </a-form-item>
            <a-form-item label="检查间隔">
              <a-input-number v-model="jddiConfig.interval" :min="1" :max="60">
                <template #suffix>分钟</template>
              </a-input-number>
            </a-form-item>
            <a-form-item label="无头模式">
              <a-switch v-model="jddiConfig.headless" />
              <a-typography-text type="secondary" style="margin-left: 8px">
                开启后浏览器后台运行
              </a-typography-text>
            </a-form-item>
            <a-form-item label="监控状态">
              <a-checkbox-group v-model="jddjConfig.target_status">
                <a-checkbox value="待接单">待接单</a-checkbox>
                <a-checkbox value="待打印">待打印</a-checkbox>
              </a-checkbox-group>
            </a-form-item>
            <a-form-item :wrapper-col-props="{ offset: 4 }">
              <a-button type="primary" @click="saveJddjConfig" :loading="saving">保存配置</a-button>
            </a-form-item>
          </a-form>
        </a-card>
      </a-tab-pane>

      <!-- 通知配置 -->
      <a-tab-pane key="notification" title="通知设置">
        <a-row :gutter="16">
          <a-col :span="12">
            <a-card title="企业微信">
              <a-form :model="wechatConfig" layout="vertical">
                <a-form-item label="Webhook URL">
                  <a-input v-model="wechatConfig.webhook_url" placeholder="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx" />
                </a-form-item>
                <a-form-item>
                  <a-button type="primary" @click="saveWechatConfig" :loading="saving">保存</a-button>
                  <a-button style="margin-left: 8px" @click="testWechat">测试发送</a-button>
                </a-form-item>
              </a-form>
            </a-card>
          </a-col>
          <a-col :span="12">
            <a-card title="邮件通知">
              <a-form :model="emailConfig" layout="vertical">
                <a-form-item label="SMTP 服务器">
                  <a-input v-model="emailConfig.smtp_server" placeholder="smtp.qq.com" />
                </a-form-item>
                <a-form-item label="端口">
                  <a-input-number v-model="emailConfig.smtp_port" :min="1" :max="65535" />
                </a-form-item>
                <a-form-item label="发件邮箱">
                  <a-input v-model="emailConfig.sender_email" placeholder="xxx@qq.com" />
                </a-form-item>
                <a-form-item label="授权码">
                  <a-input-password v-model="emailConfig.sender_password" placeholder="邮箱授权码" />
                </a-form-item>
                <a-form-item label="收件邮箱">
                  <a-input v-model="emailConfig.receiver_email" placeholder="xxx@qq.com" />
                </a-form-item>
                <a-form-item>
                  <a-button type="primary" @click="saveEmailConfig" :loading="saving">保存</a-button>
                </a-form-item>
              </a-form>
            </a-card>
          </a-col>
        </a-row>
      </a-tab-pane>

      <!-- 模拟器配置 -->
      <a-tab-pane key="emulator" title="模拟器">
        <a-card title="MuMu 模拟器配置">
          <a-form :model="emulatorConfig" layout="horizontal" :label-col-props="{ span: 4 }" :wrapper-col-props="{ span: 16 }">
            <a-form-item label="ADB 端口">
              <a-input v-model="emulatorConfig.adb_port" placeholder="127.0.0.1:16448" />
            </a-form-item>
            <a-form-item :wrapper-col-props="{ offset: 4 }">
              <a-button type="primary" @click="saveEmulatorConfig" :loading="saving">保存配置</a-button>
            </a-form-item>
          </a-form>
        </a-card>
      </a-tab-pane>
    </a-tabs>

    <!-- 添加/编辑门店弹窗 -->
    <a-modal v-model:visible="storeModalVisible" :title="editingIndex >= 0 ? '编辑门店' : '添加门店'" @ok="saveStore" @cancel="closeStoreModal">
      <a-form :model="editingStore" layout="vertical">
        <a-form-item label="门店名称" required>
          <a-input v-model="editingStore.name" placeholder="胶南合美MALL店" />
        </a-form-item>
        <a-form-item label="简称">
          <a-input v-model="editingStore.short_name" placeholder="胶南合美" />
        </a-form-item>
        <a-form-item label="编码">
          <a-input v-model="editingStore.code" placeholder="SCN075029" />
        </a-form-item>
        <a-form-item label="抖音主页链接">
          <a-input v-model="editingStore.douyin_url" placeholder="https://www.douyin.com/user/..." />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { Message } from '@arco-design/web-vue'

const activeTab = ref('stores')
const saving = ref(false)

// 门店数据
const stores = ref<any[]>([])
const storeModalVisible = ref(false)
const editingIndex = ref(-1)
const editingStore = reactive({
  name: '',
  short_name: '',
  code: '',
  douyin_url: ''
})

// 京东配置
const jddjConfig = reactive({
  username: '',
  password: '',
  interval: 10,
  headless: true,
  target_status: ['待接单', '待打印']
})

// 通知配置
const wechatConfig = reactive({ webhook_url: '' })
const emailConfig = reactive({
  smtp_server: 'smtp.qq.com',
  smtp_port: 587,
  sender_email: '',
  sender_password: '',
  receiver_email: ''
})

// 模拟器配置
const emulatorConfig = reactive({ adb_port: '127.0.0.1:16448' })

onMounted(async () => {
  await loadAllConfig()
})

async function loadAllConfig() {
  try {
    const config = await window.api.config.get()

    // 加载门店
    if (config.stores?.stores) {
      stores.value = config.stores.stores
    }

    // 加载京东配置
    if (config.tasks?.jddj_orders) {
      Object.assign(jddjConfig, config.tasks.jddj_orders)
    }

    // 加载通知配置
    if (config.notification?.wechat) {
      Object.assign(wechatConfig, config.notification.wechat)
    }
    if (config.notification?.email) {
      Object.assign(emailConfig, config.notification.email)
    }

    // 加载模拟器配置
    if (config.emulator) {
      Object.assign(emulatorConfig, config.emulator)
    }
  } catch (e) {
    console.error('加载配置失败:', e)
  }
}

// 门店管理
function showAddStore() {
  editingIndex.value = -1
  Object.assign(editingStore, { name: '', short_name: '', code: '', douyin_url: '' })
  storeModalVisible.value = true
}

function editStore(index: number) {
  editingIndex.value = index
  Object.assign(editingStore, stores.value[index])
  storeModalVisible.value = true
}

function saveStore() {
  if (!editingStore.name) {
    Message.warning('请输入门店名称')
    return
  }

  if (editingIndex.value >= 0) {
    stores.value[editingIndex.value] = { ...editingStore }
  } else {
    stores.value.push({ ...editingStore })
  }

  storeModalVisible.value = false
}

function deleteStore(index: number) {
  stores.value.splice(index, 1)
}

async function saveStores() {
  saving.value = true
  try {
    await window.api.config.set('stores', { mumu: { adb_port: emulatorConfig.adb_port }, stores: stores.value })
    Message.success('保存成功')
  } catch (e) {
    Message.error('保存失败')
  } finally {
    saving.value = false
  }
}

// 京东配置
async function saveJddjConfig() {
  saving.value = true
  try {
    await window.api.config.set('tasks.jddj_orders', { ...jddjConfig, enabled: true })
    Message.success('保存成功')
  } catch (e) {
    Message.error('保存失败')
  } finally {
    saving.value = false
  }
}

// 通知配置
async function saveWechatConfig() {
  saving.value = true
  try {
    await window.api.config.set('notification.wechat', wechatConfig)
    Message.success('保存成功')
  } catch (e) {
    Message.error('保存失败')
  } finally {
    saving.value = false
  }
}

async function saveEmailConfig() {
  saving.value = true
  try {
    await window.api.config.set('notification.email', emailConfig)
    Message.success('保存成功')
  } catch (e) {
    Message.error('保存失败')
  } finally {
    saving.value = false
  }
}

async function testWechat() {
  Message.info('测试发送功能开发中...')
}

// 模拟器配置
async function saveEmulatorConfig() {
  saving.value = true
  try {
    await window.api.config.set('emulator', emulatorConfig)
    Message.success('保存成功')
  } catch (e) {
    Message.error('保存失败')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
:deep(.arco-card) {
  margin-bottom: 16px;
}
</style>
