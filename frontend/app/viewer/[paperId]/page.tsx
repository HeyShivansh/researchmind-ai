"use client";

import { use, useState, useCallback, useEffect, useRef } from "react";
import dynamic from "next/dynamic";
import { useQuery } from "@tanstack/react-query";
import { viewerApi } from "@/services/viewer";
import {
  ViewerHeader,
  ChunkSidebar,
} from "@/features/viewer";

// Lazy-load the PDF container (heavy component with pdf.js)
const PDFContainer = dynamic(
  () => import("@/features/viewer/PDFContainer"),
  {
    ssr: false,
    loading: () => (
      <div className="flex-1 flex items-center justify-center bg-muted/10">
        <div className="flex flex-col items-center gap-4">
          <div className="h-[600px] w-[450px] rounded-lg bg-muted/30 animate-pulse" />
        </div>
      </div>
    ),
  }
);
import { Skeleton } from "@/components/ui/skeleton";
import { AlertCircle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useIsMobile } from "@/hooks";
import type { PDFState } from "@/types";

// =============================================================================
// Viewer Page (Dynamic Route: /viewer/[paperId])
// =============================================================================

interface ViewerPageProps {
  params: Promise<{ paperId: string }>;
}

export default function ViewerPage({ params }: ViewerPageProps) {
  const { paperId } = use(params);
  const isMobile = useIsMobile();
  const pdfContainerRef = useRef<HTMLDivElement>(null);

  // State
  const [sidebarOpen, setSidebarOpen] = useState(!isMobile);
  const [selectedChunkId, setSelectedChunkId] = useState<string | null>(null);
  const [pdfUrl, setPdfUrl] = useState("");
  const [pdfState, setPDFState] = useState<PDFState>({
    currentPage: 1,
    numPages: 1,
    scale: 1,
    rotation: 0,
  });
  // Responsive: auto-close sidebar on mobile
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (isMobile) setSidebarOpen(false);
  }, [isMobile]);

  // Fetch viewer data
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["viewer", paperId],
    queryFn: () => viewerApi.getViewerData(paperId),
  });

  // Fetch PDF URL
  useEffect(() => {
    viewerApi.getPdfUrl(paperId).then(setPdfUrl);
  }, [paperId]);

  // Handle chunk selection - navigate to the chunk's page
  const handleSelectChunk = useCallback(
    (chunkId: string) => {
      setSelectedChunkId(chunkId);
      const chunk = data?.chunks.find((c) => c.id === chunkId);
      if (chunk) {
        setPDFState((prev) => ({ ...prev, currentPage: chunk.page_number }));
      }
    },
    [data?.chunks]
  );

  // Handle page change from PDF viewer - clear selected chunk if navigating away
  const handlePageChange = useCallback(
    (page: number) => {
      if (selectedChunkId && data) {
        const chunk = data.chunks.find((c) => c.id === selectedChunkId);
        if (chunk && chunk.page_number !== page) {
          setSelectedChunkId(null);
        }
      }
    },
    [selectedChunkId, data]
  );

  // Handle PDF search
  // TODO: Implement PDF text search when react-pdf text layer is enabled
  const handleSearch = useCallback((_query: string) => {
    void _query;
  }, []);

  // Global keyboard shortcuts
  useEffect(() => {
    const handler = (e: globalThis.KeyboardEvent) => {
      // Escape to close sidebar on mobile
      if (e.key === "Escape" && isMobile && sidebarOpen) {
        setSidebarOpen(false);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [isMobile, sidebarOpen]);

  // Error state
  if (isError) {
    return (
      <div className="flex flex-col items-center justify-center h-[80vh] text-center">
        <div className="mb-4 flex size-16 items-center justify-center rounded-full bg-destructive/10">
          <AlertCircle className="size-8 text-destructive" />
        </div>
        <h2 className="text-lg font-semibold">Failed to load paper</h2>
        <p className="mt-1 text-sm text-muted-foreground max-w-sm">
          {error instanceof Error
            ? error.message
            : "An unexpected error occurred."}
        </p>
        <Button onClick={() => refetch()} className="mt-4 gap-2">
          <RefreshCw className="size-4" />
          Try Again
        </Button>
      </div>
    );
  }

  // Loading state
  if (isLoading || !data) {
    return (
      <div className="flex flex-col h-screen">
        {/* Header skeleton */}
        <div className="flex items-center gap-4 border-b px-4 py-3">
          <Skeleton className="size-8 rounded-md" />
          <div className="space-y-1.5">
            <Skeleton className="h-4 w-64" />
            <Skeleton className="h-3 w-48" />
          </div>
        </div>
        {/* Content skeleton */}
        <div className="flex flex-1">
          <div className="flex-1 flex items-center justify-center bg-muted/10">
            <div className="flex flex-col items-center gap-4">
              <Skeleton className="h-[600px] w-[450px] rounded-lg" />
            </div>
          </div>
        </div>
      </div>
    );
  }

  const { paper, chunks, highlights } = data;
  const currentHighlights = selectedChunkId
    ? highlights.filter((h) => h.chunk_id === selectedChunkId)
    : highlights;

  return (
    <div className="flex flex-col h-[calc(100vh-3.5rem)]">
      {/* Header */}
      <ViewerHeader paper={paper} />

      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden" ref={pdfContainerRef}>
        {/* PDF Viewer */}
        <div className="flex-1 min-w-0">
          <PDFContainer
            pdfUrl={pdfUrl}
            highlights={currentHighlights}
            selectedChunkId={selectedChunkId}
            onPageChange={handlePageChange}
            pdfState={pdfState}
            onPDFStateChange={setPDFState}
            onSearch={handleSearch}
          />
        </div>

        {/* Chunk Sidebar */}
        <ChunkSidebar
          paper={paper}
          chunks={chunks}
          selectedChunkId={selectedChunkId}
          onSelectChunk={handleSelectChunk}
          isLoading={isLoading}
          isOpen={sidebarOpen}
          onToggle={() => setSidebarOpen(!sidebarOpen)}
        />
      </div>
    </div>
  );
}
