<template>
  <section id="capability" ref="root" :class="['capability', { ready: isInView }]">
    <header class="capability__head container-wide">
      <p class="eyebrow">
        <span class="eyebrow__bar" />
        Section 01 · Core Capabilities
      </p>
      <div class="capability__head-row">
        <h2 class="capability__title">
          四个能力，<br />
          串起整个<span class="accent">问答循环</span>。
        </h2>
        <p class="capability__intro">
          从 PDF 接入、到答案生成，<br />
          每一步都经得起审查与回溯。
        </p>
      </div>
    </header>

    <div class="capability__list">
      <article
        v-for="(item, i) in items"
        :key="item.num"
        class="cap-row"
        :class="{ 'cap-row--in': isInView }"
        :style="{ '--row-delay': `${i * 90}ms` }"
      >
        <div class="cap-row__inner">
          <div class="cap-row__num">{{ item.num }}</div>
          <div class="cap-row__main">
            <div class="cap-row__top">
              <h3 class="cap-row__title">{{ item.title }}</h3>
              <span class="cap-row__tag">{{ item.tag }}</span>
            </div>
            <p class="cap-row__desc">{{ item.desc }}</p>
            <ul class="cap-row__points">
              <li v-for="p in item.points" :key="p">
                <span class="cap-row__bullet" />
                {{ p }}
              </li>
            </ul>
          </div>
          <div class="cap-row__visual" v-html="item.visual" />
        </div>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";

import { useReveal } from "../../composables/useReveal";

const { target: root, isInView } = useReveal<HTMLElement>({ threshold: 0.1 });

