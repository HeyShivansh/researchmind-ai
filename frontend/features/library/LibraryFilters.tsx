"use client";

import { motion, AnimatePresence } from "framer-motion";
import { RotateCcw } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

// =============================================================================
// Library Filters
// =============================================================================

export interface LibraryFilterValues {
  year?: number;
  dateRange?: string;
  minPages?: number;
  maxPages?: number;
  status?: string;
  titleSearch?: string;
  doiSearch?: string;
}

interface LibraryFiltersProps {
  filters: LibraryFilterValues;
  onFiltersChange: (filters: LibraryFilterValues) => void;
  isVisible: boolean;
}

export function LibraryFilters({
  filters,
  onFiltersChange,
  isVisible,
}: LibraryFiltersProps) {
  const updateFilter = <K extends keyof LibraryFilterValues>(
    key: K,
    value: LibraryFilterValues[K]
  ) => {
    onFiltersChange({ ...filters, [key]: value });
  };

  const resetFilters = () => {
    onFiltersChange({});
  };

  const hasChanges = Object.keys(filters).length > 0;

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          exit={{ opacity: 0, height: 0 }}
          transition={{ duration: 0.2, ease: "easeInOut" }}
          className="overflow-hidden mb-4"
        >
          <div className="rounded-lg border bg-card p-4">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-medium text-muted-foreground">
                Filters
              </span>
              {hasChanges && (
                <Button
                  variant="ghost"
                  size="xs"
                  onClick={resetFilters}
                  className="gap-1 text-xs text-muted-foreground h-6"
                >
                  <RotateCcw className="size-3" />
                  Reset
                </Button>
              )}
            </div>

            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {/* Publication Year */}
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

              {/* Upload Date */}
              <div className="space-y-1.5">
                <Label className="text-xs text-muted-foreground">
                  Upload Date
                </Label>
                <Select
                  value={filters.dateRange ?? ""}
                  onValueChange={(v: string | null) =>
                    updateFilter("dateRange", v ?? undefined)
                  }
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Any time" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="today">Today</SelectItem>
                    <SelectItem value="week">Past 7 days</SelectItem>
                    <SelectItem value="month">Past 30 days</SelectItem>
                    <SelectItem value="quarter">Past 90 days</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Pages */}
              <div className="space-y-1.5">
                <Label className="text-xs text-muted-foreground">
                  Pages (min - max)
                </Label>
                <div className="flex items-center gap-2">
                  <Input
                    type="number"
                    placeholder="Min"
                    value={filters.minPages ?? ""}
                    onChange={(e) =>
                      updateFilter(
                        "minPages",
                        e.target.value ? Number(e.target.value) : undefined
                      )
                    }
                    min={1}
                    className="h-8"
                  />
                  <span className="text-muted-foreground text-xs">-</span>
                  <Input
                    type="number"
                    placeholder="Max"
                    value={filters.maxPages ?? ""}
                    onChange={(e) =>
                      updateFilter(
                        "maxPages",
                        e.target.value ? Number(e.target.value) : undefined
                      )
                    }
                    min={1}
                    className="h-8"
                  />
                </div>
              </div>

              {/* Search by Title */}
              <div className="space-y-1.5">
                <Label className="text-xs text-muted-foreground">
                  Search by Title
                </Label>
                <Input
                  type="text"
                  placeholder="Filter by title..."
                  value={filters.titleSearch ?? ""}
                  onChange={(e) =>
                    updateFilter(
                      "titleSearch",
                      e.target.value || undefined
                    )
                  }
                />
              </div>

              {/* Search by DOI */}
              <div className="space-y-1.5">
                <Label className="text-xs text-muted-foreground">
                  Search by DOI
                </Label>
                <Input
                  type="text"
                  placeholder="Filter by DOI..."
                  value={filters.doiSearch ?? ""}
                  onChange={(e) =>
                    updateFilter(
                      "doiSearch",
                      e.target.value || undefined
                    )
                  }
                />
              </div>

              {/* Status */}
              <div className="space-y-1.5">
                <Label className="text-xs text-muted-foreground">
                  Indexed Status
                </Label>
                <Select
                  value={filters.status ?? ""}
                  onValueChange={(v: string | null) =>
                    updateFilter("status", v ?? undefined)
                  }
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Any status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ready">Ready</SelectItem>
                    <SelectItem value="processing">Processing</SelectItem>
                    <SelectItem value="error">Error</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

export default LibraryFilters;
