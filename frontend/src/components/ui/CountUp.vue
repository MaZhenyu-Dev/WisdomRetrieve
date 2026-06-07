<template>
  <span ref="root" class="count-up" :class="{ ready: isInView }">
    <span class="num">{{ display }}</span>
    <span v-if="suffix" class="suffix">{{ suffix }}</span>
  </span>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";

import { useReveal } from "../../composables/useReveal";

interface Props {
  /** 目标值 */
  value: number;
  /** 起始值 */
  start?: number;
  /** 动画时长 ms */
  duration?: number;
  /** 小数位 */
  decimals?: number;
  /** 前缀，如 "≈" */
  prefix?: string;
  /** 后缀，如 "%", "ms" */
  suffix?: string;
  /** 进入视口后是否自动开始（默认 true） */
  autoStart?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  start: 0,
  duration: 1400,
  decimals: 0,
  prefix: "",
  suffix: "",
  autoStart: true
});

const { target: root, isInView } = useReveal<HTMLElement>({
  threshold: 0.4
});

const current = ref(props.autoStart ? props.start : props.start);
const localStart = props.start;

watch(isInView, (v) => {
  if (v) start();
});

function start() {
  const t0 = performance.now();
  const easeOut = (t: number) => (t === 1 ? 1 : 1 - Math.pow(2, -10 * t));
  const tick = (now: number) => {
    const t = Math.min(1, (now - t0) / props.duration);
    const v = localStart + (props.value - localStart) * easeOut(t);
    current.value =
      props.decimals > 0 ? Number(v.toFixed(props.decimals)) : Math.round(v);
    if (t < 1) requestAnimationFrame(tick);
    else current.value = props.value;
  };
  requestAnimationFrame(tick);
}

const display = computed(() => `${props.prefix}${current.value}`);
</script>

<style scoped>
.count-up {
  display: inline-flex;
  align-items: baseline;
  gap: 2px;
  font-variant-numeric: tabular-nums;
  font-feature-settings: "tnum";
}
.suffix {
  font-size: 0.5em;
  color: var(--ink-muted);
  margin-left: 4px;
}
</style>
