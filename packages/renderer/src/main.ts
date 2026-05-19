import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHashHistory } from 'vue-router'
import ArcoVue from '@arco-design/web-vue'
import '@arco-design/web-vue/dist/arco.css'
import App from './App.vue'

import Dashboard from './views/Dashboard.vue'
import General from './views/General.vue'
import ModuleDetail from './views/ModuleDetail.vue'
import ModuleSettings from './views/ModuleSettings.vue'

const routes = [
  { path: '/', name: 'dashboard', component: Dashboard },
  { path: '/general', name: 'general', component: General },
  { path: '/modules/:moduleName', name: 'module-detail', component: ModuleDetail },
  { path: '/modules/:moduleName/settings', name: 'module-settings', component: ModuleSettings }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(ArcoVue)
app.mount('#app')
