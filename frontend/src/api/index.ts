import { http } from "./http";
import { getAuthToken } from "../utils/auth";
import type {
  ApiResponse,
  ChatHistoryResponse,
  ChatResponse,
  ChatSessionListResponse,
  DocumentIndexResponse,
  DocumentChunkItem,
  DocumentChunkListResponse,
  DocumentListResponse,
  DocumentUploadResponse,
  HealthResponse,
  MonitorOverview,
  PageData,
  ChatHistoryMessage,
  ChatSession,
  ChatSource,
  DocumentItem,
  StreamQuestionCallbacks
} from "../types";

function unwrap<T>(response: ApiResponse<T>): T {
  if (response.code !== 200) {
    throw new Error(response.msg || "Request failed");
  }
  return response.data as T;
}

export async function getHealth(): Promise<HealthResponse> {
  const { data } = await http.get<ApiResponse<HealthResponse>>("/health");
  return unwrap(data);
}

export interface DocumentListParams {
  page?: number;
  pageSize?: number;
  keyword?: string;
  parseStatus?: string;
}

export async function listDocuments(params: DocumentListParams = {}): Promise<DocumentListResponse> {
  const { data } = await http.get<ApiResponse<PageData<DocumentItem>>>("/api/document/list", {
    params: {
      page: params.page ?? 1,
      page_size: params.pageSize ?? 10,
      keyword: params.keyword || undefined,
      parse_status: params.parseStatus || undefined
    }
  });
  const page = unwrap(data);
  return { total: page.total, page: page.page, page_size: page.page_size, documents: page.items };
}

export async function uploadDocument(file: File): Promise<DocumentUploadResponse> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await http.post<ApiResponse<DocumentUploadResponse>>("/api/document/upload", form);
  return unwrap(data);
}

export async function deleteDocument(documentId: number): Promise<void> {
  await http.delete(`/api/document/${documentId}`);
}

export async function retryDocument(documentId: number): Promise<DocumentItem> {
  const { data } = await http.post<ApiResponse<DocumentItem>>(`/api/document/${documentId}/retry`);
  return unwrap(data);
}

export interface DocumentChunkListParams {
  page?: number;
  pageSize?: number;
}

export async function listDocumentChunks(
  documentId: number,
  params: DocumentChunkListParams = {}
): Promise<DocumentChunkListResponse> {
  const { data } = await http.get<ApiResponse<PageData<DocumentChunkItem>>>(
    `/api/document/${documentId}/chunks`,
    {
      params: {
        page: params.page ?? 1,
        page_size: params.pageSize ?? 10
      }
    }
  );
  const page = unwrap(data);
  return { total: page.total, page: page.page, page_size: page.page_size, chunks: page.items };
}

export function documentPreviewUrl(documentId: number): string {
  const baseURL = (http.defaults.baseURL ?? "") as string;
  return `${baseURL || ""}/api/document/${encodeURIComponent(documentId)}/file`;
}

export async function rebuildIndex(): Promise<DocumentIndexResponse> {
  const { data } = await http.post<ApiResponse<DocumentIndexResponse>>("/api/document/index");
  return unwrap(data);
}

export async function sendQuestion(sessionId: string, question: string, topK: number): Promise<ChatResponse> {
  const { data } = await http.post<ApiResponse<ChatResponse>>("/api/chat", {
    session_id: sessionId,
    question,
    top_k: topK
  });
  return unwrap(data);
}

