"use client";

import { cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";

// =============================================================================
// Page Header Component
// =============================================================================

interface PageHeaderProps {
  title: string;
  description?: string;
  actions?: React.ReactNode;
  className?: string;
}

export function PageHeader({
  title,
  description,
  actions,
  className,
}: PageHeaderProps) {
  return (
    <div
      className={cn(
        "flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between mb-6 md:mb-8",
        className
      )}
    >
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight md:text-3xl">
          {title}
        </h1>
        {description && (
          <p className="text-sm text-muted-foreground">{description}</p>
        )}
      </div>
      {actions && <div className="flex items-center gap-2 mt-2 sm:mt-0">{actions}</div>}
    </div>
  );
}

// =============================================================================
// Page Header Skeleton
// =============================================================================

export function PageHeaderSkeleton() {
  return (
    <div className="mb-6 md:mb-8 space-y-2">
      <Skeleton className="h-9 w-64" />
      <Skeleton className="h-5 w-96" />
    </div>
  );
}

export default PageHeader;
