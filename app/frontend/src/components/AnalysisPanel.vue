<template>
  <section class="analysis-panel">
    <div class="panel-header">
      <div>
        <div class="panel-title">解析详情</div>
        <div class="panel-subtitle">所有内容都按结构化文本渲染</div>
      </div>
      <el-tag type="success" effect="light">Safe Render</el-tag>
    </div>

    <div v-if="data" class="analysis-grid">
      <section class="content-block">
        <div class="block-title">思路分析</div>
        <ol class="text-list">
          <li v-for="(item, index) in (data.analysis || [])" :key="`analysis-${index}`" v-html="safeRenderMath(item)">
          </li>
        </ol>
      </section>

      <section class="content-block">
        <div class="block-title">详细解答</div>
        <ol class="text-list">
          <li v-for="(item, index) in (data.solution || [])" :key="`solution-${index}`" v-html="safeRenderMath(item)">
          </li>
        </ol>
      </section>

      <section class="content-block">
        <div class="block-title">知识点归纳</div>
        <div class="knowledge-list">
          <el-tag v-for="(item, index) in (data.knowledge || [])" :key="`knowledge-${index}`" size="large" effect="plain" v-html="safeRenderMath(item)">
          </el-tag>
        </div>
      </section>
    </div>
  </section>
</template>

<script setup>
import { renderMath } from '../utils/mathHandler';
defineProps({
  data: { type: Object, default: null },
});

const safeRenderMath = (text) => {
  try {
    return renderMath(text);
  } catch (err) {
    console.error('Render math error:', err);
    return text;
  }
};
</script>

<style scoped>
.panel-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.panel-title {
  font-size: 18px;
  font-weight: 650;
  color: #0f172a;
  letter-spacing: -0.02em;
}

.panel-subtitle {
  font-size: 13px;
  color: #6b7280;
  margin-top: 4px;
}

.analysis-grid {
  display: grid;
  gap: 28px;
  margin-top: 18px;
}

.content-block {
  padding-top: 4px;
  border-top: 1px solid #eef2f7;
  padding-top: 20px;
}

.block-title {
  color: #111827;
  font-size: 17px;
  font-weight: 600;
  margin-bottom: 12px;
}

.text-list {
  margin: 0;
  padding-left: 20px;
  color: #334155;
  line-height: 1.8;
}

.text-list li + li {
  margin-top: 10px;
}

.knowledge-list {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}
</style>
