<template>
  <div class="module-settings">
    <a-page-header>
      <template #title>
        <a-space>
          <a-button @click="router.back()" type="text">
            <template #icon><icon-left /></template>
          </a-button>
          <span>{{ moduleDisplayName }}</span>
        </a-space>
      </template>
    </a-page-header>

    <div class="settings-content">
      <a-card :loading="loading">
        <!-- 启用开关 -->
        <a-form-item label="启用模块">
          <div class="enabled-row">
            <a-switch
              v-model="enabled"
              checked-text="已启用"
              unchecked-text="已禁用"
            />
            <div v-if="enabled" class="next-run-display">
              <span class="next-run-label">下次执行:</span>
              <a-input
                v-if="scheduleType === 'none'"
                v-model="manualTime"
                placeholder="mm-dd HH:MM:SS"
                style="width: 150px"
              />
              <span v-else class="next-run-time">{{ nextRunTime }}</span>
            </div>
          </div>
        </a-form-item>

        <a-divider />

        <!-- 定时任务设置 -->
        <a-form-item label="定时执行">
          <a-radio-group v-model="scheduleType" type="button" size="small">
            <a-radio value="none">不定时</a-radio>
            <a-radio value="daily">每天</a-radio>
            <a-radio value="weekly">每周</a-radio>
            <a-radio value="interval">间隔</a-radio>
            <a-radio value="custom">自定义</a-radio>
          </a-radio-group>
        </a-form-item>

        <!-- 不定时 - 手动输入执行时间 -->
        <div v-if="scheduleType === 'none'" class="schedule-config">
          <span class="schedule-label">执行时间</span>
          <a-input
            v-model="manualTime"
            placeholder="mm-dd HH:MM:SS"
            style="width: 160px"
          />
          <span class="schedule-hint">到时间自动执行（格式：月-日 时:分:秒）</span>
        </div>

        <!-- 每天 -->
        <div v-if="scheduleType === 'daily'" class="schedule-config">
          <span class="schedule-label">每天</span>
          <a-time-picker v-model="dailyTime" format="HH:mm" style="width: 120px" />
          <span class="schedule-hint">执行</span>
        </div>

        <!-- 每周 -->
        <div v-if="scheduleType === 'weekly'" class="schedule-config">
          <span class="schedule-label">每周</span>
          <a-select v-model="weeklyDay" style="width: 100px">
            <a-option :value="1">周一</a-option>
            <a-option :value="2">周二</a-option>
            <a-option :value="3">周三</a-option>
            <a-option :value="4">周四</a-option>
            <a-option :value="5">周五</a-option>
            <a-option :value="6">周六</a-option>
            <a-option :value="0">周日</a-option>
          </a-select>
          <a-time-picker v-model="weeklyTime" format="HH:mm" style="width: 120px" />
          <span class="schedule-hint">执行</span>
        </div>

        <!-- 间隔 -->
        <div v-if="scheduleType === 'interval'" class="schedule-config interval-config">
          <div class="interval-row">
            <span class="schedule-label">每隔</span>
            <a-input-number v-model="intervalMinutes" :min="1" :max="1440" style="width: 100px" />
            <span class="schedule-hint">分钟执行一次</span>
          </div>
          <div class="interval-row">
            <span class="schedule-label">生效时间</span>
            <a-time-picker v-model="intervalStartTime" format="HH:mm" style="width: 100px" />
            <span class="schedule-hint">至</span>
            <a-time-picker v-model="intervalEndTime" format="HH:mm" style="width: 100px" />
          </div>
          <div class="interval-row">
            <span class="schedule-label">生效日期</span>
            <a-checkbox-group v-model="intervalDays">
              <a-checkbox :value="1">一</a-checkbox>
              <a-checkbox :value="2">二</a-checkbox>
              <a-checkbox :value="3">三</a-checkbox>
              <a-checkbox :value="4">四</a-checkbox>
              <a-checkbox :value="5">五</a-checkbox>
              <a-checkbox :value="6">六</a-checkbox>
              <a-checkbox :value="0">日</a-checkbox>
            </a-checkbox-group>
          </div>
        </div>

        <!-- 自定义 -->
        <div v-if="scheduleType === 'custom'" class="schedule-config custom">
          <div class="custom-times">
            <div v-for="(time, i) in customTimes" :key="i" class="custom-time-item">
              <a-time-picker v-model="customTimes[i]" format="HH:mm" style="width: 120px" />
              <a-button size="small" type="text" status="danger" @click="removeCustomTime(i)">
                <template #icon><icon-close /></template>
              </a-button>
            </div>
            <a-button size="small" type="dashed" @click="addCustomTime">
              <template #icon><icon-plus /></template>
              添加时间点
            </a-button>
          </div>
          <div class="custom-days">
            <span class="schedule-label">执行日期：</span>
            <a-checkbox-group v-model="customDays">
              <a-checkbox :value="1">周一</a-checkbox>
              <a-checkbox :value="2">周二</a-checkbox>
              <a-checkbox :value="3">周三</a-checkbox>
              <a-checkbox :value="4">周四</a-checkbox>
              <a-checkbox :value="5">周五</a-checkbox>
              <a-checkbox :value="6">周六</a-checkbox>
              <a-checkbox :value="0">周日</a-checkbox>
            </a-checkbox-group>
          </div>
        </div>

        <a-divider />

        <!-- 模块配置 - 根据设置定义动态渲染 -->
        <template v-if="settingsDef.fields && settingsDef.fields.length > 0">
          <a-form-item
            v-for="field in settingsDef.fields"
            :key="field.key"
            :label="getFieldLabel(field)"
            v-show="!isNotifyTargetHidden(field)"
          >
            <!-- 文本输入 -->
            <a-input
              v-if="field.type === 'text'"
              v-model="moduleConfig[field.key]"
              :placeholder="field.placeholder"
              allow-clear
            />
            <!-- 密码输入 -->
            <a-input-password
              v-else-if="field.type === 'password'"
              v-model="moduleConfig[field.key]"
              :placeholder="field.placeholder"
              allow-clear
            />
            <!-- 数字输入 -->
            <a-input-number
              v-else-if="field.type === 'number'"
              v-model="moduleConfig[field.key]"
              :min="field.min"
              :max="field.max"
              style="width: 100%"
            />
            <!-- 开关 -->
            <a-switch
              v-else-if="field.type === 'switch'"
              v-model="moduleConfig[field.key]"
              checked-text="是"
              unchecked-text="否"
            />
            <!-- 下拉选择 -->
            <a-select
              v-else-if="field.type === 'select'"
              v-model="moduleConfig[field.key]"
              style="width: 100%"
            >
              <a-option
                v-for="opt in getFieldOptions(field)"
                :key="opt.value"
                :value="opt.value"
              >
                {{ opt.label }}
              </a-option>
            </a-select>
            <!-- 复选框组 -->
            <a-checkbox-group
              v-else-if="field.type === 'checkbox'"
              v-model="moduleConfig[field.key]"
            >
              <a-checkbox
                v-for="opt in getFieldOptions(field)"
                :key="opt.value"
                :value="opt.value"
              >
                {{ opt.label }}
              </a-checkbox>
            </a-checkbox-group>
            <!-- 文本列表 -->
            <div v-else-if="field.type === 'list'" class="list-editor">
              <div v-for="(item, i) in (moduleConfig[field.key] || [])" :key="i" class="list-item">
                <a-input v-model="moduleConfig[field.key][i]" style="flex: 1" />
                <a-button size="small" type="text" status="danger" @click="removeListItem(field.key, i)">
                  <template #icon><icon-delete /></template>
                </a-button>
              </div>
              <a-button size="small" type="dashed" @click="addListItem(field.key)">
                <template #icon><icon-plus /></template>
                添加
              </a-button>
            </div>
            <!-- 对象列表 -->
            <div v-else-if="field.type === 'object_list'" class="array-editor">
              <div v-for="(item, i) in (moduleConfig[field.key] || [])" :key="i" class="array-item">
                <template v-for="subField in field.fields" :key="subField.key">
                  <a-input
                    v-model="item[subField.key]"
                    :placeholder="subField.placeholder || subField.label"
                    :style="{ width: subField.width ? subField.width + 'px' : undefined, flex: subField.width ? undefined : 1 }"
                  />
                </template>
                <a-button size="small" type="text" status="danger" @click="removeArrayItem(field.key, i)">
                  <template #icon><icon-delete /></template>
                </a-button>
              </div>
              <a-button size="small" type="dashed" @click="addArrayItem(field.key, field.fields)">
                <template #icon><icon-plus /></template>
                添加
              </a-button>
            </div>
            <!-- 默认文本 -->
            <a-input
              v-else
              v-model="moduleConfig[field.key]"
              :placeholder="field.placeholder"
              allow-clear
            />
            <div v-if="field.hint" class="field-hint">{{ field.hint }}</div>
          </a-form-item>
        </template>

        <!-- 没有设置定义时使用旧逻辑 -->
        <template v-else>
          <a-form-item
            v-for="(value, key) in moduleConfig"
            :key="key"
            :label="formatLabel(String(key))"
          >
            <a-input
              v-if="typeof value === 'string'"
              v-model="moduleConfig[key]"
              allow-clear
            />
            <a-input-number
              v-else-if="typeof value === 'number'"
              v-model="moduleConfig[key]"
              style="width: 100%"
            />
            <a-switch
              v-else-if="typeof value === 'boolean'"
              v-model="moduleConfig[key]"
              checked-text="是"
              unchecked-text="否"
            />
          </a-form-item>
        </template>

        <a-divider />

        <div class="actions">
          <a-button @click="router.back()">取消</a-button>
          <a-button type="outline" status="success" @click="runTest" :loading="testing">
            <template #icon><icon-play-arrow /></template>
            测试执行
          </a-button>
          <a-button type="primary" @click="saveConfig" :loading="saving">
            保存配置
          </a-button>
        </div>

        <!-- 测试结果 -->
        <div v-if="testResult" class="test-result">
          <a-alert :type="testResult.success ? 'success' : 'error'">
            <template #title>{{ testResult.success ? '执行成功' : '执行失败' }}</template>
            {{ testResult.message }}
          </a-alert>
        </div>
      </a-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import * as api from '../services/api'