const items = [
  {
    num: "01",
    title: "文档解析",
    tag: "Ingest",
    desc: "上传 PDF 后自动切分章节，识别表格与扫描件，保留上下文结构。",
    points: ["多页 PDF · 表格 · OCR", "结构化 chunk 与原文双向锚定", "失败任务可重试 · 可回滚"],
    visual: `
      <svg viewBox="0 0 200 140" xmlns="http://www.w3.org/2000/svg">
        <rect x="20" y="14" width="60" height="80" rx="2" fill="none" stroke="currentColor" stroke-width="1" opacity="0.5"/>
        <rect x="32" y="26" width="36" height="2" fill="currentColor" opacity="0.6"/>
        <rect x="32" y="34" width="28" height="2" fill="currentColor" opacity="0.4"/>
        <rect x="32" y="42" width="40" height="2" fill="currentColor" opacity="0.6"/>
        <rect x="32" y="50" width="32" height="2" fill="currentColor" opacity="0.4"/>
        <rect x="32" y="62" width="36" height="2" fill="currentColor" opacity="0.6"/>
        <rect x="32" y="70" width="40" height="2" fill="currentColor" opacity="0.4"/>
        <rect x="100" y="20" width="80" height="100" rx="2" fill="none" stroke="currentColor" stroke-width="1" opacity="0.3" stroke-dasharray="2 4"/>
        <rect x="110" y="32" width="60" height="2" fill="currentColor" opacity="0.4"/>
        <rect x="110" y="42" width="40" height="2" fill="currentColor" opacity="0.3"/>
        <rect x="110" y="50" width="50" height="2" fill="currentColor" opacity="0.4"/>
        <rect x="110" y="58" width="38" height="2" fill="currentColor" opacity="0.3"/>
        <rect x="110" y="72" width="50" height="2" fill="currentColor" opacity="0.4"/>
        <rect x="110" y="80" width="42" height="2" fill="currentColor" opacity="0.3"/>
        <path d="M 80 54 L 100 54" stroke="currentColor" stroke-width="1" opacity="0.5"/>
        <polygon points="96,51 100,54 96,57" fill="currentColor" opacity="0.5"/>
      </svg>
    `
  },
  {
    num: "02",
    title: "智能检索",
    tag: "Retrieve",
    desc: "向量召回 + BM25 关键词 + 精排三段式，把最相关的 chunk 推到 LLM 面前。",
    points: ["BGE / OpenAI 嵌入可切换", "Hybrid 召回 + Rerank 精排", "Top-K 可调 · 引用可追溯"],
    visual: `
      <svg viewBox="0 0 200 140" xmlns="http://www.w3.org/2000/svg">
        <circle cx="40" cy="70" r="14" fill="none" stroke="currentColor" stroke-width="1" opacity="0.6"/>
        <circle cx="40" cy="70" r="3" fill="currentColor"/>
        <text x="40" y="100" text-anchor="middle" fill="currentColor" opacity="0.6" font-size="8" font-family="monospace">query</text>
        <line x1="54" y1="60" x2="100" y2="36" stroke="currentColor" stroke-width="1" opacity="0.5"/>
        <line x1="54" y1="65" x2="100" y2="60" stroke="currentColor" stroke-width="1" opacity="0.5"/>
        <line x1="54" y1="70" x2="100" y2="86" stroke="currentColor" stroke-width="1" opacity="0.5"/>
        <line x1="54" y1="75" x2="100" y2="110" stroke="currentColor" stroke-width="1" opacity="0.5"/>
        <rect x="100" y="28" width="60" height="14" rx="2" fill="none" stroke="currentColor" stroke-width="1" opacity="0.4"/>
        <rect x="100" y="52" width="60" height="14" rx="2" fill="none" stroke="currentColor" stroke-width="1" opacity="0.6" fill="currentColor" fill-opacity="0.06"/>
        <rect x="100" y="78" width="60" height="14" rx="2" fill="none" stroke="currentColor" stroke-width="1" opacity="0.4"/>
        <rect x="100" y="102" width="60" height="14" rx="2" fill="none" stroke="currentColor" stroke-width="1" opacity="0.6" fill="currentColor" fill-opacity="0.06"/>
        <text x="130" y="38" text-anchor="middle" fill="currentColor" opacity="0.5" font-size="7" font-family="monospace">v0.71</text>
        <text x="130" y="62" text-anchor="middle" fill="currentColor" opacity="0.8" font-size="7" font-family="monospace">v0.92</text>
        <text x="130" y="88" text-anchor="middle" fill="currentColor" opacity="0.5" font-size="7" font-family="monospace">v0.68</text>
        <text x="130" y="112" text-anchor="middle" fill="currentColor" opacity="0.8" font-size="7" font-family="monospace">v0.85</text>
      </svg>
    `
  },
  {
    num: "03",
    title: "答案生成",
    tag: "Generate",
    desc: "把召回片段与历史对话拼成 prompt，LLM 输出带引用、可读的最终答案。",
    points: ["Markdown 原生输出", "引用编号自动绑定原文", "可配置 temperature / model"],
    visual: `
      <svg viewBox="0 0 200 140" xmlns="http://www.w3.org/2000/svg">
        <rect x="20" y="20" width="160" height="100" rx="4" fill="none" stroke="currentColor" stroke-width="1" opacity="0.4"/>
        <rect x="32" y="34" width="100" height="2" fill="currentColor" opacity="0.5"/>
        <rect x="32" y="44" width="130" height="2" fill="currentColor" opacity="0.3"/>
        <rect x="32" y="52" width="120" height="2" fill="currentColor" opacity="0.5"/>
        <rect x="32" y="60" width="90" height="2" fill="currentColor" opacity="0.3"/>
        <rect x="32" y="76" width="80" height="2" fill="currentColor" opacity="0.5"/>
        <rect x="32" y="84" width="110" height="2" fill="currentColor" opacity="0.3"/>
        <rect x="32" y="100" width="60" height="2" fill="currentColor" opacity="0.4"/>
        <circle cx="160" cy="38" r="6" fill="none" stroke="currentColor" stroke-width="1" opacity="0.6"/>
        <text x="160" y="42" text-anchor="middle" fill="currentColor" font-size="7" font-family="monospace" opacity="0.7">1</text>
        <circle cx="160" cy="78" r="6" fill="none" stroke="currentColor" stroke-width="1" opacity="0.6"/>
        <text x="160" y="82" text-anchor="middle" fill="currentColor" font-size="7" font-family="monospace" opacity="0.7">2</text>
      </svg>
    `
  },
  {
    num: "04",
    title: "运行监控",
    tag: "Observe",
    desc: "缓存命中率、平均响应、问答量一目了然，瓶颈永远不藏在黑盒里。",
    points: ["实时缓存命中统计", "响应时间分位数", "问答日志全留痕"],
    visual: `
      <svg viewBox="0 0 200 140" xmlns="http://www.w3.org/2000/svg">
        <line x1="20" y1="110" x2="180" y2="110" stroke="currentColor" stroke-width="1" opacity="0.4"/>
        <line x1="20" y1="20" x2="20" y2="110" stroke="currentColor" stroke-width="1" opacity="0.4"/>
        <polyline points="20,90 45,72 70,82 95,46 120,58 145,30 170,38" fill="none" stroke="currentColor" stroke-width="1.5" opacity="0.7"/>
        <polyline points="20,96 45,88 70,92 95,76 120,80 145,68 170,72" fill="none" stroke="currentColor" stroke-width="1.5" opacity="0.3" stroke-dasharray="2 3"/>
        <circle cx="120" cy="58" r="3" fill="currentColor"/>
        <circle cx="170" cy="38" r="3" fill="currentColor"/>
        <text x="100" y="130" text-anchor="middle" fill="currentColor" opacity="0.5" font-size="8" font-family="monospace">response · ms</text>
      </svg>
    `
  }
];
</script>

