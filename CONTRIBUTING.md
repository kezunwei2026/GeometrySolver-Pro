# 贡献指南 (Contributing Guide)

感谢你对 **Geometry Solver Pro** 的关注！我们非常欢迎来自社区的贡献。无论是修复 Bug、改进文档，还是增加新的几何模型，你的帮助都非常有意义。

## 如何参与

### 1. 提交 Issue
如果你发现了 Bug 或有新功能的想法，请先提交一个 [Issue](https://github.com/kezunwei2026/GeometrySolver-Pro/issues)。
*   **Bug 报告**：请描述问题的现象、如何复现以及你的运行环境。
*   **功能建议**：请描述你希望增加的功能及其应用场景。

### 2. 提交 Pull Request (PR)
1.  Fork 本仓库。
2.  创建一个新的分支 (`git checkout -b feature/your-feature` 或 `git checkout -b fix/your-bug`)。
3.  提交你的修改。
4.  确保代码风格一致，并尽可能添加测试。
5.  推送到你的仓库并提交 Pull Request。

## 几何模型贡献
如果你想增加新的几何模型：
1.  在 `app/backend/solver/models.py` (或相应逻辑层) 中实现计算逻辑。
2.  在 `app/frontend/src/components/ProblemInput.vue` 的 `examples` 数组中添加对应的标签和描述。
3.  确保模型能够生成正确的 LaTeX 描述和 Canvas 绘图指令。

## 代码规范
*   **后端**：遵循 PEP 8 规范，使用异步 (Async/Await) 处理请求。
*   **前端**：使用 Vue 3 (Composition API)，保持组件简洁。
*   **文档**：注释请尽量使用中文，方便国内用户和开发者理解。

## 社区公约
请遵守我们的 [Code of Conduct](CODE_OF_CONDUCT.md)。保持尊重，共同维护良好的开源环境。
