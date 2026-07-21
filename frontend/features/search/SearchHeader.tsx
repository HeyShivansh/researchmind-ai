"use client";

import { motion } from "framer-motion";
import { Search } from "lucide-react";

// =============================================================================
// Search Header
// =============================================================================

export function SearchHeader() {
  return (
    <motion.div
      initial={{ opacity: 0, y: -12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
      className="flex flex-col items-center text-center mb-8"
    >
      <div className="flex items-center gap-3 mb-2">
        <div className="flex size-10 items-center justify-center rounded-xl bg-primary/10 ring-1 ring-primary/20">
          <Search className="size-5 text-primary" />
        </div>
        <h1 className="text-2xl font-semibold tracking-tight md:text-3xl">
          Research Search
        </h1>
      </div>
      <p className="text-sm text-muted-foreground max-w-md">
        Search scientific literature using hybrid semantic retrieval.
      </p>
    </motion.div>
  );
}

export default SearchHeader;