import { useRoute, useRouter, onBeforeRouteUpdate } from 'vue-router'
import { useModuleStore } from '../stores/module'
import { Message } from '@arco-design/web-vue'
import { IconLeft, IconDelete, IconPlus, IconClose, IconPlayArrow } from '@arco-design/web-vue/es/icon'

const route = useRoute()
const router = useRouter()
const moduleStore = useModuleStore()

const moduleName = computed(() => String(route.params.moduleName || ''))
const moduleDisplayName = computed(() => {
  const mod = moduleStore.modules.find(m => m.name === moduleName.value)
  return mod?.display_name || moduleName.value
})

const loading = ref(true)
const saving = ref(false)
const testing = ref(false)
const testResult = ref<{ success: boolean; message: string } | null>(null)
const enabled = ref(true)

// 定时任务配置
const scheduleType = ref('none')
const manualTime = ref('01-01 00:00:00')
const dailyTime = ref('09:00')
const weeklyDay = ref(1)
const weeklyTime = ref('09:00')
const intervalMinutes = ref(60)
const intervalStartTime = ref('00:00')
const intervalEndTime = ref('23:59')
const intervalDays = ref<number[]>([1, 2, 3, 4, 5])
const customTimes = ref<string[]>(['09:00'])
const customDays = ref<number[]>([1, 2, 3, 4, 5])

