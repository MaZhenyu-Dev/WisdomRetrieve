<template>
  <footer class="site-foot">
    <div class="site-foot__inner container-wide">
      <div class="foot-top">
        <div class="foot-cta">
          <h2 class="foot-cta__title">
            现在就让 <span class="accent">企业知识</span><br />
            开始被问。
          </h2>
          <MagneticButton variant="primary" :strength="0.2" @click="$emit('try')">
            立即体验
            <el-icon class="el-icon--right"><ArrowRight /></el-icon>
          </MagneticButton>
        </div>

        <div class="foot-cols">
          <div class="foot-col">
            <div class="foot-col__head">产品</div>
            <a class="foot-link" href="#capability" @click.prevent="$emit('jump', 'capability')">核心能力</a>
            <a class="foot-link" href="#workflow" @click.prevent="$emit('jump', 'workflow')">工作流</a>
            <a class="foot-link" href="#demo" @click.prevent="$emit('jump', 'demo')">在线演示</a>
            <a class="foot-link" href="#stats" @click.prevent="$emit('jump', 'stats')">性能指标</a>
          </div>
          <div class="foot-col">
            <div class="foot-col__head">资源</div>
            <a class="foot-link" href="#" @click.prevent>技术白皮书</a>
            <a class="foot-link" href="#" @click.prevent>API 文档</a>
            <a class="foot-link" href="#" @click.prevent>更新日志</a>
            <a class="foot-link" href="https://github.com/MaZhenyu-Dev" target="_blank" rel="noopener noreferrer">GitHub</a>
          </div>
          <div class="foot-col">
            <div class="foot-col__head">联系</div>
            <a class="foot-link" href="mailto:2283388143@qq.com">2283388143@qq.com</a>
            <span class="foot-link foot-link--mute">北京</span>
            <span class="foot-link foot-link--mute">v1.0 · 2026</span>
          </div>
        </div>  
      </div>

      <div class="foot-giant" ref="giantRef" aria-hidden="true">
        <span class="foot-giant__layer foot-giant__base">WisdomRAG</span>
        <span class="foot-giant__layer foot-giant__strokes">WisdomRAG</span>
      </div>

      <div class="foot-bottom">
        <span>© 2026 WisdomRAG</span>
        <span class="foot-bottom__sep">·</span>
        <span>Built for teams that read carefully.</span>
        <span class="foot-bottom__push">Crafted with care · MaZhenyu-Dev</span>
      </div>
    </div>
  </footer>
</template>

<script setup lang="ts">
import { ArrowRight } from "@element-plus/icons-vue";
import { onBeforeUnmount, onMounted, ref } from "vue";

import MagneticButton from "../ui/MagneticButton.vue";

defineEmits<{
  (e: "try"): void;
  (e: "jump", id: string): void;
}>();

// 仿 LangChain 官方底部的"描边扫描"效果：
// 两层相同的文字，底色是常驻的淡色描边层，描边层用 radial-gradient 蒙版
// 按滚动进度从左到右划过，描边颜色仅在蒙版范围内可见。
const giantRef = ref<HTMLElement | null>(null);
let rafId: number | null = null;
let targetX = -1000;
let currentX = -1000;

function tick() {
  if (!giantRef.value) {
    rafId = null;
    return;
  }
  const rect = giantRef.value.getBoundingClientRect();
  const vh = window.innerHeight;
  const radius = Math.max(160, rect.width * 0.18);

  // 关键：进度对齐 LangChain —— 当 footer 底到达视口底时为 1，
  // 这样无论页面长短，只要滚到底，光束都会停在 wordmark 右侧
  const footer = giantRef.value.closest<HTMLElement>(".site-foot");
  if (!footer) {
    rafId = null;
    return;
  }
  const footerRect = footer.getBoundingClientRect();
  const startOffset = rect.height * 0.1;

  const totalRange = footerRect.bottom - rect.top - startOffset;
  const scrolled = vh - rect.top - startOffset;
  const progress = Math.max(0, Math.min(1, scrolled / totalRange));

  // 关键：targetX 终点 = width - radius（光束停在 wordmark 右侧，不是越过去）
  targetX = -radius + progress * rect.width;

  // 缓动：往目标 x 方向逼近
  currentX += (targetX - currentX) * 0.12;

  const grad = `radial-gradient(${radius}px at ${currentX}px 50%, black 0%, rgba(0,0,0,0.3) 100%)`;
  giantRef.value.style.setProperty("--strokes-mask", grad);

  if (Math.abs(targetX - currentX) > 0.3) {
    rafId = requestAnimationFrame(tick);
  } else {
    // 收尾：snap 到目标，避免永远循环
    currentX = targetX;
    const finalGrad = `radial-gradient(${radius}px at ${currentX}px 50%, black 0%, rgba(0,0,0,0.3) 100%)`;
    giantRef.value.style.setProperty("--strokes-mask", finalGrad);
    rafId = null;
  }
}

