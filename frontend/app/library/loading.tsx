import { LibraryHeader } from "@/features/library";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

// =============================================================================
// Library Loading State
// =============================================================================

export default function LibraryLoading() {
  return (
    <div>
      <LibraryHeader />

      {/* Toolbar skeleton */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2 mb-4">
        <Skeleton className="h-9 w-full sm:max-w-sm" />
        <div className="flex items-center gap-2 w-full sm:w-auto">
          <Skeleton className="h-9 w-36" />
          <Skeleton className="h-9 w-20" />
          <Skeleton className="size-9 rounded-md" />
          <Skeleton className="h-9 w-24" />
        </div>
      </div>

      {/* Table skeleton */}
      <div className="rounded-lg border">
        <Table>
          <TableHeader>
            <TableRow>
              {["Title", "Authors", "Year", "Pages", "Chunks", "Uploaded", "Status", ""].map((h) => (
                <TableHead key={h}>{h}</TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {Array.from({ length: 6 }).map((_, i) => (
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
    </div>
  );
}