// 模块配置
const moduleConfig = ref<Record<string, any>>({})
const settingsDef = ref<{ fields: any[] }>({ fields: [] })

function formatLabel(key: string): string {
  const labels: Record<string, string> = {
    'adb_port': 'ADB 端口',
    'headless': '无头模式',
    'max_posts_per_store': '每店最大帖子数',
    'stores': '门店列表',
    'accounts': '账号列表',
    'username': '用户名',
    'password': '密码',
    'target_status': '目标状态'
  }
  return labels[key] || key
}

function getFieldLabel(field: any): string {
  // 推送目标根据推送方式显示不同标签
  if (field.key === 'notify_target') {
    const notifyType = moduleConfig.value['notify_type'] || 'wechat'
    return notifyType === 'wechat' ? 'Webhook地址' : '目标邮箱'
  }
  return field.label
}

function getFieldOptions(field: any) {
  if (field.options_from) {
    return moduleConfig.value[field.options_from] || []
  }
  return field.options || []
}

function isNotifyTargetHidden(field: any): boolean {
  // 推送目标字段只在启用推送时显示
  if (field.key === 'notify_target') {
    return !moduleConfig.value['notify_enabled']
  }
  // notify_type 也只在启用推送时显示
  if (field.key === 'notify_type') {
    return !moduleConfig.value['notify_enabled']
  }
  // 处理 show_if 条件
  if (field.show_if) {
    return !moduleConfig.value[field.show_if]
  }
  return false
}

