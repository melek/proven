# Topological Sort with DAG Proof

## Overview
Topological sort produces a linear ordering of vertices in a directed acyclic graph such that for every edge (u, v), u appears before v in the ordering. The verification challenge combines graph representation invariants, DFS ghost state tracking, and a global ordering correctness property that quantifies over all edges. AlgoVeri reports near-zero LLM success on graph algorithms requiring ghost state.

## Data Structure
A directed graph represented as an adjacency list: a sequence of sequences, where graph[u] contains the list of vertices that u has edges to. Vertices are integers in the range [0, |graph|).

## Functions
1. **TopologicalSort(graph)**: Given a directed acyclic graph, return a sequence containing all vertices in a valid topological order. Precondition: the graph is well-formed and is a DAG.
2. **IsDAG(graph)**: Return whether the graph is a directed acyclic graph. Defined via the existence of a ranking function: a graph is a DAG if and only if there exists a function rank: vertex -> int such that for every edge (u, v), rank(u) < rank(v). This is equivalent to cycle freedom but avoids quantifying over unbounded paths, which is not directly expressible in first-order logic.

## Properties to Prove

### Graph validity
- **Well-formed adjacency list**: Every vertex referenced in any adjacency list is a valid vertex index (0 <= v < |graph|).

### DAG property
- **Ranking characterization**: IsDAG returns true if and only if there exists a ranking function rank: vertex -> int such that for every edge (u, v), rank(u) < rank(v). Note: self-loops and cycles are both ruled out by this definition.

### Topological order correctness
- **Completeness**: The output contains every vertex exactly once (it is a permutation of [0, |graph|)).
- **Ordering correctness**: For every edge (u, v) in the graph, u appears before v in the output sequence. Formally: for all u, v where v in graph[u], there exist indices i and j such that output[i] == u and output[j] == v and i < j.
- **No fabrication**: Every element in the output is a valid vertex index.

### Algorithm properties
- **Termination**: The algorithm terminates on all DAG inputs.

### Implementation hints (not formal properties)
The following are guidance for the implementation strategy, not properties to appear in the specification:
- **Ghost state**: A DFS-based approach requires tracking a visited set and a finish-order stack as ghost state. The visited set must satisfy: once a vertex is marked visited, it is never unmarked. The finish order must satisfy: a vertex is added only after all its descendants have been added.
- **DFS invariant**: At any point during DFS, for every visited vertex u and every edge (u, v), either v is already visited or v is currently being processed. This invariant supports proving ordering correctness.
