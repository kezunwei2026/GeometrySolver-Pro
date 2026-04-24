export const MathUtils = {
  dist: (p1, p2) => Math.hypot(p2.x - p1.x, p2.y - p1.y),
  lerp: (p1, p2, t) => ({ x: p1.x + (p2.x - p1.x) * t, y: p1.y + (p2.y - p1.y) * t }),
};

const DEFAULT_VIEWPORT = {
  width: 800,
  height: 600,
  origin: { x: 400, y: 300 },
  scale: 40,
  showGrid: true,
  showAxes: true,
};

const DEFAULT_SCENE = {
  mode: 'canvas',
  viewport: DEFAULT_VIEWPORT,
  points: {},
  shapes: [],
  animations: [],
};

const clamp = (value, min, max) => Math.max(min, Math.min(max, value));
const safeNumber = (value, fallback = 0) => (Number.isFinite(Number(value)) ? Number(value) : fallback);

export function validateScene(scene) {
  if (!scene || typeof scene !== 'object') return JSON.parse(JSON.stringify(DEFAULT_SCENE));

  const viewport = {
    width: safeNumber(scene.viewport?.width, 800),
    height: safeNumber(scene.viewport?.height, 600),
    origin: {
      x: safeNumber(scene.viewport?.origin?.x, 400),
      y: safeNumber(scene.viewport?.origin?.y, 300),
    },
    scale: clamp(safeNumber(scene.viewport?.scale, 40), 8, 120),
    showGrid: scene.viewport?.showGrid !== false,
    showAxes: scene.viewport?.showAxes !== false,
  };

  const points = {};
  for (const [name, point] of Object.entries(scene.points || {}).slice(0, 24)) {
    points[String(name).slice(0, 12)] = {
      x: safeNumber(point?.x),
      y: safeNumber(point?.y),
      label: String(point?.label || name).slice(0, 12),
      draggable: Boolean(point?.draggable),
      space: point?.space === 'canvas' ? 'canvas' : 'plane',
    };
  }

  const normalizeShape = (shape) => {
    if (!shape || typeof shape !== 'object') return shape;
    const normalized = { ...shape };
    if (normalized.from_ && !normalized.from) {
      normalized.from = normalized.from_;
    }
    if (normalized.valueFrom && typeof normalized.valueFrom === 'object' && normalized.valueFrom.from_ && !normalized.valueFrom.from) {
      normalized.valueFrom = {
        ...normalized.valueFrom,
        from: normalized.valueFrom.from_,
      };
    }
    return normalized;
  };

  return {
    mode: scene.mode === 'plane' ? 'plane' : 'canvas',
    viewport,
    points,
    shapes: Array.isArray(scene.shapes) ? scene.shapes.slice(0, 80).map(normalizeShape) : [],
    animations: Array.isArray(scene.animations) ? scene.animations.slice(0, 8) : [],
  };
}

export function getAnimatedPoints(scene, time) {
  const points = JSON.parse(JSON.stringify(scene.points || {}));
  for (const animation of scene.animations || []) {
    const target = points[animation.point];
    if (!target) continue;

    const duration = clamp(safeNumber(animation.duration, 8), 1, 60);
    const progress = (time / duration) % 1; // 0 to 1 cycle
    const animSpace = animation.space || scene.mode || 'plane';
    
    if (animation.kind === 'line' && animation.from && animation.to) {
      // 使用线性插值来回运动
      const lerpProgress = progress < 0.5 ? progress * 2 : 2 - progress * 2;
      const nextPoint = MathUtils.lerp(animation.from, animation.to, lerpProgress);
      target.x = nextPoint.x;
      target.y = nextPoint.y;
      target.space = animSpace;
    } else if (animation.kind === 'orbit' && animation.center && animation.radius) {
      const angle = (animation.startAngle || 0) + progress * Math.PI * 2;
      target.x = animation.center.x + Math.cos(angle) * animation.radius;
      target.y = animation.center.y + Math.sin(angle) * animation.radius;
      target.space = animSpace;
    }
  }
  return points;
}

