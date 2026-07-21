"use client";

import { useState, useCallback } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { papersApi } from "@/services/papers";
import {
  LibraryHeader,
  LibraryToolbar,
  LibraryFilters,
  LibraryTable,
  LibraryPagination,
} from "@/features/library";
import type { LibraryFilterValues } from "@/features/library";
import { AlertCircle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

// =============================================================================
// Paper Library Page
// =============================================================================

const DEFAULT_PAGE_SIZE = 10;

export default function LibraryPage() {
  const queryClient = useQueryClient();

  // State
  const [searchQuery, setSearchQuery] = useState("");
  const [activeSearch, setActiveSearch] = useState("");
  const [sortBy, setSortBy] = useState("newest");
  const [currentPage, setCurrentPage] = useState(1);
  const [filtersVisible, setFiltersVisible] = useState(false);
  const [filters, setFilters] = useState<LibraryFilterValues>({});

  // Query
  const {
    data,
    isLoading,
    isError,
    error,
    isRefetching,
    refetch,
  } = useQuery({
    queryKey: ["papers", currentPage, DEFAULT_PAGE_SIZE, activeSearch],
    queryFn: () => papersApi.getAll(currentPage, DEFAULT_PAGE_SIZE, activeSearch),
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (id: string) => papersApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["papers"] });
      toast.success("Paper deleted successfully");
    },
    onError: () => {
      toast.error("Failed to delete paper");
    },
  });

  // Reindex mutation
  const reindexMutation = useMutation({
    mutationFn: (id: string) => papersApi.reindex(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["papers"] });
      toast.success("Paper reindexing started");
    },
    onError: () => {
      toast.error("Failed to reindex paper");
    },
  });

  // Handlers
  const handleSearch = useCallback(() => {
    setActiveSearch(searchQuery);
    setCurrentPage(1);
  }, [searchQuery]);

  const handleSearchChange = useCallback((query: string) => {
    setSearchQuery(query);
    if (!query) {
      setActiveSearch("");
      setCurrentPage(1);
    }
  }, []);

  const handleSortChange = useCallback((sort: string) => {
    setSortBy(sort);
  }, []);

  const handleRefresh = useCallback(() => {
    refetch();
  }, [refetch]);

  const handleDelete = useCallback(
    (id: string) => {
      deleteMutation.mutate(id);
    },
    [deleteMutation]
  );

  const handleReindex = useCallback(
    (id: string) => {
      reindexMutation.mutate(id);
    },
    [reindexMutation]
  );

  // Sort papers locally (mock data handling)
  const sortedPapers = data?.items
    ? [...data.items].sort((a, b) => {
        switch (sortBy) {
          case "oldest":
            return (
              new Date(a.created_at).getTime() -
              new Date(b.created_at).getTime()
            );
          case "title":
            return a.title.localeCompare(b.title);
          case "pages":
            return (b.page_count ?? 0) - (a.page_count ?? 0);
          case "newest":
          default:
            return (
              new Date(b.created_at).getTime() -
              new Date(a.created_at).getTime()
            );
        }
      })
    : [];

  // Error state
  if (isError) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-center">
        <div className="mb-4 flex size-16 items-center justify-center rounded-full bg-destructive/10">
          <AlertCircle className="size-8 text-destructive" />
        </div>
        <h2 className="text-xl font-semibold">Failed to load papers</h2>
        <p className="mt-1 text-sm text-muted-foreground max-w-sm">
          {error instanceof Error
            ? error.message
            : "An unexpected error occurred."}
        </p>
        <Button onClick={() => refetch()} className="mt-4 gap-2">
          <RefreshCw className="size-4" />
          Try Again
        </Button>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <LibraryHeader />

      {/* Toolbar */}
      <LibraryToolbar
        searchQuery={searchQuery}
        onSearchChange={handleSearchChange}
        onSearch={handleSearch}
        sortBy={sortBy}
        onSortChange={handleSortChange}
        isRefreshing={isRefetching}
        onRefresh={handleRefresh}
        onToggleFilters={() => setFiltersVisible(!filtersVisible)}
        filtersVisible={filtersVisible}
      />

      {/* Filters */}
      <LibraryFilters
        filters={filters}
        onFiltersChange={setFilters}
        isVisible={filtersVisible}
      />

      {/* Table */}
      <LibraryTable
        papers={sortedPapers}
        isLoading={isLoading}
        sortBy={sortBy}
        searchQuery={activeSearch}
        onDelete={handleDelete}
        onReindex={handleReindex}
      />

      {/* Pagination */}
      {data && (
        <LibraryPagination
          currentPage={currentPage}
          totalPages={data.total_pages}
          totalItems={data.total}
          pageSize={DEFAULT_PAGE_SIZE}
          onPageChange={setCurrentPage}
        />
      )}
    </div>
  );
}
