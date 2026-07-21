"use client";

import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import {
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
} from "lucide-react";

// =============================================================================
// Library Pagination
// =============================================================================

interface LibraryPaginationProps {
  currentPage: number;
  totalPages: number;
  totalItems: number;
  pageSize: number;
  onPageChange: (page: number) => void;
}

export function LibraryPagination({
  currentPage,
  totalPages,
  totalItems,
  pageSize,
  onPageChange,
}: LibraryPaginationProps) {
  if (totalPages <= 1) return null;

  const startItem = (currentPage - 1) * pageSize + 1;
  const endItem = Math.min(currentPage * pageSize, totalItems);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3, delay: 0.2 }}
      className="flex flex-col sm:flex-row items-center justify-between gap-2 mt-4"
    >
      <p className="text-xs text-muted-foreground order-2 sm:order-1">
        Showing{" "}
        <span className="font-medium text-foreground">{startItem}</span>
        {" - "}
        <span className="font-medium text-foreground">{endItem}</span>
        {" of "}
        <span className="font-medium text-foreground">{totalItems}</span>{" "}
        papers
      </p>

      <div className="flex items-center gap-1 order-1 sm:order-2">
        <Button
          variant="ghost"
          size="icon-xs"
          onClick={() => onPageChange(1)}
          disabled={currentPage <= 1}
          aria-label="First page"
        >
          <ChevronsLeft className="size-3.5" />
        </Button>
        <Button
          variant="ghost"
          size="icon-xs"
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage <= 1}
          aria-label="Previous page"
        >
          <ChevronLeft className="size-3.5" />
        </Button>

        <div className="flex items-center gap-1 mx-1">
          {generatePageNumbers(currentPage, totalPages).map((page, i) =>
            page === "..." ? (
              <span
                key={`ellipsis-${i}`}
                className="px-1 text-xs text-muted-foreground"
              >
                ...
              </span>
            ) : (
              <Button
                key={page}
                variant={currentPage === page ? "default" : "ghost"}
                size="icon-xs"
                onClick={() => onPageChange(page as number)}
                className="text-xs min-w-[28px]"
                aria-label={`Page ${page}`}
                aria-current={currentPage === page ? "page" : undefined}
              >
                {page}
              </Button>
            )
          )}
        </div>

        <Button
          variant="ghost"
          size="icon-xs"
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage >= totalPages}
          aria-label="Next page"
        >
          <ChevronRight className="size-3.5" />
        </Button>
        <Button
          variant="ghost"
          size="icon-xs"
          onClick={() => onPageChange(totalPages)}
          disabled={currentPage >= totalPages}
          aria-label="Last page"
        >
          <ChevronsRight className="size-3.5" />
        </Button>
      </div>
    </motion.div>
  );
}

// =============================================================================
// Helpers
// =============================================================================

function generatePageNumbers(
  current: number,
  total: number
): (number | "...")[] {
  const pages: (number | "...")[] = [];

  if (total <= 7) {
    for (let i = 1; i <= total; i++) pages.push(i);
    return pages;
  }

  pages.push(1);

  if (current > 3) pages.push("...");

  const start = Math.max(2, current - 1);
  const end = Math.min(total - 1, current + 1);

  for (let i = start; i <= end; i++) {
    pages.push(i);
  }

  if (current < total - 2) pages.push("...");

  pages.push(total);

  return pages;
}

export default LibraryPagination;
