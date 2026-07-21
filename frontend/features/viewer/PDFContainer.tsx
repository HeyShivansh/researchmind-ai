"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { pdfjs, Document, Page } from "react-pdf";
import { cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";
import { PDFToolbar } from "./PDFToolbar";
import { FileQuestion } from "lucide-react";
import type { HighlightRegion, PDFState } from "@/types";

// =============================================================================
// PDF.js Worker Configuration (CDN)
// =============================================================================

pdfjs.GlobalWorkerOptions.workerSrc =
  "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.9.155/pdf.worker.min.mjs";

// =============================================================================
// PDF Container
// =============================================================================

interface PDFContainerProps {
  pdfUrl: string;
  highlights: HighlightRegion[];
  selectedChunkId: string | null;
  onPageChange: (page: number) => void;
  pdfState: PDFState;
  onPDFStateChange: (state: PDFState) => void;
  onSearch?: (query: string) => void;
}

export function PDFContainer({
  pdfUrl,
  highlights,
  selectedChunkId,
  onPageChange,
  pdfState,
  onPDFStateChange,
  onSearch,
}: PDFContainerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [, setIsFullscreen] = useState(false);

  const handleDocumentLoadSuccess = ({ numPages }: { numPages: number }) => {
    onPDFStateChange({ ...pdfState, numPages });
  };

  const handlePageChange = (page: number) => {
    onPDFStateChange({ ...pdfState, currentPage: page });
    onPageChange(page);
  };

  const zoomIn = () => {
    const newScale = Math.min(pdfState.scale + 0.25, 3);
    onPDFStateChange({ ...pdfState, scale: newScale });
  };

  const zoomOut = () => {
    const newScale = Math.max(pdfState.scale - 0.25, 0.25);
    onPDFStateChange({ ...pdfState, scale: newScale });
  };

  const rotate = () => {
    onPDFStateChange({
      ...pdfState,
      rotation: (pdfState.rotation + 90) % 360,
    });
  };

  const fitWidth = useCallback(() => {
    if (containerRef.current) {
      const containerWidth = containerRef.current.clientWidth - 64;
      const scale = containerWidth / 612;
      onPDFStateChange({
        ...pdfState,
        scale: Math.round(scale * 100) / 100,
      });
    }
  }, [pdfState, onPDFStateChange]);

  const fitPage = useCallback(() => {
    if (containerRef.current) {
      const containerHeight = containerRef.current.clientHeight - 100;
      const scale = containerHeight / 792;
      onPDFStateChange({
        ...pdfState,
        scale: Math.round(scale * 100) / 100,
      });
    }
  }, [pdfState, onPDFStateChange]);

  const toggleFullscreen = useCallback(() => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  }, []);

  useEffect(() => {
    const handler = () => setIsFullscreen(!!document.fullscreenElement);
    document.addEventListener("fullscreenchange", handler);
    return () => document.removeEventListener("fullscreenchange", handler);
  }, []);

  // Filter highlights for current page
  const pageHighlights = highlights.filter(
    (h) => h.page_number === pdfState.currentPage
  );

  // If no PDF URL, show a placeholder with sample PDF from arXiv
  if (!pdfUrl) {
    return (
      <div className="flex flex-col h-full">
        <PDFToolbar
          currentPage={pdfState.currentPage}
          numPages={pdfState.numPages}
          scale={pdfState.scale}
          onPageChange={handlePageChange}
          onZoomIn={zoomIn}
          onZoomOut={zoomOut}
          onRotate={rotate}
          onFullscreen={toggleFullscreen}
          onFitWidth={fitWidth}
          onFitPage={fitPage}
          onSearch={onSearch ?? (() => {})}
        />
        <div className="flex-1 flex items-center justify-center">
          <div className="flex flex-col items-center gap-3 text-center">
            <FileQuestion className="size-12 text-muted-foreground/30" />
            <div className="space-y-1">
              <p className="text-sm font-medium">PDF Preview Unavailable</p>
              <p className="text-xs text-muted-foreground max-w-xs">
                Upload this paper to enable PDF viewing with highlighted
                chunk regions.
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full" ref={containerRef}>
      {/* Toolbar */}
      <PDFToolbar
        currentPage={pdfState.currentPage}
        numPages={pdfState.numPages}
        scale={pdfState.scale}
        onPageChange={handlePageChange}
        onZoomIn={zoomIn}
        onZoomOut={zoomOut}
        onRotate={rotate}
        onFullscreen={toggleFullscreen}
        onFitWidth={fitWidth}
        onFitPage={fitPage}
        onSearch={onSearch ?? (() => {})}
      />

      {/* PDF Viewer */}
      <div className="flex-1 overflow-auto bg-muted/20">
        <div
          className="flex flex-col items-center py-4 min-h-full"
          style={{
            backgroundImage:
              "radial-gradient(circle, hsl(var(--border)) 1px, transparent 1px)",
            backgroundSize: "20px 20px",
          }}
        >
          <Document
            file={pdfUrl}
            onLoadSuccess={handleDocumentLoadSuccess}
            loading={
              <div className="flex flex-col items-center gap-3 py-12">
                <Skeleton className="h-[600px] w-[450px] rounded-lg" />
              </div>
            }
            error={
              <div className="flex flex-col items-center gap-3 py-12 text-center">
                <FileQuestion className="size-10 text-destructive/50" />
                <p className="text-sm text-muted-foreground">
                  Failed to load PDF
                </p>
              </div>
            }
          >
            <div className="relative">
              <Page
                pageNumber={pdfState.currentPage}
                scale={pdfState.scale}
                rotate={pdfState.rotation}
                className="rounded-lg shadow-2xl"
                renderTextLayer={false}
                renderAnnotationLayer={false}
                loading={
                  <Skeleton
                    className="rounded-lg"
                    style={{
                      width: pdfState.scale * 612,
                      height: pdfState.scale * 792,
                    }}
                  />
                }
              />

              {/* Highlight Overlays */}
              {pageHighlights.map((highlight) => {
                const isSelected = highlight.chunk_id === selectedChunkId;
                return (
                  <div
                    key={highlight.chunk_id}
                    className={cn(
                      "absolute pointer-events-none rounded-sm transition-all duration-300",
                      isSelected && "ring-2 ring-primary/60"
                    )}
                    style={{
                      left: highlight.bounds.x * pdfState.scale,
                      top: highlight.bounds.y * pdfState.scale,
                      width: highlight.bounds.width * pdfState.scale,
                      height: highlight.bounds.height * pdfState.scale,
                      backgroundColor: isSelected
                        ? "rgba(139, 92, 246, 0.35)"
                        : highlight.color,
                    }}
                  />
                );
              })}
            </div>
          </Document>
        </div>
      </div>
    </div>
  );
}

export default PDFContainer;
