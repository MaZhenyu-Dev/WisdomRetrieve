import { createRouter, createWebHistory } from "vue-router";

import { isAuthenticated } from "../utils/auth";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      name: "home",
      component: () => import("../views/LandingView.vue"),
      meta: { layout: "public", title: "WisdomRetrieve · 企业知识中枢" }
    },
    {
      path: "/login",
      name: "login",
      component: () => import("../views/LoginView.vue"),
      meta: { layout: "public", title: "登录 · WisdomRetrieve" }
    },
    {
      path: "/app",
      component: () => import("../layouts/WorkspaceLayout.vue"),
      redirect: "/app/knowledge",
      meta: { requiresAuth: true },
      children: [
        {
          path: "knowledge",
          name: "knowledge",
          component: () => import("../views/KnowledgeView.vue"),
          meta: { title: "知识库管理" }
        },
        {
          path: "chat",
          name: "chat",
          component: () => import("../views/ChatView.vue"),
          meta: { title: "智能问答" }
        },
        {
          path: "monitor",
          name: "monitor",
          component: () => import("../views/MonitorView.vue"),
          meta: { title: "系统监控" }
        }
      ]
    },
    {
      path: "/:pathMatch(.*)*",
      redirect: "/"
    }
  ],
  scrollBehavior(to, _from, savedPosition) {
    if (savedPosition) return savedPosition;
    if (to.hash) return { el: to.hash, behavior: "smooth" };
    return { top: 0, behavior: "smooth" };
  }
});

router.beforeEach((to) => {
  if (to.meta.requiresAuth && !isAuthenticated()) {
    return { name: "login", query: { next: to.fullPath } };
  }
  if (to.name === "login" && isAuthenticated()) {
    return { name: "knowledge" };
  }
  return true;
});

router.afterEach((to) => {
  const title = to.meta.title as string | undefined;
  if (title && typeof document !== "undefined") {
    document.title = title;
  }
});

export default router;
