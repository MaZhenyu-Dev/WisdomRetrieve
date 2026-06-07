<template>
  <section id="workflow" ref="root" :class="['workflow', { ready: isInView }]">
    <header class="workflow__head container-wide">
      <p class="eyebrow"><span class="eyebrow__bar" />Section 02 · Pipeline</p>
      <h2 class="workflow__title">
        一份 PDF，<br />五次<span class="accent">转身</span>，变成可问的知识。
      </h2>
    </header>

    <div class="workflow__rail">
      <div class="workflow__line">
        <span class="workflow__line-fill" :style="{ width: isInView ? '100%' : '0%' }" />
      </div>

      <ol class="workflow__steps">
        <li
          v-for="(step, i) in steps"
          :key="step.id"
          class="step"
          :class="{ 'step--in': isInView }"
          :style="{ '--step-delay': `${300 + i * 140}ms` }"
        >
          <div class="step__node">
            <div class="step__dot" />
            <span class="step__ring" />
          </div>
          <div class="step__num">{{ step.num }}</div>
          <h3 class="step__title">{{ step.title }}</h3>
          <p class="step__desc">{{ step.desc }}</p>
          <div class="step__icon" v-html="step.icon" />
        </li>
      </ol>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";

import { useReveal } from "../../composables/useReveal";

const { target: root, isInView } = useReveal<HTMLElement>({ threshold: 0.15 });

const steps = [
  {
    id: "ingest",
    num: "01",
    title: "拖入 PDF",
    desc: "支持单文件 · 批量上传 · 拖拽即传。",
    icon: `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M12 4v12m0-12l-4 4m4-4l4 4" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="M4 17v2a2 2 0 002 2h12a2 2 0 002-2v-2" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
    </svg>`
  },
  {
    id: "parse",
    num: "02",
    title: "解析",
    desc: "PyMuPDF + 表格识别，结构化还原。",
    icon: `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="4" y="3" width="14" height="18" rx="1" stroke="currentColor" stroke-width="1.4"/>
      <path d="M8 8h6M8 12h6M8 16h4" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
      <path d="M18 7l3 3-3 3" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>`
  },
  {
    id: "chunk",
    num: "03",
    title: "切分",
    desc: "段落 · 表格 · 标题，三级粒度切分。",
    icon: `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="3" y="3" width="8" height="8" rx="1" stroke="currentColor" stroke-width="1.4"/>
      <rect x="13" y="3" width="8" height="8" rx="1" stroke="currentColor" stroke-width="1.4"/>
      <rect x="3" y="13" width="8" height="8" rx="1" stroke="currentColor" stroke-width="1.4"/>
      <rect x="13" y="13" width="8" height="8" rx="1" stroke="currentColor" stroke-width="1.4" stroke-dasharray="2 2"/>
    </svg>`
  },
  {
    id: "embed",
    num: "04",
    title: "索引",
    desc: "BGE / OpenAI 写入 Chroma 向量库。",
    icon: `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="6" cy="6" r="2" stroke="currentColor" stroke-width="1.4"/>
      <circle cx="18" cy="6" r="2" stroke="currentColor" stroke-width="1.4"/>
      <circle cx="6" cy="18" r="2" stroke="currentColor" stroke-width="1.4"/>
      <circle cx="18" cy="18" r="2" stroke="currentColor" stroke-width="1.4"/>
      <path d="M8 6h8M6 8v8M18 8v8M8 18h8" stroke="currentColor" stroke-width="1.4"/>
    </svg>`
  },
  {
    id: "ask",
    num: "05",
    title: "问答",
    desc: "混合检索 + Rerank + LLM 生成答案。",
    icon: `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M21 12a8 8 0 11-3.5-6.6L21 4l-1 4.5A8 8 0 0121 12z" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/>
      <circle cx="9" cy="12" r="1" fill="currentColor"/>
      <circle cx="13" cy="12" r="1" fill="currentColor"/>
      <circle cx="17" cy="12" r="1" fill="currentColor"/>
    </svg>`
  }
];
</script>

<style scoped>
.workflow {
  padding: var(--s-13) 0;
  background: var(--bg-soft);
  border-top: 1px solid var(--line);
  border-bottom: 1px solid var(--line);
}

