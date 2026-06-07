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
              @click="selectSession(session.session_id)"
            >
              <strong>{{ session.title || session.session_id }}</strong>
              <span>{{ isDraftSession(session) ? "尚未发送" : formatDate(session.updated_at) }}</span>
            </button>
            <el-tooltip content="删除会话" placement="right">
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
            </el-tooltip>
          </div>
        </template>
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
        <div v-else-if="messages.length === 0" class="empty-chat">
          <span>尚未开始提问</span>
          <strong>上传并索引文档后，在这里验证知识库答案和来源。</strong>
        </div>

        <article
          v-for="message in messages"
          :key="message.id"
          :class="['message-row', message.role === 'user' ? 'user' : 'assistant']"
        >
          <div class="message-meta">{{ message.role === "user" ? "你" : "WisdomRetrieve" }}</div>
          <div v-if="message.role === 'assistant'" class="message-bubble markdown-body" v-html="renderMarkdown(message.content)"></div>
          <div v-else class="message-bubble">{{ message.content }}</div>
        </article>

        <div v-if="answering" class="message-row assistant">
          <div class="message-meta">WisdomRetrieve</div>
          <div class="message-bubble thinking">
            <span></span>
            <span></span>
            <span></span>
            正在检索、重排并生成答案
          </div>
        </div>
      </div>

      <div class="composer">
        <el-input
          v-model="question"
          type="textarea"
          :autosize="{ minRows: 2, maxRows: 5 }"
          placeholder="输入你的问题，例如：这份制度里报销审批流程是什么？"
          @keydown="handleQuestionKeydown"
        />
        <el-button type="primary" :loading="answering" :disabled="answering || !question.trim()" @click="ask">
          <el-icon><Search /></el-icon>
          提问
        </el-button>
      </div>
    </main>

    <aside class="source-panel panel">
      <div class="panel-head compact">
        <div>
          <p class="section-kicker">Citations</p>
          <h2>来源引用</h2>
        </div>
        <el-tag effect="plain">{{ sources.length }} 条</el-tag>
      </div>

      <div class="source-list">
        <div v-if="sources.length === 0" class="empty-sources">
          回答后会在这里展示命中文档、页码和检索分数。
        </div>

        <div v-for="source in sources" :key="sourceKey(source)" class="source-card">
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
import { Delete, Plus, Search } from "@element-plus/icons-vue";
import { ElMessage, ElMessageBox } from "element-plus";
import MarkdownIt from "markdown-it";
import { nextTick, onMounted, ref } from "vue";

import { deleteChatSession, getChatHistory, getChatSessions, sendQuestion } from "../api";
import { extractErrorMessage } from "../api/http";
import type { ChatHistoryMessage, ChatSession, ChatSource } from "../types";

const CURRENT_SESSION_KEY = "wisdomretrieve_current_session";
const DRAFT_SESSION_TITLE = "新的知识库会话";
const SESSION_PAGE_SIZE = 100;
const HISTORY_PAGE_SIZE = 100;
const md = new MarkdownIt({ html: false, linkify: true, breaks: true });

const sessions = ref<ChatSession[]>([]);
const activeSessionId = ref(localStorage.getItem(CURRENT_SESSION_KEY) || "");
const messages = ref<ChatHistoryMessage[]>([]);
const sources = ref<ChatSource[]>([]);
const question = ref("");
const answering = ref(false);
const sessionsLoading = ref(false);
const historyLoading = ref(false);
const topK = ref(5);
const messageList = ref<HTMLElement | null>(null);

async function loadSessions() {
  sessionsLoading.value = true;
  try {
    const data = await getChatSessions(1, SESSION_PAGE_SIZE);
    const draft = sessions.value.find((session) => isDraftSession(session));
    const serverSessions = data.sessions;
    sessions.value = draft && !serverSessions.some((session) => session.session_id === draft.session_id)
      ? [draft, ...serverSessions]
      : serverSessions;

    if (activeSessionId.value && !sessions.value.some((session) => session.session_id === activeSessionId.value)) {
      activeSessionId.value = sessions.value[0]?.session_id || "";
    }
    if (!activeSessionId.value && sessions.value.length > 0) {
      activeSessionId.value = sessions.value[0].session_id;
    }
    if (!activeSessionId.value) {
      createSession();
    } else {
      localStorage.setItem(CURRENT_SESSION_KEY, activeSessionId.value);
      if (isActiveDraftSession()) {
        messages.value = [];
        sources.value = [];
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

function createSession() {
  const existingDraft = sessions.value.find((session) => isDraftSession(session));
  if (existingDraft) {
    activeSessionId.value = existingDraft.session_id;
    localStorage.setItem(CURRENT_SESSION_KEY, existingDraft.session_id);
    messages.value = [];
    sources.value = [];
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
  sources.value = [];
}

async function selectSession(sessionId: string) {
  activeSessionId.value = sessionId;
  localStorage.setItem(CURRENT_SESSION_KEY, sessionId);
  sources.value = [];
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
    const data = await getChatHistory(activeSessionId.value, 1, HISTORY_PAGE_SIZE);
    messages.value = data.messages;
    await scrollToBottom();
  } catch (error) {
    ElMessage.error(extractErrorMessage(error));
  } finally {
    historyLoading.value = false;
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
  messages.value.push({
    id: localId,
    session_id: activeSessionId.value,
    role: "user",
    content,
    create_time: new Date().toISOString()
  });
  question.value = "";
  answering.value = true;
  await scrollToBottom();

  try {
    const response = await sendQuestion(activeSessionId.value, content, topK.value);
    messages.value.push({
      id: localId + 1,
      session_id: activeSessionId.value,
      role: "assistant",
      content: response.answer,
      create_time: new Date().toISOString()
    });
    sources.value = response.sources;
    await loadSessions();
  } catch (error) {
    ElMessage.error(extractErrorMessage(error));
  } finally {
    answering.value = false;
    await scrollToBottom();
  }
}

async function deleteSession(session: ChatSession) {
  if (isDraftSession(session)) {
    const wasActive = activeSessionId.value === session.session_id;
    removeLocalSession(session.session_id);
    if (wasActive && activeSessionId.value && !isActiveDraftSession()) {
      await loadHistory();
    }
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
    await loadSessions();
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

  activeSessionId.value = sessions.value[0]?.session_id || "";
  if (activeSessionId.value) {
    localStorage.setItem(CURRENT_SESSION_KEY, activeSessionId.value);
  } else {
    localStorage.removeItem(CURRENT_SESSION_KEY);
    createSession();
  }
  messages.value = [];
  sources.value = [];
}

function handleQuestionKeydown(event: KeyboardEvent) {
  if (event.key !== "Enter" || event.shiftKey) return;
  event.preventDefault();
  void ask();
}

function renderMarkdown(value: string): string {
  return md.render(value || "");
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
