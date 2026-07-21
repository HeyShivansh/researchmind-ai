// =============================================================================
// Core Domain Types
// =============================================================================

export interface Paper {
  id: string;
  title: string;
  authors?: string[];
  abstract?: string;
  subject?: string;
  keywords?: string[];
  filename?: string;
  file_size?: number;
  page_count?: number;
  chunk_count?: number;
  created_at: string;
  updated_at?: string;
  status?: PaperStatus;
}

export type PaperStatus = "processing" | "ready" | "error";

export interface PaperChunk {
  id: string;
  paper_id: string;
  text: string;
  page_number: number;
  chunk_index: number;
  char_count?: number;
  created_at?: string;
}

export interface RetrievedChunk {
  chunk_id: string;
  paper_id: string;
  text: string;
  page_number: number;
  chunk_index: number;
  score: number;
  paper_title?: string;
}

export interface PaperUploadResponse {
  id: string;
  title: string;
  filename: string;
  status: PaperStatus;
  message: string;
}

// =============================================================================
// Dashboard Types
// =============================================================================

export interface DashboardStats {
  total_papers: number;
  total_chunks: number;
  storage_used: number;
  papers_processed: number;
  papers_processing: number;
  recent_papers: Paper[];
  storage_used_formatted: string;
}

// =============================================================================
// Search Types
// =============================================================================

export type SearchMode = "semantic" | "keyword" | "hybrid";

export type SearchSource = "semantic" | "keyword" | "hybrid";

export type SortBy = "relevance" | "newest" | "oldest";

export interface SearchFilters {
  mode: SearchMode;
  top_k: number;
  threshold: number;
  year?: number;
  sort_by: SortBy;
}

export const DEFAULT_SEARCH_FILTERS: SearchFilters = {
  mode: "hybrid",
  top_k: 10,
  threshold: 0.0,
  sort_by: "relevance",
};

export interface SearchRequest {
  query: string;
  filters: SearchFilters;
}

export interface SearchQuery {
  q: string;
  top_k?: number;
  mode?: SearchMode;
}

export interface SearchResult {
  chunk_id: string;
  paper_id: string;
  paper_title: string;
  text: string;
  page_number: number;
  chunk_index: number;
  score: number;
  source: SearchSource;
  authors?: string[];
  year?: number;
  keywords?: string[];
}

export interface SearchResults {
  results: RetrievedChunk[];
  query: string;
  total_results: number;
  mode: string;
}

export interface SearchResponse {
  results: SearchResult[];
  total_results: number;
  query: string;
  filters: SearchFilters;
  took_ms: number;
}

export interface SearchHistoryItem {
  id: string;
  query: string;
  mode: SearchMode;
  timestamp: string;
  result_count: number;
}

// =============================================================================
// API Response Types
// =============================================================================

export interface ApiResponse<T> {
  data: T;
  message?: string;
}

export interface ApiError {
  detail: string;
  status_code: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// =============================================================================
// Dashboard Types
// =============================================================================

export type SystemService =
  | "Backend API"
  | "PostgreSQL"
  | "Qdrant"
  | "Embedding Provider"
  | "Hybrid Retrieval";

export type ServiceStatus = "online" | "offline" | "loading";

export interface SystemServiceStatus {
  name: SystemService;
  status: ServiceStatus;
  latency?: string;
  description?: string;
}

export interface RecentUpload {
  id: string;
  title: string;
  upload_date: string;
  pages: number;
  chunks: number;
  status: "processing" | "ready" | "error";
  filename: string;
}

export interface RecentSearch {
  id: string;
  query: string;
  mode: "semantic" | "keyword" | "hybrid";
  timestamp: string;
  result_count: number;
}

export interface QuickAction {
  id: string;
  label: string;
  description: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
}

export interface DashboardData {
  stats: DashboardStats;
  systemStatus: SystemServiceStatus[];
  recentUploads: RecentUpload[];
  recentSearches: RecentSearch[];
  quickActions: QuickAction[];
}

// =============================================================================
// Viewer Types
// =============================================================================

export interface ViewerPaper {
  id: string;
  title: string;
  authors: string[];
  year: number;
  doi?: string;
  abstract?: string;
  subject?: string;
  keywords: string[];
  page_count: number;
  chunk_count: number;
  embedding_model: string;
  filename: string;
  file_size: number;
  upload_date: string;
  status: PaperStatus;
  pdf_url?: string;
}

export interface ViewerChunk {
  id: string;
  paper_id: string;
  text: string;
  page_number: number;
  chunk_index: number;
  score: number;
  source: SearchSource;
}

export interface HighlightRegion {
  chunk_id: string;
  page_number: number;
  bounds: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  color: string;
}

export interface PDFState {
  currentPage: number;
  numPages: number;
  scale: number;
  rotation: number;
}

export interface ViewerSettings {
  sidebarOpen: boolean;
  showHighlights: boolean;
  currentChunkId: string | null;
}

export interface ViewerData {
  paper: ViewerPaper;
  chunks: ViewerChunk[];
  highlights: HighlightRegion[];
}

// =============================================================================
// Auth Types
// =============================================================================

export interface UserProfile {
  id: string;
  email: string;
  username: string;
  created_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  username: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: UserProfile;
}

export interface AuthState {
  user: UserProfile | null;
  accessToken: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
}

// =============================================================================
// UI State Types
// =============================================================================

export interface Breadcrumb {
  label: string;
  href?: string;
}

export interface NavItem {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: number;
}
