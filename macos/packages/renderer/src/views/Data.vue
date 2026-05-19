<template>
  <div class="data-page">
    <a-page-header title="数据查看" subtitle="查看采集的数据" :show-back="false" />

    <a-spin :loading="loading" style="width: 100%">
      <a-tabs v-model:active-key="activeModule">
        <a-tab-pane v-for="mod in modulesWithData" :key="mod.name" :title="mod.display_name">
          <a-card>
            <template #extra>
              <a-button @click="refreshData(mod.name)">刷新</a-button>
            </template>
            <a-spin :loading="mod.loading">
              <template v-if="mod.error">
                <a-empty description="数据加载失败">
                  <template #extra>
                    <a-button size="small" @click="refreshData(mod.name)">重试</a-button>
                  </template>
                </a-empty>
              </template>
              <template v-else-if="!mod.data || Object.keys(mod.data).length === 0">
                <a-empty description="暂无数据" />
              </template>
              <template v-else>
                <!-- 渲染数据内容 -->
                <component :is="getDataComponent(mod.name)" :data="mod.data" />
              </template>
            </a-spin>
          </a-card>
        </a-tab-pane>

        <template v-if="modulesWithData.length === 0 && !loading">
          <a-tab-pane key="empty" title="暂无数据">
            <a-empty description="没有可用的模块数据" />
          </a-tab-pane>
        </template>
      </a-tabs>
    </a-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, shallowRef, h } from 'vue'
import { useModuleStore } from '../stores/module'

interface ModuleData {
  name: string
  display_name: string
  data: any
  loading: boolean
  error: boolean
}

const moduleStore = useModuleStore()
const activeModule = ref('')
const loading = ref(true)
const moduleDataMap = ref<Map<string, ModuleData>>(new Map())

// 获取有数据的模块列表
const modulesWithData = computed(() => {
  const modules: ModuleData[] = []
  moduleDataMap.value.forEach((mod, name) => {
    modules.push(mod)
  })
  return modules
})

onMounted(async () => {
  await moduleStore.loadModules()
  await loadAllModuleData()
})

async function loadAllModuleData() {
  loading.value = true

  // 初始化所有模块的数据状态
  for (const mod of moduleStore.modules) {
    if (mod.has_task) {
      moduleDataMap.value.set(mod.name, {
        name: mod.name,
        display_name: mod.display_name,
        data: null,
        loading: false,
        error: false
      })
    }
  }

  // 并行加载所有模块数据
  await Promise.all(
    Array.from(moduleDataMap.value.keys()).map(name => refreshData(name))
  )

  // 设置默认激活的标签页
  if (moduleDataMap.value.size > 0) {
    activeModule.value = moduleDataMap.value.keys().next().value
  }

  loading.value = false
}

async function refreshData(moduleName: string) {
  const mod = moduleDataMap.value.get(moduleName)
  if (!mod) return

  mod.loading = true
  mod.error = false

  try {
    const result = await window.electronAPI.getModuleData(moduleName)
    mod.data = result.data
  } catch (e) {
    console.error(`加载 ${moduleName} 数据失败:`, e)
    mod.error = true
  } finally {
    mod.loading = false
  }
}

// 根据模块名获取数据渲染组件
function getDataComponent(moduleName: string) {
  return {
    props: ['data'],
    setup(props: { data: any }) {
      // 根据模块类型渲染不同的数据视图
      switch (moduleName) {
        case 'douyin':
          return () => renderDouyinData(props.data)
        case 'jddj_orders':
          return () => renderJddjOrdersData(props.data)
        default:
          return () => renderGenericData(props.data)
      }
    }
  }
}

