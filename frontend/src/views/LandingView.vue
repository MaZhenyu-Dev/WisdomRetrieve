<template>
  <div class="landing">
    <NavBar
      :is-solid="isScrolled"
      :active-id="activeId"
      @top="scrollToTop"
      @jump="scrollTo"
      @try="goLogin"
    />

    <main>
      <HeroSection @try="goLogin" @learn="goWorkflow" @scroll-down="goCapability" />

      <CapabilityList id="capability" />

      <WorkflowTimeline id="workflow" />

      <ChatDemo id="demo" />

      <StatsBar id="stats" />

      <SiteFooter @try="goLogin" @jump="scrollTo" />
    </main>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from "vue";
import { useRouter } from "vue-router";

import CapabilityList from "../components/landing/CapabilityList.vue";
import ChatDemo from "../components/landing/ChatDemo.vue";
import HeroSection from "../components/landing/HeroSection.vue";
import NavBar from "../components/landing/NavBar.vue";
import SiteFooter from "../components/landing/SiteFooter.vue";
import StatsBar from "../components/landing/StatsBar.vue";
import WorkflowTimeline from "../components/landing/WorkflowTimeline.vue";

const router = useRouter();

const isScrolled = ref(false);
const activeId = ref("");

let scrollRaf = 0;
const navOffset = 120;
const sectionIds = ["capability", "workflow", "demo", "stats"];

function goLogin() {
  router.push("/login");
}

function scrollToTop() {
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function scrollTo(id: string) {
  const el = document.getElementById(id);
  if (el) {
    const top = el.getBoundingClientRect().top + window.scrollY - 72;
    window.scrollTo({ top, behavior: "smooth" });
  }
}

function goWorkflow() {
  scrollTo("workflow");
}

function goCapability() {
  scrollTo("capability");
}

// 取"顶部已滑过 navOffset、最接近 navOffset"的 section 作为激活项；
// 这样在 hero 阶段（所有 section 都在视口下方）不会误激活，
// 在 section 边界与快速滚动时表现稳定。
function updateActive() {
  let bestId = "";
  let bestDistance = Infinity;
  for (const id of sectionIds) {
    const el = document.getElementById(id);
    if (!el) continue;
    const top = el.getBoundingClientRect().top;
    if (top - navOffset <= 0) {
      const distance = navOffset - top;
      if (distance < bestDistance) {
        bestDistance = distance;
        bestId = id;
      }
    }
  }
  activeId.value = bestId;
}

function onScroll() {
  cancelAnimationFrame(scrollRaf);
  scrollRaf = requestAnimationFrame(() => {
    isScrolled.value = window.scrollY > 80;
    updateActive();
  });
}

onMounted(() => {
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();
});

onBeforeUnmount(() => {
  window.removeEventListener("scroll", onScroll);
});
</script>

<style scoped>
.landing {
  min-height: 100vh;
  position: relative;
}

main {
  display: block;
}
</style>
