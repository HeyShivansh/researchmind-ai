import { Skeleton } from "@/components/ui/skeleton";

// =============================================================================
// Viewer Loading State
// =============================================================================

export default function ViewerLoading() {
  return (
    <div className="flex flex-col h-screen">
      {/* Header skeleton */}
      <div className="flex items-center justify-between border-b bg-card px-4 py-3">
        <div className="flex items-center gap-3 min-w-0 flex-1">
          <Skeleton className="size-8 rounded-md shrink-0" />
          <div className="min-w-0 space-y-1.5">
            <Skeleton className="h-4 w-64" />
            <Skeleton className="h-3 w-48" />
          </div>
        </div>
      </div>

      {/* Content skeleton */}
      <div className="flex flex-1 overflow-hidden">
        <div className="flex-1 flex items-center justify-center bg-muted/10">
          <div className="flex flex-col items-center gap-4">
            <Skeleton className="h-[600px] w-[450px] rounded-lg" />
          </div>
        </div>

        {/* Sidebar skeleton */}
        <div className="w-[380px] border-l bg-card flex flex-col">
          <div className="border-b px-4 py-3">
            <Skeleton className="h-5 w-32" />
          </div>
          <div className="flex-1 p-3 space-y-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="rounded-lg border p-3 space-y-2">
                <Skeleton className="h-3 w-24" />
                <Skeleton className="h-3 w-full" />
                <Skeleton className="h-3 w-4/5" />
                <Skeleton className="h-3 w-16" />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
