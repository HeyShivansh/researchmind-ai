"use client";

import { useState } from "react";
import { usePathname } from "next/navigation";
import { Sidebar } from "./sidebar";
import { TopNav } from "./top-nav";
import { RouteGuard } from "@/components/auth/route-guard";
import { cn } from "@/lib/utils";

// =============================================================================
// Main Application Layout
// =============================================================================

interface MainLayoutProps {
  children: React.ReactNode;
}

// Public routes that don't require authentication
const PUBLIC_ROUTES = ["/login", "/register"];

export function MainLayout({ children }: MainLayoutProps) {
  const pathname = usePathname();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  const toggleSidebar = () => {
    setSidebarCollapsed((prev) => !prev);
  };

  const isPublicRoute = PUBLIC_ROUTES.includes(pathname);

  // Public routes (login, register) — no sidebar, full-screen layout
  if (isPublicRoute) {
    return <>{children}</>;
  }

  return (
    <RouteGuard>
      <div className="relative min-h-screen bg-background">
        {/* Sidebar */}
        <Sidebar collapsed={sidebarCollapsed} onToggle={toggleSidebar} />

        {/* Main Content Area */}
        <div
          className={cn(
            "flex min-h-screen flex-col transition-all duration-300",
            sidebarCollapsed ? "md:ml-16" : "md:ml-60"
          )}
        >
          {/* Top Navigation */}
          <TopNav
            sidebarCollapsed={sidebarCollapsed}
            onMenuToggle={toggleSidebar}
          />

          {/* Page Content */}
          <main className="flex-1 p-4 md:p-6 lg:p-8">
            {children}
          </main>

          {/* Footer */}
          <footer className="border-t py-3 px-4 md:px-6 lg:px-8">
            <p className="text-center text-xs text-muted-foreground">
              ResearchMind AI &copy; {new Date().getFullYear()}
            </p>
          </footer>
        </div>
      </div>
    </RouteGuard>
  );
}

export default MainLayout;
