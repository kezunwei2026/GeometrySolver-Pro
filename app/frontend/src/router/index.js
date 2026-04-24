import { createRouter, createWebHistory } from 'vue-router'
import WorkspaceView from '../views/WorkspaceView.vue'
import SettingsView from '../views/SettingsView.vue'
import HistoryView from '../views/HistoryView.vue'

const routes = [
  { path: '/', component: WorkspaceView },
  { path: '/settings', component: SettingsView },
  { path: '/history', component: HistoryView },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
