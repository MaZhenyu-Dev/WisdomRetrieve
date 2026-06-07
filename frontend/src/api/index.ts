import { http } from "./http";
import type {
  ApiResponse,
  ChatHistoryResponse,
  ChatResponse,
  ChatSessionListResponse,
  DocumentIndexResponse,
  DocumentListResponse,
  DocumentUploadResponse,
  HealthResponse,
  MonitorOverview,
  PageData,
  ChatHistoryMessage,
  ChatSession,
  DocumentItem
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

export async function listDocuments(): Promise<DocumentListResponse> {
  const { data } = await http.get<ApiResponse<PageData<DocumentItem>>>("/api/document/list", {
    params: { page: 1, page_size: 100 }
  });
  const page = unwrap(data);
  return { total: page.total, documents: page.items };
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
