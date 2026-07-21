import apiClient from "./api";
import type { ViewerData, ViewerPaper, ViewerChunk, HighlightRegion } from "@/types";

// =============================================================================
// Viewer API Service
// =============================================================================

function mapPaperToViewerPaper(
  paper: {
    id: string;
    title: string;
    abstract?: string | null;
    author?: string | null;
    subject?: string | null;
    filename?: string | null;
    file_size?: number | null;
    page_count?: number | null;
    chunk_count?: number | null;
    status?: string;
    created_at: string;
    pdf_path?: string;
  },
  baseUrl: string
): ViewerPaper {
  return {
    id: paper.id,
    title: paper.title,
    authors: paper.author ? [paper.author] : [],
    year: new Date(paper.created_at).getFullYear(),
    doi: undefined,
    abstract: paper.abstract ?? undefined,
    subject: paper.subject ?? undefined,
    keywords: [],
    page_count: paper.page_count ?? 0,
    chunk_count: paper.chunk_count ?? 0,
    embedding_model: "default",
    filename: paper.filename ?? "unknown.pdf",
    file_size: paper.file_size ?? 0,
    upload_date: paper.created_at,
    status: (paper.status as "processing" | "ready" | "error") ?? "processing",
    pdf_url: `${baseUrl}/papers/${paper.id}/file`,
  };
}

export const viewerApi = {
  /**
   * Fetch paper data with chunks and highlights
   */
  async getViewerData(paperId: string): Promise<ViewerData> {
    const [paper, chunks] = await Promise.all([
      apiClient.get<{
        id: string;
        title: string;
        abstract?: string | null;
        author?: string | null;
        subject?: string | null;
        filename?: string | null;
        file_size?: number | null;
        page_count?: number | null;
        chunk_count?: number | null;
        status?: string;
        created_at: string;
        pdf_path?: string;
      }>(`/papers/${paperId}`),
      apiClient.get<
        Array<{
          id: string;
          paper_id: string;
          text: string;
          page_number: number;
          chunk_index: number;
          char_count?: number;
          created_at?: string;
        }>
      >(`/papers/${paperId}/chunks`),
    ]);

    const baseUrl = apiClient.baseURL;

    const viewerPaper = mapPaperToViewerPaper(paper, baseUrl);

    const viewerChunks: ViewerChunk[] = chunks.map((c) => ({
      id: c.id,
      paper_id: c.paper_id,
      text: c.text,
      page_number: c.page_number,
      chunk_index: c.chunk_index,
      score: 0,
      source: "semantic" as const,
    }));

    // Highlights are not supported by the backend yet
    const highlights: HighlightRegion[] = [];

    return {
      paper: viewerPaper,
      chunks: viewerChunks,
      highlights,
    };
  },

  /**
   * Get PDF URL for a paper
   */
  async getPdfUrl(paperId: string): Promise<string> {
    return `${apiClient.baseURL}/papers/${paperId}/file`;
  },
};

export default viewerApi;