<style scoped>
.capability {
  padding: var(--s-13) 0 var(--s-12);
}

.capability__head {
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

.capability__head-row {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: var(--s-7);
  align-items: end;
  margin-top: var(--s-5);
}

.capability__title {
  font-family: var(--font-display);
  font-size: var(--text-5xl);
  font-weight: 600;
  line-height: 1.05;
  letter-spacing: var(--track-tight);
  color: var(--ink);
  margin: 0;
}
.capability__title .accent {
  font-style: italic;
  color: var(--accent);
  font-weight: 600;
}

.capability__intro {
  font-size: var(--text-md);
  color: var(--ink-muted);
  line-height: 1.7;
  letter-spacing: var(--track-snug);
  max-width: 380px;
  justify-self: end;
}

.capability__list {
  border-top: 1px solid var(--line);
}

.cap-row {
  position: relative;
  border-bottom: 1px solid var(--line);
  background: transparent;
  transition: background-color var(--d-slow) var(--ease-out);
  opacity: 0;
  transform: translateY(20px);
}
.cap-row--in {
  opacity: 1;
  transform: translateY(0);
  transition:
    opacity 720ms var(--ease-out),
    transform 720ms var(--ease-out),
    background-color var(--d-slow) var(--ease-out);
  transition-delay: var(--row-delay, 0ms);
}

.cap-row:hover {
  background-color: var(--bg-soft);
}

.cap-row__inner {
  display: grid;
  grid-template-columns: 100px 1fr 200px;
  gap: var(--s-7);
  align-items: center;
  padding: var(--s-8) var(--s-7);
  max-width: var(--container-wide);
  margin: 0 auto;
}

.cap-row__num {
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--ink-faint);
  letter-spacing: var(--track-wide);
  position: relative;
  padding-left: var(--s-4);
}
.cap-row__num::before {
  content: "";
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 1px;
  height: 32px;
  background: var(--accent);
  transform-origin: top;
  transition: height var(--d-slow) var(--ease-out);
}
.cap-row:hover .cap-row__num::before {
  height: 56px;
}

.cap-row__main {
  display: grid;
  gap: 10px;
}

.cap-row__top {
  display: flex;
  align-items: baseline;
  gap: var(--s-4);
}

.cap-row__title {
  font-family: var(--font-display);
  font-size: var(--text-3xl);
  font-weight: 600;
  color: var(--ink);
  margin: 0;
  letter-spacing: var(--track-tight);
  line-height: 1.1;
}

.cap-row__tag {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--accent);
  text-transform: uppercase;
  letter-spacing: var(--track-extra);
  border: 1px solid var(--accent);
  padding: 3px 8px;
  border-radius: 2px;
}

.cap-row__desc {
  font-size: var(--text-md);
  color: var(--ink-soft);
  line-height: 1.6;
  max-width: 540px;
  margin: 0;
}

.cap-row__points {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-top: 6px;
}
.cap-row__points li {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--ink-muted);
  letter-spacing: var(--track-wide);
}
.cap-row__bullet {
  width: 4px;
  height: 4px;
  background: var(--accent);
  border-radius: 50%;
}

.cap-row__visual {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--accent);
}
.cap-row__visual svg {
  width: 100%;
  max-width: 200px;
  height: auto;
  filter: drop-shadow(0 6px 18px var(--accent-soft));
  transition: transform var(--d-slow) var(--ease-out);
}
.cap-row:hover .cap-row__visual svg {
  transform: translateY(-2px) scale(1.03);
}

@media (max-width: 880px) {
  .capability__head-row {
    grid-template-columns: 1fr;
    align-items: start;
  }
  .capability__intro {
    justify-self: start;
  }
  .cap-row__inner {
    grid-template-columns: 60px 1fr;
    padding: var(--s-6) var(--s-4);
  }
  .cap-row__visual {
    grid-column: 1 / -1;
    max-width: 200px;
    margin: 0 auto;
  }
}
</style>
