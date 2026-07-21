"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { SlidersHorizontal, RotateCcw, ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";
import type { SearchFilters as SearchFiltersType, SearchMode, SortBy } from "@/types";
import { DEFAULT_SEARCH_FILTERS } from "@/types";

// =============================================================================
// Search Filters
// =============================================================================

interface SearchFiltersProps {
  filters: SearchFiltersType;
  onFiltersChange: (filters: SearchFiltersType) => void;
}

export function SearchFilters({ filters, onFiltersChange }: SearchFiltersProps) {
  const [isOpen, setIsOpen] = useState(false);

  const updateFilter = <K extends keyof SearchFiltersType>(
    key: K,
    value: SearchFiltersType[K]
  ) => {
    onFiltersChange({ ...filters, [key]: value });
  };

  const resetFilters = () => {
    onFiltersChange(DEFAULT_SEARCH_FILTERS);
  };

  const hasChanges =
    filters.mode !== DEFAULT_SEARCH_FILTERS.mode ||
    filters.top_k !== DEFAULT_SEARCH_FILTERS.top_k ||
    filters.threshold !== DEFAULT_SEARCH_FILTERS.threshold ||
    filters.sort_by !== DEFAULT_SEARCH_FILTERS.sort_by ||
    filters.year !== undefined;

  return (
    <div className="mb-4">
      {/* Toggle */}
      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setIsOpen(!isOpen)}
          className={cn(
            "gap-2 text-muted-foreground hover:text-foreground",
            isOpen && "text-foreground"
          )}
        >
          <SlidersHorizontal className="size-4" />
          Filters
          <ChevronDown
            className={cn(
              "size-3.5 transition-transform",
              isOpen && "rotate-180"
            )}
          />
        </Button>
        {hasChanges && (
          <Button
            variant="ghost"
            size="xs"
            onClick={resetFilters}
            className="gap-1.5 text-xs text-muted-foreground"
          >
            <RotateCcw className="size-3" />
            Reset
          </Button>
        )}
      </div>

      {/* Filters Panel */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2, ease: "easeInOut" }}
            className="overflow-hidden"
          >
            <div className="mt-3 grid gap-4 rounded-lg border bg-card p-4 sm:grid-cols-2 lg:grid-cols-5">
              {/* Search Mode */}
              <div className="space-y-1.5">
                <Label className="text-xs text-muted-foreground">Search Type</Label>
                <Select
                  value={filters.mode}
                  onValueChange={(v: SearchMode | null) => {
                    if (v) updateFilter("mode", v);
                  }}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="hybrid">Hybrid</SelectItem>
                    <SelectItem value="semantic">Semantic Only</SelectItem>
                    <SelectItem value="keyword">Keyword Only</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Top K */}
              <div className="space-y-1.5">
                <Label className="text-xs text-muted-foreground">Top K</Label>
                <Select
                  value={String(filters.top_k)}
                  onValueChange={(v: string | null) => {
                    if (v) updateFilter("top_k", Number(v));
                  }}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {[5, 10, 15, 20, 30, 50].map((k) => (
                      <SelectItem key={k} value={String(k)}>
                        {k} results
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Threshold */}
              <div className="space-y-1.5">
                <Label className="text-xs text-muted-foreground">
                  Similarity Threshold
                </Label>
                <Select
                  value={String(filters.threshold)}
                  onValueChange={(v: string | null) => {
                    if (v) updateFilter("threshold", Number(v));
                  }}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {[
                      { label: "None (0.0)", value: "0" },
                      { label: "Low (0.3)", value: "0.3" },
                      { label: "Medium (0.5)", value: "0.5" },
                      { label: "High (0.7)", value: "0.7" },
                    ].map((opt) => (
                      <SelectItem key={opt.value} value={opt.value}>
                        {opt.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Year */}
              <div className="space-y-1.5">
                <Label className="text-xs text-muted-foreground">
                  Publication Year
                </Label>
                <Input
                  type="number"
                  placeholder="Any year"
                  value={filters.year ?? ""}
                  onChange={(e) =>
                    updateFilter(
                      "year",
                      e.target.value ? Number(e.target.value) : undefined
                    )
                  }
                  min={1900}
                  max={2030}
                />
              </div>

              {/* Sort By */}
              <div className="space-y-1.5">
                <Label className="text-xs text-muted-foreground">Sort By</Label>
                <Select
                  value={filters.sort_by}
                  onValueChange={(v: SortBy | null) => {
                    if (v) updateFilter("sort_by", v);
                  }}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="relevance">Relevance</SelectItem>
                    <SelectItem value="newest">Newest</SelectItem>
                    <SelectItem value="oldest">Oldest</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default SearchFilters;
