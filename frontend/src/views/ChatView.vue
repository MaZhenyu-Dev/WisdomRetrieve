<template>
  <section class="chat-workbench reveal">
    <aside class="session-panel panel">
      <div class="panel-head compact">
        <div>
          <p class="section-kicker">Sessions</p>
          <h2>历史会话</h2>
        </div>
        <el-button circle class="icon-action" :disabled="answering" title="新建会话" @click="createSession">
          <el-icon><Plus /></el-icon>
        </el-button>
      </div>

      <div class="session-list">
        <div v-if="sessionsLoading" class="list-status">正在加载会话...</div>
        <div v-else-if="sessions.length === 0" class="list-status">暂无历史会话</div>
        <template v-else>
          <div
            v-for="session in sessions"
            :key="session.session_id"
            :class="['session-entry', { active: session.session_id === activeSessionId }]"
          >
            <button
              class="session-item"
              :disabled="answering"
              @click="selectSession(session.session_id)"
            >
              <strong>{{ session.title || session.session_id }}</strong>
              <span>{{ isDraftSession(session) ? "尚未发送" : formatDate(session.updated_at) }}</span>
            </button>
            <el-button
              circle
              text
              class="session-delete"
              :disabled="answering"
              :aria-label="`删除会话：${session.title || session.session_id}`"
              @click.stop="deleteSession(session)"
            >
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
        </template>
        <button
          v-if="hasMoreSessions"
          type="button"
          class="load-more"
          :disabled="sessionsPageLoading || answering"
          @click="loadMoreSessions"
        >
          加载更多会话
        </button>
      </div>
    </aside>

    <main class="chat-panel panel">
      <div class="chat-header">
        <div>
          <p class="section-kicker">Ask with Evidence</p>
          <h2>智能问答</h2>
        </div>
        <div class="top-k-control">
          <span>Top K</span>
          <el-input-number v-model="topK" :min="1" :max="10" size="small" controls-position="right" />
        </div>
      </div>

      <div ref="messageList" class="message-list">
        <div v-if="historyLoading" class="list-status">正在加载消息...</div>
        <div v-else-if="messages.length === 0" class="empty-chat quick-start">
          <div class="quick-start-head">
            <p class="eyebrow">Quick Start</p>
            <strong>挑一个示例问题快速体验，或在下方输入自己的问题</strong>
          </div>
          <ul class="quick-questions">
            <li v-for="item in QUICK_QUESTIONS" :key="item.id">
              <button
                type="button"
                class="quick-question"
                :disabled="answering"
                @click="askQuickQuestion(item.question)"
              >
                <el-icon class="quick-question-icon"><component :is="item.icon" /></el-icon>
                <span class="quick-question-text">{{ item.question }}</span>
                <el-icon class="quick-question-arrow"><ArrowRight /></el-icon>
              </button>
            </li>
          </ul>
        </div>

        <button
          v-if="messages.length > 0 && hasMoreHistory"
          type="button"
          class="load-more"
          :disabled="historyPageLoading"
          @click="loadOlderHistory"
        >
          加载更早消息
        </button>

        <ChatMessageItem
          v-for="message in messages"
          :key="message.id"
          :message="message"
          :regenerating="answering"
          @select="selectMessageSources"
          @copy="copyMessage"
          @regenerate="regenerateMessage"
        />

      </div>

      <div class="composer">
        <el-input
          v-model="question"
          type="textarea"
          :autosize="{ minRows: 1, maxRows: 8 }"
          placeholder="输入你的问题，例如：这份制度里报销审批流程是什么？"
          :disabled="answering"
          @keydown="handleQuestionKeydown"
        />
        <button
          v-if="!answering"
          type="button"
          class="composer__send"
          :disabled="!question.trim()"
          :aria-label="'提问'"
          @click="ask"
        >
          <el-icon><Promotion /></el-icon>
        </button>
        <el-button v-else type="danger" @click="stopGeneration">
          <el-icon><CircleClose /></el-icon>
          停止生成
        </el-button>
      </div>
    </main>

    <aside class="source-panel panel">
      <div class="panel-head compact">
        <div>
          <p class="section-kicker">Citations</p>
          <h2>来源引用</h2>
        </div>
        <el-tag effect="plain">{{ activeSources.length }} 条</el-tag>
      </div>

      <div class="source-list">
        <div v-if="activeSources.length === 0" class="empty-sources">
          回答后会在这里展示命中文档、页码和检索分数。
        </div>

        <div v-for="source in activeSources" :key="sourceKey(source)" class="source-card">
          <div class="source-title">
            <strong>{{ source.file }}</strong>
            <span v-if="source.page">P{{ source.page }}</span>
          </div>
          <p v-if="source.title">{{ source.title }}</p>
          <div class="source-tags">
            <span v-if="source.chunk_index !== null">chunk {{ source.chunk_index }}</span>
            <span v-for="kind in source.retrieval_sources" :key="kind">{{ kind }}</span>
          </div>
          <dl class="score-grid">
            <div>
              <dt>Vector</dt>
              <dd>{{ score(source.vector_score) }}</dd>
            </div>
            <div>
              <dt>BM25</dt>
              <dd>{{ score(source.bm25_score) }}</dd>
            </div>
            <div>
              <dt>Hybrid</dt>
              <dd>{{ score(source.hybrid_score) }}</dd>
            </div>
            <div>
              <dt>Rerank</dt>
              <dd>{{ score(source.rerank_score) }}</dd>
            </div>
          </dl>
        </div>
      </div>
    </aside>
  </section>