function addListItem(key: string) {
  if (!moduleConfig.value[key]) {
    moduleConfig.value[key] = []
  }
  moduleConfig.value[key].push('')
}

function removeListItem(key: string, index: number) {
  moduleConfig.value[key].splice(index, 1)
}

function addArrayItem(key: string, fields?: any[]) {
  if (!moduleConfig.value[key]) {
    moduleConfig.value[key] = []
  }
  const newItem: Record<string, string> = {}
  if (fields) {
    for (const f of fields) {
      newItem[f.key] = ''
    }
  } else {
    newItem.name = ''
    newItem.url = ''
  }
  moduleConfig.value[key].push(newItem)
}

function removeArrayItem(key: string, index: number) {
  moduleConfig.value[key].splice(index, 1)
}

function addCustomTime() {
  customTimes.value.push('09:00')
}

function removeCustomTime(index: number) {
  customTimes.value.splice(index, 1)
}

// 解析 schedule 到 UI
function parseSchedule(schedule: string | string[] | undefined) {
  if (!schedule) {
    scheduleType.value = 'none'
    return
  }

  const schedules = Array.isArray(schedule) ? schedule : [schedule]
  const s = schedules[0]

  if (s.includes('*/')) {
    const match = s.match(/\*\/(\d+)/)
    if (match) {
      scheduleType.value = 'interval'
      intervalMinutes.value = parseInt(match[1])
      return
    }
  }

  const parts = s.split(' ')
  if (parts.length !== 5) return

  const [min, hour, day, month, dow] = parts
  const timeStr = `${hour.padStart(2, '0')}:${min.padStart(2, '0')}`

  if (day === '*' && dow === '*') {
    scheduleType.value = 'daily'
    dailyTime.value = timeStr
    return
  }

  if (dow !== '*' && day === '*') {
    scheduleType.value = 'weekly'
    weeklyDay.value = parseInt(dow)
    weeklyTime.value = timeStr
    return
  }

  scheduleType.value = 'custom'
}

// 生成 schedule 配置
function generateScheduleConfig(): Record<string, any> {
  const config: Record<string, any> = { enabled: enabled.value }

  switch (scheduleType.value) {
    case 'none':
      if (manualTime.value) {
        config.manual_time = manualTime.value
      }
      break

    case 'daily': {
      const [h, m] = dailyTime.value.split(':')
      config.schedule = `${m} ${h} * * *`
      break
    }

    case 'weekly': {
      const [h, m] = weeklyTime.value.split(':')
      config.schedule = `${m} ${h} * * ${weeklyDay.value}`
      break
    }

    case 'interval': {
      config.interval = intervalMinutes.value
      config.interval_start = intervalStartTime.value
      config.interval_end = intervalEndTime.value
      config.interval_days = intervalDays.value
      break
    }

    case 'custom': {
      const schedules: string[] = []
      const days = customDays.value.length > 0 ? customDays.value.join(',') : '*'

      for (const time of customTimes.value) {
        const [h, m] = time.split(':')
        if (days === '*') {
          schedules.push(`${m} ${h} * * *`)
        } else {
          schedules.push(`${m} ${h} * * ${days}`)
        }
      }

      if (schedules.length > 0) {
        config.schedule = schedules.length === 1 ? schedules[0] : schedules
      }
      break
    }
  }

  return config
}

async function saveConfig() {
  saving.value = true
  try {
    const schedulerConfig = generateScheduleConfig()

    // 深拷贝配置，解决 IPC 序列化问题
    const configToSave = {
      scheduler: JSON.parse(JSON.stringify(schedulerConfig)),
      module: JSON.parse(JSON.stringify(moduleConfig.value))
    }

    const result = await moduleStore.saveModuleConfig(moduleName.value, configToSave)

    if (result.success) {
      Message.success('配置已保存')
    } else {
      Message.error('保存失败: ' + (result.error || '未知错误'))
    }
  } catch (e) {
    console.error('Save error:', e)
    Message.error('保存失败: ' + e)
  } finally {
    saving.value = false
  }
}

