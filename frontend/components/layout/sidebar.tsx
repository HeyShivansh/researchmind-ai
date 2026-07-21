"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Upload,
  Library,
  Search,
  Settings,
  ChevronLeft,
  Brain,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { useIsMobile } from "@/hooks";
import type { NavItem } from "@/types";

// =============================================================================
// Sidebar Component
// =============================================================================

const navItems: NavItem[] = [
  { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { label: "Upload Papers", href: "/upload", icon: Upload },
  { label: "Paper Library", href: "/library", icon: Library },
  { label: "Search", href: "/search", icon: Search },
  { label: "Settings", href: "/settings", icon: Settings },
];

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

export function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const pathname = usePathname();
  const isMobile = useIsMobile();

  return (
    <TooltipProvider>
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-30 flex flex-col border-r bg-sidebar transition-all duration-300 ease-in-out",
          collapsed ? "w-16" : "w-60",
          isMobile && collapsed ? "-translate-x-full" : "translate-x-0"
        )}
      >
        {/* Logo Area */}
        <div
          className={cn(
            "flex h-14 items-center border-b px-4 transition-all duration-300",
            collapsed ? "justify-center" : "gap-3"
          )}
        >
          <div className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <Brain className="size-5" />
          </div>
          {!collapsed && (
            <span className="text-sm font-semibold tracking-tight whitespace-nowrap">
              ResearchMind
            </span>
          )}
        </div>

        {/* Navigation */}
        <nav className="flex-1 space-y-1 p-2">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            const Icon = item.icon;

            return collapsed ? (
              <Tooltip key={item.href}>
                <TooltipTrigger>
                  <Link
                    href={item.href}
                    className={cn(
                      "flex size-11 items-center justify-center rounded-lg transition-colors",
                      isActive
                        ? "bg-sidebar-accent text-sidebar-accent-foreground"
                        : "text-sidebar-foreground/70 hover:bg-sidebar-accent/50 hover:text-sidebar-foreground"
                    )}
                  >
                    <Icon className="size-5" />
                  </Link>
                </TooltipTrigger>
                <TooltipContent side="right" className="ml-1">
                  {item.label}
                </TooltipContent>
              </Tooltip>
            ) : (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-sidebar-accent text-sidebar-accent-foreground"
                    : "text-sidebar-foreground/70 hover:bg-sidebar-accent/50 hover:text-sidebar-foreground"
                )}
              >
                <Icon className="size-5 shrink-0" />
                <span className="truncate">{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Collapse Toggle (Desktop) */}
        <div className="hidden p-2 md:block">
          <Separator className="mb-2" />
          <Button
            variant="ghost"
            size="sm"
            onClick={onToggle}
            className={cn(
              "w-full transition-all",
              collapsed ? "justify-center px-0" : "justify-start gap-2"
            )}
          >
            <ChevronLeft
              className={cn(
                "size-4 transition-transform",
                collapsed && "rotate-180"
              )}
            />
            {!collapsed && <span className="text-xs">Collapse</span>}
          </Button>
        </div>
      </aside>

      {/* Mobile Overlay */}
      {isMobile && !collapsed && (
        <div
          className="fixed inset-0 z-20 bg-black/50 backdrop-blur-sm"
          onClick={onToggle}
        />
      )}
    </TooltipProvider>
  );
}

export default Sidebar;
