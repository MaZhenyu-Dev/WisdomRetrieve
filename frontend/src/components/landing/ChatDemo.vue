<template>
  <section id="demo" ref="root" :class="['demo', { ready: isInView }]">
    <header class="demo__head container-wide">
      <p class="eyebrow"><span class="eyebrow__bar" />Section 03 · Interactive Demo</p>
      <div class="demo__head-row">
        <h2 class="demo__title">
          试试看，<br />它<span class="accent">真的</span>在答。
        </h2>
        <p class="demo__intro">
          点击下列问题，观看从检索到生成的完整链路。<br />
          引用卡片可点击，会在答案中标记对应位置。
        </p>
      </div>
    </header>

    <div class="demo__stage container-wide">
      <!-- Preset questions -->
      <div class="demo__presets">
        <div class="presets__label">试一试这些问题</div>
        <div class="presets__list">
          <button
            v-for="preset in presets"
            :key="preset.id"
            class="preset"
            :disabled="busy"
            @click="ask(preset)"
          >
            <span class="preset__num">Q</span>
            <span class="preset__text">{{ preset.question }}</span>
          </button>
        </div>
      </div>

      <!-- Chat panel -->
      <div class="demo__panel">
        <div class="panel__bar">
          <span class="dot dot--r" />
          <span class="dot dot--y" />
          <span class="dot dot--g" />
          <div class="panel__title">live · ask with evidence</div>
          <div class="panel__status">
            <span class="status-dot" :class="busy ? 'is-busy' : 'is-idle'" />
            {{ busy ? "检索中" : "就绪" }}
          </div>
        </div>

        <div ref="scrollRef" class="panel__body">
          <!-- Empty state -->
          <div v-if="!messages.length" class="panel__empty">
            <svg viewBox="0 0 24 24" fill="none" width="40" height="40" xmlns="http://www.w3.org/2000/svg">
              <circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="1.2" opacity="0.4"/>
              <path d="M9 10a3 3 0 015 1.7c0 1.5-2 2-2 3" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
              <circle cx="12" cy="17" r="0.8" fill="currentColor"/>
            </svg>
            <p>选一个问题，或直接输入</p>
          </div>

          <!-- Messages -->
          <article
            v-for="(m, idx) in messages"
            :key="m.id"
            class="msg"
            :class="['msg--' + m.role, { 'msg--highlight': highlightedId === m.id }]"
          >
            <div class="msg__meta">
              {{ m.role === "user" ? "你" : "WisdomRetrieve" }}
            </div>

            <div v-if="m.role === 'user'" class="msg__bubble msg__bubble--user">
              {{ m.text }}
            </div>

            <div v-else class="msg__bubble msg__bubble--bot">
              <!-- sources first (appear before answer) -->
              <div v-if="m.sources && m.sources.length" class="msg__sources">
                <button
                  v-for="src in m.sources"
                  :key="src.tag"
                  class="source-chip"
                  :class="{ active: activeSource === src.tag }"
                  @click="toggleSource(src.tag)"
                >
                  <span class="source-chip__tag">[{{ src.tag }}]</span>
                  <span class="source-chip__file">{{ src.file }}</span>
                  <span class="source-chip__page">P{{ src.page }}</span>
                </button>
              </div>

              <div class="msg__answer" v-html="renderAnswer(m)" />

              <div v-if="m.sources && m.sources.length" class="msg__footer">
                <span class="footer__num">{{ m.sources.length }} 条来源</span>
                <span class="footer__sep">·</span>
                <span class="footer__time">{{ m.elapsed }}ms</span>
              </div>
            </div>
          </article>

          <!-- Thinking indicator -->
          <div v-if="thinking" class="msg msg--bot is-thinking">
            <div class="msg__meta">WisdomRetrieve</div>
            <div class="msg__bubble msg__bubble--bot">
              <div class="thinking-row">
                <span class="dot-a"></span><span class="dot-b"></span><span class="dot-c"></span>
                <span class="thinking-text">{{ thinkingText }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Composer -->
        <div class="panel__composer">
          <input
            v-model="draft"
            class="composer__input"
            :placeholder="busy ? '正在生成答案...' : '输入你的问题，回车发送'"
            :disabled="busy"
            @keydown.enter="onSubmit"
          />
          <button
            class="composer__send"
            :disabled="busy || !draft.trim()"
            @click="onSubmit"
          >
            <el-icon><Promotion /></el-icon>
          </button>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { Promotion } from "@element-plus/icons-vue";
import { nextTick, ref, watch } from "vue";

import { useReveal } from "../../composables/useReveal";

interface Source {
  tag: string;
  file: string;
  page: number;
  snippet: string;
}
type TokType = "text" | "bold" | "ref" | "nl";
interface Tok {
  type: TokType;
  content: string;
}
interface Message {
  id: number;
  role: "user" | "bot";
  text: string;
  tokens?: Tok[];
  sources?: Source[];
  elapsed?: number;
  typed?: number;
  done?: boolean;
}
interface Preset {
  id: string;
  question: string;
  sources: Source[];
  answer: string;
}

const { target: root, isInView } = useReveal<HTMLElement>({ threshold: 0.1 });

const presets: Preset[] = [
  {
    id: "travel",
    question: "差旅审批的金额上限是多少？",
    sources: [
      { tag: "1", file: "差旅报销制度 v3.pdf", page: 4, snippet: "单次差旅审批上限为 ¥8,000..." },
      { tag: "2", file: "财务手册 2025.pdf", page: 12, snippet: "超过 ¥8,000 需财务总监复核..." }
    ],
    answer:
      "根据**差旅报销制度 v3**第 4 条，单次差旅审批上限为 **¥8,000**；超出部分需 **财务总监** 复核 [1]。同时，根据财务手册 2025 第 12 页，超过 5,000 的餐饮需要单独票据 [2]。"
  },
  {
    id: "onboard",
    question: "新员工入职第一天需要做什么？",
    sources: [
      { tag: "1", file: "员工手册.pdf", page: 8, snippet: "入职第一天由 HRBP 接待..." },
      { tag: "2", file: "IT 设备申请单.pdf", page: 2, snippet: "入职前 3 天发放笔记本..." }
    ],
    answer:
      "入职第一天由 **HRBP** 接待，签署劳动合同并领取工牌 [1]。IT 设备通常提前 3 个工作日发放，包含笔记本和门禁卡 [2]。如有远程办公需求，请提前 5 天提交 **VPN 申请**。"
  },
  {
    id: "rag",
    question: "WisdomRetrieve 的检索策略是什么？",
    sources: [
      { tag: "1", file: "技术白皮书.pdf", page: 6, snippet: "我们采用四路召回策略..." }
    ],
    answer:
      "WisdomRetrieve 采用 **四路混合召回**：Vector 语义检索 + BM25 关键词 + Hybrid 融合 + Rerank 精排 [1]。系统优先命中缓存，未命中时进入完整链路，平均响应 312ms。"
  }
];

const messages = ref<Message[]>([]);
const draft = ref("");
const busy = ref(false);
const thinking = ref(false);
const thinkingText = ref("正在检索相关文档...");
const activeSource = ref<string | null>(null);
const highlightedId = ref<number | null>(null);
const scrollRef = ref<HTMLElement | null>(null);

let idSeq = 1;
const tick = () => idSeq++;

function onSubmit() {
  const text = draft.value.trim();
  if (!text || busy.value) return;
  draft.value = "";
  ask({ id: "custom", question: text, sources: [], answer: "" });
}

async function ask(preset: Preset) {
  if (busy.value) return;
  busy.value = true;
  activeSource.value = null;
  highlightedId.value = null;

  const userId = tick();
  messages.value.push({ id: userId, role: "user", text: preset.question });
  await nextTick();
  scroll();

  // thinking stage 1: retrieve
  thinking.value = true;
  thinkingText.value = "正在向 Chroma 发起向量检索...";
  await wait(700);
  thinkingText.value = "执行 BM25 关键词匹配...";
  await wait(500);
  thinkingText.value = "Hybrid 融合 + Rerank 精排...";
  await wait(600);

  if (preset.sources.length === 0) {
    // generic answer
    thinking.value = false;
    const botId = tick();
    const ans =
      "这是 WisdomRetrieve 演示版，您可以选中上面的问题来体验完整检索流程。本组件会在生产环境对接真实接口。";
    const tokens = parseAnswer(ans);
    const botMsg: Message = {
      id: botId,
      role: "bot",
      text: ans,
      tokens,
      sources: [],
      elapsed: 480,
      typed: 0,
      done: false
    };
    const idx = messages.value.length;
    messages.value.push(botMsg);
    await nextTick();
    scroll();
    for (let i = 1; i <= tokens.length; i++) {
      messages.value[idx].typed = i;
      await wait(20 + Math.random() * 22);
      if (i % 4 === 0) scroll();
    }
    messages.value[idx].done = true;
    busy.value = false;
    return;
  }

  thinking.value = false;
  const botId = tick();
  const tokens = parseAnswer(preset.answer);
  const botMsg: Message = {
    id: botId,
    role: "bot",
    text: preset.answer,
    tokens,
    sources: preset.sources,
    elapsed: 312 + Math.floor(Math.random() * 80),
    typed: 0,
    done: false
  };
  const idx = messages.value.length;
  messages.value.push(botMsg);
  await nextTick();
  scroll();

  // 逐字打字机：保留 **bold** / [ref] / \n 的结构；必须通过 reactive 数组索引赋值
  // 才能触发 v-for 重新渲染（直接改 botMsg 变量只动了原普通对象，模板看不见）。
  for (let i = 1; i <= tokens.length; i++) {
    messages.value[idx].typed = i;
    await wait(20 + Math.random() * 22);
    if (i % 4 === 0) scroll();
  }
  messages.value[idx].done = true;
  busy.value = false;
  scroll();
}

function wait(ms: number) {
  return new Promise((r) => setTimeout(r, ms));
}

function scroll() {
  if (scrollRef.value) {
    scrollRef.value.scrollTo({ top: scrollRef.value.scrollHeight, behavior: "smooth" });
  }
}

// 将答案解析为 token 流：每个字符都是独立 token（**bold** 内部也是逐字），
// 以保证逐字打字机效果；[n] 引用和换行被识别为独立 token。
function parseAnswer(text: string): Tok[] {
  const out: Tok[] = [];
  let i = 0;
  while (i < text.length) {
    if (text.slice(i, i + 2) === "**") {
      const end = text.indexOf("**", i + 2);
      if (end !== -1) {
        for (const ch of text.slice(i + 2, end)) {
          out.push({ type: "bold", content: ch });
        }
        i = end + 2;
        continue;
      }
    }
    if (text[i] === "[") {
      const end = text.indexOf("]", i);
      if (end !== -1) {
        out.push({ type: "ref", content: text.slice(i, end + 1) });
        i = end + 1;
        continue;
      }
    }
    if (text[i] === "\n") {
      out.push({ type: "nl", content: "\n" });
      i++;
      continue;
    }
    out.push({ type: "text", content: text[i] });
    i++;
  }
  return out;
}

function renderAnswer(m: Message): string {
  if (m.tokens === undefined) return escapeHtml(m.text);
  return m.tokens
    .slice(0, m.typed ?? 0)
    .map((t) => {
      if (t.type === "bold") {
        return `<strong class="ans-bold">${escapeHtml(t.content)}</strong>`;
      }
      if (t.type === "ref") {
        const n = t.content.slice(1, -1);
        return `<button class="ans-ref" data-tag="${n}" onclick="window.dispatchEvent(new CustomEvent('demo-ref', { detail: '${n}' }))">${escapeHtml(t.content)}</button>`;
      }
      if (t.type === "nl") return "<br/>";
      return escapeHtml(t.content);
    })
    .join("");
}

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function toggleSource(tag: string) {
  activeSource.value = activeSource.value === tag ? null : tag;
}

// listen for inline ref clicks
if (typeof window !== "undefined") {
  window.addEventListener("demo-ref", (e: Event) => {
    const tag = (e as CustomEvent<string>).detail;
    activeSource.value = tag;
  });
}
</script>

<style scoped>
.demo {
  padding: var(--s-13) 0;
}

.demo__head {
  margin-bottom: var(--s-9);
}
.eyebrow__bar {
  display: inline-block;
  width: 24px;
  height: 1px;
  background: var(--accent);
  margin-right: 12px;
  vertical-align: middle;
}
.demo__head-row {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: var(--s-7);
  align-items: end;
  margin-top: var(--s-5);
}
.demo__title {
  font-family: var(--font-display);
  font-size: var(--text-5xl);
  font-weight: 600;
  line-height: 1.05;
  letter-spacing: var(--track-tight);
  color: var(--ink);
  margin: 0;
}
.demo__title .accent {
  font-style: italic;
  color: var(--accent);
}
.demo__intro {
  font-size: var(--text-md);
  color: var(--ink-muted);
  line-height: 1.7;
  letter-spacing: var(--track-snug);
  max-width: 380px;
  justify-self: end;
}

.demo__stage {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: var(--s-6);
  opacity: 0;
  transform: translateY(20px);
  transition: opacity 720ms var(--ease-out) 200ms, transform 720ms var(--ease-out) 200ms;
}
.demo.ready .demo__stage {
  opacity: 1;
  transform: translateY(0);
}

/* Presets */
.demo__presets {
  display: flex;
  flex-direction: column;
  gap: var(--s-4);
}
.presets__label {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--ink-muted);
  text-transform: uppercase;
  letter-spacing: var(--track-extra);
}
.presets__list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.preset {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  text-align: left;
  padding: 12px 14px;
  border: 1px solid var(--line);
  border-radius: 4px;
  background: var(--bg-card);
  color: var(--ink-soft);
  font-size: var(--text-sm);
  cursor: pointer;
  transition: all var(--d-base) var(--ease-out);
}
.preset:hover:not(:disabled) {
  border-color: var(--accent);
  background: var(--bg-soft);
  transform: translateX(2px);
}
.preset:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.preset__num {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--accent);
  background: var(--accent-soft);
  padding: 2px 6px;
  border-radius: 2px;
  flex-shrink: 0;
  margin-top: 1px;
}
.preset__text {
  line-height: 1.5;
}

