<template>
  <div class="settings-page">
    <div class="settings-page-header">
      <div>
        <div class="workspace-title">模型设置</div>
        <div class="workspace-subtitle">配置后端网关和上游模型服务</div>
      </div>
      <div class="settings-summary-inline">
        <div class="settings-summary-label">当前生效</div>
        <div class="settings-summary-main">{{ providerLabel }}</div>
        <div class="settings-summary-sub">{{ modelName }}</div>
      </div>
    </div>
    <div class="settings-modal settings-modal-page">

      <div class="settings-grid">
        <section class="settings-section">
          <div class="settings-card-title">1. 后端网关</div>
          <div class="settings-card-tip">这里是你本地 FastAPI 服务地址，不是大模型厂商地址。</div>
          <el-form label-position="top">
            <el-form-item label="Gateway 地址">
              <el-input v-model="apiBase" placeholder="http://127.0.0.1:8001" />
            </el-form-item>
          </el-form>
          <div class="status-strip">
            <span class="status-pill">{{ backendHealth }}</span>
            <span class="status-note">历史记录和解析请求都会经过这里。</span>
          </div>
        </section>

        <section class="settings-section settings-section-main">
          <div class="settings-card-title">2. 上游模型服务</div>
          <div class="settings-card-tip">可以先选预设，再按需微调模型名或 Base URL。</div>

          <div class="preset-grid">
            <button
              v-for="preset in providerPresets"
              :key="preset.id"
              type="button"
              class="preset-chip"
              :class="{ active: providerPreset === preset.id }"
              @click="applyPreset(preset.id)"
            >
              <span class="preset-chip-title">{{ preset.label }}</span>
              <span class="preset-chip-text">{{ preset.description }}</span>
            </button>
          </div>

          <el-form label-position="top" class="settings-form">
            <el-form-item label="接入协议">
              <el-select v-model="provider" style="width: 100%">
                <el-option label="Gemini 原生接口" value="gemini" />
                <el-option label="OpenAI 兼容接口" value="openai_compatible" />
              </el-select>
            </el-form-item>

            <el-form-item v-if="requiresUpstreamBaseUrl" label="上游 Base URL">
              <el-input v-model="upstreamBaseUrl" placeholder="https://api.openai.com/v1" />
            </el-form-item>

            <el-form-item :label="apiKeyOptional ? 'API Key（可选）' : 'API Key'">
              <el-input v-model="apiKey" type="password" show-password :placeholder="apiKeyPlaceholder" />
            </el-form-item>

            <el-form-item label="模型名称">
              <el-input v-model="modelName" placeholder="例如：gemini-3.1-flash-lite-preview / deepseek-chat / gpt-4.1-mini" />
            </el-form-item>
          </el-form>

          <div class="model-suggestions">
            <div class="model-suggestions-label">快捷填写</div>
            <div class="model-suggestions-list">
              <button
                v-for="suggestion in activeModelSuggestions"
                :key="suggestion"
                type="button"
                class="model-chip"
                @click="modelName = suggestion"
              >
                {{ suggestion }}
              </button>
            </div>
          </div>
        </section>
      </div>

      <section class="settings-footnote">
        <div class="footnote-title">如果要接入其他厂商大模型</div>
        <div class="footnote-list">
          <div>Gemini 官方：选择 `Gemini 原生接口`，填 Google API Key。</div>
          <div>DeepSeek、Qwen 兼容模式、SiliconFlow、OpenAI、Ollama：选择 `OpenAI 兼容接口`，再填对应 `Base URL + API Key + 模型名`。</div>
          <div>只要对方提供 OpenAI 兼容 `/v1/chat/completions`，这套设置基本都能接。</div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { Fold } from '@element-plus/icons-vue';
import {
  apiBase,
  apiKey,
  apiKeyOptional,
  apiKeyPlaceholder,
  activeModelSuggestions,
  applyPreset,
  backendHealth,
  modelName,
  provider,
  providerLabel,
  providerPreset,
  providerPresets,
  requiresUpstreamBaseUrl,
  upstreamBaseUrl,
} from '../stores/appStore';
</script>