.workflow__head {
  margin-bottom: var(--s-10);
}
.eyebrow__bar {
  display: inline-block;
  width: 24px;
  height: 1px;
  background: var(--accent);
  margin-right: 12px;
  vertical-align: middle;
}
.workflow__title {
  font-family: var(--font-display);
  font-size: var(--text-5xl);
  font-weight: 600;
  line-height: 1.05;
  letter-spacing: var(--track-tight);
  color: var(--ink);
  margin: var(--s-4) 0 0;
}
.workflow__title .accent {
  font-style: italic;
  color: var(--accent);
}

.workflow__rail {
  position: relative;
  max-width: var(--container-wide);
  margin: 0 auto;
  padding: 0 var(--s-7);
}

.workflow__line {
  position: absolute;
  top: 30px;
  left: calc(var(--s-7) + 60px);
  right: calc(var(--s-7) + 60px);
  height: 1px;
  background: var(--line);
  z-index: 0;
}

.workflow__line-fill {
  display: block;
  height: 100%;
  background: linear-gradient(90deg, var(--accent), var(--accent-strong));
  transition: width 1.6s var(--ease-out);
  box-shadow: 0 0 12px var(--accent-glow);
}

.workflow__steps {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: var(--s-4);
  position: relative;
  z-index: 1;
}

.step {
  position: relative;
  padding-top: 80px;
  opacity: 0;
  transform: translateY(20px);
  transition: opacity 700ms var(--ease-out), transform 700ms var(--ease-out);
  transition-delay: var(--step-delay, 0ms);
}
.workflow.ready .step.step--in {
  opacity: 1;
  transform: translateY(0);
}

.step__node {
  position: absolute;
  top: 18px;
  left: 50%;
  transform: translateX(-50%);
  width: 24px;
  height: 24px;
  display: grid;
  place-items: center;
}

.step__dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--bg);
  border: 2px solid var(--accent);
  position: relative;
  z-index: 2;
  transition: background var(--d-base) var(--ease-out);
}

.workflow.ready .step:nth-child(1) .step__dot { transition-delay: 200ms; background: var(--accent); }
.workflow.ready .step:nth-child(2) .step__dot { transition-delay: 500ms; background: var(--accent); }
.workflow.ready .step:nth-child(3) .step__dot { transition-delay: 800ms; background: var(--accent); }
.workflow.ready .step:nth-child(4) .step__dot { transition-delay: 1100ms; background: var(--accent); }
.workflow.ready .step:nth-child(5) .step__dot { transition-delay: 1400ms; background: var(--accent); }

.step__ring {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  border: 1px solid var(--accent);
  opacity: 0;
}
.workflow.ready .step__ring {
  animation: ring-pulse 2.4s var(--ease-out) infinite;
}
.workflow.ready .step:nth-child(1) .step__ring { animation-delay: 400ms; }
.workflow.ready .step:nth-child(2) .step__ring { animation-delay: 700ms; }
.workflow.ready .step:nth-child(3) .step__ring { animation-delay: 1000ms; }
.workflow.ready .step:nth-child(4) .step__ring { animation-delay: 1300ms; }
.workflow.ready .step:nth-child(5) .step__ring { animation-delay: 1600ms; }

@keyframes ring-pulse {
  0% { transform: scale(0.6); opacity: 0.8; }
  100% { transform: scale(2); opacity: 0; }
}

.step__num {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--ink-faint);
  letter-spacing: var(--track-extra);
  margin-bottom: 8px;
}

.step__title {
  font-family: var(--font-display);
  font-size: var(--text-xl);
  font-weight: 600;
  color: var(--ink);
  margin: 0 0 8px;
  letter-spacing: var(--track-snug);
}

.step__desc {
  font-size: var(--text-sm);
  color: var(--ink-muted);
  line-height: 1.6;
  margin: 0;
}

.step__icon {
  margin-top: 16px;
  color: var(--accent);
  width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
  border: 1px solid var(--line);
  border-radius: 4px;
  background: var(--bg-card);
  transition: transform var(--d-slow) var(--ease-out), border-color var(--d-base) var(--ease-out);
}
.step:hover .step__icon {
  transform: translateY(-2px);
  border-color: var(--accent);
}
.step__icon svg {
  width: 20px;
  height: 20px;
}

@media (max-width: 880px) {
  .workflow__steps {
    grid-template-columns: 1fr;
  }
  .workflow__line {
    display: none;
  }
  .step {
    padding: var(--s-4) 0 var(--s-4) 60px;
    border-left: 1px dashed var(--line);
    margin-left: 20px;
  }
  .step__node {
    top: var(--s-4);
    left: -12px;
    transform: none;
  }
}
</style>