/* Panel */
.demo__panel {
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--bg-card);
  box-shadow: var(--shadow-md);
  display: flex;
  flex-direction: column;
  height: 560px;
  overflow: hidden;
}

.panel__bar {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--line);
  background: var(--bg-soft);
}
.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}
.dot--r { background: #ed6a5e; }
.dot--y { background: #f5b342; }
.dot--g { background: #62c554; }
.panel__title {
  margin-left: 12px;
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--ink-muted);
  letter-spacing: var(--track-wide);
  text-transform: uppercase;
}
.panel__status {
  margin-left: auto;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--ink-muted);
  letter-spacing: var(--track-wide);
}
.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--success);
  box-shadow: 0 0 6px var(--success);
}
.status-dot.is-busy {
  background: var(--warning);
  box-shadow: 0 0 6px var(--warning);
  animation: pulse-ring 1.4s var(--ease-out) infinite;
}

.panel__body {
  flex: 1;
  overflow-y: auto;
  padding: var(--s-5) var(--s-6);
  display: flex;
  flex-direction: column;
  gap: 16px;
  scroll-behavior: smooth;
}

.panel__empty {
  flex: 1;
  display: grid;
  place-content: center;
  text-align: center;
  color: var(--ink-muted);
  gap: 12px;
}
.panel__empty p {
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: var(--track-wide);
  text-transform: uppercase;
  color: var(--ink-muted);
}

