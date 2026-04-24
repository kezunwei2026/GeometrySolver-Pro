import { computed, ref, watch } from 'vue';
import axios from 'axios';
import { ElMessage } from 'element-plus';

const getDefaultApiBase = () => {
  if (typeof window === 'undefined') return 'http://127.0.0.1:8001';
  const { hostname, protocol } = window.location;
  const backendProtocol = protocol === 'https:' ? 'https:' : 'http:';
  return `${backendProtocol}//${hostname}:8001`;
};

export const DEFAULT_API_BASE = getDefaultApiBase();

export const STORAGE_KEYS = {
  apiBase: 'apiBase',
  provider: 'modelProvider',
  providerPreset: 'providerPreset',
  upstreamBaseUrl: 'upstreamBaseUrl',
  modelName: 'modelName',
  apiKey: 'apiKey',
};

export const providerPresets = [
  {
    id: 'gemini',
    label: 'Google Gemini',
    description: '官方原生接口，适合直接接 Google',
    provider: 'gemini',
    upstreamBaseUrl: '',
    model: 'gemini-3.1-flash-lite-preview',
    apiKeyPlaceholder: 'AIza...',
    suggestions: ['gemini-3.1-flash-lite-preview', 'gemini-2.5-flash', 'gemini-2.5-flash-lite', 'gemini-1.5-pro'],
  },
  {
    id: 'openai',
    label: 'OpenAI',
    description: '官方 OpenAI 接口',
    provider: 'openai_compatible',
    upstreamBaseUrl: 'https://api.openai.com/v1',
    model: 'gpt-4o-mini',
    apiKeyPlaceholder: 'sk-...',
    suggestions: ['gpt-4o-mini', 'gpt-4.1', 'gpt-4o-mini'],
  },
  {
    id: 'deepseek',
    label: 'DeepSeek',
    description: 'OpenAI 兼容，常用 `deepseek-chat`',
    provider: 'openai_compatible',
    upstreamBaseUrl: 'https://api.deepseek.com/v1',
    model: 'deepseek-chat',
    apiKeyPlaceholder: 'sk-...',
    suggestions: ['deepseek-chat', 'deepseek-reasoner'],
  },
  {
    id: 'dashscope',
    label: 'Qwen / 百炼',
    description: '阿里云兼容模式接入 Qwen',
    provider: 'openai_compatible',
    upstreamBaseUrl: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    model: 'qwen-plus',
    apiKeyPlaceholder: 'sk-...',
    suggestions: ['qwen-plus', 'qwen-turbo', 'qwen-vl-plus'],
  },
  {
    id: 'siliconflow',
    label: 'SiliconFlow',
    description: '兼容接口，可接多种开源模型',
    provider: 'openai_compatible',
    upstreamBaseUrl: 'https://api.siliconflow.cn/v1',
    model: 'deepseek-ai/DeepSeek-V3',
    apiKeyPlaceholder: 'sk-...',
    suggestions: ['deepseek-ai/DeepSeek-V3', 'Qwen/Qwen2.5-72B-Instruct'],
  },
  {
    id: 'ollama',
    label: '本地 Ollama',
    description: '本地 OpenAI 兼容服务，可不填 Key',
    provider: 'openai_compatible',
    upstreamBaseUrl: 'http://127.0.0.1:11434/v1',
    model: 'qwen2.5vl:7b',
    apiKeyPlaceholder: '本地服务可留空',
    suggestions: ['qwen2.5vl:7b', 'llava:7b', 'gemma3:12b'],
  },
];

export const getPresetById = (presetId) => providerPresets.find((item) => item.id === presetId) || null;
export const defaultModelForProvider = (providerValue) => (providerValue === 'openai_compatible' ? 'gpt-4o-mini' : 'gemini-3.1-flash-lite-preview');
export const isLocalBaseUrl = (url) => /^http:\/\/(127\.0\.0\.1|localhost)/i.test((url || '').trim());
export const modelSupportsImages = (providerValue, modelValue) => {
  const model = (modelValue || '').trim().toLowerCase();
  if (providerValue === 'gemini') return true;
  return /(?:^|[-_/])(vl|vision)(?:[-_/]|$)|gpt-4o|gpt-4\.1|llava|qwen2\.5vl|qwen-vl|gemma3/i.test(model);
};