<style scoped>
.settings-page {
  width: min(860px, calc(100% - 24px));
  margin-left: auto;
  margin-right: auto;
}

.settings-page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 22px;
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

.settings-modal {
  color: #0f172a;
  padding: 0;
  background: transparent;
  border: 0;
  box-shadow: none;
}

.settings-modal-page {
  padding: 0;
}

.settings-summary-inline {
  text-align: right;
}

.settings-summary-inline .settings-summary-label {
  color: #7a8799;
  font-size: 12px;
}

.settings-summary-inline .settings-summary-main {
  margin-top: 4px;
  color: #253246;
  font-size: 16px;
  font-weight: 500;
}

.settings-summary-inline .settings-summary-sub {
  margin-top: 2px;
  color: #66758a;
  font-size: 12px;
  line-height: 1.5;
  word-break: break-word;
}

.settings-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 24px;
  align-items: start;
}

.settings-section {
  padding: 4px 0 0;
}

.settings-section-main {
  padding-left: 0;
  padding-top: 18px;
  border-left: 0;
  border-top: 1px solid #e8edf5;
}

.settings-card-title {
  color: #253246;
  font-size: 17px;
  font-weight: 500;
  line-height: 1.45;
}

.settings-card-tip {
  margin-top: 4px;
  color: #6c7b8f;
  font-size: 13px;
  line-height: 1.68;
}

.status-strip {
  margin-top: 8px;
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  min-height: 32px;
  padding: 0 12px;
  border-radius: 999px;
  background: #f3f6fb;
  color: #5e759a;
  font-size: 12px;
  font-weight: 500;
}

.status-note {
  color: #6c7b8f;
  font-size: 12px;
}

.preset-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-top: 16px;
}

.preset-chip {
  width: 100%;
  padding: 14px;
  border: 1px solid #e4e9f3;
  border-radius: 14px;
  background: transparent;
  text-align: left;
  cursor: pointer;
  transition: border-color 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease;
}

.preset-chip:hover,
.preset-chip.active {
  border-color: #b9c8dc;
  transform: none;
  box-shadow: none;
  background: #fafcff;
}

.preset-chip-title {
  display: block;
  color: #2a3648;
  font-size: 14px;
  font-weight: 500;
}

.preset-chip-text {
  display: block;
  margin-top: 6px;
  color: #6c7b8f;
  font-size: 12px;
  line-height: 1.6;
}

.settings-form {
  margin-top: 16px;
}

.model-suggestions {
  margin-top: 8px;
  padding-top: 14px;
  border-top: 1px solid #edf1f6;
}

.model-suggestions-label {
  color: #6c7b8f;
  font-size: 12px;
  margin-bottom: 10px;
}

.model-suggestions-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.model-chip {
  border: 1px solid #dfe7f4;
  background: transparent;
  color: #5a6f93;
  border-radius: 999px;
  min-height: 34px;
  padding: 0 12px;
  cursor: pointer;
  font: inherit;
}

.settings-footnote {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #e8edf5;
}

.footnote-title {
  color: #253246;
  font-size: 15px;
  font-weight: 500;
  margin-bottom: 8px;
}

.footnote-list {
  display: grid;
  gap: 8px;
  color: #617086;
  font-size: 13px;
  line-height: 1.72;
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

@media (max-width: 768px) {
  .settings-page-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .settings-summary-inline {
    text-align: left;
    margin-top: 16px;
  }

  .settings-section-main {
    padding-left: 0;
    border-left: 0;
    border-top: 1px solid #e8edf5;
    padding-top: 18px;
  }

  .preset-grid {
    grid-template-columns: 1fr;
  }

  .settings-grid {
    grid-template-columns: 1fr;
  }

  .workspace-title {
    font-size: 26px;
  }
}
</style>
