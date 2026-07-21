"use client";

import { motion } from "framer-motion";
import { ArrowLeft, Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";
import type { ViewerPaper } from "@/types";

// =============================================================================
// Viewer Header
// =============================================================================

interface ViewerHeaderProps {
  paper: ViewerPaper;
}

export function ViewerHeader({ paper }: ViewerHeaderProps) {
  const router = useRouter();

  return (
    <motion.header
      initial={{ opacity: 0, y: -12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className="flex items-center justify-between gap-4 border-b bg-card px-4 py-3"
    >
      {/* Left: Back button + title */}
      <div className="flex items-center gap-3 min-w-0 flex-1">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => router.back()}
          aria-label="Go back"
          className="shrink-0"
        >
          <ArrowLeft className="size-4" />
        </Button>

        <div className="min-w-0">
          <h1 className="text-sm font-semibold truncate">{paper.title}</h1>
          <p className="text-xs text-muted-foreground truncate">
            {paper.authors.slice(0, 3).join(", ")}
            {paper.authors.length > 3 && " et al."}
            {" · "}
            {paper.year}
            {paper.doi && <> · DOI: {paper.doi}</>}
          </p>
        </div>
      </div>

      {/* Right: Actions */}
      <div className="flex items-center gap-1 shrink-0">
        <Button variant="outline" size="sm" className="gap-1.5 text-xs">
          <Download className="size-3.5" />
          <span className="hidden sm:inline">Download</span>
        </Button>
      </div>
    </motion.header>
  );
}

export default ViewerHeader;