function onScroll() {
  if (rafId === null) {
    rafId = requestAnimationFrame(tick);
  }
}

onMounted(() => {
  currentX = -1000;
  targetX = -1000;
  window.addEventListener("scroll", onScroll, { passive: true });
  window.addEventListener("resize", onScroll);
  onScroll();
});

onBeforeUnmount(() => {
  window.removeEventListener("scroll", onScroll);
  window.removeEventListener("resize", onScroll);
  if (rafId !== null) cancelAnimationFrame(rafId);
});
</script>

<style scoped>
.site-foot {
  position: relative;
  border-top: 1px solid var(--line);
  background: var(--bg);
  padding: var(--s-12) 0 var(--s-7);
  overflow: hidden;
}

.foot-top {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: var(--s-9);
  align-items: start;
  margin-bottom: var(--s-10);
}

.foot-cta__title {
  font-family: var(--font-display);
  font-size: var(--text-5xl);
  font-weight: 600;
  line-height: 1.05;
  letter-spacing: var(--track-tight);
  color: var(--ink);
  margin: 0 0 var(--s-6);
}
.foot-cta__title .accent {
  font-style: italic;
  color: var(--accent);
}

.foot-cols {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--s-7);
}

.foot-col {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.foot-col__head {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--ink-muted);
  text-transform: uppercase;
  letter-spacing: var(--track-extra);
  margin-bottom: 4px;
}

.foot-link {
  font-size: var(--text-sm);
  color: var(--ink-soft);
  text-decoration: none;
  position: relative;
  display: inline-block;
  transition: color var(--d-base) var(--ease-out), transform var(--d-base) var(--ease-out);
}
.foot-link::after {
  content: "";
  position: absolute;
  left: 0;
  right: 100%;
  bottom: -2px;
  height: 1px;
  background: var(--accent);
  transition: right var(--d-base) var(--ease-out);
}
.foot-link:hover {
  color: var(--ink);
  transform: translateX(2px);
}
.foot-link:hover::after {
  right: 0;
}
.foot-link--mute {
  color: var(--ink-muted);
  cursor: default;
}
.foot-link--mute::after { display: none; }

.foot-giant {
  position: relative;
  font-family: var(--font-display);
  font-weight: 700;
  font-size: clamp(80px, 16vw, 240px);
  letter-spacing: -0.04em;
  line-height: 0.95;
  text-align: center;
  margin: var(--s-7) 0;
  user-select: none;
  pointer-events: none;
}
.foot-giant__layer {
  display: block;
  font: inherit;
  letter-spacing: inherit;
  line-height: inherit;
  white-space: nowrap;
}
.foot-giant__base {
  color: var(--ink-faint);
  opacity: 0.18;
}
.foot-giant__strokes {
  position: absolute;
  inset: 0;
  color: transparent;
  -webkit-text-stroke: 1.5px var(--accent);
  -webkit-mask-image: var(--strokes-mask, radial-gradient(0px at -9999px 50%, black, transparent));
          mask-image: var(--strokes-mask, radial-gradient(0px at -9999px 50%, black, transparent));
  -webkit-mask-repeat: no-repeat;
          mask-repeat: no-repeat;
  opacity: 0.95;
}

.foot-bottom {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--ink-muted);
  letter-spacing: var(--track-wide);
  text-transform: uppercase;
  border-top: 1px solid var(--line);
  padding-top: var(--s-5);
}
.foot-bottom__sep { opacity: 0.4; }
.foot-bottom__push { margin-left: auto; }

@media (max-width: 880px) {
  .foot-top {
    grid-template-columns: 1fr;
  }
  .foot-cols {
    grid-template-columns: 1fr 1fr;
  }
  .foot-bottom__push { margin-left: 0; }
}
</style>
