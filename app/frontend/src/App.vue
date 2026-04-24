<template>
  <el-config-provider>
    <div class="shell">
      <div class="topbar-fixed" :class="{ 'sidebar-collapsed': sidebarCollapsed, 'sidebar-hidden': isMobile && !sidebarOpen }">
        <div class="topbar-fixed-left">
          <button class="nav-toggle" type="button" @click="toggleSidebar">
            <el-icon>
              <Expand v-if="isMobile ? !sidebarOpen : sidebarCollapsed" />
              <Fold v-else />
            </el-icon>
          </button>
          <div class="topbar-brand">AI Geometry</div>
        </div>
        <div class="workspace-meta">
          <span class="meta-item">{{ loading ? '思考中' : backendHealth }}</span>
          <span class="meta-item meta-item-accent">{{ providerLabel }}</span>
          <span class="meta-item">{{ modelName }}</span>
        </div>
      </div>

      <div class="app-frame" :class="{ 'sidebar-collapsed': sidebarCollapsed, 'sidebar-hidden': isMobile && !sidebarOpen }">
        <aside class="sidebar">
          <div class="brand-row">
            <div class="brand-main">
              <div class="brand-mark">
                <span class="brand-orbit brand-orbit-a"></span>
                <span class="brand-orbit brand-orbit-b"></span>
                <span class="brand-core"></span>
              </div>
              <div class="brand-copy">
                <div class="brand-title">AI Geometry</div>
                <div class="brand-subtitle">Structured geometry workspace</div>
              </div>
            </div>
          </div>

          <button class="sidebar-action primary" type="button" @click="resetSession($router)" :title="sidebarCollapsed ? '新建聊天' : ''">
            <el-icon><Plus /></el-icon>
            <span class="sidebar-action-label">新建聊天</span>
          </button>
          <button class="sidebar-action" type="button" @click="$router.push('/history')" :title="sidebarCollapsed ? '全部' : ''">
            <el-icon><Clock /></el-icon>
            <span class="sidebar-action-label">查看全部</span>
          </button>

          <div class="sidebar-label">历史记录</div>
          <div class="history-list">
            <button
              v-for="item in historyList"
              :key="item.id"
              type="button"
              class="history-item"
              @click="loadHistory(item, $router)"
            >
              <div class="history-item-title">{{ item.response_data?.title || '未命名解析' }}</div>
              <div class="history-item-problem">{{ item.problem }}</div>
            </button>

            <div v-if="historyList.length === 0" class="history-empty">
              <div class="history-empty-title">暂无历史记录</div>
              <div class="history-empty-text">完成一次解析后，这里会显示最近的题目。</div>
            </div>
          </div>

          <button class="sidebar-action sidebar-action-bottom" type="button" @click="$router.push('/settings')" :title="sidebarCollapsed ? '设置' : ''">
            <el-icon><Setting /></el-icon>
            <span class="sidebar-action-label">模型设置</span>
          </button>
        </aside>

        <main class="workspace">
          <router-view></router-view>
        </main>
      </div>
    </div>
  </el-config-provider>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue';
import { Clock, Expand, Fold, Plus, Setting } from '@element-plus/icons-vue';
import {
  backendHealth,
  historyList,
  initStore,
  loadHistory,
  loading,
  modelName,
  providerLabel,
  resetSession,
} from './stores/appStore';

const sidebarCollapsed = ref(false);
const sidebarOpen = ref(true);
const isMobile = ref(typeof window !== 'undefined' ? window.innerWidth <= 980 : false);

const handleResize = () => {
  if (typeof window === 'undefined') return;
  const nextIsMobile = window.innerWidth <= 980;
  isMobile.value = nextIsMobile;
  if (!nextIsMobile) {
    sidebarOpen.value = true;
  } else {
    sidebarCollapsed.value = false;
    sidebarOpen.value = false;
  }
};

const toggleSidebar = () => {
  if (isMobile.value) {
    sidebarOpen.value = !sidebarOpen.value;
    return;
  }
  sidebarCollapsed.value = !sidebarCollapsed.value;
};

onMounted(() => {
  initStore();
  handleResize();
  window.addEventListener('resize', handleResize);
});

onUnmounted(() => {
  window.removeEventListener('resize', handleResize);
});
</script>

<style scoped>
.shell {
  min-height: 100vh;
  background:
    radial-gradient(circle at top left, rgba(79, 124, 255, 0.08), transparent 28%),
    radial-gradient(circle at top right, rgba(106, 211, 198, 0.08), transparent 26%),
    #f7f8fc;
}

.topbar-fixed {
  position: fixed;
  top: 0;
  left: 320px;
  right: 0;
  z-index: 30;
  min-height: 64px;
  padding: 12px 18px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  background: rgba(255, 255, 255, 0.88);
  backdrop-filter: blur(18px);
  border-bottom: 1px solid #e8ebf2;
}

.topbar-fixed.sidebar-collapsed {
  left: 88px;
}

.topbar-fixed.sidebar-hidden {
  left: 0;
}

.topbar-fixed-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.topbar-brand {
  color: #111827;
  font-size: 15px;
  font-weight: 600;
  line-height: 1;
  display: flex;
  align-items: center;
}

.nav-toggle {
  height: 36px;
  width: 36px;
  padding: 0;
  border: 0;
  border-radius: 999px;
  background: transparent;
  color: #475569;
  cursor: pointer;
  font: inherit;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}

.app-frame {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr);
}

.app-frame.sidebar-collapsed {
  grid-template-columns: 88px minmax(0, 1fr);
}