export function createDrawUtils(ctx, width, height, viewport = DEFAULT_VIEWPORT) {
  const state = {
    width,
    height,
    origin: viewport.origin || DEFAULT_VIEWPORT.origin,
    scale: viewport.scale || DEFAULT_VIEWPORT.scale,
    mode: 'canvas',
  };

  const projectPoint = (point) => {
    const space = point.space || state.mode;
    if (space === 'canvas') return { x: point.x, y: point.y };
    return {
      x: state.origin.x + point.x * state.scale,
      y: state.origin.y - point.y * state.scale,
    };
  };

  const unprojectPoint = (point, space = state.mode) => {
    if (space === 'canvas') {
      return { x: point.x, y: point.y };
    }
    return {
      x: (point.x - state.origin.x) / state.scale,
      y: (state.origin.y - point.y) / state.scale,
    };
  };

  const drawGrid = () => {
    ctx.save();
    ctx.strokeStyle = 'rgba(148, 163, 184, 0.16)';
    ctx.lineWidth = 1;
    for (let x = 0; x <= state.width; x += 40) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, state.height);
      ctx.stroke();
    }
    for (let y = 0; y <= state.height; y += 40) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(state.width, y);
      ctx.stroke();
    }
    ctx.restore();
  };

  const drawAxes = () => {
    ctx.save();
    ctx.strokeStyle = 'rgba(71, 85, 105, 0.45)';
    ctx.lineWidth = 1.2;
    ctx.beginPath();
    ctx.moveTo(0, state.origin.y);
    ctx.lineTo(state.width, state.origin.y);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(state.origin.x, 0);
    ctx.lineTo(state.origin.x, state.height);
    ctx.stroke();
    ctx.restore();
  };

  const drawPoint = (point) => {
    const pixel = projectPoint(point);
    ctx.beginPath();
    ctx.arc(pixel.x, pixel.y, 4.5, 0, Math.PI * 2);
    ctx.fillStyle = point.draggable ? '#f59e0b' : '#0f172a';
    ctx.fill();
    if (point.label) {
      ctx.fillStyle = '#0f172a';
      ctx.font = '600 13px "Segoe UI", sans-serif';
      ctx.fillText(point.label, pixel.x + 8, pixel.y - 8);
    }
  };

  const drawShape = (shape, points) => {
    const color = shape.color || shape.stroke || '#2563eb';
    const widthValue = safeNumber(shape.width, 2);
    const pointOf = (name) => (points[name] ? projectPoint(points[name]) : null);

    ctx.save();
    ctx.lineWidth = widthValue;
    ctx.strokeStyle = color;
    ctx.fillStyle = shape.fill || 'transparent';
    if (shape.dashed) ctx.setLineDash([6, 6]);

    if (shape.type === 'segment' || shape.type === 'ray' || shape.type === 'line') {
      const from = pointOf(shape.from);
      const to = pointOf(shape.to);
      if (!from || !to) {
        ctx.restore();
        return;
      }
      let start = from;
      let end = to;
      if (shape.type === 'ray' || shape.type === 'line') {
        const dx = to.x - from.x;
        const dy = to.y - from.y;
        const len = Math.hypot(dx, dy) || 1;
        const ux = dx / len;
        const uy = dy / len;
        if (shape.type === 'ray') {
          end = { x: from.x + ux * 2000, y: from.y + uy * 2000 };
        } else {
          start = { x: from.x - ux * 2000, y: from.y - uy * 2000 };
          end = { x: from.x + ux * 2000, y: from.y + uy * 2000 };
        }
      }
      ctx.beginPath();
      ctx.moveTo(start.x, start.y);
      ctx.lineTo(end.x, end.y);
      ctx.stroke();
    } else if (shape.type === 'polygon' || shape.type === 'polyline') {
      const polyPoints = (shape.points || []).map(pointOf).filter(Boolean);
      if (polyPoints.length < 2) {
        ctx.restore();
        return;
      }
      ctx.beginPath();
      ctx.moveTo(polyPoints[0].x, polyPoints[0].y);
      for (const pixel of polyPoints.slice(1)) {
        ctx.lineTo(pixel.x, pixel.y);
      }
      if (shape.type === 'polygon' || shape.closed) {
        ctx.closePath();
        if (shape.fill) ctx.fill();
      }
      ctx.stroke();
    } else if (shape.type === 'circle') {
      const center = pointOf(shape.center);
      if (!center) {
        ctx.restore();
        return;
      }
      const radius = shape.radiusSpace === 'canvas' ? safeNumber(shape.radius, 0) : safeNumber(shape.radius, 0) * state.scale;
      ctx.beginPath();
      ctx.arc(center.x, center.y, radius, 0, Math.PI * 2);
      if (shape.fill) ctx.fill();
      ctx.stroke();
    } else if (shape.type === 'angle') {
      const p1 = pointOf(shape.points?.[0]);
      const p2 = pointOf(shape.points?.[1]); // Vertex
      const p3 = pointOf(shape.points?.[2]);
      if (!p1 || !p2 || !p3) {
        ctx.restore();
        return;
      }
      const a1 = Math.atan2(p1.y - p2.y, p1.x - p2.x);
      const a3 = Math.atan2(p3.y - p2.y, p3.x - p2.x);
      const r = (shape.radius || 0.4) * state.scale;
      ctx.beginPath();
      ctx.arc(p2.x, p2.y, r, a1, a3, Math.abs(a3 - a1) > Math.PI);
      ctx.stroke();
      if (shape.showValue) {
        const midA = (a1 + a3) / 2 + (Math.abs(a3 - a1) > Math.PI ? Math.PI : 0);
        ctx.fillStyle = color;
        ctx.font = '12px sans-serif';
        const deg = Math.abs((a3 - a1) * 180 / Math.PI);
        const finalDeg = deg > 180 ? 360 - deg : deg;
        ctx.fillText(`${finalDeg.toFixed(1)}°`, p2.x + Math.cos(midA) * (r + 15), p2.y + Math.sin(midA) * (r + 15));
      }
    } else if (shape.type === 'perp') {
      const p1 = pointOf(shape.points?.[0]);
      const p2 = pointOf(shape.points?.[1]); // Corner
      const p3 = pointOf(shape.points?.[2]);
      if (!p1 || !p2 || !p3) {
        ctx.restore();
        return;
      }
      const s = (shape.size || 0.2) * state.scale;
      const v1 = { x: (p1.x - p2.x), y: (p1.y - p2.y) };
      const v3 = { x: (p3.x - p2.x), y: (p3.y - p2.y) };
      const l1 = Math.hypot(v1.x, v1.y) || 1;
      const l3 = Math.hypot(v3.x, v3.y) || 1;
      const u1 = { x: v1.x / l1, y: v1.y / l1 };
      const u3 = { x: v3.x / l3, y: v3.y / l3 };
      
      ctx.beginPath();
      ctx.moveTo(p2.x + u1.x * s, p2.y + u1.y * s);
      ctx.lineTo(p2.x + (u1.x + u3.x) * s, p2.y + (u1.y + u3.y) * s);
      ctx.lineTo(p2.x + u3.x * s, p2.y + u3.y * s);
      ctx.stroke();
    } else if (shape.type === 'label') {
      const pixel = projectPoint({
        x: safeNumber(shape.x),
        y: safeNumber(shape.y),
        space: shape.space || state.mode,
      });
      ctx.fillStyle = shape.color || '#0f172a';
      ctx.font = '14px "Segoe UI", sans-serif';
      ctx.fillText(shape.text || '', pixel.x, pixel.y);
    } else if (shape.type === 'value') {
      const pixel = projectPoint({
        x: safeNumber(shape.x),
        y: safeNumber(shape.y),
        space: shape.space || state.mode,
      });
      let value = '';
      if (shape.valueFrom?.kind === 'distance' && points[shape.valueFrom.from] && points[shape.valueFrom.to]) {
        value = MathUtils.dist(points[shape.valueFrom.from], points[shape.valueFrom.to]).toFixed(2);
      }
      ctx.fillStyle = shape.color || '#dc2626';
      ctx.font = '13px "Segoe UI", sans-serif';
      ctx.fillText(`${shape.text || '值'} = ${value}`, pixel.x, pixel.y);
    } else if (shape.type === 'parabola') {
      const vertex = pointOf(shape.vertex);
      if (!vertex) {
        ctx.restore();
        return;
      }
      const a = safeNumber(shape.a, 1);
      const width = safeNumber(shape.width, 10);
      ctx.beginPath();
      const steps = 100;
      const range = width / 2;
      for (let i = 0; i <= steps; i++) {
        const x = -range + (range * 2 * i / steps);
        const y = a * x * x;
        const pixelX = vertex.x + x * state.scale;
        const pixelY = vertex.y - y * state.scale;
        if (i === 0) ctx.moveTo(pixelX, pixelY);
        else ctx.lineTo(pixelX, pixelY);
      }
      ctx.stroke();
    } else if (shape.type === 'function') {
      const { fn, range = [-10, 10], steps = 100 } = shape;
      if (!fn || typeof fn !== 'string') {
        ctx.restore();
        return;
      }
      ctx.beginPath();
      let first = true;
      for (let i = 0; i <= steps; i++) {
        const x = range[0] + (range[1] - range[0]) * i / steps;
        try {
          const y = new Function('x', `return ${fn}`)(x);
          if (!Number.isFinite(y)) {
            first = true;
            continue;
          }
          const pixelX = state.origin.x + x * state.scale;
          const pixelY = state.origin.y - y * state.scale;
          if (first) {
            ctx.moveTo(pixelX, pixelY);
            first = false;
          } else {
            ctx.lineTo(pixelX, pixelY);
          }
        } catch {
          first = true;
        }
      }
      ctx.stroke();
    }

    ctx.restore();
  };

  const renderScene = (scene, points) => {
    state.origin = scene.viewport.origin || DEFAULT_VIEWPORT.origin;
    state.scale = scene.viewport.scale || DEFAULT_VIEWPORT.scale;
    state.mode = scene.mode || 'canvas';

    if (scene.viewport.showGrid) drawGrid();
    if (scene.mode === 'plane' && scene.viewport.showAxes) drawAxes();
    for (const shape of scene.shapes || []) drawShape(shape, points);
    Object.values(points).forEach(drawPoint);
  };

  return {
    projectPoint,
    unprojectPoint,
    renderScene,
  };
}
