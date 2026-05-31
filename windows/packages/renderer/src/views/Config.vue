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
              <a-table-column title="企微接收人" data-index="wechat_userids" :width="150">
                <template #cell="{ record }">
                  <span v-if="record.wechat_userids?.length">{{ record.wechat_userids.join(', ') }}</span>
                  <span v-else class="text-gray">-</span>
                </template>
              </a-table-column>
              <a-table-column title="别称" data-index="aliases" :width="150">
                <template #cell="{ record }">
                  <span v-if="record.aliases?.length">{{ record.aliases.join(', ') }}</span>
                  <span v-else class="text-gray">-</span>
                </template>
              </a-table-column>
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
    <a-modal v-model:visible="storeModalVisible" :title="editingIndex >= 0 ? '编辑门店' : '添加门店'" @ok="saveStore" @cancel="closeStoreModal" :width="500">
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
            <span class="text-hint">企微应用推送时的接收人 userid</span>
          </template>
        </a-form-item>
        <a-form-item label="别称">
          <a-input-tag v-model="editingStore.aliases" placeholder="输入别称后回车添加" />
          <template #extra>
            <span class="text-hint">用于匹配订单中的门店名</span>
          </template>
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
  wechat_userids: [] as string[],
  aliases: [] as string[]
})

// 京东配置
const jddjConfig = reactive({
  username: '',
  password: '',
  interval: 10,
  headless: true,
  target_status: ['待接单', '待打印']
})

// 模拟器配置
const emulatorConfig = reactive({ adb_port: '127.0.0.1:16448' })

onMounted(async () => {
  await loadAllConfig()
})

async function loadAllConfig() {
  try {
    // 加载门店
    const storesData = await window.api.stores.get()
    if (storesData.stores) {
      stores.value = storesData.stores
    }

    // 加载京东配置
    const config = await window.api.config.get()
    if (config.tasks?.jddj_orders) {
      Object.assign(jddjConfig, config.tasks.jddj_orders)
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
  Object.assign(editingStore, { name: '', short_name: '', code: '', wechat_userids: [], aliases: [] })
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
    await window.api.stores.save({ stores: stores.value })
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
