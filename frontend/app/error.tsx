"use client";

import { useEffect } from "react";
import { AlertCircle, RefreshCw, Home } from "lucide-react";
import { Button } from "@/components/ui/button";
import Link from "next/link";

// =============================================================================
// Global Error Boundary
// =============================================================================

interface ErrorPageProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function ErrorPage({ error, reset }: ErrorPageProps) {
  useEffect(() => {
    console.error("Application error:", error);
  }, [error]);

  return (
    <div className="flex min-h-[70vh] flex-col items-center justify-center text-center px-4">
      <div className="mb-6 flex size-20 items-center justify-center rounded-full bg-destructive/10 ring-1 ring-destructive/20">
        <AlertCircle className="size-10 text-destructive" />
      </div>
      <h1 className="text-2xl font-semibold tracking-tight">
        Something went wrong
      </h1>
      <p className="mt-2 text-sm text-muted-foreground max-w-md">
        An unexpected error occurred. Our team has been notified. Please try
        again or return to the dashboard.
      </p>
      {error.digest && (
        <p className="mt-2 text-[10px] text-muted-foreground/50 font-mono">
          Error ID: {error.digest}
        </p>
      )}
      <div className="mt-8 flex items-center gap-3">
        <Button onClick={reset} className="gap-2">
          <RefreshCw className="size-4" />
          Try Again
        </Button>
        <Link href="/dashboard">
          <Button variant="outline" className="gap-2">
            <Home className="size-4" />
            Dashboard
          </Button>
        </Link>
      </div>
    </div>
  );
}
