<template>
  <section class="page-grid knowledge-page">
    <div class="panel upload-panel reveal">
      <div class="panel-head">
        <div>
          <p class="section-kicker">Knowledge Base</p>
          <h2>PDF 文档接入</h2>
        </div>
        <el-button type="primary" :loading="indexing" @click="handleRebuild">
          <el-icon><Refresh /></el-icon>
          重建索引
        </el-button>
      </div>

      <el-upload
        drag
        accept=".pdf,application/pdf"
        :disabled="uploading"
        :http-request="handleUpload"
        :show-file-list="false"
        class="pdf-upload"
      >
        <el-icon class="upload-icon"><UploadFilled /></el-icon>
        <div class="upload-title">{{ uploading ? "正在上传并解析…" : "拖拽 PDF 到这里，或点击选择文件" }}</div>
        <p class="upload-hint">上传后会自动解析、切分并写入向量库</p>
      </el-upload>

      <div v-if="lastIndex" class="index-result" aria-live="polite">
        <span>索引完成</span>
        <strong>{{ lastIndex.chunk_count }}</strong>
        <span>chunks</span>
        <code>{{ lastIndex.knowledge_base_version || "no-version" }}</code>
      </div>
    </div>

    <div class="metric-strip reveal delay-1">
      <div class="mini-metric">
        <span>文档总数</span>
        <strong>{{ totalDocuments }}</strong>
      </div>
      <div class="mini-metric">
        <span>当前页页数</span>
        <strong>{{ currentPagePages }}</strong>
      </div>
      <div class="mini-metric">
        <span>当前页 Chunks</span>
        <strong>{{ currentPageChunks }}</strong>
      </div>
      <div class="mini-metric">
        <span>当前页失败</span>
        <strong>{{ failedDocuments }}</strong>
      </div>
    </div>

    <div class="panel document-panel reveal delay-2">
      <div class="panel-head compact">
        <div>
          <p class="section-kicker">Documents</p>
          <h2>文档状态</h2>
        </div>
        <div class="document-actions">
          <el-input
            v-model="keywordDraft"
            clearable
            class="document-search"
            placeholder="搜索文件名…"
            @clear="handleSearch"
            @keyup.enter="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          <el-select v-model="parseStatus" class="status-filter" placeholder="全部状态" @change="handleFilterChange">
            <el-option label="全部状态" value="" />
            <el-option label="已解析" value="parsed" />
            <el-option label="解析中" value="parsing" />
            <el-option label="失败" value="failed" />
            <el-option label="等待中" value="pending" />
          </el-select>
          <el-button class="ghost-action" @click="handleSearch">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button class="ghost-action" :loading="loading" @click="loadDocuments">刷新</el-button>
        </div>
      </div>

      <el-table v-loading="loading" :data="documents" class="document-table" empty-text="暂无文档">
        <el-table-column prop="file_name" label="文件" min-width="260">
          <template #default="{ row }">
            <div class="file-cell">
              <strong>{{ row.file_name }}</strong>
              <span>{{ formatFileSize(row.file_size) }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="parse_status" label="状态" width="130">
          <template #default="{ row }">
            <button v-if="row.parse_status === 'failed'" class="status-button" @click="openFailureDialog(row)">
              <el-tag :type="statusType(row.parse_status)" effect="plain">
                <el-icon><WarningFilled /></el-icon>
                {{ statusLabel(row.parse_status) }}
              </el-tag>
            </button>
            <el-tag v-else :type="statusType(row.parse_status)" effect="plain">
              {{ statusLabel(row.parse_status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="page_count" label="页数" width="90" />
        <el-table-column prop="chunk_count" label="Chunks" width="100" />
        <el-table-column prop="updated_at" label="更新时间" min-width="170">
          <template #default="{ row }">{{ formatDate(row.updated_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="300" fixed="right">
          <template #default="{ row }">
            <div class="table-actions">
              <el-button text type="primary" @click="openPreview(row)">
                <el-icon><View /></el-icon>
                预览
              </el-button>
              <el-button text type="primary" :disabled="row.chunk_count <= 0" @click="openChunks(row)">
                <el-icon><Files /></el-icon>
                分块
              </el-button>
              <el-button
                v-if="row.parse_status === 'failed'"
                text
                type="warning"
                :loading="retryingId === row.id"
                @click="handleRetry(row)"
              >
                <el-icon><RefreshRight /></el-icon>
                重试
              </el-button>
              <el-button text type="danger" @click="handleDelete(row.id)">
                <el-icon><Delete /></el-icon>
                删除
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div class="table-pagination">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          background
          layout="total, sizes, prev, pager, next"
          :page-sizes="[10, 20, 50, 100]"
          :total="totalDocuments"
          @current-change="handlePageChange"
          @size-change="handlePageSizeChange"
        />
      </div>
    </div>

    <el-drawer v-model="previewVisible" class="document-drawer" size="72%">
      <template #header>
        <div class="drawer-title">
          <span>文档预览</span>
          <strong>{{ activeDocument?.file_name }}</strong>
        </div>
      </template>
      <iframe
        v-if="activeDocument"
        class="pdf-frame"
        :src="documentPreviewUrl(activeDocument.id)"
        :title="`${activeDocument.file_name} 预览`"
      ></iframe>
    </el-drawer>

    <el-drawer v-model="chunksVisible" class="document-drawer chunk-drawer" size="64%" @closed="resetChunks">
      <template #header>
        <div class="drawer-title">
          <span>解析分块</span>
          <strong>{{ activeDocument?.file_name }}</strong>
        </div>
      </template>

      <el-table v-loading="chunksLoading" :data="chunks" class="chunk-table" empty-text="暂无分块">
        <el-table-column prop="chunk_index" label="#" width="74" />
        <el-table-column prop="page_number" label="页码" width="86" />
        <el-table-column label="内容" min-width="420">
          <template #default="{ row }">
            <article class="chunk-content">
              <strong v-if="row.title">{{ row.title }}</strong>
              <p>{{ row.content }}</p>
              <code>{{ row.chroma_id }}</code>
            </article>
          </template>
        </el-table-column>
      </el-table>

      <div class="table-pagination">
        <el-pagination
          v-model:current-page="chunkPage"
          v-model:page-size="chunkPageSize"
          background
          small
          layout="total, sizes, prev, pager, next"
          :page-sizes="[10, 20, 50]"
          :total="chunkTotal"
          @current-change="loadChunks"
          @size-change="handleChunkPageSizeChange"
        />
      </div>
    </el-drawer>

    <el-dialog v-model="failureVisible" title="解析失败详情" width="560px">
      <div class="failure-detail">
        <strong>{{ failureDocument?.file_name }}</strong>
        <p>{{ failureDocument?.error_message || "后端未返回具体错误。" }}</p>
      </div>
      <template #footer>
        <el-button @click="failureVisible = false">关闭</el-button>
        <el-button
          v-if="failureDocument"
          type="warning"
          :loading="retryingId === failureDocument.id"
          @click="handleRetry(failureDocument)"
        >
          重新解析
        </el-button>
      </template>
    </el-dialog>
  </section>
</template>

<script setup lang="ts">
import {
  Delete,
  Files,
  Refresh,
  RefreshRight,
  Search,
  UploadFilled,
  View,
  WarningFilled
} from "@element-plus/icons-vue";
import { ElMessage, ElMessageBox } from "element-plus";
import type { UploadRequestOptions } from "element-plus";
import { computed, onMounted, ref } from "vue";
import { useRoute } from "vue-router";

import {
  deleteDocument,
  documentPreviewUrl,
  listDocumentChunks,
  listDocuments,
  rebuildIndex,
  retryDocument,
  uploadDocument
} from "../api";
import { extractErrorMessage } from "../api/http";
import type { DocumentChunkItem, DocumentIndexResponse, DocumentItem } from "../types";

const route = useRoute();

const loading = ref(false);
const uploading = ref(false);
const indexing = ref(false);
const retryingId = ref<number | null>(null);
const documents = ref<DocumentItem[]>([]);
const totalDocuments = ref(0);
const lastIndex = ref<DocumentIndexResponse | null>(null);

const keyword = ref(readStringQuery("keyword"));
const keywordDraft = ref(keyword.value);
const parseStatus = ref(readStringQuery("status"));
const page = ref(readNumberQuery("page", 1));
const pageSize = ref(readNumberQuery("page_size", 10));

const previewVisible = ref(false);
const chunksVisible = ref(false);
const failureVisible = ref(false);
const activeDocument = ref<DocumentItem | null>(null);
const failureDocument = ref<DocumentItem | null>(null);

const chunks = ref<DocumentChunkItem[]>([]);
const chunksLoading = ref(false);
const chunkTotal = ref(0);
const chunkPage = ref(1);
const chunkPageSize = ref(10);

const currentPagePages = computed(() => documents.value.reduce((sum, item) => sum + item.page_count, 0));
const currentPageChunks = computed(() => documents.value.reduce((sum, item) => sum + item.chunk_count, 0));
const failedDocuments = computed(() => documents.value.filter((item) => item.parse_status === "failed").length);

async function loadDocuments() {
  loading.value = true;
  try {
    const data = await listDocuments({
      page: page.value,
      pageSize: pageSize.value,
      keyword: keyword.value,
      parseStatus: parseStatus.value
    });
    documents.value = data.documents;
    totalDocuments.value = data.total;
    syncQuery();
  } catch (error) {
    ElMessage.error(extractErrorMessage(error));
  } finally {
    loading.value = false;
  }
}

async function handleSearch() {
  keyword.value = keywordDraft.value.trim();
  page.value = 1;
  await loadDocuments();
}

async function handleFilterChange() {
  page.value = 1;
  await loadDocuments();
}

async function handlePageChange() {
  await loadDocuments();
}

async function handlePageSizeChange() {
  page.value = 1;
  await loadDocuments();
}

async function handleUpload(options: UploadRequestOptions) {
  const file = options.file as File;
  if (!file.name.toLowerCase().endsWith(".pdf")) {
    ElMessage.warning("仅支持上传 PDF 文件");
    return;
  }
  uploading.value = true;
  try {
    const data = await uploadDocument(file);
    options.onSuccess(data);
    ElMessage.success(`上传成功，已生成 ${data.chunk_count} 个 chunk`);
    page.value = 1;
    await loadDocuments();
  } catch (error) {
    const message = extractErrorMessage(error);
    const uploadError = new Error(message) as Parameters<NonNullable<UploadRequestOptions["onError"]>>[0];
    options.onError(uploadError);
    ElMessage.error(message);
  } finally {
    uploading.value = false;
  }
}

async function handleDelete(documentId: number) {
  try {
    await ElMessageBox.confirm("删除后对应向量也会被移除，确认继续？", "删除文档", {
      type: "warning",
      confirmButtonText: "删除",
      cancelButtonText: "取消"
    });
    await deleteDocument(documentId);
    ElMessage.success("文档已删除");
    await loadDocuments();
  } catch (error) {
    if (error !== "cancel") ElMessage.error(extractErrorMessage(error));
  }
}

async function handleRetry(document: DocumentItem) {
  try {
    await ElMessageBox.confirm("将重新解析该 PDF，并替换它现有的分块与向量。确认继续？", "重新解析", {
      type: "warning",
      confirmButtonText: "重新解析",
      cancelButtonText: "取消"
    });
    retryingId.value = document.id;
    await retryDocument(document.id);
    ElMessage.success("文档已重新解析");
    failureVisible.value = false;
    await loadDocuments();
  } catch (error) {
    if (error !== "cancel") ElMessage.error(extractErrorMessage(error));
  } finally {
    retryingId.value = null;
  }
}

async function handleRebuild() {
  indexing.value = true;
  try {
    lastIndex.value = await rebuildIndex();
    ElMessage.success(`索引已重建：${lastIndex.value.chunk_count} chunks`);
  } catch (error) {
    ElMessage.error(extractErrorMessage(error));
  } finally {
    indexing.value = false;
  }
}

function openPreview(document: DocumentItem) {
  activeDocument.value = document;
  previewVisible.value = true;
}

async function openChunks(document: DocumentItem) {
  activeDocument.value = document;
  chunkPage.value = 1;
  chunksVisible.value = true;
  await loadChunks();
}

async function loadChunks() {
  if (!activeDocument.value) return;
  chunksLoading.value = true;
  try {
    const data = await listDocumentChunks(activeDocument.value.id, {
      page: chunkPage.value,
      pageSize: chunkPageSize.value
    });
    chunks.value = data.chunks;
    chunkTotal.value = data.total;
  } catch (error) {
    ElMessage.error(extractErrorMessage(error));
  } finally {
    chunksLoading.value = false;
  }
}

async function handleChunkPageSizeChange() {
  chunkPage.value = 1;
  await loadChunks();
}

function resetChunks() {
  chunks.value = [];
  chunkTotal.value = 0;
}

function openFailureDialog(document: DocumentItem) {
  failureDocument.value = document;
  failureVisible.value = true;
}

function statusLabel(status: string): string {
  const labels: Record<string, string> = {
    parsed: "已解析",
    parsing: "解析中",
    failed: "失败",
    pending: "等待中"
  };
  return labels[status] || status;
}

function statusType(status: string): "success" | "warning" | "danger" | "info" {
  if (status === "parsed") return "success";
  if (status === "failed") return "danger";
  if (status === "parsing") return "warning";
  return "info";
}

function formatFileSize(size: number): string {
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / 1024 / 1024).toFixed(1)} MB`;
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false
  }).format(new Date(value));
}

function syncQuery() {
  if (typeof window === "undefined") return;
  const query = new URLSearchParams();
  if (keyword.value) query.set("keyword", keyword.value);
  if (parseStatus.value) query.set("status", parseStatus.value);
  if (page.value > 1) query.set("page", String(page.value));
  if (pageSize.value !== 10) query.set("page_size", String(pageSize.value));

  const nextUrl = query.toString() ? `${route.path}?${query.toString()}` : route.path;
  window.history.replaceState(window.history.state, "", nextUrl);
}

function readStringQuery(key: string): string {
  const value = route.query[key];
  return typeof value === "string" ? value : "";
}

function readNumberQuery(key: string, fallback: number): number {
  const value = Number(route.query[key]);
  return Number.isFinite(value) && value > 0 ? value : fallback;
}

onMounted(loadDocuments);
</script>