// 抖音数据渲染
function renderDouyinData(data: any) {
  const posts = data?.posts?.data || data?.posts || []

  if (!Array.isArray(posts) || posts.length === 0) {
    return h('div', { class: 'empty-tip' }, '暂无采集数据')
  }

  const columns = [
    { title: '门店', dataIndex: 'store_name' },
    { title: '标题', dataIndex: 'title', width: 300 },
    { title: '点赞', dataIndex: 'likes' },
    { title: '采集时间', dataIndex: 'crawl_time' }
  ]

  return h('div', [
    h('div', { class: 'data-summary' }, `共 ${posts.length} 条数据`),
    h('div', { class: 'data-table-wrapper' }, [
      h('table', { class: 'data-table' }, [
        h('thead', [
          h('tr', columns.map(col => h('th', { style: col.width ? `width: ${col.width}px` : '' }, col.title)))
        ]),
        h('tbody', posts.slice(0, 100).map((post: any) =>
          h('tr', [
            h('td', post.store_name || '-'),
            h('td', { class: 'title-cell' }, post.title || '-'),
            h('td', post.likes?.toString() || '0'),
            h('td', post.crawl_time || '-')
          ])
        ))
      ])
    ])
  ])
}

// 京东到家订单数据渲染
function renderJddjOrdersData(data: any) {
  const ordersData = data?.pending_orders || data

  if (!ordersData) {
    return h('div', { class: 'empty-tip' }, '暂无订单数据')
  }

  const orders = ordersData?.订单列表 || []
  const time = ordersData?.时间 || '-'
  const pendingCount = ordersData?.待接单数量 || 0
  const printCount = ordersData?.待打印数量 || 0

  return h('div', [
    h('div', { class: 'data-summary' }, [
      h('span', {}, `更新时间: ${time}`),
      h('span', { class: 'summary-item' }, `待接单: ${pendingCount} 单`),
      h('span', { class: 'summary-item' }, `待打印: ${printCount} 单`)
    ]),
    orders.length > 0 ? h('div', { class: 'data-table-wrapper' }, [
      h('table', { class: 'data-table' }, [
        h('thead', [
          h('tr', [
            h('th', '订单号'),
            h('th', '状态'),
            h('th', '门店')
          ])
        ]),
        h('tbody', orders.map((order: any) =>
          h('tr', [
            h('td', order.订单号 || '-'),
            h('td', [
              h('span', {
                class: `status-tag ${order.状态 === '待接单' ? 'status-red' : 'status-orange'}`
              }, order.状态 || '-')
            ]),
            h('td', order.门店 || '-')
          ])
        ))
      ])
    ]) : h('div', { class: 'empty-tip' }, '暂无待处理订单')
  ])
}

// 通用数据渲染
function renderGenericData(data: any) {
  if (!data) {
    return h('div', { class: 'empty-tip' }, '暂无数据')
  }

  // 如果是数组
  if (Array.isArray(data)) {
    if (data.length === 0) {
      return h('div', { class: 'empty-tip' }, '暂无数据')
    }
    return h('div', { class: 'data-summary' }, `共 ${data.length} 条数据`)
  }

  // 如果是对象，显示 JSON 预览
  return h('div', { class: 'json-preview' }, [
    h('pre', JSON.stringify(data, null, 2))
  ])
}
</script>

<style scoped>
.data-page {
  padding: 16px;
}

.data-summary {
  margin-bottom: 16px;
  color: var(--color-text-2);
}

.summary-item {
  margin-left: 16px;
}

.data-table-wrapper {
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.data-table th,
.data-table td {
  padding: 12px 16px;
  text-align: left;
  border-bottom: 1px solid var(--color-border);
}

.data-table th {
  background: var(--color-fill-1);
  font-weight: 500;
}

.data-table tr:hover {
  background: var(--color-fill-1);
}

.title-cell {
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.status-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.status-red {
  background: rgb(var(--danger-6));
  color: #fff;
}

.status-orange {
  background: rgb(var(--warning-6));
  color: #fff;
}

.empty-tip {
  color: var(--color-text-3);
  text-align: center;
  padding: 24px;
}

.json-preview {
  background: var(--color-fill-1);
  padding: 16px;
  border-radius: 4px;
  overflow: auto;
  max-height: 400px;
}

.json-preview pre {
  margin: 0;
  font-size: 12px;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
