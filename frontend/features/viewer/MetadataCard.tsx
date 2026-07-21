"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  BookOpen,
  Calendar,
  Hash,
  Database,
  HardDrive,
  Clock,
  User,
  Tags,
} from "lucide-react";
import type { ViewerPaper } from "@/types";

// =============================================================================
// Metadata Card
// =============================================================================

interface MetadataCardProps {
  paper: ViewerPaper;
}

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function MetadataCard({ paper }: MetadataCardProps) {
  return (
    <Card className="overflow-hidden">
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <BookOpen className="size-4 text-muted-foreground" />
          <CardTitle className="text-sm font-medium">
            Paper Information
          </CardTitle>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Title */}
        <div>
          <p className="text-sm font-semibold leading-snug">{paper.title}</p>
          <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
            <User className="size-3 shrink-0" />
            {paper.authors.join(", ")}
          </p>
        </div>

        <Separator />

        {/* Metadata Grid */}
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="flex items-center gap-1.5 text-muted-foreground">
            <Calendar className="size-3.5 shrink-0" />
            <span>Published {paper.year}</span>
          </div>
          <div className="flex items-center gap-1.5 text-muted-foreground">
            <Hash className="size-3.5 shrink-0" />
            <span>{paper.page_count} pages</span>
          </div>
          <div className="flex items-center gap-1.5 text-muted-foreground">
            <Database className="size-3.5 shrink-0" />
            <span>{paper.chunk_count} chunks</span>
          </div>
          <div className="flex items-center gap-1.5 text-muted-foreground">
            <HardDrive className="size-3.5 shrink-0" />
            <span>{formatBytes(paper.file_size)}</span>
          </div>
        </div>

        {paper.doi && (
          <div className="text-xs text-muted-foreground">
            <span className="font-medium">DOI:</span> {paper.doi}
          </div>
        )}

        <Separator />

        {/* Embedding Model */}
        <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <Database className="size-3.5 shrink-0" />
          <span>Embedding: {paper.embedding_model}</span>
        </div>

        <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <Clock className="size-3.5 shrink-0" />
          <span>Uploaded {formatDate(paper.upload_date)}</span>
        </div>

        {/* Keywords */}
        {paper.keywords.length > 0 && (
          <>
            <Separator />
            <div className="flex items-start gap-1.5 text-xs">
              <Tags className="size-3.5 shrink-0 text-muted-foreground mt-0.5" />
              <div className="flex flex-wrap gap-1">
                {paper.keywords.map((kw) => (
                  <Badge
                    key={kw}
                    variant="secondary"
                    className="text-[10px] px-1.5 py-0 h-4 font-normal"
                  >
                    {kw}
                  </Badge>
                ))}
              </div>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}

export default MetadataCard;
