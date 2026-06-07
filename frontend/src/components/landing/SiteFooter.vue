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
            <a class="foot-link" href="#" @click.prevent>GitHub</a>
          </div>
          <div class="foot-col">
            <div class="foot-col__head">联系</div>
            <a class="foot-link" href="mailto:hi@wisdomretrieve.dev">hi@wisdomretrieve.dev</a>
            <span class="foot-link foot-link--mute">北京 · 上海 · 远程</span>
            <span class="foot-link foot-link--mute">v1.0 · 2025</span>
          </div>
        </div>
      </div>

      <div class="foot-giant" aria-hidden="true">WisdomRetrieve</div>

      <div class="foot-bottom">
        <span>© 2025 WisdomRetrieve</span>
        <span class="foot-bottom__sep">·</span>
        <span>Built for teams that read carefully.</span>
        <span class="foot-bottom__push">Crafted with care · Not generated</span>
      </div>
    </div>
  </footer>
</template>

<script setup lang="ts">
import { ArrowRight } from "@element-plus/icons-vue";

import MagneticButton from "../ui/MagneticButton.vue";

defineEmits<{
  (e: "try"): void;
  (e: "jump", id: string): void;
}>();
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
  font-family: var(--font-display);
  font-size: clamp(80px, 18vw, 280px);
  font-weight: 700;
  letter-spacing: var(--track-tight);
  color: transparent;
  -webkit-text-stroke: 1px var(--line-strong);
  text-stroke: 1px var(--line-strong);
  line-height: 0.85;
  text-align: center;
  margin: var(--s-7) 0;
  user-select: none;
  pointer-events: none;
  white-space: nowrap;
  overflow: hidden;
  background: linear-gradient(180deg, var(--line-strong) 0%, transparent 80%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
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
