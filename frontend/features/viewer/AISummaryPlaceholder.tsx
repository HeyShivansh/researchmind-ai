"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Sparkles, Lightbulb } from "lucide-react";

// =============================================================================
// AI Summary Placeholder
// =============================================================================

/**
 * Placeholder component for future AI-generated paper summaries.
 * When answer generation is implemented, replace the placeholder content
 * with the actual AI summary and citations.
 */

export function AISummaryPlaceholder() {
  return (
    <Card className="overflow-hidden border-dashed">
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <div className="flex size-6 items-center justify-center rounded-md bg-gradient-to-br from-violet-500/20 to-violet-500/5">
            <Sparkles className="size-3.5 text-violet-500" />
          </div>
          <CardTitle className="text-sm font-medium">AI Summary</CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col items-center justify-center py-4 text-center">
          <Lightbulb className="size-8 text-muted-foreground/30 mb-2" />
          <p className="text-xs text-muted-foreground leading-relaxed max-w-[250px]">
            AI-generated summaries will appear here. They will synthesize
            retrieved chunks into a coherent overview with citations.
          </p>
        </div>
      </CardContent>
    </Card>
  );
}

export default AISummaryPlaceholder;
