"use client";

import { useState, useRef, useEffect, type KeyboardEvent } from "react";
import {
  Minus,
  Plus,
  RotateCw,
  Maximize,
  ChevronLeft,
  ChevronRight,
  FileText,
  Search,
  X,
  Maximize2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

// =============================================================================
// PDF Toolbar
// =============================================================================

interface PDFToolbarProps {
  currentPage: number;
  numPages: number;
  scale: number;
  onPageChange: (page: number) => void;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onRotate: () => void;
  onFullscreen: () => void;
  onFitWidth: () => void;
  onFitPage: () => void;
  onSearch: (query: string) => void;
}

export function PDFToolbar({
  currentPage,
  numPages,
  scale,
  onPageChange,
  onZoomIn,
  onZoomOut,
  onRotate,
  onFullscreen,
  onFitWidth,
  onFitPage,
  onSearch,
}: PDFToolbarProps) {
  const [showSearch, setShowSearch] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const searchInputRef = useRef<HTMLInputElement>(null);
  const zoomPercent = Math.round(scale * 100);

  useEffect(() => {
    if (showSearch && searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, [showSearch]);

  // Keyboard shortcuts
  useEffect(() => {
    const handler = (e: globalThis.KeyboardEvent) => {
      // Ctrl+F or Cmd+F for search
      if ((e.ctrlKey || e.metaKey) && e.key === "f") {
        e.preventDefault();
        setShowSearch((prev) => !prev);
      }
      // Escape to close search
      if (e.key === "Escape" && showSearch) {
        setShowSearch(false);
        setSearchQuery("");
      }
      // Page Up / Down (only when not typing in an input)
      if (
        e.key === "PageUp" &&
        document.activeElement?.tagName !== "INPUT"
      ) {
        e.preventDefault();
        onPageChange(currentPage - 1);
      }
      if (
        e.key === "PageDown" &&
        document.activeElement?.tagName !== "INPUT"
      ) {
        e.preventDefault();
        onPageChange(currentPage + 1);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [currentPage, showSearch, onPageChange]);

  const handleSearchKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      onSearch(searchQuery);
    }
    if (e.key === "Escape") {
      setShowSearch(false);
      setSearchQuery("");
    }
  };

  return (
    <div className="flex flex-col">
      {/* Main Toolbar */}
      <div className="flex items-center justify-between gap-2 border-b bg-muted/30 px-3 py-1.5">
        {/* Page Navigation */}
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon-xs"
            onClick={() => onPageChange(currentPage - 1)}
            disabled={currentPage <= 1}
            aria-label="Previous page (Page Up)"
          >
            <ChevronLeft className="size-3.5" />
          </Button>

          <div className="flex items-center gap-1 mx-1">
            <Input
              type="number"
              value={currentPage}
              onChange={(e) => {
                const val = Number(e.target.value);
                if (val >= 1 && val <= numPages) onPageChange(val);
              }}
              className="h-6 w-10 text-center text-xs [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
              aria-label="Current page number"
            />
            <span className="text-xs text-muted-foreground">
              / {numPages}
            </span>
          </div>

          <Button
            variant="ghost"
            size="icon-xs"
            onClick={() => onPageChange(currentPage + 1)}
            disabled={currentPage >= numPages}
            aria-label="Next page (Page Down)"
          >
            <ChevronRight className="size-3.5" />
          </Button>
        </div>

        {/* Right Controls */}
        <div className="flex items-center gap-1">
          {/* Search within PDF */}
          <Button
            variant="ghost"
            size="icon-xs"
            onClick={() => setShowSearch(!showSearch)}
            aria-label="Search within PDF (Ctrl+F)"
            className={cn(showSearch && "bg-accent text-accent-foreground")}
          >
            <Search className="size-3.5" />
          </Button>

          {/* Fit Page */}
          <Button
            variant="ghost"
            size="icon-xs"
            onClick={onFitPage}
            aria-label="Fit to page"
            className="hidden sm:flex"
          >
            <Maximize2 className="size-3.5" />
          </Button>

          {/* Fit Width */}
          <Button
            variant="ghost"
            size="icon-xs"
            onClick={onFitWidth}
            aria-label="Fit to width"
            className="hidden sm:flex"
          >
            <FileText className="size-3.5" />
          </Button>

          {/* Zoom Out */}
          <Button
            variant="ghost"
            size="icon-xs"
            onClick={onZoomOut}
            disabled={scale <= 0.25}
            aria-label="Zoom out"
          >
            <Minus className="size-3.5" />
          </Button>

          <span
            className="tabular-nums text-xs text-muted-foreground min-w-[3ch] text-center cursor-pointer"
            onClick={() => onFitWidth()}
            title="Click to reset zoom"
          >
            {zoomPercent}%
          </span>

          {/* Zoom In */}
          <Button
            variant="ghost"
            size="icon-xs"
            onClick={onZoomIn}
            disabled={scale >= 3}
            aria-label="Zoom in"
          >
            <Plus className="size-3.5" />
          </Button>

          {/* Separator */}
          <div className="mx-1 h-4 w-px bg-border" />

          {/* Rotate */}
          <Button
            variant="ghost"
            size="icon-xs"
            onClick={onRotate}
            aria-label="Rotate clockwise"
          >
            <RotateCw className="size-3.5" />
          </Button>

          {/* Fullscreen */}
          <Button
            variant="ghost"
            size="icon-xs"
            onClick={onFullscreen}
            aria-label="Enter fullscreen (F11)"
          >
            <Maximize className="size-3.5" />
          </Button>
        </div>
      </div>

      {/* Search Bar */}
      {showSearch && (
        <div className="flex items-center gap-2 border-b bg-muted/10 px-3 py-1.5">
          <Search className="size-3.5 text-muted-foreground shrink-0" />
          <input
            ref={searchInputRef}
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={handleSearchKeyDown}
            placeholder="Search within PDF..."
            className="flex-1 bg-transparent text-xs outline-none placeholder:text-muted-foreground/50"
            aria-label="Search text within PDF"
          />
          <span className="text-[10px] text-muted-foreground">
            {searchQuery ? "Enter to search" : "Ctrl+F"}
          </span>
          <Button
            variant="ghost"
            size="icon-xs"
            onClick={() => {
              setShowSearch(false);
              setSearchQuery("");
            }}
            aria-label="Close search"
          >
            <X className="size-3" />
          </Button>
        </div>
      )}
    </div>
  );
}

export default PDFToolbar;
