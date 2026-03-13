# Scholar Postconditions — Phase 4 (Extraction)

## Data Structure
Pure validation functions over parsed workspace data.

Input types:
- `included_paper`: record with `id` (string)
- `extraction`: record with `paper_id` (string), `source` (string: "full_text" or "abstract"), `fields` (sequence of field_entry)
- `field_entry`: record with `field_name` (string), `value` (string), `source_location` (string), `confidence` (string: "high", "medium", or "low")
- `concept`: record with `concept_id` (string), `definition` (string)
- `concept_matrix_exists`: boolean (whether concept-matrix.md exists and is non-empty)
- `phase_log_entry`: record with `event` (string), `phase` (integer), `saturation_metric` (rational or null)

## Operations
1. **CheckAllPapersExtracted(included, extractions)**: For every included paper, there exists at least one extraction with matching paper_id. Returns (satisfied, failures) listing unextracted paper ids.
2. **CheckExtractionSchemaValid(extractions)**: Every extraction has a source field that is "full_text" or "abstract". Every field_entry has non-null field_name, value, source_location, and confidence. Confidence must be one of "high", "medium", "low". Returns (satisfied, failures).
3. **CheckConceptsNonEmpty(concepts)**: concepts sequence has length > 0. Returns (satisfied, failures).
4. **CheckConceptMatrixExists(concept_matrix_exists)**: concept_matrix_exists is true. Returns (satisfied, failures).
5. **CheckAllConceptsDefined(extractions, concepts)**: Every concept_id referenced in any extraction's concepts_identified list exists in the concepts sequence with a non-empty definition. Returns (satisfied, failures) listing undefined concept ids.
6. **CheckSaturationComputed(phase_log)**: There exists a phase_log_entry with event == "saturation_check" and phase == 4 and saturation_metric is non-null. Returns (satisfied, failures).
7. **CheckPhase4All(included, extractions, concepts, concept_matrix_exists, phase_log)**: Runs checks 1–6. Returns (satisfied, failures).

## Properties to Prove
- **Soundness**: If CheckPhase4All returns satisfied == true, all six individual checks pass.
- **Completeness**: If any check fails, CheckPhase4All returns satisfied == false with non-empty failures.
- **Determinism**: Same inputs produce the same output.
- **All operations are read-only**: No operation modifies its inputs.
