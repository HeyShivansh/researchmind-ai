"use client";

import { useState, useRef, useEffect, type KeyboardEvent } from "react";
import { motion } from "framer-motion";
import { Search, X, Sparkles, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

// =============================================================================
// Search Bar
// =============================================================================

const EXAMPLE_QUERIES = [
  "What are transformer architectures?",
  "Applications of attention mechanisms",
  "Vector databases for semantic search",
];

interface SearchBarProps {
  onSearch: (query: string) => void;
  isSearching: boolean;
  initialQuery?: string;
}

export function SearchBar({ onSearch, isSearching, initialQuery }: SearchBarProps) {
  const [query, setQuery] = useState(initialQuery ?? "");
  const [showExamples, setShowExamples] = useState(true);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (initialQuery) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setQuery(initialQuery);
      setShowExamples(false);
    }
  }, [initialQuery]);

  const handleSearch = () => {
    const trimmed = query.trim();
    if (trimmed.length === 0) return;
    setShowExamples(false);
    onSearch(trimmed);
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      handleSearch();
    }
  };

  const handleClear = () => {
    setQuery("");
    setShowExamples(true);
    inputRef.current?.focus();
  };

  const handleExampleClick = (example: string) => {
    setQuery(example);
    setShowExamples(false);
    onSearch(example);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.1, ease: "easeOut" }}
      className="mb-6"
    >
      {/* Search Input */}
      <div
        className={cn(
          "relative flex items-center gap-2 rounded-xl border bg-card px-4 py-3 transition-all duration-300 ring-1 ring-foreground/10",
          "focus-within:ring-2 focus-within:ring-primary/30 focus-within:border-primary/50",
          "shadow-sm hover:shadow-md"
        )}
      >
        <Search className="size-5 shrink-0 text-muted-foreground" />
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            if (e.target.value.length === 0) setShowExamples(true);
          }}
          onKeyDown={handleKeyDown}
          placeholder="Search papers..."
          className="flex-1 bg-transparent text-base outline-none placeholder:text-muted-foreground/60 md:text-lg"
          disabled={isSearching}
          autoFocus
        />
        <div className="flex items-center gap-1.5">
          {query.length > 0 && (
            <button
              onClick={handleClear}
              className="flex size-7 items-center justify-center rounded-md text-muted-foreground/60 transition-colors hover:text-foreground hover:bg-muted/50"
              aria-label="Clear search"
            >
              <X className="size-4" />
            </button>
          )}
          <kbd className="hidden sm:inline-flex h-6 items-center gap-1 rounded-md border bg-muted/50 px-1.5 text-[10px] text-muted-foreground/60 font-mono">
            <span className="text-[9px]">⌘</span>K
          </kbd>
          <Button
            size="sm"
            onClick={handleSearch}
            disabled={isSearching || query.trim().length === 0}
            className="gap-1.5"
          >
            {isSearching ? (
              <>
                <div className="size-3.5 animate-spin rounded-full border-2 border-current border-t-transparent" />
                Searching
              </>
            ) : (
              <>
                <Sparkles className="size-3.5" />
                Search
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Example Queries */}
      {showExamples && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          exit={{ opacity: 0, height: 0 }}
          transition={{ duration: 0.2 }}
          className="mt-3 flex flex-wrap items-center gap-2"
        >
          <span className="text-xs text-muted-foreground mr-1">
            Try searching:
          </span>
          {EXAMPLE_QUERIES.map((example, i) => (
            <motion.button
              key={example}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.2 + i * 0.08, ease: "easeOut" }}
              onClick={() => handleExampleClick(example)}
              className="group inline-flex items-center gap-1.5 rounded-full border bg-muted/30 px-3 py-1 text-xs text-muted-foreground transition-all hover:bg-muted/70 hover:text-foreground hover:border-foreground/20"
            >
              {example}
              <ArrowRight className="size-3 opacity-0 -ml-1 transition-all group-hover:opacity-100 group-hover:ml-0" />
            </motion.button>
          ))}
        </motion.div>
      )}
    </motion.div>
  );
}

export default SearchBar;
