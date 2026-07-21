"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  Menu,
  Moon,
  Sun,
  Bell,
  User,
  LogOut,
  Settings,
  ChevronDown,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { useTheme } from "@/providers/theme-provider";
import { useAuth } from "@/providers/auth-provider";
import { cn } from "@/lib/utils";

// =============================================================================
// Top Navigation Bar
// =============================================================================

interface TopNavProps {
  sidebarCollapsed: boolean;
  onMenuToggle: () => void;
}

export function TopNav({ sidebarCollapsed: _sidebarCollapsed, onMenuToggle }: TopNavProps) {
  void _sidebarCollapsed;
  const router = useRouter();
  const { theme, toggleTheme } = useTheme();
  const { user, logout, isAuthenticated } = useAuth();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown on click outside
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(e.target as Node)
      ) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const handleLogout = async () => {
    setDropdownOpen(false);
    await logout();
    router.push("/login");
  };

  return (
    <header
      className={cn(
        "sticky top-0 z-10 flex h-14 items-center justify-between border-b bg-background/80 backdrop-blur-md px-4 md:px-6"
      )}
    >
      {/* Left: Mobile Menu Toggle */}
      <div className="flex items-center gap-3">
        <Button
          variant="ghost"
          size="icon"
          onClick={onMenuToggle}
          className="md:hidden"
          aria-label="Toggle sidebar"
        >
          <Menu className="size-5" />
        </Button>
      </div>

      {/* Right: Actions */}
      <div className="flex items-center gap-2">
        {/* Notifications */}
        <Button
          variant="ghost"
          size="icon"
          className="relative"
          aria-label="Notifications"
        >
          <Bell className="size-5" />
          <span className="absolute -top-0.5 -right-0.5 flex size-4 items-center justify-center rounded-full bg-destructive text-[10px] font-medium text-destructive-foreground">
            0
          </span>
        </Button>

        {/* Theme Toggle */}
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleTheme}
          aria-label="Toggle theme"
        >
          {theme === "dark" ? (
            <Sun className="size-5" />
          ) : (
            <Moon className="size-5" />
          )}
        </Button>

        {/* User Profile Dropdown */}
        {isAuthenticated && user && (
          <div className="relative" ref={dropdownRef}>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setDropdownOpen(!dropdownOpen)}
              className="gap-2 px-2"
              aria-label="User menu"
            >
              <div className="flex size-7 items-center justify-center rounded-full bg-primary/10 text-primary">
                <User className="size-3.5" />
              </div>
              <span className="hidden text-xs font-medium sm:inline max-w-[100px] truncate">
                {user.username}
              </span>
              <ChevronDown className="size-3 text-muted-foreground" />
            </Button>

            {dropdownOpen && (
              <div className="absolute right-0 top-full mt-1 w-48 rounded-lg border bg-popover p-1 shadow-lg">
                <div className="border-b px-2.5 py-2">
                  <p className="text-xs font-medium truncate">
                    {user.username}
                  </p>
                  <p className="text-[10px] text-muted-foreground truncate">
                    {user.email}
                  </p>
                </div>
                <button
                  onClick={() => {
                    setDropdownOpen(false);
                    router.push("/settings");
                  }}
                  className="flex w-full items-center gap-2 rounded-md px-2.5 py-1.5 text-xs transition-colors hover:bg-muted"
                >
                  <Settings className="size-3.5" />
                  Settings
                </button>
                <button
                  onClick={handleLogout}
                  className="flex w-full items-center gap-2 rounded-md px-2.5 py-1.5 text-xs transition-colors hover:bg-destructive/10 hover:text-destructive"
                >
                  <LogOut className="size-3.5" />
                  Log out
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </header>
  );
}

export default TopNav;