</template>

<script setup lang="ts">
import {
  ArrowRight,
  ChatLineRound,
  CircleClose,
  DataAnalysis,
  Delete,
  Document,
  MagicStick,
  Plus,
  Promotion,
  QuestionFilled,
  Reading
} from "@element-plus/icons-vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { computed, nextTick, onMounted, ref } from "vue";

import { deleteChatSession, getChatHistory, getChatSessions, streamQuestion } from "../api";
import { extractErrorMessage } from "../api/http";
import ChatMessageItem from "../components/chat/ChatMessageItem.vue";
import type { ChatMessage, ChatSession, ChatSource } from "../types";

const CURRENT_SESSION_KEY = "wisdomretrieve_current_session";
const DRAFT_SESSION_TITLE = "新的知识库会话";
const SESSION_PAGE_SIZE = 30;
const HISTORY_PAGE_SIZE = 50;

interface QuickQuestion {
  id: string;
  icon: typeof Document;
  question: string;
}

const QUICK_QUESTIONS: QuickQuestion[] = [
  { id: "summary", icon: Document, question: "请用一段话总结知识库的核心内容" },
  { id: "process", icon: MagicStick, question: "知识库里涉及哪些关键流程或步骤？" },
  { id: "points", icon: ChatLineRound, question: "有哪些需要特别注意的条款或风险点？" },
  { id: "terms", icon: Reading, question: "请列出其中出现的重要术语与定义" },
  { id: "qa", icon: QuestionFilled, question: "这份文档中提到了哪些常见问题与解答？" },
  { id: "topics", icon: DataAnalysis, question: "根据知识库内容，给出三个最常被检索的主题" }
];

const sessions = ref<ChatSession[]>([]);
const activeSessionId = ref("");
const messages = ref<ChatMessage[]>([]);
const selectedSourceMessageId = ref<number | null>(null);
const question = ref("");
const answering = ref(false);
const streaming = ref(false);
const sessionsLoading = ref(false);
const sessionsPageLoading = ref(false);
const historyLoading = ref(false);
const historyPageLoading = ref(false);
const topK = ref(5);
const messageList = ref<HTMLElement | null>(null);
let streamAbortController: AbortController | null = null;
let generationStopped = false;
const sessionsPage = ref(1);
const sessionsTotal = ref(0);
const historyPage = ref(1);
const historyTotal = ref(0);

const activeSources = computed(() => {
  const selectedMessage = messages.value.find((message) => message.id === selectedSourceMessageId.value);
  if (selectedMessage?.role === "assistant") {
    return selectedMessage.sources ?? [];
  }
  const latestAssistant = [...messages.value].reverse().find((message) => message.role === "assistant");
  return latestAssistant?.sources ?? [];
});

const hasMoreSessions = computed(() => sessions.value.filter((session) => !isDraftSession(session)).length < sessionsTotal.value);
const hasMoreHistory = computed(() => historyPage.value > 1);

