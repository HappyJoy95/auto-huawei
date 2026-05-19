<template>
  <div class="data-page">
    <a-page-header title="数据查看" subtitle="查看采集的数据" :show-back="false" />

    <a-tabs v-model:active-key="activePlatform">
      <a-tab-pane key="xiaohongshu" title="小红书">
        <a-card>
          <template #extra>
            <a-button @click="refreshData('xiaohongshu')">刷新</a-button>
          </template>
          <a-table :data="xhsData" :pagination="{ pageSize: 10 }">
            <template #columns>
              <a-table-column title="门店" data-index="store_name" />
              <a-table-column title="标题" data-index="title" :width="300" />
              <a-table-column title="点赞" data-index="likes" />
              <a-table-column title="发布时间" data-index="post_time" />
            </template>
          </a-table>
        </a-card>
      </a-tab-pane>

      <a-tab-pane key="douyin" title="抖音">
        <a-card>
          <template #extra>
            <a-button @click="refreshData('douyin')">刷新</a-button>
          </template>
          <a-table :data="douyinData" :pagination="{ pageSize: 10 }">
            <template #columns>
              <a-table-column title="门店" data-index="store_name" />
              <a-table-column title="标题" data-index="title" :width="300" />
              <a-table-column title="点赞" data-index="likes" />
              <a-table-column title="采集时间" data-index="crawl_time" />
            </template>
          </a-table>
        </a-card>
      </a-tab-pane>

      <a-tab-pane key="inspection" title="点检数据">
        <a-card>
          <template #extra>
            <a-button @click="refreshData('inspection')">刷新</a-button>
          </template>
          <a-table :data="inspectionData" :pagination="{ pageSize: 20 }">
            <template #columns>
              <a-table-column title="门店" data-index="short_name" />
              <a-table-column title="月度得分" data-index="monthly_score" />
              <a-table-column title="月度次数" data-index="monthly_count" />
              <a-table-column title="年度得分" data-index="yearly_score" />
              <a-table-column title="年度次数" data-index="yearly_count" />
            </template>
          </a-table>
        </a-card>
      </a-tab-pane>

      <a-tab-pane key="orders" title="京东订单">
        <a-card>
          <template #extra>
            <a-button @click="refreshData('orders')">刷新</a-button>
          </template>
          <a-descriptions :column="2" bordered>
            <a-descriptions-item label="更新时间">{{ ordersData.时间 }}</a-descriptions-item>
            <a-descriptions-item label="待接单">{{ ordersData.待接单数量 }} 单</a-descriptions-item>
            <a-descriptions-item label="待打印">{{ ordersData.待打印数量 }} 单</a-descriptions-item>
          </a-descriptions>
          <a-table :data="ordersData.订单列表 || []" style="margin-top: 16px">
            <template #columns>
              <a-table-column title="订单号" data-index="订单号" />
              <a-table-column title="状态" data-index="状态">
                <template #cell="{ record }">
                  <a-tag :color="record.状态 === '待接单' ? 'red' : 'orange'">{{ record.状态 }}</a-tag>
                </template>
              </a-table-column>
              <a-table-column title="门店" data-index="门店" />
            </template>
          </a-table>
        </a-card>
      </a-tab-pane>
    </a-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const activePlatform = ref('xiaohongshu')
const xhsData = ref<any[]>([])
const douyinData = ref<any[]>([])
const inspectionData = ref<any[]>([])
const ordersData = ref<any>({})

onMounted(async () => {
  await Promise.all([
    refreshData('xiaohongshu'),
    refreshData('douyin'),
    refreshData('inspection'),
    refreshData('orders')
  ])
})

async function refreshData(type: string) {
  try {
    switch (type) {
      case 'xiaohongshu':
        const xhs = await window.api.data.xiaohongshu()
        xhsData.value = xhs?.posts || []
        break
      case 'douyin':
        const dy = await window.api.data.douyin()
        douyinData.value = dy?.posts || []
        break
      case 'inspection':
        const insp = await window.api.data.inspection()
        inspectionData.value = insp?.stores || []
        break
      case 'orders':
        ordersData.value = await window.api.data.orders() || {}
        break
    }
  } catch (e) {
    console.error('加载数据失败:', e)
  }
}
</script>