.msg {
  max-width: 88%;
  display: flex;
  flex-direction: column;
  gap: 6px;
  animation: rise 320ms var(--ease-out) both;
}
.msg--user {
  align-self: flex-end;
}
.msg__meta {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--ink-muted);
  letter-spacing: var(--track-wide);
  text-transform: uppercase;
}
.msg--user .msg__meta { text-align: right; }

.msg__bubble {
  padding: 12px 14px;
  border: 1px solid var(--line);
  border-radius: 6px;
  font-size: var(--text-sm);
  line-height: 1.7;
}
.msg__bubble--user {
  background: var(--accent-soft);
  border-color: var(--accent);
  color: var(--ink);
}
.msg__bubble--bot {
  background: var(--bg-soft);
  color: var(--ink-soft);
}

.msg__sources {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 10px;
  padding-bottom: 10px;
  border-bottom: 1px dashed var(--line);
}
.source-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  border: 1px solid var(--line);
  border-radius: 2px;
  background: var(--bg-card);
  color: var(--ink-soft);
  font-family: var(--font-mono);
  font-size: 10px;
  cursor: pointer;
  letter-spacing: var(--track-wide);
  transition: all var(--d-base) var(--ease-out);
}
.source-chip:hover,
.source-chip.active {
  border-color: var(--accent);
  color: var(--accent-strong);
  background: var(--accent-soft);
}
.source-chip__tag {
  color: var(--accent);
  font-weight: 700;
}
.source-chip__page {
  color: var(--ink-faint);
}

