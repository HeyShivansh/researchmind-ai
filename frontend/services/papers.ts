import apiClient from "./api";
import type { Paper, PaperChunk, PaginatedResponse } from "@/types";

// =============================================================================
// Papers API Service
// =============================================================================

export const papersApi = {
  /**
   * Get all papers with pagination
   */
  async getAll(
    page = 1,
    pageSize = 20,
    _search?: string
  ): Promise<PaginatedResponse<Paper>> {
    const skip = (page - 1) * pageSize;
    const params: Record<string, string | number> = {
      skip,
      limit: pageSize,
    };
    if (_search) {
      params.search = _search;
    }
    const papers = await apiClient.get<Paper[]>("/papers/", { params });
    if (!Array.isArray(papers)) {
      return { items: [], total: 0, page, page_size: pageSize, total_pages: 0 };
    }
    const total = papers.length;
    return {
      items: papers,
      total,
      page,
      page_size: pageSize,
      total_pages: Math.ceil(total / pageSize),
    };
  },

  /**
   * Get a single paper by ID
   */
  async getById(id: string): Promise<Paper> {
    return apiClient.get<Paper>(`/papers/${id}`);
  },

  /**
   * Delete a paper
   */
  async delete(id: string): Promise<{ success: boolean }> {
    await apiClient.delete<void>(`/papers/${id}`);
    return { success: true };
  },

  /**
   * Get chunks for a paper
   */
  async getChunks(paperId: string): Promise<PaperChunk[]> {
    return apiClient.get<PaperChunk[]>(`/papers/${paperId}/chunks`);
  },

  /**
   * Reindex a paper (placeholder - triggers rebuild)
   */
  async reindex(id: string): Promise<{ success: boolean }> {
    // Backend reindex not yet implemented; return success placeholder
    void id;
    return { success: true };
  },

  /**
   * Get paper metadata for download
   */
  async getMetadata(id: string): Promise<Paper> {
    return apiClient.get<Paper>(`/papers/${id}`);
  },
};

export default papersApi;
