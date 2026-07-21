"use client";

import { motion } from "framer-motion";
import { ChunkCard } from "./ChunkCard";
import { MetadataCard } from "./MetadataCard";
import { AISummaryPlaceholder } from "./AISummaryPlaceholder";
import { Skeleton } from "@/components/ui/skeleton";
import type { ViewerPaper, ViewerChunk } from "@/types";
import { Search, PanelRightClose, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useIsMobile } from "@/hooks";

// =============================================================================
// Chunk Sidebar
// =============================================================================

interface ChunkSidebarProps {
  paper: ViewerPaper;
  chunks: ViewerChunk[];
  selectedChunkId: string | null;
  onSelectChunk: (chunkId: string) => void;
  isLoading: boolean;
  isOpen: boolean;
  onToggle: () => void;
}

export function ChunkSidebar({
  paper,
  chunks,
  selectedChunkId,
  onSelectChunk,
  isLoading,
  isOpen,
  onToggle,
}: ChunkSidebarProps) {
  const isMobile = useIsMobile();

  if (!isOpen) {
    return (
      <Button
        variant="ghost"
        size="sm"
        onClick={onToggle}
        className="fixed right-3 top-20 z-10 gap-1.5 text-xs"
        aria-label="Open sidebar"
      >
        <PanelRightClose className="size-3.5" />
        <span className="hidden sm:inline">Chunks</span>
      </Button>
    );
  }

  return (
    <motion.aside
      initial={false}
      animate={{ width: isMobile ? "100%" : 380 }}
      transition={{ duration: 0.3, ease: "easeInOut" }}
      className={cn(
        "flex flex-col border-l bg-card h-full overflow-hidden",
        isMobile ? "fixed inset-0 z-30" : "w-[380px] shrink-0"
      )}
    >
      {/* Sidebar Header */}
      <div className="flex items-center justify-between border-b px-4 py-3">
        <div className="flex items-center gap-2">
          <Search className="size-4 text-muted-foreground" />
          <h2 className="text-sm font-semibold">Retrieved Chunks</h2>
          <span className="text-xs text-muted-foreground">
            ({chunks.length})
          </span>
        </div>
        <Button
          variant="ghost"
          size="icon"
          onClick={onToggle}
          aria-label="Close sidebar"
        >
          <X className="size-4" />
        </Button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-3 space-y-4">
        {/* Chunks List */}
        {isLoading ? (
          <div className="space-y-2">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="rounded-lg border p-3 space-y-2">
                <Skeleton className="h-3 w-24" />
                <Skeleton className="h-3 w-full" />
                <Skeleton className="h-3 w-4/5" />
                <Skeleton className="h-3 w-16" />
              </div>
            ))}
          </div>
        ) : chunks.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <Search className="size-8 text-muted-foreground/30 mb-2" />
            <p className="text-xs text-muted-foreground">
              No chunks retrieved for this paper.
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {chunks.map((chunk, index) => (
              <ChunkCard
                key={chunk.id}
                chunk={chunk}
                isSelected={selectedChunkId === chunk.id}
                onSelect={() => onSelectChunk(chunk.id)}
                index={index}
              />
            ))}
          </div>
        )}

        {/* Metadata Card */}
        <MetadataCard paper={paper} />

        {/* AI Summary Placeholder */}
        <AISummaryPlaceholder />
      </div>
    </motion.aside>
  );
}

export default ChunkSidebar;