.msg__answer :deep(.ans-bold) {
  color: var(--ink);
  font-weight: 600;
}
.msg__answer :deep(.ans-ref) {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 4px;
  border: 1px solid var(--accent);
  border-radius: 2px;
  background: var(--accent-soft);
  color: var(--accent-strong);
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 700;
  margin: 0 2px;
  vertical-align: middle;
  cursor: pointer;
  transition: all var(--d-base) var(--ease-out);
}
.msg__answer :deep(.ans-ref:hover) {
  background: var(--accent);
  color: var(--accent-ink);
}

.msg__footer {
  margin-top: 10px;
  padding-top: 8px;
  border-top: 1px dashed var(--line);
  display: flex;
  gap: 8px;
  align-items: center;
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--ink-faint);
  letter-spacing: var(--track-wide);
}
.footer__sep { opacity: 0.5; }

.thinking-row {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.thinking-row .dot-a,
.thinking-row .dot-b,
.thinking-row .dot-c {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--accent);
  display: inline-block;
  animation: blink 1100ms infinite both;
}
.thinking-row .dot-b { animation-delay: 160ms; }
.thinking-row .dot-c { animation-delay: 320ms; }
.thinking-text {
  margin-left: 8px;
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--ink-muted);
  letter-spacing: var(--track-wide);
}

