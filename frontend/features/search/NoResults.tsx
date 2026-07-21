"use client";

import { motion } from "framer-motion";
import { SearchX, Lightbulb } from "lucide-react";

// =============================================================================
// No Results
// =============================================================================

export function NoResults() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: "easeOut" }}
      className="flex flex-col items-center justify-center py-16 text-center"
    >
      <div className="mb-4 flex size-14 items-center justify-center rounded-full bg-muted">
        <SearchX className="size-7 text-muted-foreground/60" />
      </div>
      <h3 className="text-base font-semibold">No papers matched your query</h3>
      <p className="mt-1 text-sm text-muted-foreground max-w-xs">
        Try adjusting your search terms or filters to find relevant papers.
      </p>
      <div className="mt-6 space-y-2">
        <div className="flex items-start gap-2 text-xs text-muted-foreground">
          <Lightbulb className="size-3.5 shrink-0 mt-0.5 text-amber-500" />
          <span>Try fewer keywords for broader results</span>
        </div>
        <div className="flex items-start gap-2 text-xs text-muted-foreground">
          <Lightbulb className="size-3.5 shrink-0 mt-0.5 text-amber-500" />
          <span>Use Semantic mode to find conceptually related papers</span>
        </div>
        <div className="flex items-start gap-2 text-xs text-muted-foreground">
          <Lightbulb className="size-3.5 shrink-0 mt-0.5 text-amber-500" />
          <span>Remove filters to search across all papers</span>
        </div>
      </div>
    </motion.div>
  );
}

export default NoResults;
