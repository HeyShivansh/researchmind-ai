"use client";

import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Search, History } from "lucide-react";
import { cn } from "@/lib/utils";
import type { RecentSearch } from "@/types";

// =============================================================================
// Recent Searches
// =============================================================================

interface RecentSearchesProps {
  searches?: RecentSearch[];
  isLoading: boolean;
}

function formatTimestamp(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));

  if (diffHours < 1) {
    const diffMinutes = Math.floor(diffMs / (1000 * 60));
    return `${diffMinutes}m ago`;
  }
  if (diffHours < 24) {
    return `${diffHours}h ago`;
  }
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
}

const modeConfig = {
  semantic: { label: "Semantic", className: "bg-blue-500/10 text-blue-500 border-blue-500/20" },
  keyword: { label: "Keyword", className: "bg-amber-500/10 text-amber-500 border-amber-500/20" },
  hybrid: { label: "Hybrid", className: "bg-violet-500/10 text-violet-500 border-violet-500/20" },
};

export function RecentSearches({
  searches,
  isLoading,
}: RecentSearchesProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.35, ease: "easeOut" }}
    >
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <History className="size-4 text-muted-foreground" />
            <CardTitle className="text-sm font-medium">
              Recent Searches
            </CardTitle>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="space-y-3 px-4 pb-4">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="flex items-center justify-between">
                  <div className="space-y-1">
                    <Skeleton className="h-4 w-36" />
                    <Skeleton className="h-3 w-20" />
                  </div>
                  <Skeleton className="h-5 w-16" />
                </div>
              ))}
            </div>
          ) : !searches || searches.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <Search className="size-8 text-muted-foreground/50 mb-2" />
              <p className="text-sm text-muted-foreground">No searches yet</p>
            </div>
          ) : (
            <div className="divide-y divide-border/50">
              {searches.map((search, index) => {
                const mode = modeConfig[search.mode];
                return (
                  <motion.div
                    key={search.id}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{
                      duration: 0.3,
                      delay: 0.05 * index,
                      ease: "easeOut",
                    }}
                    className="flex items-center justify-between px-4 py-3 transition-colors hover:bg-muted/30"
                  >
                    <div className="min-w-0 flex-1 mr-4">
                      <p className="text-sm font-medium truncate">
                        &ldquo;{search.query}&rdquo;
                      </p>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        {search.result_count} results
                      </p>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <Badge
                        variant="outline"
                        className={cn(
                          "text-[10px] px-1.5 py-0 h-5 border font-medium",
                          mode.className
                        )}
                      >
                        {mode.label}
                      </Badge>
                      <span className="text-[11px] text-muted-foreground tabular-nums">
                        {formatTimestamp(search.timestamp)}
                      </span>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}

export default RecentSearches;
