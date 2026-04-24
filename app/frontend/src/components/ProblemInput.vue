<template>
  <div class="composer">
    <div class="composer-box">
      <textarea
        v-model="text"
        class="composer-input"
        rows="2"
        placeholder="输入几何题目，或先上传截图再补充条件。尽量把已知条件、所求结论、图形关系写完整。"
        @paste="handlePaste"
      ></textarea>

      <div v-if="imageSupportHint" class="composer-hint">
        {{ imageSupportHint }}
      </div>

      <div v-if="imageBase64" class="preview-block">
        <div class="preview-header">
          <div class="preview-title">题目图片</div>
          <button class="remove-btn" type="button" @click="imageBase64 = null">移除</button>
        </div>
        <img class="preview-image" :src="imageBase64" alt="题目预览" />
      </div>

      <div class="composer-toolbar">
        <div class="toolbar-left">
          <el-upload
            action="#"
            :auto-upload="false"
            :show-file-list="false"
            accept="image/*"
            :disabled="!allowImage"
            @change="handleUpload"
          >
            <button class="tool-btn" type="button" :disabled="!allowImage">
              <el-icon><UploadFilled /></el-icon>
              <span>上传图片</span>
            </button>
          </el-upload>
          <button class="tool-btn" type="button" :disabled="loading" @click="fillDemo">填入示例</button>
        </div>

        <button
          class="send-btn"
          type="button"
          :disabled="loading || (!text && !imageBase64)"
          @click="handleSolve"
        >
          {{ loading ? '解析中' : '开始解析' }}
        </button>
      </div>
    </div>

    <div class="example-strip">
      <button
        v-for="ex in examples"
        :key="ex.title"
        class="example-chip"
        type="button"
        @click="text = ex.text"
      >
        {{ ex.title }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { ElMessage } from 'element-plus';

const emit = defineEmits(['solve']);
const props = defineProps({
  loading: Boolean,
  allowImage: { type: Boolean, default: true },
  imageSupportHint: { type: String, default: '' },
});

const text = ref('');
const imageBase64 = ref(null);

const examples = [
  { title: '将军饮马', text: '已知点 A(1, 4) 和点 B(5, 2) 位于 x 轴同侧，请在 x 轴上求作一点 P，使得折线段 PA + PB 的长度之和达到最小值，并求出该最小值及点 P 的坐标。' },
  { title: '胡不归', text: '在平面内，点 A(0, 3) 到直线 l 的距离为 3，定点 C(4, 0) 在直线 l 上。动点 P 在直线 l 上运动，请计算当 AP + 1/2PC 的值最小时，点 P 的位置以及该最小值的具体数值。' },
  { title: '一箭穿心', text: '在 △ABC 中，AB=3, AC=4, ∠BAC=60°。请在三角形内部寻找一点 P，使得该点到三个顶点距离之和 PA + PB + PC 最小，并说明此时 ∠APB, ∠BPC, ∠CPA 的度数关系。' },
  { title: '瓜豆模型', text: '已知定点 A(4, 0)，动点 P 在半径为 2 且圆心在原点 O 的圆上运动。若点 Q 是线段 AP 的中点，请描述当主动点 P 运动一周时，从动点 Q 轨迹图形的形状、位置及路径长度。' },
  { title: '阿氏圆', text: '已知线段 BC = 6，动点 A 在平面内运动且始终满足 AB = 2AC。请确定动点 A 的轨迹方程，并求该轨迹围成图形的圆心坐标与面积。' },
  { title: '手拉手模型', text: '△ABC 与 △ADE 均为等腰直角三角形（∠BAC = ∠DAE = 90°）。请通过旋转变换证明连接对应顶点的线段 BD 与 CE 具有相等且互相垂直的关系。' },
  { title: '一线三等角', text: '直线 l 上依次有三点 B, C, D，且 AB ⊥ l, ED ⊥ l。若点 A, C, E 构成直角三角形且 ∠ACE = 90°，已知 AB=4, BC=2，请计算线段 ED 的长度。' },
  { title: '半角模型', text: '在正方形 ABCD 中，点 E, F 分别在边 BC, CD 上，且满足 ∠EAF = 45°。请通过图形剪拼或旋转，证明线段 EF 长度恒等于 BE + DF 之和。' },
  { title: '12345模型', text: '在 4x4 的正方形格点图中，连接点 A(0,0) 与 B(2,1)。请利用格点构造出 tan α = 1/2 的直角三角形，并求出线段 AB 在此模型下的比例关系及斜边长度。' },
  { title: '十字架模型', text: '在四边形 ABCD 中，AC ⊥ BD 于点 O。若 AB=3, BC=4, CD=5，请利用对角线垂直的几何特征，计算出剩余边 AD 的长度。' },
  { title: '射影定理', text: '已知 Rt△ABC 中 AD 是斜边 BC 上的高。若 BD=4, CD=9，请根据射影定理求出 AD 的长；若以 AD 为半径作圆，请判断直线 BC 与该圆的位置关系。' },
  { title: '燕尾与欧拉线', text: '在 △ABC 中，点 P 是内部任意一点。若已知 S△BPC, S△APB, S△APC 的面积比为 3:4:5，请确定点 P 的几何位置；并探讨该三角形的外心、重心、垂心是否共线（欧拉线）。' },
  { title: '飞镖模型', text: '在凹四边形 ABDC 中，点 D 位于 △ABC 内部，利用三角形内角和定理或外角性质证明中间“镖头”角 ∠BDC 的度数恒等于三个“镖尾”角 ∠A, ∠B, ∠C 的和。' },
  { title: '旋转模型', text: '将 △ABC 绕顶点 A 逆时针旋转 α 角度得到 △AB\'C\'，连接对应点 BB\' 和 CC\'，观察并证明在旋转过程中 △ABB\' 与 △ACC\' 始终保持相似关系且位似中心为 A。' },
  { title: '位似模型', text: '已知 △ABC，以点 O 为位似中心，将原三角形按 2:1 的比例放大得到 △A\'B\'C\'，请展示当位似中心 O 分别位于三角形内部、外部及顶点上时，两个三角形位置关系的动态演变。' },
  { title: '切割线定理', text: '从圆 ⊙O 外一点 P 引圆的切线 PT（切点为 T）和割线 PAB（交圆于 A, B），通过构造相似三角形证明切线长的平方等于割线段与圆相交两点到 P 点距离的乘积，即 PT² = PA · PB。' },
  { title: '蝴蝶定理', text: '在圆 ⊙O 中，点 M 是弦 PQ 的中点，过 M 任作两条弦 AB 和 CD，连接 AD 和 BC 分别交 PQ 于 X, Y，请验证并展示点 M 始终是线段 XY 的中点这一对称特性。' },
  { title: '蝴蝶面积法', text: '在四边形 ABCD 中，对角线 AC 与 BD 相交于点 O，展示由对角线分割出的四个三角形面积之间的关系，即 S△AOB · S△COD = S△BOC · S△AOD。' },
  { title: '燕尾面积比', text: '在 △ABC 中，点 P 为内部任一点，连接 AP, BP, CP 并延长交对边于 D, E, F，利用“燕尾形”面积比例关系证明 BD/CD = S△ABP / S△ACP。' },
  { title: '九点圆', text: '给定任意 △ABC，绘制出其三边的中点、三条高的垂足、以及垂心与三个顶点连线的中点，并验证这九个点始终共圆且该圆半径等于外接圆半径的一半。' },
  { title: '欧拉线', text: '在一个动态三角形中，同时绘制出其重心 G、外心 O 和垂心 H，展示这三个点始终在一条直线上（欧拉线）运动，且满足线段比例 HG = 2GO。' },
  { title: '米勒角', text: '已知点 A, B 是直线 l 同侧的两个定点，在直线 l 上寻找一点 P，使得张角 ∠APB 达到最大，并展示此时点 P 恰好是过 A, B 两点且与直线 l 相切的圆的切点。' },
  { title: '函数几何最大面积', text: '在抛物线 y = -x^2 + 4x 上有一动点 M，在 x 轴上有两定点 A(1,0), B(3,0)，请寻找使 △MAB 面积最大时点 M 的坐标，并展示面积随点 M 运动的变化曲线。' },
];

const readFile = (rawFile) =>
  new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (event) => resolve(event.target?.result || null);
    reader.onerror = reject;
    reader.readAsDataURL(rawFile);
  });

