"use client";

import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Clock, FileText } from "lucide-react";
import { cn } from "@/lib/utils";
import type { RecentUpload } from "@/types";

// =============================================================================
// Recent Uploads Table
// =============================================================================

interface RecentUploadsTableProps {
  uploads?: RecentUpload[];
  isLoading: boolean;
}

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function getRelativeTime(dateString: string): string {
  const now = new Date();
  const date = new Date(dateString);
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays === 0) return "Today";
  if (diffDays === 1) return "Yesterday";
  return `${diffDays} days ago`;
}

const statusBadge = {
  ready: { label: "Ready", variant: "default" as const },
  processing: { label: "Processing", variant: "outline" as const },
  error: { label: "Error", variant: "destructive" as const },
};

export function RecentUploadsTable({
  uploads,
  isLoading,
}: RecentUploadsTableProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.3, ease: "easeOut" }}
    >
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Clock className="size-4 text-muted-foreground" />
            <CardTitle className="text-sm font-medium">
              Recent Uploads
            </CardTitle>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="space-y-3 px-4 pb-4">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="flex items-center justify-between">
                  <div className="space-y-1">
                    <Skeleton className="h-4 w-48" />
                    <Skeleton className="h-3 w-24" />
                  </div>
                  <Skeleton className="h-5 w-16" />
                </div>
              ))}
            </div>
          ) : !uploads || uploads.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <FileText className="size-8 text-muted-foreground/50 mb-2" />
              <p className="text-sm text-muted-foreground">No uploads yet</p>
            </div>
          ) : (
            <div className="divide-y divide-border/50">
              {uploads.map((upload, index) => (
                <motion.div
                  key={upload.id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{
                    duration: 0.3,
                    delay: 0.05 * index,
                    ease: "easeOut",
                  }}
                  className="flex items-center justify-between px-4 py-3 transition-colors hover:bg-muted/30"
                >
                  <div className="min-w-0 flex-1 mr-4">
                    <p className="text-sm font-medium truncate">
                      {upload.title}
                    </p>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className="text-xs text-muted-foreground">
                        {formatDate(upload.upload_date)}
                      </span>
                      <span className="text-[10px] text-muted-foreground/50">
                        &middot;
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {upload.pages} pages &middot; {upload.chunks} chunks
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className="hidden sm:inline text-[11px] text-muted-foreground tabular-nums">
                      {getRelativeTime(upload.upload_date)}
                    </span>
                    <Badge
                      variant={statusBadge[upload.status].variant}
                      className={cn(
                        "text-[10px] px-1.5 py-0 h-5",
                        upload.status === "processing" &&
                          "animate-pulse"
                      )}
                    >
                      {statusBadge[upload.status].label}
                    </Badge>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}

export default RecentUploadsTable;
