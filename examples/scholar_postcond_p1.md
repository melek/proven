# Scholar Postconditions — Phase 1 (Search)

## Data Structure
Pure validation functions over parsed workspace data. Each check function returns a record with `satisfied` (boolean) and `failures` (sequence of strings describing what failed).

Input types:
- `protocol_query`: record with `database` (string) and `query` (string)
- `search_log_entry`: record with `database` (string) and `query` (string)
- `candidate`: record with `id` (string), `title` (string or null), `abstract` (string or null), `authors` (sequence of strings, possibly empty), `year` (integer or null)

## Operations
1. **CheckAllQueriesExecuted(protocol_queries, search_log)**: For every protocol_query, there exists at least one search_log_entry with matching database and query. Returns (satisfied, failures) where failures lists any unmatched (database, query) pairs.
2. **CheckCandidatesNonEmpty(candidates)**: candidates sequence has length > 0. Returns (satisfied, failures).
3. **CheckNoDuplicateIds(candidates)**: No two candidates share the same id. Returns (satisfied, failures) where failures lists duplicate ids found.
4. **CheckMinimumMetadata(candidates)**: Every candidate has non-null id, title, abstract, authors (non-empty), and year. Returns (satisfied, failures) where failures lists candidate ids missing required fields.
5. **CheckPhase1All(protocol_queries, search_log, candidates)**: Runs checks 1–4. Returns (satisfied, failures) where satisfied is true only if all four checks pass, and failures is the concatenation of all individual failure lists.

## Properties to Prove
- **Soundness**: If CheckPhase1All returns satisfied == true, then all four individual checks return satisfied == true.
- **Completeness**: If any individual check returns satisfied == false, then CheckPhase1All returns satisfied == false and its failures list is non-empty.
- **Determinism**: Same inputs produce the same (satisfied, failures) output.
- **All operations are read-only**: No operation modifies its inputs.
