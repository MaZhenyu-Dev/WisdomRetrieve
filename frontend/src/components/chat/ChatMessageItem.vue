<template>
  <article
    :class="['message-row', message.role === 'user' ? 'user' : 'assistant']"
    @click="emit('select', message)"
  >
    <div class="message-meta">
      <span>{{ message.role === "user" ? "你" : "WisdomRetrieve" }}</span>
      <div class="message-actions" @click.stop>
        <button type="button" title="复制消息" @click="emit('copy', message)">
          <el-icon><CopyDocument /></el-icon>
        </button>
        <button type="button" title="重新生成" :disabled="regenerating" @click="emit('regenerate', message)">
          <el-icon><RefreshRight /></el-icon>
        </button>
      </div>
    </div>

    <div v-if="message.role === 'assistant'" class="message-bubble markdown-body" @click="handleMarkdownClick">
      <div v-if="message.content" v-html="renderedMarkdown"></div>
      <div v-else-if="isWorkingMessage" class="thinking">
        <span></span>
        <span></span>
        <span></span>
        正在检索、重排并生成答案
      </div>
      <div v-else class="message-status">{{ message.status === "error" ? "生成出错" : "已停止生成" }}</div>
    </div>
    <div v-else class="message-bubble">{{ message.content }}</div>
  </article>
</template>

<script setup lang="ts">
import { CopyDocument, RefreshRight } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import MarkdownIt from "markdown-it";
import { computed } from "vue";

import type { ChatMessage } from "../../types";

const md = new MarkdownIt({ html: false, linkify: true, breaks: true });

md.renderer.rules.fence = (tokens, idx) => {
  const token = tokens[idx];
  const info = token.info.trim().split(/\s+/)[0] ?? "";
  const languageClass = info ? ` class="language-${md.utils.escapeHtml(info)}"` : "";
  const encodedCode = encodeURIComponent(token.content);

  return [
    '<div class="code-block">',
    `<button type="button" class="code-copy" data-code="${encodedCode}">复制</button>`,
    `<pre><code${languageClass}>${md.utils.escapeHtml(token.content)}</code></pre>`,
    "</div>"
  ].join("");
};

const props = defineProps<{
  message: ChatMessage;
  regenerating?: boolean;
}>();

const emit = defineEmits<{
  select: [message: ChatMessage];
  copy: [message: ChatMessage];
  regenerate: [message: ChatMessage];
}>();

const renderedMarkdown = computed(() => md.render(props.message.content || ""));

const isWorkingMessage = computed(() => (
  props.message.status === "pending" || props.message.status === "streaming" || !props.message.status
));

async function handleMarkdownClick(event: MouseEvent) {
  const target = event.target instanceof HTMLElement ? event.target : null;
  const button = target?.closest<HTMLButtonElement>(".code-copy");
  if (!button) return;

  const code = decodeURIComponent(button.dataset.code ?? "");
  if (!code) return;

  try {
    await navigator.clipboard.writeText(code);
    ElMessage.success("代码已复制");
  } catch {
    ElMessage.error("复制失败");
  }
}
</script>
