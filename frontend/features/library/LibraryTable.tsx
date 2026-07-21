"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Eye,
  Trash2,
  RefreshCw,
  Download,
  FileText,
  Library,
  AlertTriangle,
} from "lucide-react";
import type { Paper } from "@/types";
import { useRouter } from "next/navigation";

// =============================================================================
// Library Table
// =============================================================================

interface LibraryTableProps {
  papers: Paper[];
  isLoading: boolean;
  sortBy: string;
  searchQuery: string;
  onDelete: (id: string) => void;
  onReindex: (id: string) => void;
}

const statusConfig: Record<string, { label: string; variant: "default" | "outline" | "destructive" }> = {
  ready: { label: "Ready", variant: "default" as const },
  processing: { label: "Processing", variant: "outline" as const },
  error: { label: "Error", variant: "destructive" as const },
};

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays === 0) return "Today";
  if (diffDays === 1) return "Yesterday";
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export function LibraryTable({
  papers,
  isLoading,
  sortBy: _sortBy,
  searchQuery,
  onDelete,
  onReindex,
}: LibraryTableProps) {
  void _sortBy;
  const router = useRouter();
  const [deleteTarget, setDeleteTarget] = useState<Paper | null>(null);

  if (isLoading) {
    return (
      <div className="rounded-lg border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Title</TableHead>
              <TableHead className="hidden md:table-cell">Authors</TableHead>
              <TableHead className="hidden lg:table-cell">Year</TableHead>
              <TableHead className="hidden sm:table-cell">Pages</TableHead>
              <TableHead className="hidden lg:table-cell">Chunks</TableHead>
              <TableHead className="hidden md:table-cell">Uploaded</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {Array.from({ length: 5 }).map((_, i) => (
              <TableRow key={i}>
                {Array.from({ length: 8 }).map((_, j) => (
                  <TableCell key={j}>
                    <Skeleton className="h-4 w-full" />
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    );
  }

  if (papers.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center rounded-lg border">
        <div className="mb-4 flex size-14 items-center justify-center rounded-full bg-muted">
          <Library className="size-7 text-muted-foreground/50" />
        </div>
        <h3 className="text-base font-semibold">
          {searchQuery ? "No papers match your search" : "No papers yet"}
        </h3>
        <p className="mt-1 text-sm text-muted-foreground max-w-sm">
          {searchQuery
            ? "Try adjusting your search query or filters."
            : "Upload your first paper to get started."}
        </p>
      </div>
    );
  }

  return (
    <>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.3 }}
        className="rounded-lg border"
      >
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="min-w-[200px]">Title</TableHead>
              <TableHead className="min-w-[140px] hidden md:table-cell">
                Authors
              </TableHead>
              <TableHead className="w-16 hidden lg:table-cell">Year</TableHead>
              <TableHead className="w-16 hidden sm:table-cell">Pages</TableHead>
              <TableHead className="w-16 hidden lg:table-cell">Chunks</TableHead>
              <TableHead className="w-24 hidden md:table-cell">
                Uploaded
              </TableHead>
              <TableHead className="w-24">Status</TableHead>
              <TableHead className="w-24 text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {papers.map((paper, index) => {
              const statusKey = paper.status ?? "processing";
              const status = statusConfig[statusKey] ?? statusConfig.processing;

              return (
                <motion.tr
                  key={paper.id}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{
                    duration: 0.25,
                    delay: 0.03 * index,
                    ease: "easeOut",
                  }}
                  className="group/cell border-b transition-colors hover:bg-muted/30 cursor-pointer"
                  onClick={() => router.push(`/viewer/${paper.id}`)}
                >
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <div className="flex size-8 shrink-0 items-center justify-center rounded-md bg-muted">
                        <FileText className="size-4 text-muted-foreground" />
                      </div>
                      <div className="min-w-0">
                        <p className="text-sm font-medium truncate max-w-[200px] lg:max-w-[280px] group-hover/cell:text-primary transition-colors">
                          {paper.title}
                        </p>
                        <p className="text-[10px] text-muted-foreground truncate max-w-[200px] lg:hidden">
                          {paper.authors?.slice(0, 2).join(", ")}
                        </p>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell className="hidden md:table-cell">
                    <span className="text-xs text-muted-foreground">
                      {paper.authors?.slice(0, 2).join(", ")}
                      {(paper.authors?.length ?? 0) > 2 ? " et al." : ""}
                    </span>
                  </TableCell>
                  <TableCell className="hidden lg:table-cell">
                    <span className="text-xs tabular-nums text-muted-foreground">
                      {paper.created_at?.slice(0, 4)}
                    </span>
                  </TableCell>
                  <TableCell className="hidden sm:table-cell">
                    <span className="text-xs tabular-nums text-muted-foreground">
                      {paper.page_count ?? "-"}
                    </span>
                  </TableCell>
                  <TableCell className="hidden lg:table-cell">
                    <span className="text-xs tabular-nums text-muted-foreground">
                      {paper.chunk_count ?? "-"}
                    </span>
                  </TableCell>
                  <TableCell className="hidden md:table-cell">
                    <span className="text-xs text-muted-foreground whitespace-nowrap">
                      {formatDate(paper.created_at)}
                    </span>
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant={status.variant}
                      className={cn(
                        "text-[10px] px-1.5 py-0 h-5 font-normal",
                        paper.status === "processing" && "animate-pulse"
                      )}
                    >
                      {status.label}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div
                      className="flex items-center justify-end gap-1"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <Button
                        variant="ghost"
                        size="icon-xs"
                        onClick={() => router.push(`/viewer/${paper.id}`)}
                        aria-label="View paper"
                      >
                        <Eye className="size-3.5" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon-xs"
                        onClick={() => onReindex(paper.id)}
                        aria-label="Reindex paper"
                      >
                        <RefreshCw className="size-3.5" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon-xs"
                        onClick={() => {
                          const blob = new Blob(
                            [JSON.stringify(paper, null, 2)],
                            { type: "application/json" }
                          );
                          const url = URL.createObjectURL(blob);
                          const a = document.createElement("a");
                          a.href = url;
                          a.download = `${paper.id}-metadata.json`;
                          a.click();
                          URL.revokeObjectURL(url);
                        }}
                        aria-label="Download metadata"
                      >
                        <Download className="size-3.5" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon-xs"
                        onClick={() => setDeleteTarget(paper)}
                        aria-label="Delete paper"
                        className="hover:text-destructive"
                      >
                        <Trash2 className="size-3.5" />
                      </Button>
                    </div>
                  </TableCell>
                </motion.tr>
              );
            })}
          </TableBody>
        </Table>
      </motion.div>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={!!deleteTarget}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
      >
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <AlertTriangle className="size-4 text-destructive" />
              Delete Paper
            </DialogTitle>
            <DialogDescription>
              Are you sure you want to delete{" "}
              <span className="font-medium text-foreground">
                &ldquo;{deleteTarget?.title}&rdquo;
              </span>
              ? This will permanently remove the paper, all its chunks, and
              vector embeddings. This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="gap-2">
            <Button
              variant="outline"
              onClick={() => setDeleteTarget(null)}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={() => {
                if (deleteTarget) {
                  onDelete(deleteTarget.id);
                  setDeleteTarget(null);
                }
              }}
            >
              <Trash2 className="size-4 mr-1.5" />
              Delete Paper
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

export default LibraryTable;
