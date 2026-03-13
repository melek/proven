# Section Parser

## Data Structure

A **Section** has fields:
- `heading`: string (the heading text, or "preamble" for text before the first heading)
- `level`: integer in [0, 6] (0 = preamble, 1-6 = heading levels)
- `start`: non-negative integer (character offset, inclusive)
- `end`: non-negative integer (character offset, exclusive)

Input: `text`, a string of markdown content.
Output: a sequence of Section records (SectionList).

## Operations

1. **ParseSections(text: string) → SectionList**: Split `text` into sections at markdown heading boundaries. A markdown heading is a line that starts with one or more `#` characters followed by a space. The heading level is the count of `#` characters. Rules: (a) If `text` is empty, return an empty sequence. (b) If `text` has no headings, return a single Section with heading="preamble", level=0, start=0, end=|text|. (c) If text before the first heading is non-empty (after stripping whitespace), it becomes a preamble section. (d) Each heading starts a new section. The section's `start` is the character offset of the `#` character. The section's `end` is the `start` of the next section, or `|text|` for the last section. (e) The heading text is extracted by stripping the `#` prefix and leading/trailing whitespace.

2. **FindSectionsByPattern(sections: SectionList, patterns: sequence of strings) → SectionList**: Return sections whose heading matches any pattern (case-insensitive substring match). If no sections match, return an empty list.

## Properties to Prove

- **Coverage**: For non-empty text: the union of all [start, end) intervals equals [0, |text|). Formally: if |text| > 0 then sections[0].start == 0 AND sections[last].end == |text|.
- **Contiguity**: For adjacent sections i, i+1: sections[i].end == sections[i+1].start. No gaps, no overlaps.
- **Ordering**: For all i: sections[i].start < sections[i].end (non-empty sections). For all i < j: sections[i].start < sections[j].start (monotonic).
- **Heading level range**: For all sections: 0 <= level <= 6. Level 0 only for the preamble section (first section, if present and heading == "preamble").
- **Determinism**: Same input text → same output SectionList (pure function, no side effects).
- **FindSections subset**: FindSectionsByPattern returns a subsequence of the input SectionList (preserves order, no new elements).
