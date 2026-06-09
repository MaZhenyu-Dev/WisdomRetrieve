<template>
  <div class="login">
    <!-- 顶部条 -->
    <header
      class="login__topbar"
      v-motion
      :initial="{ opacity: 0, y: -8 }"
      :enter="{ opacity: 1, y: 0, transition: { duration: 500, ease: [0.16, 1, 0.3, 1] } }"
    >
      <RouterLink to="/" class="login__brand">
        <img class="login__mark" :src="brandLogo" alt="WisdomRAG" />
        <span class="login__brand-name">WisdomRAG</span>
      </RouterLink>
      <RouterLink to="/" class="login__back">
        <el-icon><ArrowLeft /></el-icon>
        <span>回到首页</span>
      </RouterLink>
    </header>

    <main class="login__main">
      <!-- 左侧：编辑式品牌叙事 -->
      <section class="login__story">
        <div class="story__grid" aria-hidden="true" />
        <div class="story__glow story__glow--a" aria-hidden="true" />
        <div class="story__glow story__glow--b" aria-hidden="true" />

        <div class="story__inner">
          <p
            class="eyebrow"
            v-motion
            :initial="{ opacity: 0, y: 12 }"
            :enter="{ opacity: 1, y: 0, transition: { delay: 100, duration: 600 } }"
          >
            <span class="eyebrow__dot" />
            Sign in · 登录工作台
          </p>

          <h1 class="story__title">
            <span
              v-for="(line, i) in titleLines"
              :key="i"
              class="story__line"
              v-motion
              :initial="{ opacity: 0, y: 28, clipPath: 'inset(0 0 100% 0)' }"
              :enter="{
                opacity: 1,
                y: 0,
                clipPath: 'inset(0 0 0% 0)',
                transition: { delay: 200 + i * 120, duration: 800, ease: [0.16, 1, 0.3, 1] }
              }"
            >
              {{ line }}
            </span>
          </h1>

          <p
            class="story__sub"
            v-motion
            :initial="{ opacity: 0, y: 12 }"
            :enter="{ opacity: 1, y: 0, transition: { delay: 600, duration: 600 } }"
          >
            把每一份 PDF、每一次问答、每一条引用，
            <br />都收进属于团队的知识中枢。
          </p>

          <ul
            class="story__features"
            v-motion
            :initial="{ opacity: 0, y: 12 }"
            :enter="{ opacity: 1, y: 0, transition: { delay: 720, duration: 600 } }"
          >
            <li v-for="f in features" :key="f">
              <span class="story__bullet" />
              <span>{{ f }}</span>
            </li>
          </ul>

          <div
            class="story__ticker"
            v-motion
            :initial="{ opacity: 0 }"
            :enter="{ opacity: 1, transition: { delay: 900, duration: 800 } }"
          >
            <span class="story__ticker-dot" />
            <span>v1.0 · Hybrid 召回 + Rerank 精排 · 已就绪</span>
          </div>
        </div>
      </section>

      <!-- 右侧：登录表单 -->
      <section
        class="login__panel"
        v-motion
        :initial="{ opacity: 0, y: 24 }"
        :enter="{ opacity: 1, y: 0, transition: { delay: 250, duration: 800, ease: [0.16, 1, 0.3, 1] } }"
      >
        <div class="panel__inner">
          <div
            class="panel__head"
            v-motion
            :initial="{ opacity: 0, y: 10 }"
            :enter="{ opacity: 1, y: 0, transition: { delay: 400, duration: 500 } }"
          >
            <h2>登录工作台</h2>
            <p>使用本地 Token 进入 · 接入后端鉴权后可无缝替换</p>
          </div>

          <form class="panel__form" @submit.prevent="login" novalidate>
            <div
              class="field"
              :class="{ 'field--error': errors.username, 'field--shake': shake === 'username' }"
              v-motion
              :initial="{ opacity: 0, y: 10 }"
              :enter="{ opacity: 1, y: 0, transition: { delay: 480, duration: 500 } }"
            >
              <label for="login-username">用户名</label>
              <div class="field__line">
                <input
                  id="login-username"
                  v-model="username"
                  type="text"
                  placeholder="admin"
                  autocomplete="username"
                  @blur="validateField('username')"
                />
              </div>
              <span v-if="errors.username" class="field__msg">{{ errors.username }}</span>
            </div>

            <div
              class="field"
              :class="{ 'field--error': errors.token, 'field--shake': shake === 'token' }"
              v-motion
              :initial="{ opacity: 0, y: 10 }"
              :enter="{ opacity: 1, y: 0, transition: { delay: 560, duration: 500 } }"
            >
              <label for="login-token">密码</label>
              <div class="field__line field__line--with-action">
                <input
                  id="login-token"
                  v-model="token"
                  :type="showToken ? 'text' : 'password'"
                  placeholder="请输入密码"
                  autocomplete="current-password"
                  @blur="validateField('token')"
                />
                <button
                  type="button"
                  class="field__action"
                  :aria-label="showToken ? '隐藏 Token' : '显示 Token'"
                  @click="showToken = !showToken"
                >
                  <el-icon><component :is="showToken ? View : Hide" /></el-icon>
                </button>
              </div>
              <span v-if="errors.token" class="field__msg">{{ errors.token }}</span>
            </div>

            <div
              class="panel__row"
              v-motion
              :initial="{ opacity: 0, y: 10 }"
              :enter="{ opacity: 1, y: 0, transition: { delay: 640, duration: 500 } }"
            >
              <label class="checkbox">
                <input type="checkbox" v-model="remember" />
                <span class="checkbox__box" aria-hidden="true" />
                <span>记住此设备</span>
              </label>
              <span class="panel__hint">v1 · 本地存储</span>
            </div>

            <div
              v-motion
              :initial="{ opacity: 0, y: 10 }"
              :enter="{ opacity: 1, y: 0, transition: { delay: 720, duration: 500 } }"
            >
              <MagneticButton
                type="submit"
                variant="primary"
                :ripple="true"
                :strength="0.18"
                class="panel__submit"
                :disabled="loading"
              >
                <span v-if="!loading">进入工作台</span>
                <span v-else class="panel__loading">
                  <span class="dot" />
                  <span class="dot" />
                  <span class="dot" />
                </span>
                <el-icon v-if="!loading" class="el-icon--right"><ArrowRight /></el-icon>
              </MagneticButton>
            </div>
          </form>

          <p
            class="panel__foot"
            v-motion
            :initial="{ opacity: 0 }"
            :enter="{ opacity: 1, transition: { delay: 880, duration: 600 } }"
          >
            登录即表示同意 <a href="#">服务条款</a> 与 <a href="#">隐私政策</a>
          </p>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue";
