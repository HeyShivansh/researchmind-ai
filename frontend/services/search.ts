import apiClient from "./api";
import type {
  SearchRequest,
  SearchResponse,
  SearchResult,
  SearchHistoryItem,
} from "@/types";

// =============================================================================
// Search API Service
// =============================================================================

export const searchApi = {
  /**
   * Search papers with hybrid retrieval
   */
  async search(request: SearchRequest): Promise<SearchResponse> {
    const data = await apiClient.post<{
      results: Array<{
        chunk_id: string;
        paper_id: string;
        paper_title: string;
        text: string;
        page_number: number;
        chunk_index: number;
        score: number;
        source: string;
      }>;
      total_results: number;
      query: string;
      took_ms: number;
    }>("/search/", null, {
      params: {
        query: request.query,
        top_k: request.filters.top_k,
        mode: request.filters.mode,
      },
    });

    const results: SearchResult[] = data.results.map((r) => ({
      chunk_id: r.chunk_id,
      paper_id: r.paper_id,
      paper_title: r.paper_title,
      text: r.text,
      page_number: r.page_number,
      chunk_index: r.chunk_index,
      score: r.score,
      source: r.source as "semantic" | "keyword" | "hybrid",
    }));

    return {
      results,
      total_results: data.total_results,
      query: data.query,
      filters: request.filters,
      took_ms: data.took_ms,
    };
  },

  /**
   * Get recent search history
   * Note: Backend doesn't track search history yet
   */
  async getHistory(): Promise<SearchHistoryItem[]> {
    return [];
  },

  /**
   * Get search suggestions for autocomplete
   * Note: Backend doesn't support suggestions yet
   */
  async getSuggestions(_query: string): Promise<string[]> {
    void _query;
    return [];
  },
};

export default searchApi;
