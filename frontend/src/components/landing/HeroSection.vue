<template>
  <section id="top" class="hero">
    <!-- background layers -->
    <div class="hero__grid" aria-hidden="true" />
    <div class="hero__glow hero__glow--a" aria-hidden="true" />
    <div class="hero__glow hero__glow--b" aria-hidden="true" />
    <div class="hero__rings" aria-hidden="true">
      <span></span><span></span><span></span>
    </div>

    <div class="hero__inner container-wide">
      <!-- Left: text -->
      <div class="hero__text">
        <p
          v-motion
          :initial="{ opacity: 0, y: 12 }"
          :enter="{ opacity: 1, y: 0, transition: { delay: 100, duration: 600 } }"
          class="eyebrow"
        >
          <span class="eyebrow__dot" />
          Retrieval-Augmented Generation · v1.0
        </p>

        <h1 class="hero__title">
          <span
            v-for="(line, i) in titleLines"
            :key="i"
            class="hero__line"
            v-motion
            :initial="{ opacity: 0, y: 30, clipPath: 'inset(0 0 100% 0)' }"
            :enter="{
              opacity: 1,
              y: 0,
              clipPath: 'inset(0 0 0% 0)',
              transition: { delay: 200 + i * 120, duration: 800, ease: [0.16, 1, 0.3, 1] }
            }"
          >
            <template v-for="(token, j) in line" :key="j">
              <span v-if="token.italic" class="hero__italic">{{ token.text }}</span>
              <span v-else>{{ token.text }}</span>
            </template>
          </span>
        </h1>

        <p
          v-motion
          :initial="{ opacity: 0, y: 12 }"
          :enter="{ opacity: 1, y: 0, transition: { delay: 700, duration: 600 } }"
          class="hero__sub"
        >
          上传 PDF，<strong>向你的企业知识库提问</strong>。<br />
          智能解析 · 引用溯源 · 实时监控，开箱即用。
        </p>

        <div
          v-motion
          :initial="{ opacity: 0, y: 12 }"
          :enter="{ opacity: 1, y: 0, transition: { delay: 850, duration: 600 } }"
          class="hero__cta"
        >
          <MagneticButton variant="primary" :strength="0.22" @click="$emit('try')">
            立即体验
            <el-icon class="el-icon--right"><ArrowRight /></el-icon>
          </MagneticButton>
          <MagneticButton variant="ghost" :strength="0.22" @click="$emit('learn')">
            了解架构
            <el-icon class="el-icon--right"><Bottom /></el-icon>
          </MagneticButton>
        </div>

        <div
          v-motion
          :initial="{ opacity: 0 }"
          :enter="{ opacity: 1, transition: { delay: 1100, duration: 800 } }"
          class="hero__meta"
        >
          <span class="meta-dot" />
          <span>已对接 Chroma 向量库 · 支持 OpenAI / 兼容 LLM</span>
        </div>
      </div>

      <!-- Right: tilted product mock -->
      <div
        v-motion
        :initial="{ opacity: 0, y: 40, rotateX: 8 }"
        :enter="{
          opacity: 1,
          y: 0,
          rotateX: 0,
          transition: { delay: 500, duration: 1000, ease: [0.16, 1, 0.3, 1] }
        }"
        class="hero__preview"
        :style="previewStyle"
        @mousemove="onMove"
        @mouseleave="onLeave"
      >
        <!-- mock app window -->
        <div class="mock-app" :style="innerStyle">
          <div class="mock-app__bar">
            <span class="dot dot--r" />
            <span class="dot dot--y" />
            <span class="dot dot--g" />
            <div class="mock-app__title">wisdomretrieve · chat</div>
          </div>
          <div class="mock-app__body">
            <div class="mock-side">
              <div class="mock-side__head">Sessions</div>
              <div class="mock-item mock-item--active">Q3 报销制度</div>
              <div class="mock-item">产品白皮书</div>
              <div class="mock-item">入职指南</div>
            </div>
            <div class="mock-main">
              <div class="mock-msg mock-msg--user">差旅审批的金额上限是多少？</div>
              <div class="mock-msg mock-msg--bot">
                根据《2025 差旅报销制度》第 4 条，<br />
                单次差旅审批上限为 <em>¥8,000</em>，超出需 <em>财务总监</em> 复核。
                <div class="mock-cite">
                  <span>📄 差旅报销制度 v3.pdf</span>
                  <span>P4 · hybrid 0.92</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- floating accents -->
        <div class="float-tag float-tag--a" :style="floatAStyle">
          <span class="float-tag__dot" />
          缓存命中 92%
        </div>
        <div class="float-tag float-tag--b" :style="floatBStyle">
          <span class="float-tag__num">312</span>ms
          <span class="float-tag__label">平均响应</span>
        </div>
      </div>
    </div>

    <!-- scroll indicator -->
    <button
      class="scroll-cue"
      aria-label="向下滚动"
      @click="$emit('scroll-down')"
      v-motion
      :initial="{ opacity: 0 }"
      :enter="{ opacity: 1, transition: { delay: 1400, duration: 600 } }"
    >
      <span class="scroll-cue__label">SCROLL</span>
      <span class="scroll-cue__line" />
    </button>
  </section>
