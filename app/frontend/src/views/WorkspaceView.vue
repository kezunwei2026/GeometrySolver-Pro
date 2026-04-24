<template>
  <div class="workspace-page">
    <section class="workspace-main">
      <header class="workspace-topbar">
        <div>
          <div class="workspace-title">几何推理</div>
          <div class="workspace-subtitle">输入题目或上传图片，让 AI 生成结构化解析与动态图解。</div>
        </div>
        <button class="settings-toggle" type="button" @click="$router.push('/settings')">
          <el-icon><Setting /></el-icon>
          <span>打开设置页</span>
        </button>
      </header>

      <section v-if="showComposer" class="composer-section">
        <ProblemInput
          :key="composerResetKey"
          :loading="loading"
          :allow-image="allowImageInput"
          :image-support-hint="imageSupportHint"
          @solve="(p) => sendToAI(p, $router)"
        />
      </section>

      <section v-if="loading && !aiResponse" class="pending-state">
        <div class="pending-title">AI 正在思考中</div>
        <div class="pending-text">结果生成后，这里会显示几何沙箱和解析内容。</div>
      </section>

      <section v-if="aiResponse" class="result-section">
        <GeometryCanvas :scene="aiResponse?.scene" :title="aiResponse?.title" :loading="loading" />
      </section>

      <section v-if="aiResponse" class="result-section">
        <AnalysisPanel :data="aiResponse" />
      </section>
    </section>
  </div>
</template>

<script setup>
import { Setting } from '@element-plus/icons-vue';
import ProblemInput from '../components/ProblemInput.vue';
import GeometryCanvas from '../components/GeometryCanvas.vue';
import AnalysisPanel from '../components/AnalysisPanel.vue';
import {
  aiResponse,
  allowImageInput,
  composerResetKey,
  imageSupportHint,
  loading,
  sendToAI,
  showComposer,
} from '../stores/appStore';
</script>

<style scoped>
.workspace-page {
  width: min(860px, calc(100% - 24px));
  margin-left: auto;
  margin-right: auto;
}

.workspace-main {
  min-width: 0;
}

.workspace-topbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 30px;
  width: 100%;
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

.composer-section,
.result-section {
  margin-top: 18px;
  width: 100%;
}

.pending-state {
  margin-top: 18px;
  padding: 4px 0 0;
  width: 100%;
}

.pending-title {
  color: #111827;
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 6px;
}

.pending-text {
  color: #6b7280;
  font-size: 14px;
  line-height: 1.7;
}

@media (max-width: 768px) {
  .workspace-page {
    width: min(680px, calc(100% - 20px));
  }

  .workspace-title {
    font-size: 26px;
  }

  .workspace-topbar,
  .composer-section,
  .pending-state,
  .result-section {
    width: 100%;
  }
}
</style>