async function loadSessions(reloadHistory = true) {
  sessionsLoading.value = true;
  try {
    const data = await getChatSessions(1, SESSION_PAGE_SIZE);
    sessionsPage.value = 1;
    sessionsTotal.value = data.total;
    const draft = sessions.value.find((session) => isDraftSession(session));
    const serverSessions = data.sessions;
    sessions.value = draft && !serverSessions.some((session) => session.session_id === draft.session_id)
      ? [draft, ...serverSessions]
      : serverSessions;

    if (activeSessionId.value && !sessions.value.some((session) => session.session_id === activeSessionId.value)) {
      activeSessionId.value = "";
    }
    if (!activeSessionId.value) {
      createSession();
    } else {
      localStorage.setItem(CURRENT_SESSION_KEY, activeSessionId.value);
      if (!reloadHistory) {
        return;
      }
      if (isActiveDraftSession()) {
        messages.value = [];
        selectedSourceMessageId.value = null;
      } else {
        await loadHistory();
      }
    }
  } catch (error) {
    ElMessage.error(extractErrorMessage(error));
    if (!activeSessionId.value) createSession();
  } finally {
    sessionsLoading.value = false;
  }
}

async function loadMoreSessions() {
  if (sessionsPageLoading.value || !hasMoreSessions.value) return;
  sessionsPageLoading.value = true;
  try {
    const nextPage = sessionsPage.value + 1;
    const data = await getChatSessions(nextPage, SESSION_PAGE_SIZE);
    sessionsPage.value = nextPage;
    sessionsTotal.value = data.total;
    const existingIds = new Set(sessions.value.map((session) => session.session_id));
    sessions.value = [
      ...sessions.value,
      ...data.sessions.filter((session) => !existingIds.has(session.session_id))
    ];
  } catch (error) {
    ElMessage.error(extractErrorMessage(error));
  } finally {
    sessionsPageLoading.value = false;
  }
}

function createSession() {
  const existingDraft = sessions.value.find((session) => isDraftSession(session));
  if (existingDraft) {
    activeSessionId.value = existingDraft.session_id;
    localStorage.setItem(CURRENT_SESSION_KEY, existingDraft.session_id);
    messages.value = [];
    selectedSourceMessageId.value = null;
    return;
  }

  const sessionId = `session-${Date.now().toString(36)}`;
  activeSessionId.value = sessionId;
  localStorage.setItem(CURRENT_SESSION_KEY, sessionId);
  sessions.value = [
    {
      id: 0,
      session_id: sessionId,
      title: DRAFT_SESSION_TITLE,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    },
    ...sessions.value
  ];
  messages.value = [];
  selectedSourceMessageId.value = null;
}

async function selectSession(sessionId: string) {
  if (answering.value) return;
  activeSessionId.value = sessionId;
  localStorage.setItem(CURRENT_SESSION_KEY, sessionId);
  selectedSourceMessageId.value = null;
  if (isActiveDraftSession()) {
    messages.value = [];
    return;
  }
  await loadHistory();
}

async function loadHistory() {
  if (!activeSessionId.value) return;
  historyLoading.value = true;
  try {
    const firstPage = await getChatHistory(activeSessionId.value, 1, HISTORY_PAGE_SIZE);
    historyTotal.value = firstPage.total;
    const latestPage = Math.max(1, Math.ceil(firstPage.total / HISTORY_PAGE_SIZE));
    const data = latestPage === 1
      ? firstPage
      : await getChatHistory(activeSessionId.value, latestPage, HISTORY_PAGE_SIZE);
    historyPage.value = latestPage;
    historyTotal.value = data.total;
    messages.value = data.messages.map(markDoneMessage);
    selectedSourceMessageId.value = latestAssistantId(messages.value);
    await scrollToBottom();
  } catch (error) {
    ElMessage.error(extractErrorMessage(error));
  } finally {
    historyLoading.value = false;
  }
}