const handleUpload = async (file) => {
  if (!props.allowImage) {
    ElMessage.warning(props.imageSupportHint || '当前模型不支持图片输入');
    return;
  }
  if (!file?.raw) return;
  imageBase64.value = await readFile(file.raw);
};

const handlePaste = async (event) => {
  const items = event.clipboardData?.items || [];
  for (const item of items) {
    if (item.type?.startsWith('image/')) {
      if (!props.allowImage) {
        ElMessage.warning(props.imageSupportHint || '当前模型不支持图片输入');
        event.preventDefault();
        return;
      }
      const rawFile = item.getAsFile();
      if (rawFile) {
        imageBase64.value = await readFile(rawFile);
        break;
      }
    }
  }
};

const fillDemo = () => {
  text.value = examples[0].text;
};

const handleSolve = () => {
  emit('solve', {
    problem: text.value.trim(),
    image: imageBase64.value,
  });
};
</script>

<style scoped>
.composer-box {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(250, 252, 255, 0.98)),
    #ffffff;
  border: 1px solid #dfe6f2;
  border-radius: 26px;
  padding: 18px 18px 14px;
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.96),
    0 18px 34px rgba(15, 23, 42, 0.045);
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.composer-box:focus-within {
  border-color: #b6c5dc;
  box-shadow:
    0 0 0 4px rgba(117, 144, 194, 0.08),
    0 18px 34px rgba(15, 23, 42, 0.06);
}