export const loading = ref(false);
export const aiResponse = ref(null);
export const apiBase = ref(localStorage.getItem(STORAGE_KEYS.apiBase) || DEFAULT_API_BASE);
export const apiKey = ref(localStorage.getItem(STORAGE_KEYS.apiKey) || '');
export const provider = ref(localStorage.getItem(STORAGE_KEYS.provider) || 'gemini');
export const providerPreset = ref(localStorage.getItem(STORAGE_KEYS.providerPreset) || 'gemini');
export const upstreamBaseUrl = ref(localStorage.getItem(STORAGE_KEYS.upstreamBaseUrl) || '');
export const modelName = ref(localStorage.getItem(STORAGE_KEYS.modelName) || 'gemini-3.1-flash-lite-preview');
export const backendHealth = ref('未检查');
export const historyList = ref([]);
export const composerResetKey = ref(0);

let healthCheckSeq = 0;

export const selectedPreset = computed(() => getPresetById(providerPreset.value));
export const requiresUpstreamBaseUrl = computed(() => provider.value === 'openai_compatible');
export const allowImageInput = computed(() => modelSupportsImages(provider.value, modelName.value));
export const imageSupportHint = computed(() => {
  if (allowImageInput.value) return '';
  return '当前模型不支持图片输入，请改用支持视觉的模型，或仅提交文本题目。';
});
export const activeModelSuggestions = computed(() => {
  if (selectedPreset.value?.provider === provider.value) {
    return selectedPreset.value.suggestions;
  }
  return provider.value === 'openai_compatible'
    ? ['gpt-4o-mini', 'deepseek-chat', 'qwen-plus']
    : ['gemini-3.1-flash-lite-preview', 'gemini-2.5-flash', 'gemini-2.5-flash-lite', 'gemini-1.5-pro'];
});
export const providerLabel = computed(() => {
  if (selectedPreset.value?.provider === provider.value) {
    return selectedPreset.value.label;
  }
  return provider.value === 'openai_compatible' ? 'OpenAI 兼容接口' : 'Google Gemini';
});
export const apiKeyOptional = computed(() => provider.value === 'openai_compatible' && isLocalBaseUrl(upstreamBaseUrl.value));
export const apiKeyPlaceholder = computed(() => {
  if (selectedPreset.value?.provider === provider.value) {
    return selectedPreset.value.apiKeyPlaceholder;
  }
  return provider.value === 'openai_compatible' ? 'sk-...' : 'AIza...';
});

export function applyPreset(presetId) {
  const preset = getPresetById(presetId);
  if (!preset) return;
  providerPreset.value = preset.id;
  provider.value = preset.provider;
  upstreamBaseUrl.value = preset.upstreamBaseUrl;
  modelName.value = preset.model;
}

export function apiClient() {
  return axios.create({
    baseURL: apiBase.value.trim() || DEFAULT_API_BASE,
    timeout: 250000,
    headers: apiKey.value ? { Authorization: `Bearer ${apiKey.value.trim()}` } : {},
  });
}

export function clearStoredSettings() {
  Object.values(STORAGE_KEYS).forEach((key) => localStorage.removeItem(key));
}

export function resetSession(router) {
  aiResponse.value = null;
  composerResetKey.value += 1;
  showComposer.value = true;
  if (router) router.push('/');
  ElMessage.success('当前会话已清空');
}

export async function checkHealth() {
  const seq = ++healthCheckSeq;
  try {
    const { data } = await apiClient().get('/health');
    if (seq === healthCheckSeq) {
      backendHealth.value = data?.ok ? '网关在线' : '网关异常';
    }
  } catch {
    if (seq === healthCheckSeq) {
      backendHealth.value = '网关离线';
    }
  }
}

export async function refreshHistory(showMsg = false) {
  try {
    const { data } = await apiClient().get('/history');
    historyList.value = data;
  } catch {
    if (showMsg) ElMessage.error('获取历史失败');
  }
}

