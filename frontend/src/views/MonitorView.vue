<template>
  <section class="monitor-page">
    <div class="panel monitor-hero reveal">
      <div>
        <p class="section-kicker">Runtime Overview</p>
        <h2>系统运行概览</h2>
      </div>
      <el-button class="ghost-action" :loading="loading" @click="loadOverview">刷新数据</el-button>
    </div>

    <div class="metric-grid reveal delay-1">
      <article v-for="metric in metrics" :key="metric.label" class="metric-card">
        <span>{{ metric.label }}</span>
        <strong>{{ metric.value }}</strong>
        <p>{{ metric.caption }}</p>
      </article>
    </div>

    <div class="panel qa-panel reveal delay-2">
      <div class="panel-head">
        <div>
          <p class="section-kicker">QA Performance</p>
          <h2>问答性能</h2>
        </div>
        <el-tag effect="plain">{{ overview?.qa_count || 0 }} 次问答</el-tag>
      </div>

      <div class="performance-grid">
        <div class="rate-block">
          <span>缓存命中率</span>
          <strong>{{ cacheRate }}</strong>
          <el-progress :percentage="cacheRatePercent" :stroke-width="10" :show-text="false" />
        </div>
        <div class="latency-row">
          <div>
            <span>平均响应</span>
            <strong>{{ overview?.avg_response_time_ms || 0 }}ms</strong>
          </div>
          <div>
            <span>命中缓存</span>
            <strong>{{ overview?.avg_cache_hit_response_time_ms || 0 }}ms</strong>
          </div>
          <div>
            <span>未命中缓存</span>
            <strong>{{ overview?.avg_cache_miss_response_time_ms || 0 }}ms</strong>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ElMessage } from "element-plus";
import { computed, onMounted, ref } from "vue";

import { getMonitorOverview } from "../api";
import { extractErrorMessage } from "../api/http";
import type { MonitorOverview } from "../types";

const loading = ref(false);
const overview = ref<MonitorOverview | null>(null);

const metrics = computed(() => [
  {
    label: "文档数量",
    value: overview.value?.document_count || 0,
    caption: "已接入知识库的 PDF"
  },
  {
    label: "Chunk 数量",
    value: overview.value?.chunk_count || 0,
    caption: "可检索文本切片"
  },
  {
    label: "向量数量",
    value: overview.value?.vector_count || 0,
    caption: "Chroma 向量记录"
  },
  {
    label: "问答次数",
    value: overview.value?.qa_count || 0,
    caption: "累计 QA 请求"
  }
]);

const cacheRatePercent = computed(() => Math.round((overview.value?.cache_hit_rate || 0) * 100));
const cacheRate = computed(() => `${cacheRatePercent.value}%`);

async function loadOverview() {
  loading.value = true;
  try {
    overview.value = await getMonitorOverview();
  } catch (error) {
    ElMessage.error(extractErrorMessage(error));
  } finally {
    loading.value = false;
  }
}

onMounted(loadOverview);
</script>