.composer-input {
  width: 100%;
  min-height: 3.8em;
  border: 0;
  resize: vertical;
  outline: none;
  background: transparent;
  color: #263346;
  font: inherit;
  font-size: 16px;
  line-height: 1.9;
  letter-spacing: 0.01em;
}

.composer-input::placeholder {
  color: #93a0b2;
}

.composer-hint {
  margin-top: 8px;
  color: #8a6b32;
  font-size: 12px;
  line-height: 1.6;
}

.preview-block {
  margin: 10px 0 16px;
  padding: 14px;
  border-radius: 18px;
  background: #f8fafc;
  border: 1px solid #e8edf5;
}

.preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.preview-title {
  color: #334155;
  font-size: 13px;
  font-weight: 500;
}

.preview-image {
  width: 100%;
  max-height: 260px;
  object-fit: contain;
  border-radius: 14px;
  background: #ffffff;
}

.remove-btn {
  border: 0;
  background: transparent;
  color: #b42318;
  cursor: pointer;
  font: inherit;
  font-size: 13px;
}

.composer-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding-top: 14px;
  margin-top: 8px;
}

.toolbar-left {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.tool-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 38px;
  padding: 0 14px;
  border: 1px solid #e1e8f3;
  border-radius: 999px;
  background: transparent;
  color: #55657b;
  cursor: pointer;
  font: inherit;
  font-size: 14px;
}

.send-btn {
  min-height: 42px;
  padding: 0 18px;
  border: 0;
  border-radius: 999px;
  background: #243042;
  color: #ffffff;
  cursor: pointer;
  font: inherit;
  font-size: 14px;
}

.send-btn:disabled,
.tool-btn:disabled {
  opacity: 0.5;
  cursor: default;
}

.example-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 14px;
}

.example-chip {
  padding: 10px 14px;
  border: 1px solid #e3e8f2;
  border-radius: 999px;
  background: transparent;
  color: #5a6b82;
  cursor: pointer;
  font: inherit;
  font-size: 13px;
}

@media (max-width: 768px) {
  .composer-box {
    padding: 16px 14px 12px;
    border-radius: 22px;
  }

  .composer-input {
    min-height: 3.6em;
    font-size: 15px;
    line-height: 1.8;
  }

  .composer-toolbar {
    flex-direction: column;
    align-items: stretch;
  }

  .send-btn {
    width: 100%;
  }
}
</style>