import { useRouter, RouterLink } from "vue-router";
import { ElMessage } from "element-plus";
import { ArrowLeft, ArrowRight, View, Hide } from "@element-plus/icons-vue";

import MagneticButton from "../components/ui/MagneticButton.vue";
import brandLogo from "../assets/svg/langchain-color.svg";
import { getAuthUser, setAuthSession, clearAuthSession, verifyCredentials } from "../utils/auth";

const router = useRouter();

const username = ref(getAuthUser() || "admin");
const token = ref("");
const showToken = ref(false);
const remember = ref(true);
const loading = ref(false);
const shake = ref<"" | "username" | "token">("");

const errors = reactive<{ username: string; token: string }>({
  username: "",
  token: ""
});

const titleLines = ["Ask your", "knowledge."];
const features = [
  "Hybrid 召回 + Rerank 精排",
  "引用可追溯 · Top-K 可调",
  "BGE / OpenAI 嵌入可切换"
];

function validateField(field: "username" | "token"): boolean {
  if (field === "username") {
    errors.username = username.value.trim() ? "" : "请输入用户名";
  } else {
    errors.token = token.value.trim() ? "" : "请输入访问 Token";
  }
  return !errors[field];
}

function triggerShake(field: "username" | "token") {
  shake.value = field;
  window.setTimeout(() => {
    if (shake.value === field) shake.value = "";
  }, 420);
}

function login() {
  const okU = validateField("username");
  const okT = validateField("token");
  if (!okU) triggerShake("username");
  if (!okT) triggerShake("token");
  if (!okU || !okT) {
    ElMessage.warning("请补全登录信息");
    return;
  }

  if (!verifyCredentials(username.value, token.value)) {
    errors.token = "用户名或密码不正确";
    triggerShake("token");
    ElMessage.error("用户名或密码不正确");
    return;
  }

  loading.value = true;
  setAuthSession(username.value, token.value);
  window.setTimeout(() => {
    loading.value = false;
    router.replace((router.currentRoute.value.query.next as string) || "/app/knowledge");
  }, 480);
}
</script>

<style scoped>
/* ============================================================
   Login · Editorial split layout
   ============================================================ */

.login {
  position: relative;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg);
  overflow: hidden;
}

/* ---------- 顶部条 ---------- */
.login__topbar {
  position: relative;
  z-index: var(--z-nav);
  height: var(--nav-h);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--s-7);
  border-bottom: 1px solid var(--line-soft);
  background: rgba(10, 10, 12, 0.6);
  backdrop-filter: blur(10px);
}

.login__brand {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  color: var(--ink);
}

