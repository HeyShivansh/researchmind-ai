"""
Utility functions for text chunking.

Provides the low-level splitting primitives used by chunker
implementations.
"""

from __future__ import annotations

from .exceptions import ChunkingError

# ---------------------------------------------------------------------------
# Default separator hierarchy for recursive splitting
# ---------------------------------------------------------------------------

SEPARATORS: list[str] = [
    "\n\n",
    "\n",
    ". ",
    "; ",
    ", ",
    " ",
]

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def recursive_split(
    text: str,
    chunk_size: int,
    separators: list[str] | None = None,
) -> list[tuple[str, int, int]]:
    """
    Recursively split *text* using the provided separator hierarchy.

    Separators are **preserved** and attached to the preceding segment
    (except for the final segment which has no trailing separator).
    This means concatenating all result texts reproduces the original
    text exactly.

    **Algorithm:**

    1. If *text* fits within *chunk_size*, return it as a single segment.
    2. Try splitting by the first separator (e.g. ``"\\n\\n"``).
    3. For each resulting piece:
       - If it fits within *chunk_size*, keep it.
       - Otherwise, recurse with the next separator in the list.
    4. If no separator remains, fall back to fixed-character splitting.

    **Complexity:** O(n × s) where n is the text length and s is the
    number of separator levels (typically 6).

    **Offset guarantee:** Each result tuple ``(text, start, end)``
    satisfies ``text == original[start:end]``, so offsets are always
    valid substrings of the input.

    Parameters
    ----------
    text : str
        The text to split.
    chunk_size : int
        Maximum number of characters per segment.
    separators : list[str] or None
        Ordered separator list.  Defaults to ``SEPARATORS``.

    Returns
    -------
    list[tuple[str, int, int]]
        A list of ``(chunk_text, start_offset, end_offset)`` tuples,
        where offsets are relative to *text*.
    """
    if not text:
        return []

    if len(text) <= chunk_size:
        return [(text, 0, len(text))]

    seps = separators if separators is not None else SEPARATORS
    return _recursive_split_impl(text, chunk_size, seps)


def greedy_merge(
    segments: list[tuple[str, int, int]],
    chunk_size: int,
) -> list[tuple[str, int, int]]:
    """
    Greedily merge adjacent segments until adding another would exceed
    *chunk_size*.

    This maximises chunk utilisation by packing as much text as
    possible into each chunk.

    **Invariant:** Every incoming *segment* is expected to already
    satisfy ``len(text) <= chunk_size`` (guaranteed by
    ``recursive_split``).  If a segment larger than *chunk_size* is
    encountered, a ``ChunkingError`` is raised to prevent silent
    oversized output.

    **Offset guarantee:** Each merged result tuple ``(text, start, end)``
    satisfies ``text == original[start:end]``, where the start is the
    first merged segment's start and the end is the last merged
    segment's end.

    Parameters
    ----------
    segments : list[tuple[str, int, int]]
        Segments from ``recursive_split``, each ≤ *chunk_size*.
    chunk_size : int
        Maximum number of characters per chunk.

    Returns
    -------
    list[tuple[str, int, int]]
        Merged chunks, each ≤ *chunk_size*.

    Raises
    ------
    ChunkingError
        If any incoming segment exceeds *chunk_size*.
    """
    if not segments:
        return []

    result: list[tuple[str, int, int]] = []
    current_text: list[str] = []
    current_start = segments[0][1]
    current_len = 0

    for seg_text, seg_start, seg_end in segments:
        seg_len = seg_end - seg_start

        if seg_len > chunk_size:
            raise ChunkingError(
                f"greedy_merge received a segment of size {seg_len} "
                f"which exceeds chunk_size {chunk_size}. "
                "All segments should already satisfy chunk_size."
            )

        if current_len + seg_len <= chunk_size:
            current_text.append(seg_text)
            current_len += seg_len
        else:
            if current_text:
                result.append((
                    "".join(current_text),
                    current_start,
                    current_start + current_len,
                ))
            current_text = [seg_text]
            current_start = seg_start
            current_len = seg_len

    if current_text:
        result.append((
            "".join(current_text),
            current_start,
            current_start + current_len,
        ))

    return result


