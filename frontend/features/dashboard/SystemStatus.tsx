"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Activity, CheckCircle, XCircle, Loader2 } from "lucide-react";
import type { SystemServiceStatus as SystemServiceStatusType } from "@/types";

// =============================================================================
// Service Status Item
// =============================================================================

interface ServiceItemProps {
  service: SystemServiceStatusType;
  index: number;
}

function ServiceItem({ service, index }: ServiceItemProps) {
  const statusConfig = {
    online: {
      icon: CheckCircle,
      color: "text-emerald-500",
      bg: "bg-emerald-500/10",
      badge: "default",
      label: "Online",
    },
    offline: {
      icon: XCircle,
      color: "text-red-500",
      bg: "bg-red-500/10",
      badge: "destructive",
      label: "Offline",
    },
    loading: {
      icon: Loader2,
      color: "text-amber-500",
      bg: "bg-amber-500/10",
      badge: "outline",
      label: "Loading",
    },
  };

  const config = statusConfig[service.status];
  const StatusIcon = config.icon;

  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.3, delay: 0.05 * index, ease: "easeOut" }}
      className="flex items-center justify-between rounded-lg px-3 py-2.5 transition-colors hover:bg-muted/50"
    >
      <div className="flex items-center gap-3">
        <div
          className={cn(
            "flex size-8 items-center justify-center rounded-full",
            config.bg
          )}
        >
          <StatusIcon
            className={cn(
              "size-4",
              config.color,
              service.status === "loading" && "animate-spin"
            )}
          />
        </div>
        <div>
          <p className="text-sm font-medium">{service.name}</p>
          {service.description && (
            <p className="text-xs text-muted-foreground">
              {service.description}
            </p>
          )}
        </div>
      </div>
      <div className="flex items-center gap-2">
        {service.latency && (
          <span className="hidden sm:inline text-xs text-muted-foreground tabular-nums">
            {service.latency}
          </span>
        )}
        <Badge
          variant={
            service.status === "online"
              ? "default"
              : service.status === "offline"
                ? "destructive"
                : "outline"
          }
          className="text-[10px] px-1.5 py-0 h-5"
        >
          {config.label}
        </Badge>
      </div>
    </motion.div>
  );
}

// =============================================================================
// System Status Skeleton
// =============================================================================

function SystemStatusSkeleton() {
  return (
    <div className="space-y-2">
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="flex items-center justify-between px-3 py-2.5">
          <div className="flex items-center gap-3">
            <Skeleton className="size-8 rounded-full" />
            <div className="space-y-1">
              <Skeleton className="h-4 w-28" />
              <Skeleton className="h-3 w-20" />
            </div>
          </div>
          <Skeleton className="h-5 w-14" />
        </div>
      ))}
    </div>
  );
}

// =============================================================================
// System Status Component
// =============================================================================

interface SystemStatusProps {
  services?: SystemServiceStatusType[];
  isLoading: boolean;
}

export function SystemStatus({ services, isLoading }: SystemStatusProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.2, ease: "easeOut" }}
    >
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Activity className="size-4 text-muted-foreground" />
              <CardTitle className="text-sm font-medium">
                System Status
              </CardTitle>
            </div>
            {services && (
              <div className="flex items-center gap-1.5">
                <span className="size-1.5 rounded-full bg-emerald-500" />
                <span className="text-xs text-muted-foreground">
                  {services.filter((s) => s.status === "online").length}/
                  {services.length} online
                </span>
              </div>
            )}
          </div>
        </CardHeader>
        <CardContent className="p-0 pb-3">
          {isLoading ? (
            <SystemStatusSkeleton />
          ) : (
            <div className="divide-y divide-border/50 px-1">
              {services?.map((service, index) => (
                <ServiceItem key={service.name} service={service} index={index} />
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}

export default SystemStatus;
