import katex from 'katex';
import 'katex/dist/katex.min.css';

/**
 * 渲染字符串中的 LaTeX 公式
 * 支持 $...$ (行内) 和 $$...$$ (块级)
 * @param {string} text 
 * @returns {string} HTML string
 */
export function renderMath(text) {
  if (!text) return '';
  
  // 简单的正则匹配，实际应用中可能需要更复杂的解析
  // 本实现优先匹配 $$...$$ 块级，再匹配 $...$ 行内
  let processed = text;
  
  // 块级公式 $$...$$
  processed = processed.replace(/\$\$(.*?)\$\$/gs, (match, formula) => {
    try {
      return katex.renderToString(formula, { displayMode: true, throwOnError: false });
    } catch (e) {
      return match;
    }
  });
  
  // 行内公式 $...$
  processed = processed.replace(/\$(.*?)\$/g, (match, formula) => {
    try {
      return katex.renderToString(formula, { displayMode: false, throwOnError: false });
    } catch (e) {
      return match;
    }
  });
  
  return processed;
}