async function runTest() {
  testing.value = true
  testResult.value = null

  try {
    const result = await api.runTaskNow(moduleName.value, 'test')

    if (result.success) {
      Message.success('任务已加入执行队列')
      testResult.value = { success: true, message: '任务已开始执行，请查看 Dashboard 页面查看执行状态' }
    } else {
      testResult.value = { success: false, message: result.message || '启动失败' }
    }
  } catch (e) {
    testResult.value = { success: false, message: '连接后端失败: ' + (e instanceof Error ? e.message : String(e)) }
  } finally {
    testing.value = false
  }
}

// 加载配置
async function loadConfig() {
  loading.value = true
  try {
    await moduleStore.loadModules()
    const cfg = await moduleStore.getModuleConfig(moduleName.value)

    if (cfg) {
      enabled.value = cfg.scheduler?.enabled ?? true
      moduleConfig.value = cfg.module || {}
      settingsDef.value = cfg.settings_def || { fields: [] }

      // 初始化默认值
      if (settingsDef.value.fields) {
        for (const field of settingsDef.value.fields) {
          if (moduleConfig.value[field.key] === undefined && field.default !== undefined) {
            moduleConfig.value[field.key] = field.default
          }
        }
      }

      if (cfg.scheduler) {
        if (cfg.scheduler.manual_time) {
          scheduleType.value = 'none'
          manualTime.value = cfg.scheduler.manual_time
        } else if (cfg.scheduler.interval) {
          scheduleType.value = 'interval'
          intervalMinutes.value = cfg.scheduler.interval
          if (cfg.scheduler.interval_start) intervalStartTime.value = cfg.scheduler.interval_start
          if (cfg.scheduler.interval_end) intervalEndTime.value = cfg.scheduler.interval_end
          if (cfg.scheduler.interval_days) intervalDays.value = cfg.scheduler.interval_days
        } else if (cfg.scheduler.schedule) {
          parseSchedule(cfg.scheduler.schedule)
        } else {
          scheduleType.value = 'none'
        }
      }
    }

    // 加载模块自定义样式
    const styleResult = await moduleStore.getModuleStyle(moduleName.value)
    if (styleResult.has_style && styleResult.style) {
      injectModuleStyle(styleResult.style)
    }
  } catch (e) {
    console.error('Failed to load config:', e)
  } finally {
    loading.value = false
  }
}

// 注入模块样式
function injectModuleStyle(css: string) {
  // 移除旧样式
  const oldStyle = document.getElementById('module-custom-style')
  if (oldStyle) {
    oldStyle.remove()
  }
  // 注入新样式
  const styleEl = document.createElement('style')
  styleEl.id = 'module-custom-style'
  styleEl.textContent = css
  document.head.appendChild(styleEl)
}

// 监听路由参数变化，重新加载配置
onBeforeRouteUpdate((to, from) => {
  if (to.params.moduleName !== from.params.moduleName) {
    loadConfig()
  }
})