export async function sendToAI(payload, router) {
  if (!apiKey.value.trim() && !apiKeyOptional.value) {
    ElMessage.warning('请先在设置里填写对应服务商的 API Key');
    if (router) router.push('/settings');
    return;
  }

  loading.value = true;
  const normalizedApiBase = apiBase.value.trim() || DEFAULT_API_BASE;
  const normalizedUpstreamBaseUrl = upstreamBaseUrl.value.trim();

  const requestPayload = {
    ...payload,
    provider: provider.value,
    model: modelName.value.trim() || defaultModelForProvider(provider.value),
    upstream_base_url: requiresUpstreamBaseUrl.value ? normalizedUpstreamBaseUrl : null,
  };

  try {
    const { data } = await apiClient().post('/solve', requestPayload);
    aiResponse.value = data;
    apiBase.value = normalizedApiBase;
    upstreamBaseUrl.value = normalizedUpstreamBaseUrl;
    ElMessage.success('解析完成');
    refreshHistory();
  } catch (error) {
    const status = error?.response?.status;
    let detail = error?.response?.data?.detail || error?.message || '请求失败';

    if (status === 503) {
      detail = '模型服务繁忙，稍后再试会更稳。';
    } else if (status === 429) {
      detail = '请求频率过快，或当前服务商额度已用尽。';
    } else if (status === 401) {
      detail = 'API Key 校验未通过，或当前模型无权限调用。';
    } else if (error?.code === 'ECONNABORTED') {
      detail = '请求超时：可能是网络较慢，也可能是模型思考时间较长。';
    }

    ElMessage({
      message: detail,
      type: status >= 500 ? 'warning' : 'error',
      duration: 5000,
      showClose: true,
    });
  } finally {
    loading.value = false;
  }
}

export const showComposer = ref(true);

export function loadHistory(item, router) {
  aiResponse.value = item.response_data;
  showComposer.value = false;
  if (router) router.push('/');
  ElMessage.success('记录已加载');
}

watch(
  [apiBase, apiKey, provider, providerPreset, upstreamBaseUrl, modelName],
  ([nextApiBase, nextApiKey, nextProvider, nextPreset, nextUpstreamBaseUrl, nextModelName]) => {
    localStorage.setItem(STORAGE_KEYS.apiBase, nextApiBase);
    localStorage.setItem(STORAGE_KEYS.apiKey, nextApiKey);
    localStorage.setItem(STORAGE_KEYS.provider, nextProvider);
    localStorage.setItem(STORAGE_KEYS.providerPreset, nextPreset);
    localStorage.setItem(STORAGE_KEYS.upstreamBaseUrl, nextUpstreamBaseUrl);
    localStorage.setItem(STORAGE_KEYS.modelName, nextModelName);
  }
);

watch(
  provider,
  (nextProvider, previousProvider) => {
    if (selectedPreset.value?.provider !== nextProvider) {
      providerPreset.value = 'custom';
    }
    if (!modelName.value.trim() || modelName.value === defaultModelForProvider(previousProvider)) {
      modelName.value = defaultModelForProvider(nextProvider);
    }
    if (nextProvider === 'gemini') {
      upstreamBaseUrl.value = '';
    } else if (!upstreamBaseUrl.value.trim()) {
      upstreamBaseUrl.value = 'https://api.openai.com/v1';
    }
  }
);

watch(
  apiBase,
  () => {
    backendHealth.value = '检查中';
    checkHealth();
    refreshHistory();
  },
  { immediate: true }
);

export function initStore() {
  // Migrate legacy model names to the one that works for you
  if (modelName.value === 'gemini-1.5-flash' || modelName.value === 'gemini-1.5-flash-latest') {
    modelName.value = 'gemini-3.1-flash-lite-preview';
  }
  if (modelName.value === 'gpt-4.1-mini') {
    modelName.value = 'gpt-4o-mini';
  }

  if (!getPresetById(providerPreset.value)) {
    providerPreset.value = 'custom';
  }
}
