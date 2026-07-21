"use client";

import { motion } from "framer-motion";
import { Library } from "lucide-react";

// =============================================================================
// Library Header
// =============================================================================

export function LibraryHeader() {
  return (
    <motion.div
      initial={{ opacity: 0, y: -12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: "easeOut" }}
      className="flex items-center gap-3 mb-6"
    >
      <div className="flex size-10 items-center justify-center rounded-xl bg-primary/10 ring-1 ring-primary/20">
        <Library className="size-5 text-primary" />
      </div>
      <div>
        <h1 className="text-2xl font-semibold tracking-tight md:text-3xl">
          Paper Library
        </h1>
        <p className="text-sm text-muted-foreground">
          Browse and manage indexed research papers.
        </p>
      </div>
    </motion.div>
  );
}

export default LibraryHeader;