// 计算下次执行时间
const nextRunTime = computed(() => {
  if (!enabled.value) {
    return null
  }

  const now = new Date()

  if (scheduleType.value === 'none') {
    // 不定时时显示手动输入的时间
    if (manualTime.value) {
      return manualTime.value
    }
    return null
  }

  if (scheduleType.value === 'daily') {
    const [h, m] = dailyTime.value.split(':').map(Number)
    const next = new Date()
    next.setHours(h, m, 0, 0)
    if (next <= now) {
      next.setDate(next.getDate() + 1)
    }
    return formatNextRun(next)
  }

  if (scheduleType.value === 'weekly') {
    const [h, m] = weeklyTime.value.split(':').map(Number)
    const targetDay = weeklyDay.value // 0=周日, 1=周一...6=周六
    const next = new Date()
    next.setHours(h, m, 0, 0)

    // 转换: JS getDay() 返回 0=周日, 1=周一...
    const currentDay = next.getDay()
    let daysUntil = targetDay - currentDay
    if (daysUntil < 0 || (daysUntil === 0 && next <= now)) {
      daysUntil += 7
    }
    if (daysUntil > 0 || next <= now) {
      next.setDate(next.getDate() + daysUntil)
    }
    return formatNextRun(next)
  }

  if (scheduleType.value === 'interval') {
    const [startH, startM] = intervalStartTime.value.split(':').map(Number)
    const [endH, endM] = intervalEndTime.value.split(':').map(Number)

    // 检查今天是否在生效日期
    const jsDay = now.getDay() // 0=周日, 1=周一...
    const frontendDay = jsDay === 0 ? 0 : jsDay // 前端格式: 0=周日, 1=周一...
    if (!intervalDays.value.includes(frontendDay)) {
      return '不在生效日期内'
    }

    const start = new Date()
    start.setHours(startH, startM, 0, 0)
    const end = new Date()
    end.setHours(endH, endM, 0, 0)

    if (now < start) {
      return formatNextRun(start)
    }
    if (now > end) {
      return '今日已过生效时段'
    }

    // 在生效时段内，计算下一个间隔
    const minutesSinceStart = (now.getTime() - start.getTime()) / 60000
    const intervalsPassed = Math.floor(minutesSinceStart / intervalMinutes.value)
    const next = new Date(start.getTime() + (intervalsPassed + 1) * intervalMinutes.value * 60000)
    if (next > end) {
      return '今日已过生效时段'
    }
    return formatNextRun(next)
  }

  if (scheduleType.value === 'custom' && customTimes.value.length > 0) {
    // 找最近的一个时间点
    const todayRuns: Date[] = []
    for (const time of customTimes.value) {
      const [h, m] = time.split(':').map(Number)
      const run = new Date()
      run.setHours(h, m, 0, 0)
      todayRuns.push(run)
    }
    todayRuns.sort((a, b) => a.getTime() - b.getTime())

    // 找今天还没过的时间
    const futureToday = todayRuns.find(r => r > now)
    if (futureToday) {
      return formatNextRun(futureToday)
    }

    // 今天都过了，找下一个生效日期
    const jsDay = now.getDay()
    const frontendDay = jsDay === 0 ? 0 : jsDay
    for (let i = 1; i <= 7; i++) {
      const nextDay = (jsDay + i) % 7
      const nextFrontendDay = nextDay === 0 ? 0 : nextDay
      if (customDays.value.length === 0 || customDays.value.includes(nextFrontendDay)) {
        const next = new Date(todayRuns[0])
        next.setDate(next.getDate() + i)
        return formatNextRun(next)
      }
    }
  }

  return null
})

function formatNextRun(date: Date): string {
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hour = String(date.getHours()).padStart(2, '0')
  const min = String(date.getMinutes()).padStart(2, '0')
  const sec = String(date.getSeconds()).padStart(2, '0')
  return `${month}-${day} ${hour}:${min}:${sec}`
}

onMounted(() => {
  loadConfig()
})

onUnmounted(() => {
  // 清理模块自定义样式
  const styleEl = document.getElementById('module-custom-style')
  if (styleEl) {
    styleEl.remove()
  }
})
</script>

<style scoped>
.module-settings {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.settings-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.schedule-config {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 12px;
  padding: 12px 16px;
  background: var(--color-fill-1);
  border-radius: 6px;
}

.schedule-label {
  font-weight: 500;
  flex-shrink: 0;
}

.schedule-hint {
  color: var(--color-text-3);
}

.schedule-config.interval-config {
  flex-direction: column;
  align-items: flex-start;
}

.interval-row {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
}

.schedule-config.custom {
  flex-direction: column;
  align-items: flex-start;
}

.custom-times {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.custom-time-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.custom-days {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.array-editor {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.array-item {
  display: flex;
  gap: 8px;
  align-items: center;
}

.actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.enabled-row {
  display: flex;
  align-items: center;
  gap: 24px;
}

.next-run-display {
  display: flex;
  align-items: center;
  gap: 8px;
}

.next-run-label {
  color: var(--color-text-3);
  font-size: 13px;
}

.next-run-time {
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 14px;
  color: rgb(var(--primary-6));
  font-weight: 500;
}

.list-editor {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.list-item {
  display: flex;
  gap: 8px;
  align-items: center;
}

.field-hint {
  font-size: 12px;
  color: var(--color-text-3);
  margin-top: 4px;
}

.test-result {
  margin-top: 16px;
}
</style>
