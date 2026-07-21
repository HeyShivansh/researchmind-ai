"use client";

import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import {
  X,
  ExternalLink,
  FileText,
  BookOpen,
  Hash,
  Sparkles,
  Layers,
  Calendar,
} from "lucide-react";
import type { SearchResult } from "@/types";
import { highlightKeywords } from "@/lib/highlight";

// =============================================================================
// Search Preview
// =============================================================================

interface SearchPreviewProps {
  result: SearchResult | null;
  onClose: () => void;
  isLoading: boolean;
  query: string;
}

const sourceConfig = {
  hybrid: { label: "Hybrid Retrieval", className: "text-violet-500" },
  semantic: { label: "Semantic Search", className: "text-blue-500" },
  keyword: { label: "Keyword Search", className: "text-amber-500" },
};

export function SearchPreview({ result, onClose, isLoading, query }: SearchPreviewProps) {
  if (isLoading) {
    return (
      <div className="space-y-4 p-4">
        <Skeleton className="h-6 w-48" />
        <Skeleton className="h-4 w-32" />
        <Separator />
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-4 w-24" />
      </div>
    );
  }

  if (!result) {
    return (
      <div className="flex flex-col items-center justify-center h-full py-16 text-center">
        <div className="mb-4 flex size-12 items-center justify-center rounded-full bg-muted">
          <BookOpen className="size-6 text-muted-foreground/60" />
        </div>
        <h3 className="text-sm font-medium">Select a result</h3>
        <p className="text-xs text-muted-foreground mt-1 max-w-[200px]">
          Click on any search result to view the full excerpt and metadata.
        </p>
      </div>
    );
  }

  const source = sourceConfig[result.source] ?? sourceConfig.hybrid;

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={result.chunk_id}
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: -20 }}
        transition={{ duration: 0.25, ease: "easeOut" }}
        className="h-full flex flex-col"
      >
        {/* Header */}
        <div className="flex items-start justify-between gap-4 p-4 pb-0">
          <div className="min-w-0">
            <h2 className="text-base font-semibold leading-snug">
              {result.paper_title}
            </h2>
            {(result.authors && result.authors.length > 0) || result.year ? (
              <p className="text-xs text-muted-foreground mt-1">
                {result.authors?.join(", ")}
                {result.year && (
                  <>
                    {" "}
                    &middot;{" "}
                    <span className="inline-flex items-center gap-1">
                      <Calendar className="size-3" />
                      {result.year}
                    </span>
                  </>
                )}
              </p>
            ) : null}
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={onClose}
            className="shrink-0"
            aria-label="Close preview"
          >
            <X className="size-4" />
          </Button>
        </div>

        <Separator className="my-3" />

        {/* Score & Metadata */}
        <div className="px-4 space-y-3">
          <div className="flex items-center gap-2 flex-wrap">
            <Badge
              variant="outline"
              className={cn(
                "text-xs px-2 py-0.5 gap-1.5 font-medium",
                source.className,
                "border-current/20"
              )}
            >
              <Sparkles className="size-3" />
              {source.label}
            </Badge>
            <Badge variant="secondary" className="text-xs gap-1.5 font-normal">
              <Sparkles className="size-3 text-amber-500" />
              Score: {(result.score * 100).toFixed(0)}%
            </Badge>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <FileText className="size-3.5 shrink-0" />
              <span>Page {result.page_number}</span>
            </div>
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <Hash className="size-3.5 shrink-0" />
              <span>Chunk {result.chunk_index + 1}</span>
            </div>
            {result.keywords && result.keywords.length > 0 && (
              <div className="col-span-2 flex items-start gap-2 text-xs text-muted-foreground">
                <Layers className="size-3.5 shrink-0 mt-0.5" />
                <div className="flex flex-wrap gap-1">
                  {result.keywords.map((kw) => (
                    <span
                      key={kw}
                      className="rounded-md bg-muted px-1.5 py-0.5 text-[10px]"
                    >
                      {kw}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        <Separator className="my-3" />

        {/* Retrieved Chunk */}
        <div className="flex-1 px-4 pb-4 overflow-y-auto">
          <div className="flex items-center gap-1.5 mb-2">
            <BookOpen className="size-3.5 text-muted-foreground" />
            <span className="text-xs font-medium text-muted-foreground">
              Retrieved Excerpt
            </span>
          </div>
          <div className="rounded-lg bg-muted/30 border p-4">
            <p className="text-sm leading-relaxed text-foreground/90">
              {highlightKeywords(result.text, query)}
            </p>
          </div>
        </div>

        {/* Actions */}
        <div className="border-t p-4 flex items-center gap-2">
          <Button variant="outline" size="sm" className="gap-2 text-xs">
            <ExternalLink className="size-3.5" />
            Open Paper
          </Button>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}

export default SearchPreview;
