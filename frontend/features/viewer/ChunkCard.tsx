"use client";

import { memo } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Sparkles, FileText, ArrowRight, Layers } from "lucide-react";
import type { ViewerChunk, SearchSource } from "@/types";

// =============================================================================
// Chunk Card
// =============================================================================

interface ChunkCardProps {
  chunk: ViewerChunk;
  isSelected: boolean;
  onSelect: () => void;
  index: number;
}

const sourceConfig: Record<SearchSource, { label: string; className: string }> = {
  hybrid: {
    label: "Hybrid",
    className: "bg-violet-500/10 text-violet-500 border-violet-500/20",
  },
  semantic: {
    label: "Semantic",
    className: "bg-blue-500/10 text-blue-500 border-blue-500/20",
  },
  keyword: {
    label: "Keyword",
    className: "bg-amber-500/10 text-amber-500 border-amber-500/20",
  },
};

function ChunkCardInner({ chunk, isSelected, onSelect, index }: ChunkCardProps) {
  const source = sourceConfig[chunk.source] ?? sourceConfig.hybrid;
  const ScoreIcon = chunk.source === "keyword" ? FileText : Sparkles;

  return (
    <motion.button
      initial={{ opacity: 0, x: 12 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.3, delay: 0.03 * index, ease: "easeOut" }}
      onClick={onSelect}
      className={cn(
        "w-full text-left rounded-lg border bg-card p-3 transition-all duration-200 ring-1 ring-foreground/10",
        "hover:bg-accent/30 hover:ring-primary/20",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50",
        isSelected && "ring-2 ring-primary/40 bg-primary/[0.03]"
      )}
      aria-current={isSelected ? "page" : undefined}
      aria-label={`Chunk from page ${chunk.page_number}, score ${(chunk.score * 100).toFixed(0)}%`}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-1.5">
        <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <Layers className="size-3" aria-hidden="true" />
          <span>
            Page {chunk.page_number} · Chunk {chunk.chunk_index + 1}
          </span>
        </div>
        <div className="flex items-center gap-1.5">
          <ScoreIcon className="size-3 text-muted-foreground/50" aria-hidden="true" />
          <span className="text-xs font-mono tabular-nums text-muted-foreground">
            {(chunk.score * 100).toFixed(0)}%
          </span>
        </div>
      </div>

      {/* Text */}
      <p className="text-xs text-muted-foreground leading-relaxed line-clamp-3 mb-2">
        {chunk.text}
      </p>

      {/* Footer */}
      <div className="flex items-center justify-between">
        <Badge
          variant="outline"
          className={cn(
            "text-[9px] px-1.5 py-0 h-4 border font-medium leading-none",
            source.className
          )}
        >
          {source.label}
        </Badge>
        {isSelected && (
          <span className="text-[10px] text-primary/70 flex items-center gap-1">
            Viewing <ArrowRight className="size-2.5" aria-hidden="true" />
          </span>
        )}
      </div>
    </motion.button>
  );
}

export const ChunkCard = memo(ChunkCardInner);
export default ChunkCard;