.app-frame.sidebar-hidden {
  grid-template-columns: 0 minmax(0, 1fr);
}

.sidebar {
  position: sticky;
  top: 0;
  height: 100vh;
  padding: 16px 12px;
  background: rgba(247, 248, 252, 0.92);
  border-right: 1px solid #e8ebf2;
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow: hidden;
  transition: padding 0.2s ease, opacity 0.2s ease;
  backdrop-filter: blur(12px);
}

.sidebar-hidden .sidebar {
  width: 0;
  padding: 0;
  border-right: 0;
  opacity: 0;
}

.brand-row {
  display: flex;
  align-items: center;
  padding: 8px 12px 2px 10px;
}

.brand-main {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.brand-mark {
  position: relative;
  width: 40px;
  height: 40px;
  border-radius: 14px;
  background: #fff;
  overflow: hidden;
  box-shadow: 0 10px 24px rgba(79, 124, 255, 0.12);
}

.brand-orbit {
  position: absolute;
  border-radius: 999px;
  border: 2px solid transparent;
}

.brand-orbit-a {
  inset: 7px;
  border-top-color: #4f7cff;
  border-right-color: #6ad3c6;
  transform: rotate(24deg);
}

.brand-orbit-b {
  inset: 11px;
  border-bottom-color: #ff9a67;
  border-left-color: #7a62ff;
  transform: rotate(-28deg);
}

.brand-core {
  position: absolute;
  inset: 16px;
  border-radius: 999px;
  background: linear-gradient(135deg, #4f7cff, #7a62ff 54%, #ff9a67);
}

.brand-title {
  color: #111827;
  font-size: 16px;
  font-weight: 600;
}

.brand-subtitle {
  color: #6b7280;
  font-size: 11px;
}

.sidebar-collapsed .brand-copy,
.sidebar-collapsed .sidebar-label,
.sidebar-collapsed .history-item-title,
.sidebar-collapsed .history-item-problem,
.sidebar-collapsed .history-empty,
.sidebar-collapsed .sidebar-action-label {
  display: none;
}

.sidebar-collapsed .brand-row {
  justify-content: center;
}

.sidebar-action {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  height: 42px;
  padding: 0 12px 0 14px;
  border: 0;
  border-radius: 999px;
  background: transparent;
  color: #374151;
  font-size: 14px;
  text-align: left;
  cursor: pointer;
}

.sidebar-action:hover {
  background: #eceff6;
}

.sidebar-action.primary {
  background: linear-gradient(135deg, #edf2ff, #e9f8f3);
}

.sidebar-collapsed .sidebar-action {
  justify-content: center;
  padding: 0;
  gap: 0;
}

.sidebar-action-bottom {
  margin-top: auto;
}

.sidebar-label {
  padding: 8px 12px 0 10px;
  color: #8b95a7;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.history-list {
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

/* 隐藏滚动条轨道 */
.history-list::-webkit-scrollbar {
  width: 6px;
}

.history-list::-webkit-scrollbar-track {
  background: transparent;
}

/* 默认隐藏滚动条滑块 */
.history-list::-webkit-scrollbar-thumb {
  background: transparent;
  border-radius: 10px;
  transition: background 0.3s ease;
}

/* 鼠标悬停在列表上时显示滑块 */
.history-list:hover::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.12);
}

.history-list::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.25) !important;
}

.history-item {
  width: 100%;
  padding: 10px 12px 10px 12px;
  border: 0;
  border-radius: 16px;
  background: transparent;
  text-align: left;
  cursor: pointer;
}

.history-item:hover {
  background: #eceff6;
}

.history-item-title {
  color: #111827;
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 4px;
}

.history-item-problem {
  color: #6b7280;
  font-size: 12px;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.history-empty {
  padding: 12px 12px 12px 12px;
  color: #6b7280;
}

.history-empty-title {
  color: #111827;
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 4px;
}

.history-empty-text {
  font-size: 12px;
  line-height: 1.6;
}

.workspace {
  min-width: 0;
  padding: 88px 32px 40px;
  background: rgba(255, 255, 255, 0.88);
  min-height: 100vh;
  backdrop-filter: blur(10px);
}

.workspace-meta {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.meta-item {
  color: #6b7280;
  font-size: 12px;
  padding: 8px 12px;
  border-radius: 999px;
  background: #eef1f7;
}

.meta-item-accent {
  color: #134e4a;
  background: #e8faf3;
}

@media (max-width: 980px) {
  .app-frame {
    grid-template-columns: 1fr;
  }

  .sidebar {
    position: fixed;
    top: 0;
    left: 0;
    bottom: 0;
    z-index: 25;
    width: 320px;
    height: 100vh;
    padding-top: 80px;
    box-shadow: 10px 0 30px rgba(15, 23, 42, 0.08);
  }

  .history-list {
    max-height: 220px;
  }

  .workspace {
    padding-top: 96px;
  }

  .topbar-fixed {
    left: 0;
  }
}

@media (max-width: 768px) {
  .workspace {
    padding: 132px 14px 30px;
  }

  .topbar-fixed {
    align-items: flex-start;
    flex-direction: column;
    padding: 10px 14px;
    gap: 10px;
  }

  .workspace-meta {
    width: 100%;
    justify-content: flex-start;
  }
}

@media (max-width: 560px) {
  .topbar-brand {
    font-size: 14px;
  }

  .workspace-meta {
    gap: 8px;
  }

  .meta-item {
    max-width: 100%;
    padding: 7px 10px;
    font-size: 11px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
}
</style>
