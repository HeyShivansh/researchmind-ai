import { redirect } from "next/navigation";

// =============================================================================
// Root Page - Redirect to Dashboard
// =============================================================================

export default function RootPage() {
  redirect("/dashboard");
}
