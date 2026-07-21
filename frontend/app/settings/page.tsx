"use client";

import { useRouter } from "next/navigation";
import { useTheme } from "@/providers/theme-provider";
import { useAuth } from "@/providers/auth-provider";
import { PageHeader } from "@/components/common";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Moon,
  Sun,
  Monitor,
  User,
  Globe,
  Trash2,
  AlertTriangle,
  Check,
  Copy,
} from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

// =============================================================================
// Settings Page
// =============================================================================

export default function SettingsPage() {
  const router = useRouter();
  const { theme, setTheme } = useTheme();
  const { user, logout } = useAuth();
  const [copied, setCopied] = useState(false);

  const copyUserId = async () => {
    if (user?.id) {
      await navigator.clipboard.writeText(user.id);
      setCopied(true);
      toast.success("User ID copied to clipboard");
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleLogoutAll = async () => {
    await logout();
    router.push("/login");
  };

  return (
    <div>
      <PageHeader
        title="Settings"
        description="Manage your account and application preferences"
      />

      <div className="space-y-6 max-w-2xl">
        {/* Appearance */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Monitor className="size-4 text-muted-foreground" />
              <CardTitle className="text-sm font-medium">Appearance</CardTitle>
            </div>
            <CardDescription className="text-xs">
              Customize how ResearchMind AI looks on your device
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="theme-select" className="text-xs text-muted-foreground">
                Theme
              </Label>
              <Select value={theme} onValueChange={(v) => v && setTheme(v as "dark" | "light")}>
                <SelectTrigger id="theme-select" className="w-full sm:w-48">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="dark">
                    <div className="flex items-center gap-2">
                      <Moon className="size-3.5" />
                      Dark Mode
                    </div>
                  </SelectItem>
                  <SelectItem value="light">
                    <div className="flex items-center gap-2">
                      <Sun className="size-3.5" />
                      Light Mode
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* Profile */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <User className="size-4 text-muted-foreground" />
              <CardTitle className="text-sm font-medium">Profile</CardTitle>
            </div>
            <CardDescription className="text-xs">
              Your account information
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-1">
                <Label className="text-xs text-muted-foreground">Username</Label>
                <p className="text-sm font-medium">{user?.username ?? "—"}</p>
              </div>
              <div className="space-y-1">
                <Label className="text-xs text-muted-foreground">Email</Label>
                <p className="text-sm font-medium">{user?.email ?? "—"}</p>
              </div>
            </div>
            <div className="space-y-1">
              <Label className="text-xs text-muted-foreground">User ID</Label>
              <div className="flex items-center gap-2">
                <code className="rounded-md bg-muted px-2 py-1 text-xs font-mono text-muted-foreground truncate max-w-[200px] sm:max-w-sm">
                  {user?.id ?? "—"}
                </code>
                <Button
                  variant="ghost"
                  size="icon-xs"
                  onClick={copyUserId}
                  aria-label="Copy user ID"
                >
                  {copied ? (
                    <Check className="size-3.5 text-emerald-500" />
                  ) : (
                    <Copy className="size-3.5" />
                  )}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* API Connection */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Globe className="size-4 text-muted-foreground" />
              <CardTitle className="text-sm font-medium">API Connection</CardTitle>
            </div>
            <CardDescription className="text-xs">
              Backend service configuration
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-1">
              <Label className="text-xs text-muted-foreground">API Base URL</Label>
              <p className="text-sm font-mono text-muted-foreground">
                {typeof window !== "undefined"
                  ? process.env.NEXT_PUBLIC_API_BASE_URL ??
                    process.env.NEXT_PUBLIC_API_URL ??
                    "http://localhost:8000"
                  : "—"}
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Danger Zone */}
        <Card className="border-destructive/30">
          <CardHeader>
            <div className="flex items-center gap-2">
              <AlertTriangle className="size-4 text-destructive" />
              <CardTitle className="text-sm font-medium text-destructive">
                Danger Zone
              </CardTitle>
            </div>
            <CardDescription className="text-xs">
              Irreversible account actions
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between rounded-lg border border-destructive/20 bg-destructive/5 p-4">
              <div className="space-y-0.5">
                <p className="text-sm font-medium">Log out of all sessions</p>
                <p className="text-xs text-muted-foreground">
                  This will clear your current session and require you to log in again.
                </p>
              </div>
              <Button
                variant="destructive"
                size="sm"
                onClick={handleLogoutAll}
                className="gap-2 shrink-0 ml-4"
              >
                <Trash2 className="size-3.5" />
                Log Out
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