</template>

<script setup lang="ts">
import { ArrowRight, Bottom } from "@element-plus/icons-vue";
import { computed, ref } from "vue";

import MagneticButton from "../ui/MagneticButton.vue";

defineEmits<{
  (e: "try"): void;
  (e: "learn"): void;
  (e: "scroll-down"): void;
}>();

interface Token {
  text: string;
  italic?: boolean;
}
type Line = Token[];

const titleLines: Line[] = [
  [
    { text: "让" },
    { text: "企业的" },
    { text: "每一份" },
    { text: "知识", italic: true }
  ],
  [{ text: "都能被问、被追溯。" }]
];

const tiltX = ref(0);
const tiltY = ref(0);
const px = ref(0);
const py = ref(0);

const previewStyle = computed(() => ({
  transform: `perspective(1400px) rotateX(${tiltX.value}deg) rotateY(${tiltY.value}deg)`
}));

const innerStyle = computed(() => ({
  transform: `translate(${px.value * 0.4}px, ${py.value * 0.4}px)`
}));

const floatAStyle = computed(() => ({
  transform: `translate(${px.value * -0.6}px, ${py.value * -0.6 + 12}px)`
}));
const floatBStyle = computed(() => ({
  transform: `translate(${px.value * 0.8}px, ${py.value * 0.8 + 8}px)`
}));

function onMove(e: MouseEvent) {
  const target = e.currentTarget as HTMLElement;
  const r = target.getBoundingClientRect();
  const cx = r.left + r.width / 2;
  const cy = r.top + r.height / 2;
  const x = (e.clientX - cx) / r.width;
  const y = (e.clientY - cy) / r.height;
  tiltY.value = x * 6;
  tiltX.value = -y * 5;
  px.value = x * 14;
  py.value = y * 14;
}

function onLeave() {
  tiltX.value = 0;
  tiltY.value = 0;
  px.value = 0;
  py.value = 0;
}
</script>

<style scoped>
.hero {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  padding: calc(var(--nav-h) + 24px) 0 var(--s-9);
  overflow: hidden;
  isolation: isolate;
}

/* Background layers */
.hero__grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(90deg, var(--line) 1px, transparent 1px),
    linear-gradient(180deg, var(--line) 1px, transparent 1px);
  background-size: 80px 80px;
  mask-image: radial-gradient(ellipse 70% 60% at 50% 35%, #000 30%, transparent 80%);
  opacity: 0.35;
  z-index: 0;
}

.hero__glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  z-index: 0;
  pointer-events: none;
}
.hero__glow--a {
  top: -10%;
  right: -10%;
  width: 720px;
  height: 720px;
  background: radial-gradient(circle, var(--accent-soft) 0%, transparent 60%);
}
.hero__glow--b {
  bottom: -20%;
  left: -10%;
  width: 640px;
  height: 640px;
  background: radial-gradient(circle, rgba(245, 179, 66, 0.06) 0%, transparent 60%);
}

.hero__rings {
  position: absolute;
  top: 18%;
  right: 6%;
  width: 360px;
  height: 360px;
  z-index: 0;
  pointer-events: none;
  opacity: 0.5;
}
.hero__rings span {
  position: absolute;
  inset: 0;
  border: 1px solid var(--line-strong);
  border-radius: 50%;
  animation: ring-pulse 6s var(--ease-in-out) infinite;
}
.hero__rings span:nth-child(2) {
  inset: 30px;
  animation-delay: 1.5s;
}
.hero__rings span:nth-child(3) {
  inset: 60px;
  animation-delay: 3s;
}
@keyframes ring-pulse {
  0%, 100% { transform: scale(1); opacity: 0.4; }
  50% { transform: scale(1.04); opacity: 0.8; }
}

.hero__inner {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: minmax(0, 1.05fr) minmax(0, 1fr);
  gap: var(--s-7);
  align-items: center;
}

.hero__text {
  display: grid;
  gap: var(--s-5);
  max-width: 640px;
}

.eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  font-family: var(--font-mono);
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: var(--track-extra);
  color: var(--ink-muted);
  font-weight: 500;
}
.eyebrow__dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--accent);
  box-shadow: 0 0 0 4px var(--accent-soft);
  animation: pulse-ring 2.4s var(--ease-out) infinite;
}

.hero__title {
  font-family: var(--font-display);
  font-size: clamp(40px, 4.6vw, 72px);
  font-weight: 600;
  line-height: 1.05;
  letter-spacing: var(--track-tight);
  color: var(--ink);
  margin: 0;
}

.hero__line {
  display: block;
  overflow: hidden;
}

.hero__italic {
  font-style: italic;
  color: var(--accent);
  font-weight: 600;
  position: relative;
  display: inline-block;
}

.hero__sub {
  font-size: var(--text-lg);
  color: var(--ink-soft);
  line-height: 1.6;
  max-width: 520px;
  letter-spacing: var(--track-snug);
}
.hero__sub strong {
  color: var(--ink);
  font-weight: 600;
}

