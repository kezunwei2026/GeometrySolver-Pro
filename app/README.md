# 应用端说明

当前项目已经重构为前后端分离的应用端：

- `backend/`: FastAPI 服务，支持 `Gemini` 和 `OpenAI 兼容接口` 两种上游方式，并把模型输出归一化为安全的 `scene` 协议。
- `frontend/`: Vue 3 + Element Plus 应用，只渲染结构化文本和受限绘图场景，不执行模型代码。

## 启动

### 1. 配置后端环境变量
复制 `backend/.env.example` 为 `backend/.env`，然后填写：

```bash
MODEL_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-flash-latest
OPENAI_API_KEY=your_openai_compatible_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
GEMINI_TIMEOUT_SECONDS=180
```

说明：

- `MODEL_PROVIDER=gemini` 时，后端默认走 Gemini。
- `MODEL_PROVIDER=openai_compatible` 时，后端默认走 OpenAI 兼容接口。
- 前端设置面板里也可以按请求临时切换服务商、模型和上游 Base URL，不一定依赖后端默认值。

### 2. 启动后端

```bash
cd backend
pip install -r requirements.txt
python main.py
```

默认运行在 `http://127.0.0.1:8001`。

说明：
- 推荐使用 Python 3.10+ 环境。

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev
```

默认运行在 `http://127.0.0.1:5173`。

## 当前协议

后端返回结构：

- `title`
- `analysis: string[]`
- `solution: string[]`
- `knowledge: string[]`
- `scene`

其中 `scene` 使用受限 JSON 协议描述点、线、圆、标签、数值和动画。前端不会执行任意 JavaScript，也不会直接渲染模型返回的 HTML。

## 安全注意事项

- 不要把真实 API Key 提交到仓库。
- 后端优先从 `Authorization: Bearer <key>` 读取密钥；如果前端未传，则回退到当前服务商对应的环境变量。
- 对于本地 `Ollama` 这类开放在 `127.0.0.1` / `localhost` 的 OpenAI 兼容服务，前端可以不填 API Key。
- 图片输入已限制格式和大小，但仍建议在反向代理层增加请求体限制。
