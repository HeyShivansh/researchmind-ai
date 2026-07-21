"use client";

import { motion } from "framer-motion";
import { useRouter } from "next/navigation";
import { cn } from "@/lib/utils";
import { ArrowRight } from "lucide-react";
import type { QuickAction } from "@/types";

// =============================================================================
// Quick Actions
// =============================================================================

interface QuickActionsProps {
  actions: QuickAction[];
}

const colorMap: Record<string, { bg: string; ring: string; icon: string }> = {
  blue: {
    bg: "bg-blue-500/10",
    ring: "group-hover/card:ring-blue-500/30",
    icon: "text-blue-500",
  },
  violet: {
    bg: "bg-violet-500/10",
    ring: "group-hover/card:ring-violet-500/30",
    icon: "text-violet-500",
  },
  emerald: {
    bg: "bg-emerald-500/10",
    ring: "group-hover/card:ring-emerald-500/30",
    icon: "text-emerald-500",
  },
  amber: {
    bg: "bg-amber-500/10",
    ring: "group-hover/card:ring-amber-500/30",
    icon: "text-amber-500",
  },
};

export function QuickActions({ actions }: QuickActionsProps) {
  const router = useRouter();

  return (
    <div className="grid gap-3 sm:grid-cols-2">
      {actions.map((action, index) => {
        const colors = colorMap[action.color] ?? colorMap.blue;
        const Icon = action.icon;

        return (
          <motion.button
            key={action.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{
              duration: 0.4,
              delay: 0.4 + 0.08 * index,
              ease: "easeOut",
            }}
            onClick={() => router.push(action.href)}
            className={cn(
              "group/card relative flex items-start gap-4 rounded-xl border bg-card p-4 text-left transition-all duration-300 hover:shadow-lg hover:-translate-y-0.5 cursor-pointer ring-1 ring-foreground/10",
              colors.ring
            )}
          >
            {/* Icon */}
            <div
              className={cn(
                "flex size-10 shrink-0 items-center justify-center rounded-lg transition-colors",
                colors.bg
              )}
            >
              <Icon className={cn("size-5", colors.icon)} />
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between gap-2">
                <h3 className="text-sm font-semibold">{action.label}</h3>
                <ArrowRight className="size-4 shrink-0 text-muted-foreground/40 transition-all duration-300 group-hover/card:translate-x-0.5 group-hover/card:text-muted-foreground" />
              </div>
              <p className="mt-1 text-xs text-muted-foreground leading-relaxed">
                {action.description}
              </p>
            </div>
          </motion.button>
        );
      })}
    </div>
  );
}

export default QuickActions;
