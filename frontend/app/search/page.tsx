"use client";

import { useState, useCallback, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { searchApi } from "@/services/search";
import {
  SearchHeader,
  SearchBar,
  SearchFilters,
  SearchResults,
  SearchPreview,
  SearchHistory,
  EmptySearchState,
} from "@/features/search";
import { Button } from "@/components/ui/button";
import { History, PanelRightClose, PanelRightOpen, SearchX, RefreshCw } from "lucide-react";
import { cn } from "@/lib/utils";
import { useIsMobile, useIsTablet } from "@/hooks";
import type { SearchResult, SearchFilters as SearchFiltersType } from "@/types";
import { DEFAULT_SEARCH_FILTERS } from "@/types";

// =============================================================================
// Search Workspace
// =============================================================================

export default function SearchPage() {
  const isMobile = useIsMobile();
  const isTablet = useIsTablet();

  // State
  const [query, setQuery] = useState("");
  const [hasSearched, setHasSearched] = useState(false);
  const [filters, setFilters] = useState<SearchFiltersType>(DEFAULT_SEARCH_FILTERS);
  const [selectedResult, setSelectedResult] = useState<SearchResult | null>(null);
  const [showHistory, setShowHistory] = useState(false);
  const [showPreview, setShowPreview] = useState(!isMobile && !isTablet);

  // Responsive: auto-hide preview on mobile
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (isMobile) setShowPreview(false);
  }, [isMobile]);

  // Search query
  const {
    data: searchResponse,
    isFetching,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ["search", query, filters],
    queryFn: () =>
      searchApi.search({ query, filters }),
    enabled: query.trim().length > 0 && hasSearched,
  });

  // History query
  const { data: historyData, isLoading: historyLoading } = useQuery({
    queryKey: ["search-history"],
    queryFn: () => searchApi.getHistory(),
    staleTime: 1000 * 60 * 5,
  });

  const handleSearch = useCallback((newQuery: string) => {
    setQuery(newQuery);
    setHasSearched(true);
    setSelectedResult(null);
    if (isMobile || isTablet) setShowPreview(false);
  }, [isMobile, isTablet]);

  const handleSelectResult = useCallback((result: SearchResult) => {
    setSelectedResult(result);
    if (isMobile || isTablet) setShowPreview(true);
  }, [isMobile, isTablet]);

  const handleHistorySelect = useCallback((q: string) => {
    setQuery(q);
    setHasSearched(true);
    setSelectedResult(null);
    setShowHistory(false);
  }, []);

  const handleClosePreview = useCallback(() => {
    setSelectedResult(null);
    if (isMobile || isTablet) setShowPreview(false);
  }, [isMobile, isTablet]);

  const hasSearchResults = hasSearched && searchResponse;
  const showTwoColumn = showPreview && !isMobile;
  const showMobilePreview = showPreview && isMobile;

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <SearchHeader />

      {/* Search Bar */}
      <SearchBar
        onSearch={handleSearch}
        isSearching={isFetching}
        initialQuery={query}
      />

      {/* Filters */}
      <SearchFilters filters={filters} onFiltersChange={setFilters} />

      {/* Main Content Area */}
      <div className="flex-1 flex gap-0 min-h-0">
        {/* Left Column: Results + History */}
        <div
          className={cn(
            "flex flex-col min-w-0",
            showTwoColumn
              ? "w-1/2 pr-4 border-r"
              : "w-full",
            isMobile && showMobilePreview && "hidden"
          )}
        >
          {/* Toggle buttons */}
          <div className="flex items-center justify-between mb-3">
            {hasSearchResults && (
              <p className="text-xs text-muted-foreground">
                {searchResponse.total_results} results in{" "}
                {searchResponse.took_ms}ms
              </p>
            )}
            <div className="flex items-center gap-1 ml-auto">
              {/* History toggle */}
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowHistory(!showHistory)}
                className={cn(
                  "gap-1.5 text-xs text-muted-foreground",
                  showHistory && "text-foreground bg-muted"
                )}
              >
                <History className="size-3.5" />
                History
              </Button>

              {/* Preview toggle (desktop) */}
              {!isMobile && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowPreview(!showPreview)}
                  className="gap-1.5 text-xs text-muted-foreground"
                >
                  {showPreview ? (
                    <PanelRightClose className="size-3.5" />
                  ) : (
                    <PanelRightOpen className="size-3.5" />
                  )}
                  Preview
                </Button>
              )}
            </div>
          </div>

          {/* Search History Panel (collapsible) */}
          {showHistory && (
            <div className="mb-4 rounded-lg border bg-card p-3">
              <h3 className="text-xs font-semibold text-muted-foreground mb-2 flex items-center gap-1.5">
                <History className="size-3.5" />
                Recent Searches
              </h3>
              <SearchHistory
                items={historyData ?? []}
                isLoading={historyLoading}
                onSelectQuery={handleHistorySelect}
              />
            </div>
          )}

          {/* Results */}
          <div className="flex-1 overflow-y-auto">
            {isError ? (
              <div className="flex flex-col items-center justify-center py-16 text-center">
                <div className="mb-4 flex size-14 items-center justify-center rounded-full bg-destructive/10">
                  <SearchX className="size-7 text-destructive" />
                </div>
                <h3 className="text-sm font-semibold">Search failed</h3>
                <p className="mt-1 text-xs text-muted-foreground max-w-xs">
                  {error instanceof Error
                    ? error.message
                    : "An error occurred while searching. Please try again."}
                </p>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => refetch()}
                  className="mt-3 gap-1.5"
                >
                  <RefreshCw className="size-3.5" />
                  Try Again
                </Button>
              </div>
            ) : hasSearchResults && !isFetching ? (
              <SearchResults
                results={searchResponse.results}
                selectedId={selectedResult?.chunk_id ?? null}
                onSelectResult={handleSelectResult}
                isLoading={false}
                totalResults={searchResponse.total_results}
                tookMs={searchResponse.took_ms}
                query={query}
              />
            ) : hasSearched && isFetching ? (
              <SearchResults
                results={[]}
                selectedId={null}
                onSelectResult={() => {}}
                isLoading={true}
                totalResults={0}
                tookMs={0}
                query={query}
              />
            ) : (
              <EmptySearchState />
            )}
          </div>
        </div>

        {/* Right Column: Preview Panel */}
        {showTwoColumn && (
          <div className="w-1/2 pl-4 overflow-y-auto">
            <SearchPreview
              result={selectedResult}
              onClose={handleClosePreview}
              isLoading={false}
              query={query}
            />
          </div>
        )}
      </div>

      {/* Mobile Preview (full screen overlay) */}
      {showMobilePreview && selectedResult && (
        <div className="fixed inset-0 z-40 bg-background p-4 pt-0 overflow-y-auto">
          <SearchPreview
            result={selectedResult}
            onClose={handleClosePreview}
            isLoading={false}
            query={query}
          />
        </div>
      )}
    </div>
  );
}
