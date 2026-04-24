# 前端说明

这是应用端前端工程，技术栈为：

- Vue 3
- Vite
- Element Plus

## 本地开发

```bash
npm install
npm run dev
```

## 生产构建

```bash
npm run build
```

## 当前原则

- 不渲染模型返回的 HTML
- 不执行模型返回的 JavaScript
- 所有几何演示都基于 `scene` JSON 协议绘制
- API Key 只保留在当前页面会话内存中
