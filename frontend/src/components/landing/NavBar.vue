<template>
  <header :class="['landing-nav', { 'is-solid': isSolid }]">
    <div class="landing-nav__inner">
      <a class="brand" href="#top" @click.prevent="$emit('top')">
        <img class="brand-mark" :src="brandLogo" alt="WisdomRetrieve" />
        <div class="brand-text">
          <strong>WisdomRAG</strong>
        </div>
      </a>

      <nav class="links" aria-label="primary">
        <a
          v-for="link in links"
          :key="link.id"
          :href="`#${link.id}`"
          class="link"
          :class="{ active: activeId === link.id }"
          @click.prevent="$emit('jump', link.id)"
        >
          <span class="link__num">{{ link.num }}</span>
          <span class="link__label">{{ link.label }}</span>
        </a>
      </nav>

      <div class="actions">
        <MagneticButton variant="primary" :strength="0.2" @click="$emit('try')">
          立即体验
          <el-icon class="el-icon--right"><ArrowRight /></el-icon>
        </MagneticButton>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { ArrowRight } from "@element-plus/icons-vue";

import brandLogo from "../../assets/svg/langchain-color.svg";
import MagneticButton from "../ui/MagneticButton.vue";

defineProps<{
  isSolid: boolean;
  activeId: string;
}>();

defineEmits<{
  (e: "top"): void;
  (e: "jump", id: string): void;
  (e: "try"): void;
}>();

const links = [
  { num: "01", label: "能力", id: "capability" },
  { num: "02", label: "工作流", id: "workflow" },
  { num: "03", label: "演示", id: "demo" },
  { num: "04", label: "数据", id: "stats" }
];
</script>

<style scoped>
.landing-nav {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: var(--z-nav);
  height: var(--nav-h);
  display: flex;
  align-items: center;
  background: transparent;
  border-bottom: 1px solid transparent;
  transition:
    background-color var(--d-base) var(--ease-out),
    border-color var(--d-base) var(--ease-out),
    backdrop-filter var(--d-base) var(--ease-out);
}

.landing-nav.is-solid {
  background: rgba(10, 10, 12, 0.72);
  border-bottom-color: var(--line);
  backdrop-filter: blur(18px) saturate(140%);
  -webkit-backdrop-filter: blur(18px) saturate(140%);
}

.landing-nav__inner {
  width: 100%;
  max-width: var(--container-wide);
  margin: 0 auto;
  padding: 0 var(--s-6);
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: var(--s-7);
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  text-decoration: none;
  color: inherit;
}

.brand-mark {
  width: 32px;
  height: 32px;
  padding: 4px;
  border: 1px solid var(--line-strong);
  border-radius: 4px;
  background: var(--bg-elevated);
  color: var(--ink);
  object-fit: contain;
  transition: border-color var(--d-base) var(--ease-out);
}

.brand:hover .brand-mark {
  border-color: var(--accent);
}

.brand-text {
  display: grid;
  gap: 1px;
}

.brand-text strong {
  font-family: var(--font-display);
  font-size: 15px;
  font-weight: 600;
  color: var(--ink);
  letter-spacing: var(--track-snug);
  line-height: 1;
}

.brand-text span {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--ink-muted);
  text-transform: uppercase;
  letter-spacing: var(--track-extra);
}

.links {
  display: flex;
  justify-content: center;
  gap: var(--s-7);
}

.link {
  display: inline-flex;
  align-items: baseline;
  gap: 6px;
  padding: 6px 0;
  color: var(--ink-muted);
  font-size: var(--text-sm);
  text-decoration: none;
  position: relative;
  transition: color var(--d-base) var(--ease-out);
}

.link__num {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--ink-faint);
  letter-spacing: var(--track-wide);
}

.link::after {
  content: "";
  position: absolute;
  left: 0;
  right: 100%;
  bottom: -2px;
  height: 1px;
  background: var(--accent);
  transition: right var(--d-base) var(--ease-out);
}

.link:hover,
.link.active {
  color: var(--ink);
}

.link:hover::after,
.link.active::after {
  right: 0;
}

.actions {
  display: flex;
  align-items: center;
  gap: var(--s-3);
}

@media (max-width: 880px) {
  .links {
    display: none;
  }
  .landing-nav__inner {
    grid-template-columns: auto 1fr auto;
  }
}
</style>
