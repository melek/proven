# Scholar Postconditions — Phase 5 (Synthesis)

## Data Structure
Pure validation functions over parsed workspace data.

Input types:
- `included_paper`: record with `id` (string), `bibtex_key` (string)
- `review_citation_keys`: set of strings (unique `[@...]` citation keys found in review.md, excluding backtick-escaped occurrences)
- `review_section_headers`: set of strings (section headers found in review.md)
- `protocol_question`: string (a sub-question from the protocol)
- `question_answer`: record with `question` (string), `section` (string), `disposition` (string: "answered", "partially_answered", or "identified_as_gap")
- `bib_entry_count`: non-negative integer (number of entries in references.bib)
- `appendix_a_row_count`: non-negative integer (data rows in Appendix A table)
- `included_count`: non-negative integer (records in included.jsonl)

## Operations
1. **CheckAllPapersCited(included, review_citation_keys)**: For every included paper, either paper.id or paper.bibtex_key appears in review_citation_keys. Returns (satisfied, failures) listing uncited paper ids.
2. **CheckAllQuestionsAddressed(protocol_questions, question_answers)**: For every protocol question, there exists a question_answer with matching question text and disposition in {"answered", "partially_answered", "identified_as_gap"}. Returns (satisfied, failures).
3. **CheckQuestionAnswersComplete(protocol_questions, question_answers)**: question_answers has an entry for every protocol question. Returns (satisfied, failures).
4. **CheckBibliographyConsistent(bib_entry_count, review_citation_keys)**: bib_entry_count equals the size of review_citation_keys. Returns (satisfied, failures).
5. **CheckReviewStructure(review_section_headers)**: review_section_headers contains all required headers: "Abstract", "Introduction", "Methodology", "Results", "Discussion", "Conclusion", "References", "Appendix A", "Appendix B". Returns (satisfied, failures) listing missing headers.
6. **CheckAppendixRowCount(appendix_a_row_count, included_count)**: appendix_a_row_count equals included_count. Returns (satisfied, failures).
7. **CheckPhase5All(included, review_citation_keys, review_section_headers, protocol_questions, question_answers, bib_entry_count, appendix_a_row_count, included_count)**: Runs checks 1–6. Returns (satisfied, failures).

## Properties to Prove
- **Soundness**: If CheckPhase5All returns satisfied == true, all six individual checks pass.
- **Completeness**: If any check fails, CheckPhase5All returns satisfied == false with non-empty failures.
- **Determinism**: Same inputs produce the same output.
- **All operations are read-only**: No operation modifies its inputs.
