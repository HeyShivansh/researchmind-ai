import apiClient from "./api";
import type {
  DashboardData,
  DashboardStats,
  RecentUpload,
  RecentSearch,
  SystemServiceStatus,
  QuickAction,
} from "@/types";
import {
  Upload,
  Search,
  Library,
  BookOpen,
} from "lucide-react";

// =============================================================================
// Dashboard API Service
// =============================================================================

const MOCK_QUICK_ACTIONS: QuickAction[] = [
  {
    id: "upload",
    label: "Upload Research Paper",
    description: "Add a new PDF to your library for indexing and retrieval",
    href: "/upload",
    icon: Upload,
    color: "blue",
  },
  {
    id: "search",
    label: "Search Papers",
    description: "Search across all indexed papers with hybrid retrieval",
    href: "/search",
    icon: Search,
    color: "violet",
  },
  {
    id: "library",
    label: "Browse Library",
    description: "View and manage your complete paper collection",
    href: "/library",
    icon: Library,
    color: "emerald",
  },
  {
    id: "docs",
    label: "View Documentation",
    description: "Learn about ResearchMind AI features and architecture",
    href: "/settings",
    icon: BookOpen,
    color: "amber",
  },
];

export const dashboardApi = {
  /**
   * Fetch complete dashboard data
   */
  async getDashboardData(): Promise<DashboardData> {
    const [stats, systemStatus, recentUploads] = await Promise.all([
      this.getStats(),
      this.getSystemStatus(),
      this.getRecentUploads(),
    ]);

    return {
      stats,
      systemStatus,
      recentUploads,
      recentSearches: [],
      quickActions: MOCK_QUICK_ACTIONS,
    };
  },

  /**
   * Fetch dashboard statistics
   */
  async getStats(): Promise<DashboardStats> {
    try {
      const data = await apiClient.get<{
        total_papers: number;
        total_chunks: number;
        papers_processed: number;
        papers_processing: number;
      }>("/stats");
      return {
        total_papers: data.total_papers,
        total_chunks: data.total_chunks,
        papers_processed: data.papers_processed,
        papers_processing: data.papers_processing,
        storage_used: 0,
        recent_papers: [],
        storage_used_formatted: "0 MB",
      };
    } catch {
      return {
        total_papers: 0,
        total_chunks: 0,
        papers_processed: 0,
        papers_processing: 0,
        storage_used: 0,
        recent_papers: [],
        storage_used_formatted: "0 MB",
      };
    }
  },

  /**
   * Fetch system status
   */
  async getSystemStatus(): Promise<SystemServiceStatus[]> {
    try {
      const health = await apiClient.get<{
        status: string;
        database: string;
        database_latency: string | null;
      }>("/health");

      return [
        { name: "Backend API", status: "online", latency: "—", description: "FastAPI server" },
        { name: "PostgreSQL", status: health.database === "online" ? "online" : "offline", latency: health.database_latency || "—", description: "Primary database" },
        { name: "Qdrant", status: "online", latency: "—", description: "Vector store" },
        { name: "Embedding Provider", status: "online", latency: "—", description: "Vector embeddings" },
        { name: "Hybrid Retrieval", status: "online", latency: "—", description: "Semantic + BM25 + RRF" },
      ];
    } catch {
      return [
        { name: "Backend API", status: "offline", latency: "—", description: "FastAPI server" },
        { name: "PostgreSQL", status: "offline", latency: "—", description: "Primary database" },
        { name: "Qdrant", status: "offline", latency: "—", description: "Vector store" },
        { name: "Embedding Provider", status: "offline", latency: "—", description: "Vector embeddings" },
        { name: "Hybrid Retrieval", status: "offline", latency: "—", description: "Semantic + BM25 + RRF" },
      ];
    }
  },

  /**
   * Fetch recent uploads
   */
  async getRecentUploads(): Promise<RecentUpload[]> {
    try {
      const papers = await apiClient.get<
        Array<{
          id: string;
          title: string;
          filename?: string;
          page_count?: number;
          chunk_count?: number;
          status?: string;
          created_at: string;
        }>
      >("/papers/", { params: { skip: 0, limit: 5 } });

      return papers.map((p) => ({
        id: p.id,
        title: p.title,
        upload_date: p.created_at,
        pages: p.page_count ?? 0,
        chunks: p.chunk_count ?? 0,
        status: (p.status as "processing" | "ready" | "error") ?? "processing",
        filename: p.filename ?? "unknown.pdf",
      }));
    } catch {
      return [];
    }
  },

  /**
   * Fetch recent searches
   * Note: Backend doesn't track search history yet
   */
  async getRecentSearches(): Promise<RecentSearch[]> {
    return [];
  },
};

export default dashboardApi;
