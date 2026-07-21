import Link from "next/link";
import { FileSearch, Home } from "lucide-react";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

// =============================================================================
// 404 Not Found Page
// =============================================================================

export default function NotFound() {
  return (
    <div className="flex min-h-[80vh] flex-col items-center justify-center px-4 text-center">
      <div className="mb-6 flex size-20 items-center justify-center rounded-full bg-muted">
        <FileSearch className="size-10 text-muted-foreground/50" />
      </div>
      <h1 className="text-6xl font-bold tracking-tight">404</h1>
      <h2 className="mt-2 text-lg font-semibold">Page not found</h2>
      <p className="mt-1 max-w-sm text-sm text-muted-foreground">
        The page you&apos;re looking for doesn&apos;t exist or has been moved.
        Check the URL or navigate back to the dashboard.
      </p>
      <div className="mt-6 flex items-center gap-3">
        <Link
          href="/dashboard"
          className={cn(buttonVariants({ variant: "default" }), "gap-1.5")}
        >
          <Home className="size-4" />
          Back to Dashboard
        </Link>
        <Link
          href="/library"
          className={buttonVariants({ variant: "outline" })}
        >
          Go to Library
        </Link>
      </div>
    </div>
  );
}
