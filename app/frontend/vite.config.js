import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',
    port: 5173,
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules/vue')) return 'vue';
          if (id.includes('node_modules/element-plus') || id.includes('@element-plus/icons-vue')) return 'element-plus';
          if (id.includes('node_modules/axios')) return 'axios';
          return undefined;
        },
      },
    },
  },
})