.hero__cta {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-top: 8px;
}

.hero__meta {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--ink-muted);
  letter-spacing: var(--track-wide);
  text-transform: uppercase;
  margin-top: 8px;
}
.meta-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--success);
  box-shadow: 0 0 8px var(--success);
}

/* Right preview */
.hero__preview {
  position: relative;
  height: 440px;
  transition: transform 360ms var(--ease-out);
  transform-style: preserve-3d;
}

.mock-app {
  position: relative;
  width: 100%;
  height: 100%;
  border-radius: 8px;
  background: var(--bg-card);
  border: 1px solid var(--line);
  box-shadow: var(--shadow-lg);
  overflow: hidden;
  transition: transform 240ms var(--ease-out);
  transform-style: preserve-3d;
}

.mock-app__bar {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--line);
  background: var(--bg-soft);
}
.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--ink-faint);
}
.dot--r { background: #ed6a5e; }
.dot--y { background: #f5b342; }
.dot--g { background: #62c554; }

.mock-app__title {
  margin-left: 12px;
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--ink-muted);
  letter-spacing: var(--track-wide);
  text-transform: uppercase;
}

.mock-app__body {
  display: grid;
  grid-template-columns: 180px 1fr;
  height: calc(100% - 41px);
}

.mock-side {
  border-right: 1px solid var(--line);
  padding: 16px;
  background: var(--bg-soft);
}
.mock-side__head {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--ink-muted);
  letter-spacing: var(--track-extra);
  text-transform: uppercase;
  margin-bottom: 12px;
}
.mock-item {
  padding: 8px 10px;
  border-radius: 4px;
  font-size: 12px;
  color: var(--ink-muted);
  margin-bottom: 4px;
  transition: all var(--d-base) var(--ease-out);
}
.mock-item--active {
  background: var(--accent-soft);
  color: var(--accent-strong);
  border-left: 2px solid var(--accent);
  padding-left: 8px;
}

.mock-main {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow: hidden;
}

.mock-msg {
  max-width: 80%;
  padding: 10px 12px;
  border-radius: 6px;
  font-size: 12px;
  line-height: 1.6;
  animation: rise 600ms var(--ease-out) both;
}
.mock-msg--user {
  align-self: flex-end;
  background: var(--accent-soft);
  color: var(--ink);
  border: 1px solid var(--accent);
  animation-delay: 0.1s;
}
.mock-msg--bot {
  background: var(--bg-soft);
  color: var(--ink-soft);
  border: 1px solid var(--line);
  animation-delay: 0.4s;
}
.mock-msg--bot em {
  color: var(--accent-strong);
  font-style: normal;
  font-weight: 600;
}
.mock-cite {
  margin-top: 8px;
  display: flex;
  gap: 8px;
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--ink-muted);
  letter-spacing: var(--track-wide);
}

/* Floating tags */
.float-tag {
  position: absolute;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  border-radius: 4px;
  background: var(--bg-elevated);
  border: 1px solid var(--line);
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--ink);
  box-shadow: var(--shadow-md);
  transition: transform 360ms var(--ease-out);
  white-space: nowrap;
  z-index: 2;
}
.float-tag__dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--success);
  box-shadow: 0 0 6px var(--success);
}
.float-tag--a {
  top: 40px;
  left: -20px;
}
.float-tag--b {
  bottom: 60px;
  right: -30px;
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;
  padding: 10px 14px;
}
.float-tag__num {
  font-family: var(--font-mono);
  font-size: 16px;
  color: var(--accent);
  font-weight: 700;
}
.float-tag__label {
  font-size: 10px;
  color: var(--ink-muted);
  letter-spacing: var(--track-wide);
  text-transform: uppercase;
}

/* Scroll cue */
.scroll-cue {
  position: absolute;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  background: none;
  border: 0;
  cursor: pointer;
  color: var(--ink-muted);
  z-index: 2;
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: var(--track-mega);
  text-transform: uppercase;
}
.scroll-cue__line {
  width: 1px;
  height: 36px;
  background: linear-gradient(180deg, var(--ink-muted), transparent);
  position: relative;
  overflow: hidden;
}
.scroll-cue__line::after {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, transparent, var(--accent));
  animation: scroll-line 2.2s var(--ease-in-out) infinite;
}
@keyframes scroll-line {
  0% { transform: translateY(-100%); }
  100% { transform: translateY(100%); }
}

@media (max-width: 1024px) {
  .hero__inner {
    grid-template-columns: 1fr;
    gap: var(--s-7);
  }
  .hero__preview {
    height: 380px;
  }
  .hero__title {
    font-size: clamp(36px, 5.6vw, 60px);
  }
}

@media (max-width: 640px) {
  .hero__title {
    font-size: clamp(32px, 8vw, 48px);
  }
  .hero__preview {
    height: 320px;
  }
  .float-tag--a { left: 8px; }
  .float-tag--b { right: 8px; }
}
</style>