def apply_overlap(
    original_text: str,
    chunks: list[tuple[str, int, int]],
    overlap: int,
) -> list[tuple[str, int, int]]:
    """
    Apply *overlap* characters between consecutive chunks.

    Each chunk (except the first) is extended backward by *overlap*
    characters into the previous chunk's region.  The extension point
    is expanded to the **nearest whitespace boundary** (searched up to
    ``2 × overlap`` characters backward) to avoid starting a chunk in
    the middle of a word.

    **Boundary guarantee:** If no whitespace is found within the
    search window, the original overlap-adjusted position is kept
    unchanged — the algorithm never expands more than ``2 × overlap``
    characters beyond the planned start.

    **Overlap guarantee:** Overlap is only applied within the same page.
    When *overlap* is ``0``, chunks are returned unchanged.

    Parameters
    ----------
    original_text : str
        The original (pre-split) page text.
    chunks : list[tuple[str, int, int]]
        Split results (after greedy merging).
    overlap : int
        Number of overlapping characters.

    Returns
    -------
    list[tuple[str, int, int]]
        Overlap-adjusted chunks.
    """
    if overlap <= 0 or len(chunks) <= 1:
        return chunks

    result: list[tuple[str, int, int]] = [chunks[0]]

    for i in range(1, len(chunks)):
        _, start, end = chunks[i]
        raw_start = max(0, start - overlap)
        word_start = _nearest_word_boundary(
            original_text, raw_start, max_distance=overlap * 2
        )
        new_text = original_text[word_start:end]
        result.append((new_text, word_start, end))

    return result


# ---------------------------------------------------------------------------
# Internal
# ---------------------------------------------------------------------------


def _recursive_split_impl(
    text: str,
    chunk_size: int,
    separators: list[str],
) -> list[tuple[str, int, int]]:
    """Recursive implementation of ``recursive_split``."""
    if len(text) <= chunk_size:
        return [(text, 0, len(text))]

    if not separators:
        return _char_split(text, chunk_size)

    sep = separators[0]
    remaining = separators[1:]
    segments = _split_with_separator(text, sep)
    result: list[tuple[str, int, int]] = []

    for seg_text, seg_start, seg_end in segments:
        seg_len = seg_end - seg_start

        if seg_len <= chunk_size:
            result.append((seg_text, seg_start, seg_end))
        elif remaining:
            sub_results = _recursive_split_impl(seg_text, chunk_size, remaining)
            for sub_text, sub_start, sub_end in sub_results:
                result.append((sub_text, seg_start + sub_start, seg_start + sub_end))
        else:
            sub_results = _char_split(seg_text, chunk_size)
            for sub_text, sub_start, sub_end in sub_results:
                result.append((sub_text, seg_start + sub_start, seg_start + sub_end))

    return result


def _split_with_separator(
    text: str,
    sep: str,
) -> list[tuple[str, int, int]]:
    """
    Split *text* by *sep*, preserving the separator.

    Each piece (except the last) includes the trailing separator so
    that concatenating all pieces reproduces the original text.

    Uses ``str.find`` to locate separators — this correctly handles
    consecutive separators, leading separators, and trailing
    separators (unlike a ``text.split``-based approach which loses
    trailing empty parts).

    Parameters
    ----------
    text : str
        The text to split.
    sep : str
        The separator string.

    Returns
    -------
    list[tuple[str, int, int]]
        ``(piece_text, start, end)`` for each piece.
    """
    if not sep:
        return [(text, 0, len(text))]

    result: list[tuple[str, int, int]] = []
    pos = 0
    sep_len = len(sep)

    while True:
        next_sep = text.find(sep, pos)
        if next_sep == -1:
            # No more separator — add remaining text (may be empty)
            if pos < len(text):
                result.append((text[pos:], pos, len(text)))
            break

        if next_sep == pos and not result:
            # Leading separator: emit it alone so offsets stay correct
            result.append((sep, 0, sep_len))
        else:
            # Text from current position to separator, WITH separator
            end = next_sep + sep_len
            segment = text[pos:end]
            result.append((segment, pos, end))

        pos = next_sep + sep_len

        # If the separator is at the very end, there's no trailing text
        if pos >= len(text):
            break

    return result


def _char_split(
    text: str,
    chunk_size: int,
) -> list[tuple[str, int, int]]:
    """Split *text* into fixed-size character chunks."""
    result: list[tuple[str, int, int]] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        result.append((text[start:end], start, end))
        start = end
    return result


def _nearest_word_boundary(text: str, start: int, max_distance: int = 100) -> int:
    """
    Find the nearest whitespace boundary at or before *start*.

    Searches up to *max_distance* characters backward.  If no boundary
    is found within the search window, returns the original *start*
    unchanged — guaranteeing that the expansion never exceeds
    *max_distance*.

    Parameters
    ----------
    text : str
        The original text.
    start : int
        Desired start position.
    max_distance : int
        Maximum number of characters to search backward (default 100).

    Returns
    -------
    int
        Adjusted start position at a word boundary, or *start* if none
        is found within the search window.
    """
    if start <= 0:
        return 0

    limit = max(0, start - max_distance)

    for pos in range(start, limit - 1, -1):
        if pos > 0 and text[pos - 1].isspace():
            return pos

    return start