export async function streamQuestion(
  sessionId: string,
  question: string,
  topK: number,
  callbacks: StreamQuestionCallbacks,
  signal?: AbortSignal
): Promise<void> {
  const baseURL = (http.defaults.baseURL ?? "") as string;
  const url = `${baseURL || ""}/api/chat`;
  const token = getAuthToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Accept: "text/event-stream"
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    method: "POST",
    headers,
    body: JSON.stringify({
      session_id: sessionId,
      question,
      top_k: topK,
      stream: true
    }),
    signal
  });

  if (!response.ok) {
    let message = `请求失败 (${response.status})`;
    try {
      const errorBody = await response.json();
      if (errorBody && typeof errorBody.msg === "string") {
        message = errorBody.msg;
      } else if (errorBody && typeof errorBody.detail === "string") {
        message = errorBody.detail;
      }
    } catch {
      // ignore body parse failure
    }
    callbacks.onError?.(message);
    throw new Error(message);
  }

  const reader = response.body?.getReader();
  if (!reader) {
    const message = "浏览器不支持流式响应";
    callbacks.onError?.(message);
    throw new Error(message);
  }

  const decoder = new TextDecoder("utf-8");
  let buffer = "";
  let currentEvent = "";
  let dataLines: string[] = [];

  const dispatch = async (rawData: string) => {
    if (!rawData) return;
    let payload: unknown;
    try {
      payload = JSON.parse(rawData);
    } catch {
      return;
    }
    switch (currentEvent) {
      case "metadata": {
        const data = (payload ?? {}) as { cache_hit?: boolean };
        await callbacks.onMetadata?.({ cache_hit: Boolean(data.cache_hit) });
        break;
      }
      case "sources":
        callbacks.onSources(Array.isArray(payload) ? (payload as ChatSource[]) : []);
        break;
      case "answer_delta": {
        const content =
          payload && typeof payload === "object" && "content" in payload
            ? String((payload as { content?: unknown }).content ?? "")
            : "";
        if (content) await callbacks.onDelta(content);
        break;
      }
      case "done": {
        const data = (payload ?? {}) as { answer?: string; sources?: ChatSource[] };
        await callbacks.onDone(data.answer ?? "", Array.isArray(data.sources) ? data.sources : []);
        break;
      }
      case "error": {
        const data = (payload ?? {}) as { msg?: string };
        callbacks.onError?.(data.msg ?? "流式响应出错");
        break;
      }
      default:
        break;
    }
  };

  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      let newlineIndex = buffer.indexOf("\n");
      while (newlineIndex !== -1) {
        const line = buffer.slice(0, newlineIndex).replace(/\r$/, "");
        buffer = buffer.slice(newlineIndex + 1);

        if (line === "") {
          // 空行：一条 SSE 事件结束
          await dispatch(dataLines.join("\n"));
          currentEvent = "";
          dataLines = [];
        } else if (line.startsWith("event:")) {
          currentEvent = line.slice(6).trim();
        } else if (line.startsWith("data:")) {
          dataLines.push(line.slice(5).trimStart());
        }

        newlineIndex = buffer.indexOf("\n");
      }
    }

    // 处理流结束时尚未派发的最后一段
    if (dataLines.length > 0 || currentEvent) {
      await dispatch(dataLines.join("\n"));
    }
  } catch (error) {
    if ((error as { name?: string })?.name === "AbortError") {
      return;
    }
    const message = error instanceof Error ? error.message : "流式连接中断";
    callbacks.onError?.(message);
    throw error;
  }
}

export async function getChatHistory(
  sessionId: string,
  page = 1,
  pageSize = 100
): Promise<ChatHistoryResponse> {
  const { data } = await http.get<ApiResponse<PageData<ChatHistoryMessage>>>("/api/chat/history", {
    params: { session_id: sessionId, page, page_size: pageSize }
  });
  const pageData = unwrap(data);
  return { total: pageData.total, messages: pageData.items };
}

export async function getChatSessions(page = 1, pageSize = 100): Promise<ChatSessionListResponse> {
  const { data } = await http.get<ApiResponse<PageData<ChatSession>>>("/api/chat/sessions", {
    params: { page, page_size: pageSize }
  });
  const pageData = unwrap(data);
  return { total: pageData.total, sessions: pageData.items };
}

export async function deleteChatSession(sessionId: string): Promise<void> {
  await http.delete(`/api/chat/sessions/${encodeURIComponent(sessionId)}`);
}

export async function getMonitorOverview(): Promise<MonitorOverview> {
  const { data } = await http.get<ApiResponse<MonitorOverview>>("/api/monitor/overview");
  return unwrap(data);
}
