"use client";

import { useQuery } from "@tanstack/react-query";
import { dashboardApi } from "@/services/dashboard";
import {
  DashboardHeader,
  StatsGrid,
  SystemStatus,
  RecentUploadsTable,
  RecentSearches,
  QuickActions,
} from "@/features/dashboard";
import { AlertCircle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";

// =============================================================================
// Dashboard Page
// =============================================================================

export default function DashboardPage() {
  const {
    data,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ["dashboard"],
    queryFn: () => dashboardApi.getDashboardData(),
  });

  // Error state
  if (isError) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-center">
        <div className="mb-4 flex size-16 items-center justify-center rounded-full bg-destructive/10">
          <AlertCircle className="size-8 text-destructive" />
        </div>
        <h2 className="text-xl font-semibold">Failed to load dashboard</h2>
        <p className="mt-1 text-sm text-muted-foreground max-w-sm">
          {error instanceof Error
            ? error.message
            : "An unexpected error occurred while loading your dashboard."}
        </p>
        <Button onClick={() => refetch()} className="mt-4 gap-2">
          <RefreshCw className="size-4" />
          Try Again
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <DashboardHeader />

      {/* Statistics Cards */}
      <StatsGrid data={data} isLoading={isLoading} />

      {/* Main Grid: System Status + Recent Uploads */}
      <div className="grid gap-6 lg:grid-cols-2">
        <SystemStatus
          services={data?.systemStatus}
          isLoading={isLoading}
        />
        <RecentUploadsTable
          uploads={data?.recentUploads}
          isLoading={isLoading}
        />
      </div>

      {/* Secondary Grid: Quick Actions + Recent Searches */}
      <div className="grid gap-6 lg:grid-cols-2">
        <QuickActions actions={data?.quickActions ?? []} />
        <RecentSearches
          searches={data?.recentSearches}
          isLoading={isLoading}
        />
      </div>
    </div>
  );
}
