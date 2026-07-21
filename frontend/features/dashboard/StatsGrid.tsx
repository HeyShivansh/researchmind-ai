"use client";

import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  BookOpen,
  FileText,
  Database,
  Layers,
} from "lucide-react";
import type { DashboardData } from "@/types";

// =============================================================================
// Stats Card
// =============================================================================

interface StatItemProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  description: string;
  index: number;
}

function StatItem({ title, value, icon, description, index }: StatItemProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.1 * index, ease: "easeOut" }}
    >
      <Card className="group/card relative overflow-hidden transition-all duration-300 hover:shadow-lg hover:-translate-y-0.5">
        {/* Gradient accent bar */}
        <div className="absolute inset-x-0 top-0 h-0.5 bg-gradient-to-r from-primary/50 to-primary/20 opacity-0 transition-opacity duration-300 group-hover/card:opacity-100" />

        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            {title}
          </CardTitle>
          <div className="text-muted-foreground/60 transition-colors duration-300 group-hover/card:text-primary">
            {icon}
          </div>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold tracking-tight">{value}</div>
          <p className="mt-1 text-xs text-muted-foreground">{description}</p>
        </CardContent>
      </Card>
    </motion.div>
  );
}

// =============================================================================
// Stats Card Skeleton
// =============================================================================

function StatCardSkeleton() {
  return (
    <Card>
      <CardHeader className="pb-2">
        <Skeleton className="h-4 w-24" />
      </CardHeader>
      <CardContent>
        <Skeleton className="h-8 w-16 mb-2" />
        <Skeleton className="h-3 w-32" />
      </CardContent>
    </Card>
  );
}

// =============================================================================
// Stats Grid
// =============================================================================

interface StatsGridProps {
  data?: DashboardData;
  isLoading: boolean;
}

export function StatsGrid({ data, isLoading }: StatsGridProps) {
  if (isLoading) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-8">
        {Array.from({ length: 4 }).map((_, i) => (
          <StatCardSkeleton key={i} />
        ))}
      </div>
    );
  }

  const stats = data?.stats;

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-8">
      <StatItem
        title="Total Papers"
        value={stats?.total_papers ?? 0}
        icon={<BookOpen className="size-4" />}
        description="Papers in your library"
        index={0}
      />
      <StatItem
        title="Indexed Chunks"
        value={(stats?.total_chunks ?? 0).toLocaleString()}
        icon={<FileText className="size-4" />}
        description="Text segments indexed"
        index={1}
      />
      <StatItem
        title="Stored Embeddings"
        value={(stats?.total_chunks ?? 0).toLocaleString()}
        icon={<Database className="size-4" />}
        description="Vector embeddings in Qdrant"
        index={2}
      />
      <StatItem
        title="Qdrant Collection"
        value={stats?.papers_processing === 0 ? "Synced" : "Indexing"}
        icon={<Layers className="size-4" />}
        description={
          stats?.papers_processing
            ? `${stats.papers_processing} papers processing`
            : "All papers indexed"
        }
        index={3}
      />
    </div>
  );
}

export default StatsGrid;
