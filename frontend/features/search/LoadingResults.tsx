"use client";

import { motion } from "framer-motion";
import { Skeleton } from "@/components/ui/skeleton";

// =============================================================================
// Loading Results / Skeleton
// =============================================================================

interface LoadingResultsProps {
  count?: number;
}

export function LoadingResults({ count = 5 }: LoadingResultsProps) {
  return (
    <div className="space-y-4">
      {/* Results header skeleton */}
      <div className="flex items-center justify-between px-1">
        <Skeleton className="h-4 w-28" />
        <Skeleton className="h-3 w-16" />
      </div>

      {/* Skeleton cards */}
      <div className="space-y-3">
        {Array.from({ length: count }).map((_, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.05 * i }}
            className="rounded-xl border bg-card p-4 ring-1 ring-foreground/10"
          >
            {/* Title + score */}
            <div className="flex items-start justify-between mb-3">
              <div className="space-y-2 flex-1 mr-4">
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-3 w-1/3" />
              </div>
              <Skeleton className="h-4 w-10" />
            </div>

            {/* Text lines */}
            <div className="space-y-1.5 mb-3">
              <Skeleton className="h-3 w-full" />
              <Skeleton className="h-3 w-5/6" />
              <Skeleton className="h-3 w-4/6" />
            </div>

            {/* Footer */}
            <div className="flex items-center gap-2">
              <Skeleton className="h-5 w-16 rounded-full" />
              <Skeleton className="h-3 w-20" />
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}

export default LoadingResults;
