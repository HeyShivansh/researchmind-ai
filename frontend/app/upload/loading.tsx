import { PageHeaderSkeleton } from "@/components/common";
import { Skeleton } from "@/components/ui/skeleton";

// =============================================================================
// Upload Loading State
// =============================================================================

export default function UploadLoading() {
  return (
    <div>
      <PageHeaderSkeleton />

      <div className="flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-12">
        <Skeleton className="size-16 rounded-full mb-4" />
        <Skeleton className="h-6 w-48 mb-2" />
        <Skeleton className="h-4 w-72 mb-6" />
        <Skeleton className="h-10 w-32 rounded-md" />
      </div>

      <Skeleton className="h-4 w-48 mt-8 mb-4" />
      <div className="space-y-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="flex items-center justify-between rounded-lg border p-4">
            <div className="space-y-1">
              <Skeleton className="h-4 w-56" />
              <Skeleton className="h-3 w-32" />
            </div>
            <Skeleton className="h-6 w-20 rounded-full" />
          </div>
        ))}
      </div>
    </div>
  );
}
