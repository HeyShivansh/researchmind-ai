// =============================================================================
// Keyword Highlighting Utility
// =============================================================================

/**
 * Splits text into segments, highlighting words that match the query keywords.
 * Words shorter than 3 characters are ignored to prevent highlighting noise.
 *
 * Used by SearchResultCard and SearchPreview components.
 */

export function highlightKeywords(
  text: string,
  query: string
): React.ReactNode[] {
  if (!query.trim()) return [text];

  const words = query
    .toLowerCase()
    .split(/\s+/)
    .filter((w) => w.length > 2);

  if (words.length === 0) return [text];

  const escaped = words.map((w) => w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
  const regex = new RegExp(`(${escaped.join("|")})`, "gi");

  const parts = text.split(regex);
  return parts.map((part, i) => {
    const lower = part.toLowerCase();
    const isMatch = words.some((w) => lower === w);
    return isMatch ? (
      <mark
        key={i}
        className="rounded-sm bg-primary/20 text-foreground px-0.5 -mx-0.5"
      >
        {part}
      </mark>
    ) : (
      <span key={i}>{part}</span>
    );
  });
}
