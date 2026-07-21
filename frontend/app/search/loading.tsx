import { SearchHeader } from "@/features/search";
import { Skeleton } from "@/components/ui/skeleton";

// =============================================================================
// Search Loading State
// =============================================================================

export default function SearchLoading() {
  return (
    <div className="h-full flex flex-col">
      <SearchHeader />

      {/* Search bar skeleton */}
      <div className="mb-6">
        <div className="flex items-center gap-2 rounded-xl border bg-card px-4 py-3">
          <Skeleton className="size-5 rounded" />
          <Skeleton className="flex-1 h-6" />
          <Skeleton className="h-9 w-24 rounded-md" />
        </div>
      </div>

      {/* Results skeleton */}
      <div className="flex items-center justify-between mb-3">
        <Skeleton className="h-4 w-32" />
        <Skeleton className="h-3 w-20" />
      </div>

      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="rounded-xl border bg-card p-4 ring-1 ring-foreground/10">
            <div className="flex items-start justify-between mb-3">
              <div className="space-y-2 flex-1 mr-4">
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-3 w-1/3" />
              </div>
              <Skeleton className="h-4 w-10" />
            </div>
            <div className="space-y-1.5 mb-3">
              <Skeleton className="h-3 w-full" />
              <Skeleton className="h-3 w-5/6" />
              <Skeleton className="h-3 w-4/6" />
            </div>
            <div className="flex items-center gap-2">
              <Skeleton className="h-5 w-16 rounded-full" />
              <Skeleton className="h-3 w-20" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
