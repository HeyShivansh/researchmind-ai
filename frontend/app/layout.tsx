import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { AppProviders } from "@/providers";
import { MainLayout } from "@/components/layout";
import { Toaster } from "@/components/ui/sonner";

// =============================================================================
// Font Configuration
// =============================================================================

const inter = Inter({
  variable: "--font-sans",
  subsets: ["latin"],
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
});

// =============================================================================
// Metadata
// =============================================================================

export const metadata: Metadata = {
  title: {
    default: "ResearchMind AI",
    template: "%s | ResearchMind AI",
  },
  description:
    "Enterprise-grade Retrieval-Augmented Generation (RAG) platform for scientific literature.",
};

// =============================================================================
// Root Layout
// =============================================================================

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${jetbrainsMono.variable} dark`}
      suppressHydrationWarning
    >
      <body className="min-h-screen antialiased">
        <AppProviders>
          <MainLayout>{children}</MainLayout>
          <Toaster richColors closeButton />
        </AppProviders>
      </body>
    </html>
  );
}
