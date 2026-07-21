"use client";

import { motion } from "framer-motion";
import { Upload, Search, Brain } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";

// =============================================================================
// Dashboard Header
// =============================================================================

export function DashboardHeader() {
  const router = useRouter();

  return (
    <motion.div
      initial={{ opacity: 0, y: -12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
      className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-6 md:mb-8"
    >
      <div className="flex items-start gap-4">
        <div className="hidden sm:flex size-12 shrink-0 items-center justify-center rounded-xl bg-primary/10 ring-1 ring-primary/20">
          <Brain className="size-6 text-primary" />
        </div>
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold tracking-tight md:text-3xl">
            ResearchMind AI
          </h1>
          <p className="text-sm text-muted-foreground max-w-lg">
            Enterprise-grade Retrieval-Augmented Generation platform for
            scientific literature.
          </p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          onClick={() => router.push("/search")}
          className="gap-2"
        >
          <Search className="size-4" />
          Search Papers
        </Button>
        <Button onClick={() => router.push("/upload")} className="gap-2">
          <Upload className="size-4" />
          Upload Paper
        </Button>
      </div>
    </motion.div>
  );
}

export default DashboardHeader;
