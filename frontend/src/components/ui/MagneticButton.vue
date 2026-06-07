<template>
  <component
    :is="tag"
    ref="root"
    class="magnetic"
    :class="['magnetic--' + variant, { 'magnetic--active': isHovering }]"
    :style="magnetStyle"
    @mouseenter="onEnter"
    @mouseleave="onLeave"
    @mousemove="onMove"
    @click="onClick"
  >
    <span class="magnetic__inner" :style="innerStyle">
      <slot />
    </span>
    <span v-for="r in ripples" :key="r.id" class="magnetic__ripple" :style="r.style" />
  </component>
</template>

<script setup lang="ts">
import { ref, computed, type CSSProperties } from "vue";

interface Props {
  /** primary | ghost | outline */
  variant?: "primary" | "ghost" | "outline";
  /** 渲染标签 */
  tag?: string;
  /** 磁吸强度 0-1，越大越跟手 */
  strength?: number;
  /** 是否有点击涟漪 */
  ripple?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  variant: "primary",
  tag: "button",
  strength: 0.25,
  ripple: true
});

const root = ref<HTMLElement | null>(null);
const offsetX = ref(0);
const offsetY = ref(0);
const isHovering = ref(false);

const ripples = ref<{ id: number; style: CSSProperties }[]>([]);
let rippleId = 0;

const magnetStyle = computed<CSSProperties>(() => ({
  transform: `translate(${offsetX.value}px, ${offsetY.value}px)`
}));

const innerStyle = computed<CSSProperties>(() => ({
  transform: `translate(${-offsetX.value * 0.4}px, ${-offsetY.value * 0.4}px)`
}));

function onEnter() {
  isHovering.value = true;
}

function onLeave() {
  isHovering.value = false;
  offsetX.value = 0;
  offsetY.value = 0;
}

function onMove(e: MouseEvent) {
  if (!root.value) return;
  const rect = root.value.getBoundingClientRect();
  const cx = rect.left + rect.width / 2;
  const cy = rect.top + rect.height / 2;
  offsetX.value = (e.clientX - cx) * props.strength;
  offsetY.value = (e.clientY - cy) * props.strength;
}

function onClick(e: MouseEvent) {
  if (!props.ripple || !root.value) return;
  const rect = root.value.getBoundingClientRect();
  const x = e.clientX - rect.left;
  const y = e.clientY - rect.top;
  const size = Math.max(rect.width, rect.height) * 2;
  const id = ++rippleId;
  ripples.value.push({
    id,
    style: {
      left: `${x - size / 2}px`,
      top: `${y - size / 2}px`,
      width: `${size}px`,
      height: `${size}px`
    }
  });
  setTimeout(() => {
    ripples.value = ripples.value.filter((r) => r.id !== id);
  }, 600);
}
</script>

<style scoped>
.magnetic {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 14px 28px;
  border: 1px solid transparent;
  border-radius: 4px;
  font-family: var(--font-sans);
  font-size: var(--text-base);
  font-weight: 500;
  letter-spacing: 0;
  cursor: pointer;
  overflow: hidden;
  isolation: isolate;
  transition:
    background-color var(--d-base) var(--ease-out),
    border-color var(--d-base) var(--ease-out),
    color var(--d-base) var(--ease-out),
    box-shadow var(--d-base) var(--ease-out);
}

.magnetic__inner {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  transition: transform 220ms var(--ease-out);
  will-change: transform;
}

.magnetic--primary {
  background: var(--accent);
  color: var(--accent-ink);
  border-color: var(--accent);
  font-weight: 600;
}
.magnetic--primary:hover {
  background: var(--accent-strong);
  border-color: var(--accent-strong);
  box-shadow: 0 12px 32px var(--accent-glow);
}

.magnetic--ghost {
  background: transparent;
  color: var(--ink);
  border-color: var(--line);
}
.magnetic--ghost:hover {
  background: var(--bg-soft);
  border-color: var(--line-strong);
}

.magnetic--outline {
  background: transparent;
  color: var(--ink);
  border-color: var(--ink);
}

.magnetic__ripple {
  position: absolute;
  border-radius: 50%;
  background: currentColor;
  opacity: 0.18;
  transform: scale(0);
  pointer-events: none;
  z-index: 0;
  animation: ripple 600ms var(--ease-out) forwards;
}

@keyframes ripple {
  to {
    transform: scale(1);
    opacity: 0;
  }
}
</style>