.login__mark {
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

.login__brand:hover .login__mark {
  border-color: var(--accent);
}

.login__brand-name {
  font-family: var(--font-display);
  font-size: var(--text-md);
  font-weight: var(--w-semibold);
  letter-spacing: var(--track-snug);
}

.login__back {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--ink-muted);
  font-size: var(--text-sm);
  transition: color var(--d-fast) var(--ease-out);
}

.login__back:hover {
  color: var(--ink);
}

/* ---------- 主体：左右分屏 ---------- */
.login__main {
  flex: 1;
  display: grid;
  grid-template-columns: 1.15fr 1fr;
  min-height: calc(100vh - var(--nav-h));
}

/* ---------- 左侧：品牌叙事 ---------- */
.login__story {
  position: relative;
  overflow: hidden;
  border-right: 1px solid var(--line-soft);
  background: var(--bg-soft);
}

.story__grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(var(--line-soft) 1px, transparent 1px),
    linear-gradient(90deg, var(--line-soft) 1px, transparent 1px);
  background-size: 56px 56px;
  mask-image: radial-gradient(ellipse 80% 60% at 30% 40%, #000 30%, transparent 80%);
  opacity: 0.6;
}

.story__glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  pointer-events: none;
}

.story__glow--a {
  top: -120px;
  left: -100px;
  width: 480px;
  height: 480px;
  background: radial-gradient(circle, var(--accent-glow), transparent 60%);
  opacity: 0.45;
}

.story__glow--b {
  bottom: -160px;
  right: -80px;
  width: 520px;
  height: 520px;
  background: radial-gradient(circle, rgba(229, 138, 110, 0.18), transparent 60%);
  opacity: 0.6;
}

.story__inner {
  position: relative;
  z-index: 1;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: var(--s-12) clamp(48px, 6vw, 96px);
  gap: var(--s-6);
  max-width: 720px;
}

.story__title {
  margin: 0;
  font-family: var(--font-display);
  font-size: clamp(56px, 6.5vw, 104px);
  line-height: 1.02;
  letter-spacing: var(--track-tight);
  color: var(--ink);
  font-weight: var(--w-semibold);
}

.story__line {
  display: block;
}

.story__line:last-child {
  color: var(--ink-muted);
  font-style: italic;
  font-weight: var(--w-regular);
}

.story__sub {
  max-width: 460px;
  color: var(--ink-soft);
  font-size: var(--text-md);
  line-height: 1.7;
}

.story__features {
  display: grid;
  gap: var(--s-3);
  margin: 0;
  padding: 0;
  list-style: none;
  color: var(--ink-soft);
  font-size: var(--text-base);
}

.story__features li {
  display: flex;
  align-items: center;
  gap: var(--s-3);
}

.story__bullet {
  width: 6px;
  height: 6px;
  background: var(--accent);
  border-radius: 1px;
  flex: 0 0 auto;
  box-shadow: 0 0 0 3px var(--accent-soft);
}

.story__ticker {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  align-self: flex-start;
  padding: 8px 14px;
  border: 1px solid var(--line);
  border-radius: var(--r-pill);
  color: var(--ink-muted);
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  letter-spacing: var(--track-wide);
  text-transform: uppercase;
  background: var(--bg-overlay);
  backdrop-filter: blur(8px);
}

.story__ticker-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--success);
  box-shadow: 0 0 0 3px rgba(74, 222, 128, 0.18);
  animation: pulse-ring 2s var(--ease-in-out) infinite;
}

/* ---------- 右侧：登录面板 ---------- */
.login__panel {
  display: grid;
  place-items: center;
  padding: var(--s-9) clamp(24px, 4vw, 64px);
  background: var(--bg);
}

.panel__inner {
  width: min(420px, 100%);
  display: flex;
  flex-direction: column;
  gap: var(--s-7);
}

.panel__head h2 {
  margin: 0 0 8px;
  font-family: var(--font-display);
  font-size: var(--text-2xl);
  font-weight: var(--w-semibold);
  letter-spacing: var(--track-snug);
  color: var(--ink);
}

.panel__head p {
  margin: 0;
  color: var(--ink-muted);
  font-size: var(--text-sm);
  line-height: 1.6;
}

.panel__form {
  display: flex;
  flex-direction: column;
  gap: var(--s-6);
}

/* ---------- 字段（下划线式） ---------- */
.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field label {
  color: var(--ink-muted);
  font-size: var(--text-xs);
  font-weight: var(--w-medium);
  letter-spacing: var(--track-extra);
  text-transform: uppercase;
}

.field__line {
  position: relative;
  display: flex;
  align-items: center;
  border-bottom: 1px solid var(--line);
  transition: border-color var(--d-base) var(--ease-out);
}

.field__line::after {
  content: "";
  position: absolute;
  left: 0;
  right: 100%;
  bottom: -1px;
  height: 1px;
  background: var(--accent);
  transition: right var(--d-slow) var(--ease-out);
  pointer-events: none;
}

