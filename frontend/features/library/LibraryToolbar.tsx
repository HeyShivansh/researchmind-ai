"use client";

import { type KeyboardEvent } from "react";
import { motion } from "framer-motion";
import {
  Search,
  Upload,
  RefreshCw,
  SlidersHorizontal,
  ArrowUpDown,
} from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useRouter } from "next/navigation";
import { cn } from "@/lib/utils";

// =============================================================================
// Library Toolbar
// =============================================================================

interface LibraryToolbarProps {
  searchQuery: string;
  onSearchChange: (query: string) => void;
  onSearch: () => void;
  sortBy: string;
  onSortChange: (sort: string) => void;
  isRefreshing: boolean;
  onRefresh: () => void;
  onToggleFilters: () => void;
  filtersVisible: boolean;
}

export function LibraryToolbar({
  searchQuery,
  onSearchChange,
  onSearch,
  sortBy,
  onSortChange,
  isRefreshing,
  onRefresh,
  onToggleFilters,
  filtersVisible,
}: LibraryToolbarProps) {
  const router = useRouter();

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") onSearch();
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: 0.1, ease: "easeOut" }}
      className="flex flex-col sm:flex-row items-start sm:items-center gap-2 mb-4"
    >
      {/* Search */}
      <div className="relative flex-1 w-full sm:max-w-sm">
        <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          placeholder="Search by title, author, or keyword..."
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          onKeyDown={handleKeyDown}
          className="pl-9 h-9"
        />
      </div>

      {/* Sort */}
      <div className="flex items-center gap-2 w-full sm:w-auto">
        <Select value={sortBy} onValueChange={(v: string | null) => v && onSortChange(v)}>
          <SelectTrigger className="w-full sm:w-36 h-9">
            <ArrowUpDown className="size-3.5 mr-1.5 shrink-0" />
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="newest">Newest</SelectItem>
            <SelectItem value="oldest">Oldest</SelectItem>
            <SelectItem value="title">Title A-Z</SelectItem>
            <SelectItem value="pages">Pages</SelectItem>
          </SelectContent>
        </Select>

        {/* Toggle Filters */}
        <Button
          variant="outline"
          size="sm"
          onClick={onToggleFilters}
          className={cn(
            "gap-1.5 h-9",
            filtersVisible && "bg-accent text-accent-foreground"
          )}
        >
          <SlidersHorizontal className="size-3.5" />
          <span className="hidden sm:inline">Filters</span>
        </Button>

        {/* Refresh */}
        <Button
          variant="outline"
          size="icon"
          onClick={onRefresh}
          disabled={isRefreshing}
          className="h-9 w-9 shrink-0"
          aria-label="Refresh papers"
        >
          <RefreshCw
            className={cn("size-3.5", isRefreshing && "animate-spin")}
          />
        </Button>

        {/* Upload */}
        <Button
          size="sm"
          onClick={() => router.push("/upload")}
          className="gap-1.5 h-9"
        >
          <Upload className="size-3.5" />
          <span className="hidden sm:inline">Upload</span>
        </Button>
      </div>
    </motion.div>
  );
}

export default LibraryToolbar;
