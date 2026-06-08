export interface ApiResponse<T> {
  code: number;
  msg: string;
  data: T | null;
}

export interface PageData<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface HealthResponse {
  status: "ok" | "degraded" | string;
  service: string;
  checks: Record<string, boolean>;
}

export interface DocumentItem {
  id: number;
  file_name: string;
  file_size: number;
  parse_status: string;
  page_count: number;
  chunk_count: number;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface DocumentListResponse {
  total: number;
  documents: DocumentItem[];
}

export interface DocumentUploadResponse {
  file_id: number;
  status: string;
  page_count: number;
  chunk_count: number;
}

export interface DocumentIndexResponse {
  chunk_count: number;
  knowledge_base_version: string | null;
}

export interface ChatSource {
  document_id: number | null;
  file: string;
  page: number | null;
  title: string | null;
  chunk_index: number | null;
  retrieval_sources: string[];
  vector_score: number | null;
  bm25_score: number | null;
  hybrid_score: number | null;
  rerank_score: number | null;
}

export interface ChatResponse {
  answer: string;
  sources: ChatSource[];
}

export interface ChatHistoryMessage {
  id: number;
  session_id: string;
  role: "user" | "assistant" | string;
  content: string;
  create_time: string;
}

export interface ChatHistoryResponse {
  total: number;
  messages: ChatHistoryMessage[];
}

export interface ChatSession {
  id: number;
  session_id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
}

export interface ChatSessionListResponse {
  total: number;
  sessions: ChatSession[];
}

export interface MonitorOverview {
  document_count: number;
  chunk_count: number;
  vector_count: number;
  qa_count: number;
  cache_hit_count: number;
  cache_miss_count: number;
  cache_hit_rate: number;
  avg_response_time_ms: number;
  avg_cache_hit_response_time_ms: number;
  avg_cache_miss_response_time_ms: number;
}

export interface StreamQuestionCallbacks {
  onSources: (sources: ChatSource[]) => void;
  onDelta: (content: string) => void;
  onDone: (answer: string, sources: ChatSource[]) => void;
  onError?: (message: string) => void;
}
