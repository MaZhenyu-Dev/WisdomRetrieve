<template>
  <div class="workspace-shell">
    <aside class="sidebar">
      <div class="brand">
        <img class="brand-mark" :src="brandLogo" alt="WisdomRAG" />
        <div>
          <strong>WisdomRAG</strong>
        </div>
      </div>

      <nav class="nav-list">
        <RouterLink v-for="item in navItems" :key="item.to" :to="item.to" class="nav-item">
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
        </RouterLink>
      </nav>

      <div class="sidebar-foot">
        <div class="operator">
          <span>当前用户</span>
          <strong>{{ username || "operator" }}</strong>
        </div>
        <el-button text class="logout-button" @click="logout">
          <el-icon><SwitchButton /></el-icon>
          退出
        </el-button>
      </div>
    </aside>

    <div class="workspace-main">
      <header class="topbar">
        <div>
          <p class="section-kicker">Enterprise RAG Console</p>
          <h1>{{ route.meta.title || "工作台" }}</h1>
        </div>
        <div class="topbar-actions">
          <span :class="['health-pill', healthStatus]">
            <span class="pulse-dot"></span>
            {{ healthText }}
          </span>
          <el-button class="ghost-action" @click="refreshHealth">刷新状态</el-button>
        </div>
      </header>

      <main class="content-stage">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ChatDotRound, Collection, Monitor, SwitchButton } from "@element-plus/icons-vue";
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import brandLogo from "../assets/svg/langchain-color.svg";
import { getHealth } from "../api";
import { clearAuthSession, getAuthUser } from "../utils/auth";

const route = useRoute();
const router = useRouter();
const username = getAuthUser();
const healthStatus = ref<"ok" | "degraded" | "unknown">("unknown");

const navItems = [
  { to: "/app/knowledge", label: "知识库", icon: Collection },
  { to: "/app/chat", label: "智能问答", icon: ChatDotRound },
  { to: "/app/monitor", label: "系统监控", icon: Monitor }
];

const healthText = computed(() => {
  if (healthStatus.value === "ok") return "后端在线";
  if (healthStatus.value === "degraded") return "服务降级";
  return "状态未知";
});

async function refreshHealth() {
  try {
    const health = await getHealth();
    healthStatus.value = health.status === "ok" ? "ok" : "degraded";
  } catch {
    healthStatus.value = "unknown";
  }
}

function logout() {
  clearAuthSession();
  router.replace("/");
}

onMounted(refreshHealth);
</script>