async function loadOlderHistory() {
  if (!activeSessionId.value || historyPageLoading.value || !hasMoreHistory.value) return;

  const list = messageList.value;
  const previousHeight = list?.scrollHeight ?? 0;
  historyPageLoading.value = true;
  try {
    const previousPage = historyPage.value - 1;
    const data = await getChatHistory(activeSessionId.value, previousPage, HISTORY_PAGE_SIZE);
    historyPage.value = previousPage;
    historyTotal.value = data.total;
    const existingIds = new Set(messages.value.map((message) => message.id));
    messages.value = [
      ...data.messages.map(markDoneMessage).filter((message) => !existingIds.has(message.id)),
      ...messages.value
    ];
    await nextTick();
    if (list) {
      list.scrollTop = list.scrollHeight - previousHeight + list.scrollTop;
    }
  } catch (error) {
    ElMessage.error(extractErrorMessage(error));
  } finally {
    historyPageLoading.value = false;
  }
}

async function ask() {
  if (answering.value) return;
  const content = question.value.trim();
  if (!content) {
    ElMessage.warning("请输入问题");
    return;
  }
  if (!activeSessionId.value) createSession();

  const localId = Date.now();
  const requestSessionId = activeSessionId.value;
  const now = new Date().toISOString();
  const assistantId = localId + 1;
  messages.value.push({
    id: localId,
    session_id: requestSessionId,
    role: "user",
    content,
    sources: [],
    status: "done",
    create_time: now
  });
  messages.value.push({
    id: assistantId,
    session_id: requestSessionId,
    role: "assistant",
    content: "",
    sources: [],
    status: "pending",
    create_time: now
  });
  selectedSourceMessageId.value = assistantId;
  question.value = "";
  answering.value = true;
  streaming.value = true;
  await scrollToBottom();

  const controller = new AbortController();
  streamAbortController = controller;
  generationStopped = false;
  let cacheHit = false;
  let cachedAnswer = "";
  let completed = false;
  let failed = false;

  const patchAssistant = (patch: Partial<ChatMessage>): void => {
    const index = messages.value.findIndex((message) => message.id === assistantId);
    if (index === -1) return;
    const next = messages.value.slice();
    next[index] = { ...next[index], ...patch };
    messages.value = next;
  };

  const appendDelta = (chunk: string): void => {
    const index = messages.value.findIndex((message) => message.id === assistantId);
    if (index === -1) return;
    const next = messages.value.slice();
    next[index] = {
      ...next[index],
      content: next[index].content + chunk,
      status: "streaming"
    };
    messages.value = next;
  };

  const setAssistantSources = (incoming: ChatSource[]): void => {
    patchAssistant({ sources: incoming });
    selectedSourceMessageId.value = assistantId;
  };

  const finalizeAssistant = (answer: string, incomingSources?: ChatSource[]): void => {
    if (answer) {
      patchAssistant({ content: answer, status: "done", sources: incomingSources });
    } else {
      patchAssistant({ status: "done", sources: incomingSources });
    }
    completed = true;
  };

  const typeCachedAnswer = async (answer: string): Promise<void> => {
    patchAssistant({ content: "", status: "streaming" });
    for (const chunk of typewriterChunks(answer)) {
      if (controller.signal.aborted) break;
      appendDelta(chunk);
      await scrollToBottom();
      await sleep(18);
    }
  };

  try {
    await streamQuestion(
      requestSessionId,
      content,
      topK.value,
      {
        onMetadata: (metadata) => {
          cacheHit = metadata.cache_hit === true;
          patchAssistant({ status: cacheHit ? "pending" : "streaming" });
        },
        onSources: (incoming) => {
          setAssistantSources(incoming);
        },
        onDelta: (chunk) => {
          streaming.value = false;
          if (cacheHit) {
            cachedAnswer += chunk;
          } else {
            appendDelta(chunk);
          }
          void scrollToBottom();
        },
        onDone: async (answer, incomingSources) => {
          streaming.value = false;
          const finalAnswer = answer || cachedAnswer;
          if (incomingSources.length > 0) {
            setAssistantSources(incomingSources);
          }
          if (cacheHit && finalAnswer) {
            await typeCachedAnswer(finalAnswer);
            if (controller.signal.aborted) return;
          }
          finalizeAssistant(finalAnswer, incomingSources);
        },
        onError: (message) => {
          streaming.value = false;
          failed = true;
          patchAssistant({ status: "error" });
          ElMessage.error(message);
        }
      },
      controller.signal
    );
    if (!generationStopped && !failed) {
      await loadSessions(false);
    }
  } catch (error) {
    if ((error as { name?: string })?.name !== "AbortError") {
      patchAssistant({ status: "error" });
      ElMessage.error(extractErrorMessage(error));
    }
  } finally {
    if (generationStopped && !completed) {
      patchAssistant({ status: "stopped" });
    }
    answering.value = false;
    streaming.value = false;
    streamAbortController = null;
    generationStopped = false;
    await scrollToBottom();
  }
}