.field__line:focus-within {
  border-color: transparent;
}

.field__line:focus-within::after {
  right: 0;
}

.field__line input {
  flex: 1;
  width: 100%;
  height: 44px;
  padding: 0 0 0 2px;
  background: transparent;
  border: 0;
  outline: 0;
  color: var(--ink);
  font-family: var(--font-sans);
  font-size: var(--text-md);
  letter-spacing: 0;
}

.field__line input::placeholder {
  color: var(--ink-faint);
}

.field__line--with-action input {
  padding-right: 36px;
}

.field__action {
  position: absolute;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 32px;
  height: 32px;
  display: grid;
  place-items: center;
  color: var(--ink-muted);
  border-radius: var(--r-2);
  transition:
    color var(--d-fast) var(--ease-out),
    background-color var(--d-fast) var(--ease-out);
}

.field__action:hover {
  color: var(--ink);
  background: var(--bg-soft);
}

.field__msg {
  color: var(--danger);
  font-size: var(--text-xs);
  letter-spacing: 0;
  text-transform: none;
}

.field--error .field__line {
  border-color: var(--danger);
}

.field--error .field__line::after {
  background: var(--danger);
  right: 0;
}

.field--shake {
  animation: shake 380ms var(--ease-in-out);
}

/* ---------- 复选行 ---------- */
.panel__row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: var(--text-sm);
}

.checkbox {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: var(--ink-soft);
  cursor: pointer;
  user-select: none;
}

.checkbox input {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

.checkbox__box {
  width: 16px;
  height: 16px;
  border: 1px solid var(--line-strong);
  border-radius: 3px;
  background: var(--bg-soft);
  position: relative;
  transition:
    background-color var(--d-fast) var(--ease-out),
    border-color var(--d-fast) var(--ease-out);
}

.checkbox input:checked + .checkbox__box {
  background: var(--accent);
  border-color: var(--accent);
}

.checkbox input:checked + .checkbox__box::after {
  content: "";
  position: absolute;
  left: 4px;
  top: 1px;
  width: 5px;
  height: 9px;
  border: solid var(--accent-ink);
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}

.checkbox input:focus-visible + .checkbox__box {
  box-shadow: 0 0 0 3px var(--accent-soft);
}

.panel__hint {
  color: var(--ink-faint);
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  letter-spacing: var(--track-wide);
  text-transform: uppercase;
}

/* ---------- 提交按钮 ---------- */
.panel__submit {
  width: 100%;
  height: 52px;
  font-size: var(--text-md);
  letter-spacing: var(--track-snug);
  border-radius: var(--r-2);
}

.panel__loading {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.panel__loading .dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: currentColor;
  opacity: 0.4;
  animation: blink 1.2s var(--ease-in-out) infinite;
}

.panel__loading .dot:nth-child(2) {
  animation-delay: 0.15s;
}

.panel__loading .dot:nth-child(3) {
  animation-delay: 0.3s;
}

.el-icon--right {
  transition: transform var(--d-base) var(--ease-out);
}

.panel__submit:hover .el-icon--right {
  transform: translateX(3px);
}

/* ---------- 底部协议 ---------- */
.panel__foot {
  margin: 0;
  text-align: center;
  color: var(--ink-faint);
  font-size: var(--text-xs);
  line-height: 1.7;
}

.panel__foot a {
  color: var(--ink-muted);
  border-bottom: 1px solid var(--line);
}

.panel__foot a:hover {
  color: var(--ink);
  border-color: var(--line-strong);
}

/* ============================================================
   响应式
   ============================================================ */
@media (max-width: 1023px) {
  .login__main {
    grid-template-columns: 1fr 1fr;
  }
  .story__inner {
    padding: var(--s-9) var(--s-7);
  }
  .story__title {
    font-size: clamp(40px, 5.5vw, 64px);
  }
  .login__panel {
    padding: var(--s-7) var(--s-6);
  }
}

@media (max-width: 767px) {
  .login__topbar {
    padding: 0 var(--s-4);
  }
  .login__main {
    grid-template-columns: 1fr;
    grid-template-rows: auto 1fr;
  }
  .login__story {
    min-height: 280px;
    border-right: 0;
    border-bottom: 1px solid var(--line-soft);
  }
  .story__inner {
    padding: var(--s-7) var(--s-5);
    gap: var(--s-4);
  }
  .story__title {
    font-size: clamp(36px, 11vw, 56px);
  }
  .story__sub {
    font-size: var(--text-sm);
  }
  .story__features {
    display: none;
  }
  .story__ticker {
    font-size: 10px;
  }
  .login__panel {
    padding: var(--s-7) var(--s-5);
  }
  .panel__inner {
    gap: var(--s-6);
  }
}
</style>
