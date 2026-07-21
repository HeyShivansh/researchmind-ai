"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { History, Clock, Search } from "lucide-react";
import type { SearchHistoryItem, SearchMode } from "@/types";

// =============================================================================
// Search History
// =============================================================================

interface SearchHistoryProps {
  items: SearchHistoryItem[];
  isLoading: boolean;
  onSelectQuery: (query: string) => void;
}

const modeConfig: Record<SearchMode, { label: string; className: string }> = {
  semantic: {
    label: "Semantic",
    className: "bg-blue-500/10 text-blue-500 border-blue-500/20",
  },
  keyword: {
    label: "Keyword",
    className: "bg-amber-500/10 text-amber-500 border-amber-500/20",
  },
  hybrid: {
    label: "Hybrid",
    className: "bg-violet-500/10 text-violet-500 border-violet-500/20",
  },
};

function formatTimestamp(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));

  if (diffHours < 1) {
    const mins = Math.floor(diffMs / (1000 * 60));
    return `${mins}m ago`;
  }
  if (diffHours < 24) return `${diffHours}h ago`;
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
}

export function SearchHistory({
  items,
  isLoading,
  onSelectQuery,
}: SearchHistoryProps) {
  if (isLoading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="flex items-center gap-3 px-2 py-2">
            <Skeleton className="size-6 rounded-full" />
            <div className="flex-1 space-y-1">
              <Skeleton className="h-3.5 w-36" />
              <Skeleton className="h-2.5 w-20" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-center">
        <History className="size-6 text-muted-foreground/50 mb-2" />
        <p className="text-xs text-muted-foreground">No search history</p>
      </div>
    );
  }

  return (
    <div className="space-y-1">
      {items.map((item, index) => {
        const mode = modeConfig[item.mode];
        return (
          <motion.button
            key={item.id}
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.25, delay: 0.03 * index }}
            onClick={() => onSelectQuery(item.query)}
            className="flex w-full items-start gap-3 rounded-lg px-2 py-2 text-left transition-colors hover:bg-muted/50"
          >
            <div className="mt-0.5 flex size-6 shrink-0 items-center justify-center rounded-full bg-muted">
              <Search className="size-3 text-muted-foreground" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-xs font-medium truncate">
                &ldquo;{item.query}&rdquo;
              </p>
              <div className="flex items-center gap-2 mt-0.5">
                <Badge
                  variant="outline"
                  className={cn(
                    "text-[9px] px-1 py-0 h-4 border font-medium leading-none",
                    mode.className
                  )}
                >
                  {mode.label}
                </Badge>
                <span className="text-[10px] text-muted-foreground flex items-center gap-1">
                  <Clock className="size-2.5" />
                  {formatTimestamp(item.timestamp)}
                </span>
              </div>
            </div>
          </motion.button>
        );
      })}
    </div>
  );
}

export default SearchHistory;
