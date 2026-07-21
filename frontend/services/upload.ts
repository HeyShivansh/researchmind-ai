import apiClient from "./api";
import type { PaperUploadResponse } from "@/types";

// =============================================================================
// Upload API Service
// =============================================================================

export const uploadApi = {
  /**
   * Upload a PDF file
   */
  async upload(
    file: File,
    title?: string,
    onProgress?: (progress: number) => void
  ): Promise<PaperUploadResponse> {
    const formData = new FormData();
    formData.append("file", file);
    if (title) formData.append("title", title);

    const response = await apiClient.uploadFile<{
      id: string;
      title: string;
      filename?: string | null;
      status?: string;
    }>("/papers/upload", formData, onProgress);

    return {
      id: response.id,
      title: response.title,
      filename: response.filename ?? file.name,
      status: (response.status as "processing" | "ready" | "error") ?? "processing",
      message: `Paper "${response.title}" uploaded successfully`,
    };
  },
};

export default uploadApi;
