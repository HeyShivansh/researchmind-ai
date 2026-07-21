"use client";

import { useEffect } from "react";
import { AlertCircle, RefreshCw, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import Link from "next/link";

// =============================================================================
// Viewer Error Boundary
// =============================================================================

interface ViewerErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function ViewerError({ error, reset }: ViewerErrorProps) {
  useEffect(() => {
    console.error("Viewer error:", error);
  }, [error]);

  return (
    <div className="flex flex-col items-center justify-center h-[80vh] text-center px-4">
      <div className="mb-4 flex size-16 items-center justify-center rounded-full bg-destructive/10">
        <AlertCircle className="size-8 text-destructive" />
      </div>
      <h2 className="text-lg font-semibold">Failed to load paper</h2>
      <p className="mt-1 text-sm text-muted-foreground max-w-sm">
        {error.message || "An unexpected error occurred while loading this paper."}
      </p>
      <div className="mt-6 flex items-center gap-3">
        <Button onClick={reset} className="gap-2">
          <RefreshCw className="size-4" />
          Try Again
        </Button>
        <Link href="/library">
          <Button variant="outline" className="gap-2">
            <ArrowLeft className="size-4" />
            Back to Library
          </Button>
        </Link>
      </div>
    </div>
  );
}
