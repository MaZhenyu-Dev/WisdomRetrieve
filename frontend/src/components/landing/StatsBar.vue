<template>
  <section ref="root" :class="['stats-bar', { ready: isInView }]">
    <div class="stats-bar__inner container-wide">
      <div
        v-for="(item, i) in items"
        :key="item.label"
        class="stat"
        :style="{ transitionDelay: `${i * 100}ms` }"
      >
        <div class="stat__num">
          <CountUp
            :value="item.value"
            :suffix="item.suffix"
            :decimals="item.decimals"
            :auto-start="false"
          />
        </div>
        <div class="stat__divider" />
        <div class="stat__label">{{ item.label }}</div>
        <p class="stat__caption">{{ item.caption }}</p>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";

import CountUp from "../ui/CountUp.vue";
import { useReveal } from "../../composables/useReveal";

const { target: root, isInView } = useReveal<HTMLElement>({ threshold: 0.3 });

const items = [
  { value: 92, suffix: "%", label: "检索命中率", caption: "向量 + BM25 混合召回", decimals: 0 },
  { value: 312, suffix: "ms", label: "平均响应", caption: "端到端生成耗时", decimals: 0 },
  { value: 50, suffix: "K+", label: "可索引 Chunks", caption: "单库容量上限", decimals: 0 },
  { value: 4, suffix: " 路", label: "混合召回", caption: "Vector · BM25 · Hybrid · Rerank", decimals: 0 }
];

const triggered = ref(false);
watch(isInView, (v) => {
  if (v) triggered.value = true;
});
</script>

<style scoped>
.stats-bar {
  padding: var(--s-10) 0 var(--s-11);
  border-top: 1px solid var(--line);
  border-bottom: 1px solid var(--line);
  background: var(--bg-soft);
}

.stats-bar__inner {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--s-7);
}

.stat {
  display: grid;
  gap: 10px;
  padding: var(--s-5) var(--s-6);
  border-left: 1px solid var(--line);
  opacity: 0;
  transform: translateY(20px);
  transition: opacity 700ms var(--ease-out), transform 700ms var(--ease-out);
}
.stats-bar.ready .stat {
  opacity: 1;
  transform: translateY(0);
}
.stat:first-child {
  border-left: 0;
  padding-left: 0;
}

.stat__num {
  font-family: var(--font-display);
  font-size: var(--text-5xl);
  font-weight: 600;
  color: var(--ink);
  letter-spacing: var(--track-tight);
  line-height: 1;
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.stat__divider {
  width: 24px;
  height: 1px;
  background: var(--accent);
  margin: 8px 0 4px;
}

.stat__label {
  font-family: var(--font-sans);
  font-size: var(--text-md);
  font-weight: 600;
  color: var(--ink);
  letter-spacing: var(--track-snug);
}

.stat__caption {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--ink-muted);
  letter-spacing: var(--track-wide);
  text-transform: uppercase;
  line-height: 1.5;
}

@media (max-width: 880px) {
  .stats-bar__inner {
    grid-template-columns: repeat(2, 1fr);
  }
  .stat {
    border-left: 0;
    padding: var(--s-4);
    border-top: 1px solid var(--line);
  }
  .stat:nth-child(1), .stat:nth-child(2) {
    border-top: 0;
  }
}
</style>