function stopGeneration() {
  if (streamAbortController) {
    generationStopped = true;
    streamAbortController.abort();
  }
}

function askQuickQuestion(text: string) {
  if (answering.value) return;
  question.value = text;
  void ask();
}

async function copyMessage(message: ChatMessage) {
  if (!message.content) return;
  try {
    await navigator.clipboard.writeText(message.content);
    ElMessage.success("消息已复制");
  } catch {
    ElMessage.error("复制失败");
  }
}

async function regenerateMessage(message: ChatMessage) {
  if (answering.value) return;
  const prompt = message.role === "user"
    ? message.content
    : previousUserQuestion(message.id);
  if (!prompt) {
    ElMessage.warning("未找到可重新生成的问题");
    return;
  }
  question.value = prompt;
  await ask();
}

async function deleteSession(session: ChatSession) {
  if (isDraftSession(session)) {
    removeLocalSession(session.session_id);
    return;
  }

  try {
    await ElMessageBox.confirm(
      "删除后该会话的历史消息和问答日志会一并移除，确认继续？",
      "删除会话",
      {
        type: "warning",
        confirmButtonText: "删除",
        cancelButtonText: "取消"
      }
    );
    await deleteChatSession(session.session_id);
    ElMessage.success("会话已删除");
    removeLocalSession(session.session_id);
    await loadSessions(false);
  } catch (error) {
    if (error !== "cancel" && error !== "close") {
      ElMessage.error(extractErrorMessage(error));
    }
  }
}

function removeLocalSession(sessionId: string) {
  const wasActive = activeSessionId.value === sessionId;
  sessions.value = sessions.value.filter((session) => session.session_id !== sessionId);
  if (!wasActive) return;

  localStorage.removeItem(CURRENT_SESSION_KEY);
  messages.value = [];
  selectedSourceMessageId.value = null;
  activeSessionId.value = "";
  createSession();
}

function handleQuestionKeydown(event: KeyboardEvent) {
  if (event.key !== "Enter" || event.shiftKey) return;
  event.preventDefault();
  void ask();
}

function selectMessageSources(message: ChatMessage) {
  if (message.role === "assistant") {
    selectedSourceMessageId.value = message.id;
  }
}

function latestAssistantId(items: ChatMessage[]): number | null {
  const latestAssistant = [...items].reverse().find((message) => message.role === "assistant");
  return latestAssistant?.id ?? null;
}

function previousUserQuestion(messageId: number): string {
  const index = messages.value.findIndex((message) => message.id === messageId);
  if (index <= 0) return "";
  for (let cursor = index - 1; cursor >= 0; cursor -= 1) {
    const message = messages.value[cursor];
    if (message.role === "user") return message.content;
  }
  return "";
}

function markDoneMessage(message: ChatMessage): ChatMessage {
  return {
    ...message,
    sources: message.sources ?? [],
    status: message.status ?? "done"
  };
}

function typewriterChunks(value: string): string[] {
  const chars = Array.from(value);
  const chunks: string[] = [];
  for (let index = 0; index < chars.length; index += 3) {
    chunks.push(chars.slice(index, index + 3).join(""));
  }
  return chunks;
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

function isDraftSession(session: ChatSession): boolean {
  return session.id === 0;
}

function isActiveDraftSession(): boolean {
  return sessions.value.some(
    (session) => session.session_id === activeSessionId.value && isDraftSession(session)
  );
}

function sourceKey(source: ChatSource): string {
  return `${source.document_id}-${source.page}-${source.chunk_index}-${source.file}`;
}

function score(value: number | null): string {
  return value === null ? "-" : value.toFixed(3);
}

function formatDate(value: string): string {
  return new Date(value).toLocaleString("zh-CN", { hour12: false });
}

async function scrollToBottom() {
  await nextTick();
  if (messageList.value) {
    messageList.value.scrollTop = messageList.value.scrollHeight;
  }
}

onMounted(loadSessions);
</script>
