"use client";

import { motion } from "framer-motion";
import { SearchResultCard } from "./SearchResultCard";
import { LoadingResults } from "./LoadingResults";
import { NoResults } from "./NoResults";
import type { SearchResult } from "@/types";

// =============================================================================
// Search Results
// =============================================================================

interface SearchResultsProps {
  results: SearchResult[];
  selectedId: string | null;
  onSelectResult: (result: SearchResult) => void;
  isLoading: boolean;
  totalResults: number;
  tookMs: number;
  query: string;
}

export function SearchResults({
  results,
  selectedId,
  onSelectResult,
  isLoading,
  totalResults,
  tookMs,
  query,
}: SearchResultsProps) {
  if (isLoading) {
    return <LoadingResults count={5} />;
  }

  if (results.length === 0) {
    return <NoResults />;
  }

  return (
    <div className="space-y-4">
      {/* Results header */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="flex items-center justify-between px-1"
      >
        <p className="text-sm text-muted-foreground">
          Found{" "}
          <span className="font-medium text-foreground">{totalResults}</span>{" "}
          results
        </p>
        <p className="text-xs text-muted-foreground tabular-nums">
          in {tookMs}ms
        </p>
      </motion.div>

      {/* Result cards */}
      <div className="space-y-3">
        {results.map((result, index) => (
          <SearchResultCard
            key={result.chunk_id}
            result={result}
            isSelected={selectedId === result.chunk_id}
            onSelect={() => onSelectResult(result)}
            index={index}
            query={query}
          />
        ))}
      </div>
    </div>
  );
}

export default SearchResults;
