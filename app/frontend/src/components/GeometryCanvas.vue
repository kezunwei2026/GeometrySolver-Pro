<template>
  <section class="canvas-panel">
    <div class="canvas-header">
      <div>
        <div class="panel-title">{{ title || '几何沙箱' }}</div>
        <div class="panel-subtitle">基于受限 scene 协议渲染，不执行模型代码</div>
      </div>
      <div class="canvas-actions">
        <el-button :disabled="!hasAnimation" @click="togglePlay">
          {{ isPaused ? '继续播放' : '暂停演示' }}
        </el-button>
        <el-button :disabled="!scene" @click="resetAnim">重置</el-button>
      </div>
    </div>

    <div ref="wrapper" class="canvas-wrapper">
      <canvas
        ref="canvasEl"
        @mousedown="handleMouseDown"
        @mousemove="handleMouseMove"
        @mouseup="handleMouseUp"
        @mouseleave="handleMouseUp"
        @wheel.prevent="handleWheel"
        @contextmenu.prevent
      ></canvas>
      <div v-if="loading" class="overlay">AI 正在构建几何模型...</div>
      <div v-else-if="!scene" class="overlay subtle">解析完成后，这里会展示动态图解。</div>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue';
import { MathUtils, createDrawUtils, getAnimatedPoints, validateScene } from '../utils/geoEngine';

const props = defineProps({
  scene: { type: Object, default: null },
  title: { type: String, default: '' },
  loading: { type: Boolean, default: false },
});

const wrapper = ref(null);
const canvasEl = ref(null);
const isPaused = ref(false);
const animT = ref(0);
const dragging = ref(null);
const isPanning = ref(false);
const lastMousePos = ref({ x: 0, y: 0 });
const localScene = ref(null);

let ctx = null;
let raf = null;
let dpr = 1;

const hasAnimation = computed(() => (localScene.value?.animations?.length || 0) > 0);

const buildRuntimePoints = () => {
  if (!localScene.value) return {};
  const runtimePoints = getAnimatedPoints(localScene.value, animT.value);
  if (dragging.value && localScene.value.points[dragging.value]) {
    runtimePoints[dragging.value] = { ...localScene.value.points[dragging.value] };
  }
  return runtimePoints;
};

const resize = () => {
  if (!wrapper.value || !canvasEl.value) return;
  const rect = wrapper.value.getBoundingClientRect();
  dpr = window.devicePixelRatio || 1;
  canvasEl.value.width = rect.width * dpr;
  canvasEl.value.height = rect.height * dpr;
  ctx = canvasEl.value.getContext('2d');
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.scale(dpr, dpr);
  render();
};

const render = () => {
  if (!ctx || !canvasEl.value || !localScene.value) return;
  const width = canvasEl.value.width / dpr;
  const height = canvasEl.value.height / dpr;
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.clearRect(0, 0, canvasEl.value.width, canvasEl.value.height);
  ctx.scale(dpr, dpr);

  const runtimePoints = buildRuntimePoints();
  const u = createDrawUtils(ctx, width, height, localScene.value.viewport);
  u.renderScene(localScene.value, runtimePoints);
};

const loop = () => {
  if (localScene.value && !isPaused.value && hasAnimation.value) {
    animT.value += 0.016; // ~60fps
    render();
  }
  raf = requestAnimationFrame(loop);
};
const getMousePos = (event) => {
  if (!canvasEl.value) return { x: 0, y: 0 };
  const rect = canvasEl.value.getBoundingClientRect();
  return { x: event.clientX - rect.left, y: event.clientY - rect.top };
};

const handleWheel = (event) => {
  if (!localScene.value) return;
  const zoomSpeed = 0.1;
  const mouse = getMousePos(event);
  const v = localScene.value.viewport;
  const oldScale = v.scale;
  
  const delta = event.deltaY > 0 ? 1 / (1 + zoomSpeed) : (1 + zoomSpeed);
  const newScale = Math.max(5, Math.min(500, oldScale * delta));
  
  const mathX = (mouse.x - v.origin.x) / oldScale;
  const mathY = (v.origin.y - mouse.y) / oldScale;
  
  v.scale = newScale;
  v.origin.x = mouse.x - mathX * newScale;
  v.origin.y = mouse.y + mathY * newScale;
  
  render();
};

const handleMouseDown = (event) => {
  if (!localScene.value) return;
  const mouse = getMousePos(event);
  lastMousePos.value = mouse;

  if (event.button === 0) {
    const runtimePoints = buildRuntimePoints();
    const u = createDrawUtils(ctx, canvasEl.value.width / dpr, canvasEl.value.height / dpr, localScene.value.viewport);
    
    for (const [name, point] of Object.entries(runtimePoints)) {
      if (!point.draggable) continue;
      const pixelPoint = u.projectPoint(point);
      if (MathUtils.dist(mouse, pixelPoint) < 16) {
        dragging.value = name;
        if (localScene.value.animations?.length) {
          localScene.value.animations = localScene.value.animations.filter((item) => item.point !== name);
        }
        return;
      }
    }
  }
  isPanning.value = true;
};

const handleMouseMove = (event) => {
  if (!localScene.value) return;
  const mouse = getMousePos(event);
  const dx = mouse.x - lastMousePos.value.x;
  const dy = mouse.y - lastMousePos.value.y;

  if (dragging.value) {
    const u = createDrawUtils(ctx, canvasEl.value.width / dpr, canvasEl.value.height / dpr, localScene.value.viewport);
    const scenePoint = localScene.value.points[dragging.value];
    const converted = u.unprojectPoint(mouse, scenePoint.space || localScene.value.mode);
    localScene.value.points[dragging.value] = { ...scenePoint, ...converted };
  } else if (isPanning.value) {
    const v = localScene.value.viewport;
    v.origin.x += dx;
    v.origin.y += dy;
  }

  lastMousePos.value = mouse;
  render();
};

const handleMouseUp = () => {
  dragging.value = null;
  isPanning.value = false;
};

const togglePlay = () => {
  if (hasAnimation.value) {
    isPaused.value = !isPaused.value;
  }
};

const resetAnim = () => {
  animT.value = 0;
  render();
};

watch(
  () => props.scene,
  (value) => {
    localScene.value = value ? validateScene(value) : null;
    isPaused.value = false;
    animT.value = 0;
    render();
  },
  { immediate: true }
);

onMounted(() => {
  resize();
  window.addEventListener('resize', resize);
  loop();
});

onUnmounted(() => {
  window.removeEventListener('resize', resize);
  if (raf) cancelAnimationFrame(raf);
});
</script>

<style scoped>
.canvas-panel {
  padding-top: 8px;
}

.canvas-header {
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

.canvas-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.canvas-wrapper {
  position: relative;
  height: 560px;
  border-radius: 22px;
  overflow: hidden;
  background: linear-gradient(180deg, #ffffff, #f5f8fd);
  border: 1px solid #edf1f7;
}

canvas {
  display: block;
  width: 100%;
  height: 100%;
}

.overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  text-align: center;
  color: #0f172a;
  background: rgba(255, 255, 255, 0.78);
  backdrop-filter: blur(10px);
}

.overlay.subtle {
  color: #64748b;
}
</style>
