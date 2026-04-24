<template>
  <div class="history-page">
    <header class="history-page-header">
      <div>
        <div class="workspace-title">历史记录</div>
        <div class="workspace-subtitle">浏览和回溯之前的几何解析结果，点击任意记录即可加载到工作台。</div>
      </div>
      <button class="settings-toggle" type="button" @click="$router.push('/')">
        <el-icon><Fold /></el-icon>
        <span>返回工作台</span>
      </button>
    </header>

    <div v-if="historyList.length === 0" class="history-empty-state">
      <div class="history-empty-icon">
        <el-icon :size="48"><Clock /></el-icon>
      </div>
      <div class="history-empty-title">暂无历史记录</div>
      <div class="history-empty-text">完成一次解析后，这里会显示最近的题目。</div>
      <button class="settings-toggle" type="button" @click="$router.push('/')">
        <el-icon><Plus /></el-icon>
        <span>开始第一次解析</span>
      </button>
    </div>

    <div v-else class="history-grid">
      <button
        v-for="item in historyList"
        :key="item.id"
        type="button"
        class="history-card"
        @click="handleLoad(item)"
      >
        <div class="history-card-header">
          <div class="history-card-title">{{ item.response_data?.title || '未命名解析' }}</div>
          <span class="history-card-time">{{ formatTime(item.timestamp) }}</span>
        </div>
        <div class="history-card-problem">{{ item.problem }}</div>
        <div v-if="item.response_data?.scene?.shapes?.length" class="history-card-meta">
          <span class="history-card-tag">{{ item.response_data.scene.shapes.length }} 个图形</span>
          <span v-if="item.response_data.scene.points" class="history-card-tag">{{ Object.keys(item.response_data.scene.points).length }} 个点</span>
        </div>
      </button>
    </div>
  </div>
</template>

<script setup>
import { Clock, Fold, Plus } from '@element-plus/icons-vue';
import { useRouter } from 'vue-router';
import {
  historyList,
  loadHistory,
} from '../stores/appStore';

const router = useRouter();

const handleLoad = (item) => {
  loadHistory(item);
  router.push('/');
};

const formatTime = (ts) => {
  if (!ts) return '';
  const d = new Date(ts * 1000);
  const now = new Date();
  const diffMs = now - d;
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 1) return '刚刚';
  if (diffMin < 60) return `${diffMin} 分钟前`;
  const diffHour = Math.floor(diffMin / 60);
  if (diffHour < 24) return `${diffHour} 小时前`;
  const diffDay = Math.floor(diffHour / 24);
  if (diffDay < 7) return `${diffDay} 天前`;
  return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
};
</script>

<style scoped>
.history-page {
  width: min(860px, calc(100% - 24px));
  margin-left: auto;
  margin-right: auto;
}

.history-page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 30px;
}

.workspace-title {
  color: #243042;
  font-size: 32px;
  line-height: 1.14;
  letter-spacing: -0.03em;
  font-weight: 500;
  margin-bottom: 8px;
}

.workspace-subtitle {
  color: #66758a;
  font-size: 15px;
  line-height: 1.72;
}

.settings-toggle {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 42px;
  padding: 0 14px;
  border: 1px solid #e2e8f3;
  border-radius: 999px;
  background: #f8fbff;
  color: #334155;
  cursor: pointer;
  font: inherit;
  white-space: nowrap;
}

.history-empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  text-align: center;
}

.history-empty-icon {
  color: #c5cdd8;
  margin-bottom: 16px;
}

.history-empty-title {
  color: #111827;
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 6px;
}

.history-empty-text {
  color: #6b7280;
  font-size: 14px;
  line-height: 1.7;
  margin-bottom: 20px;
}

.history-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.history-card {
  width: 100%;
  padding: 18px;
  border: 1px solid #e4e9f3;
  border-radius: 16px;
  background: transparent;
  text-align: left;
  cursor: pointer;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.history-card:hover {
  border-color: #b9c8dc;
  background: #fafcff;
  box-shadow: 0 4px 16px rgba(79, 124, 255, 0.06);
}

.history-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
}

.history-card-title {
  color: #111827;
  font-size: 15px;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.history-card-time {
  color: #9ca3af;
  font-size: 12px;
  white-space: nowrap;
}

.history-card-problem {
  color: #6b7280;
  font-size: 13px;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.history-card-meta {
  display: flex;
  gap: 8px;
  margin-top: 10px;
}

.history-card-tag {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding: 0 8px;
  border-radius: 999px;
  background: #f3f6fb;
  color: #5e759a;
  font-size: 11px;
  font-weight: 500;
}

@media (max-width: 768px) {
  .history-page {
    width: min(680px, calc(100% - 20px));
  }

  .workspace-title {
    font-size: 26px;
  }

  .history-page-header {
    flex-direction: column;
  }

  .history-grid {
    grid-template-columns: 1fr;
  }
}
</style>