.panel__composer {
  display: flex;
  gap: 8px;
  padding: 12px 16px;
  border-top: 1px solid var(--line);
  background: var(--bg-soft);
}
.composer__input {
  flex: 1;
  padding: 10px 14px;
  border: 1px solid var(--line);
  border-radius: 4px;
  background: var(--bg-card);
  color: var(--ink);
  font-family: var(--font-sans);
  font-size: var(--text-sm);
  outline: 0;
  transition: border-color var(--d-base) var(--ease-out);
}
.composer__input:focus {
  border-color: var(--accent);
}
.composer__input::placeholder {
  color: var(--ink-faint);
}
.composer__send {
  width: 40px;
  height: 40px;
  border: 0;
  border-radius: 4px;
  background: var(--accent);
  color: var(--accent-ink);
  display: grid;
  place-items: center;
  cursor: pointer;
  transition: all var(--d-base) var(--ease-out);
}
.composer__send:hover:not(:disabled) {
  background: var(--accent-strong);
  transform: translateY(-1px);
}
.composer__send:disabled {
  background: var(--bg-elevated);
  color: var(--ink-faint);
  cursor: not-allowed;
}

@media (max-width: 880px) {
  .demo__head-row { grid-template-columns: 1fr; align-items: start; }
  .demo__intro { justify-self: start; }
  .demo__stage {
    grid-template-columns: 1fr;
  }
}
</style>
