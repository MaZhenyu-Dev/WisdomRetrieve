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
        :http-request="handleUpload"
        :show-file-list="false"
        class="pdf-upload"
      >
        <el-icon class="upload-icon"><UploadFilled /></el-icon>
        <div class="upload-title">拖拽 PDF 到这里，或点击选择文件</div>
        <p class="upload-hint">上传后会自动解析、切分并写入向量库</p>
      </el-upload>

      <div v-if="lastIndex" class="index-result">
        <span>索引完成</span>
        <strong>{{ lastIndex.chunk_count }}</strong>
        <span>chunks</span>
        <code>{{ lastIndex.knowledge_base_version || "no-version" }}</code>
      </div>
    </div>

    <div class="metric-strip reveal delay-1">
      <div class="mini-metric">
        <span>文档</span>
        <strong>{{ totalDocuments }}</strong>
      </div>
      <div class="mini-metric">
        <span>页数</span>
        <strong>{{ totalPages }}</strong>
      </div>
      <div class="mini-metric">
        <span>Chunks</span>
        <strong>{{ totalChunks }}</strong>
      </div>
      <div class="mini-metric">
        <span>解析失败</span>
        <strong>{{ failedDocuments }}</strong>
      </div>
    </div>

    <div class="panel document-panel reveal delay-2">
      <div class="panel-head">
        <div>
          <p class="section-kicker">Documents</p>
          <h2>文档状态</h2>
        </div>
        <el-button class="ghost-action" :loading="loading" @click="loadDocuments">刷新列表</el-button>
      </div>

      <el-table v-loading="loading" :data="documents" class="document-table" empty-text="暂无文档">
        <el-table-column prop="file_name" label="文件" min-width="240">
          <template #default="{ row }">
            <div class="file-cell">
              <strong>{{ row.file_name }}</strong>
              <span>{{ formatFileSize(row.file_size) }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="parse_status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="statusType(row.parse_status)" effect="plain">
              {{ statusLabel(row.parse_status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="page_count" label="页数" width="90" />
        <el-table-column prop="chunk_count" label="Chunks" width="100" />
        <el-table-column prop="updated_at" label="更新时间" min-width="170">
          <template #default="{ row }">{{ formatDate(row.updated_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="110" fixed="right">
          <template #default="{ row }">
            <el-button text type="danger" @click="handleDelete(row.id)">
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </section>
</template>

<script setup lang="ts">
import { Delete, Refresh, UploadFilled } from "@element-plus/icons-vue";
import { ElMessage, ElMessageBox } from "element-plus";
import type { UploadRequestOptions } from "element-plus";
import { computed, onMounted, ref } from "vue";

import { deleteDocument, listDocuments, rebuildIndex, uploadDocument } from "../api";
import { extractErrorMessage } from "../api/http";
import type { DocumentIndexResponse, DocumentItem } from "../types";

const loading = ref(false);
const uploading = ref(false);
const indexing = ref(false);
const documents = ref<DocumentItem[]>([]);
const lastIndex = ref<DocumentIndexResponse | null>(null);

const totalDocuments = computed(() => documents.value.length);
const totalPages = computed(() => documents.value.reduce((sum, item) => sum + item.page_count, 0));
const totalChunks = computed(() => documents.value.reduce((sum, item) => sum + item.chunk_count, 0));
const failedDocuments = computed(() => documents.value.filter((item) => item.parse_status === "failed").length);

async function loadDocuments() {
  loading.value = true;
  try {
    const data = await listDocuments();
    documents.value = data.documents;
  } catch (error) {
    ElMessage.error(extractErrorMessage(error));
  } finally {
    loading.value = false;
  }
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
    await loadDocuments();
  } catch (error) {
    ElMessage.error(extractErrorMessage(error));
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
  return new Date(value).toLocaleString("zh-CN", { hour12: false });
}

onMounted(loadDocuments);
</script>
