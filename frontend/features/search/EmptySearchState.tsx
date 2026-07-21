"use client";

import { motion } from "framer-motion";
import { Search, Sparkles, BookOpen, Lightbulb } from "lucide-react";

// =============================================================================
// Empty Search State
// =============================================================================

export function EmptySearchState() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.2, ease: "easeOut" }}
      className="flex flex-col items-center justify-center py-16 text-center"
    >
      <div className="mb-4 flex size-16 items-center justify-center rounded-2xl bg-gradient-to-br from-primary/10 to-primary/5 ring-1 ring-primary/10">
        <Search className="size-8 text-primary/70" />
      </div>
      <h3 className="text-lg font-semibold">Search your research library</h3>
      <p className="mt-1 text-sm text-muted-foreground max-w-md">
        Enter a query above to search across all indexed papers using hybrid
        retrieval. Results will appear here with relevance scores and source
        context.
      </p>

      <div className="mt-8 grid gap-3 sm:grid-cols-3 max-w-lg">
        <div className="rounded-lg border bg-card p-3 text-left">
          <Sparkles className="size-4 text-violet-500 mb-1.5" />
          <h4 className="text-xs font-semibold mb-0.5">Hybrid Search</h4>
          <p className="text-[10px] text-muted-foreground leading-relaxed">
            Combines semantic understanding with keyword precision for the best results.
          </p>
        </div>
        <div className="rounded-lg border bg-card p-3 text-left">
          <BookOpen className="size-4 text-blue-500 mb-1.5" />
          <h4 className="text-xs font-semibold mb-0.5">Full Text Index</h4>
          <p className="text-[10px] text-muted-foreground leading-relaxed">
            Every chunk of every paper is indexed and searchable by content.
          </p>
        </div>
        <div className="rounded-lg border bg-card p-3 text-left">
          <Lightbulb className="size-4 text-amber-500 mb-1.5" />
          <h4 className="text-xs font-semibold mb-0.5">Smart Filters</h4>
          <p className="text-[10px] text-muted-foreground leading-relaxed">
            Filter by search mode, year, similarity threshold, and more.
          </p>
        </div>
      </div>
    </motion.div>
  );
}

export default EmptySearchState;
