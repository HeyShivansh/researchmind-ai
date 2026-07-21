"use client";

import { memo } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  FileText,
  ExternalLink,
  Sparkles,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import type { SearchResult } from "@/types";
import { useState } from "react";
import { highlightKeywords } from "@/lib/highlight";

// =============================================================================
// Search Result Card
// =============================================================================

interface SearchResultCardProps {
  result: SearchResult;
  isSelected: boolean;
  onSelect: () => void;
  index: number;
  query: string;
}

const sourceConfig = {
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

function SearchResultCardInner({
  result,
  isSelected,
  onSelect,
  index,
  query,
}: SearchResultCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const source = sourceConfig[result.source] ?? sourceConfig.hybrid;
  const ScoreIcon = result.source === "keyword" ? FileText : Sparkles;

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay: 0.04 * index, ease: "easeOut" }}
      className={cn(
        "group/card rounded-xl border bg-card ring-1 ring-foreground/10 transition-all duration-300",
        "hover:shadow-lg hover:-translate-y-0.5 hover:ring-primary/20",
        isSelected && "ring-2 ring-primary/40 bg-primary/[0.03] shadow-md -translate-y-0.5"
      )}
    >
      {/* Clickable area for selection */}
      <button
        onClick={onSelect}
        className="w-full text-left p-4 pb-0 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50 focus-visible:ring-inset rounded-t-xl"
        aria-current={isSelected ? "true" : undefined}
        aria-label={`View details for ${result.paper_title}`}
      >
        {/* Score indicator */}
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-1.5">
            <ScoreIcon className="size-3 text-muted-foreground/50" aria-hidden="true" />
            <span className="text-xs font-mono tabular-nums text-muted-foreground">
              {(result.score * 100).toFixed(0)}% match
            </span>
          </div>
          <Badge
            variant="outline"
            className={cn(
              "text-[10px] px-1.5 py-0 h-5 border font-medium",
              source.className
            )}
          >
            {source.label}
          </Badge>
        </div>

        {/* Paper Title */}
        <h3 className="text-sm font-semibold leading-snug group-hover/card:text-primary transition-colors pr-2">
          {result.paper_title}
        </h3>
        {result.authors && result.authors.length > 0 && (
          <p className="text-xs text-muted-foreground mt-0.5">
            {result.authors.join(", ")}
            {result.year && <> &middot; {result.year}</>}
          </p>
        )}

        {/* Matched Text */}
        <div className="mt-2 mb-3">
          <p
            className={cn(
              "text-sm text-muted-foreground leading-relaxed",
              !isExpanded && "line-clamp-3"
            )}
          >
            {highlightKeywords(result.text, query)}
          </p>
        </div>
      </button>

      {/* Footer with actions */}
      <div className="flex items-center justify-between px-4 pb-3">
        <div className="flex items-center gap-1 text-[11px] text-muted-foreground">
          <span>Page {result.page_number}</span>
          <span className="text-muted-foreground/40" aria-hidden="true">&middot;</span>
          <span>Chunk {result.chunk_index + 1}</span>
        </div>

        <div className="flex items-center gap-1">
          {/* Expand button */}
          <Button
            variant="ghost"
            size="xs"
            onClick={() => setIsExpanded(!isExpanded)}
            className="gap-1 text-xs text-muted-foreground h-7"
            aria-label={isExpanded ? "Collapse excerpt" : "Expand excerpt"}
          >
            {isExpanded ? (
              <>
                <ChevronUp className="size-3" aria-hidden="true" />
                Collapse
              </>
            ) : (
              <>
                <ChevronDown className="size-3" aria-hidden="true" />
                Expand
              </>
            )}
          </Button>

          {/* Open Paper button */}
          <Button
            variant="ghost"
            size="xs"
            className="gap-1 text-xs text-muted-foreground h-7"
            onClick={() => {
              // TODO: Navigate to paper detail page
            }}
            aria-label={`Open paper: ${result.paper_title}`}
          >
            <ExternalLink className="size-3" aria-hidden="true" />
            Paper
          </Button>
        </div>
      </div>
    </motion.div>
  );
}

export const SearchResultCard = memo(SearchResultCardInner);
export default SearchResultCard;
