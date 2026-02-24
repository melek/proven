# Topological Sort with DAG Proof

## Overview
Topological sort produces a linear ordering of vertices in a directed acyclic graph such that for every edge (u, v), u appears before v in the ordering. The verification challenge combines graph representation invariants, DFS ghost state tracking, and a global ordering correctness property that quantifies over all edges. AlgoVeri reports near-zero LLM success on graph algorithms requiring ghost state.

## Data Structure
A directed graph represented as an adjacency list: a sequence of sequences, where graph[u] contains the list of vertices that u has edges to. Vertices are integers in the range [0, |graph|).

## Functions
1. **TopologicalSort(graph)**: Given a directed acyclic graph, return a sequence containing all vertices in a valid topological order. The graph must be a DAG (no cycles).
2. **IsDAG(graph)**: Return whether the graph contains no directed cycles.

## Properties to Prove

### Graph validity
- **Well-formed adjacency list**: Every vertex referenced in any adjacency list is a valid vertex index (0 <= v < |graph|).
- **No self-loops**: No vertex has an edge to itself (required for DAG property).

### DAG property
- **Cycle freedom**: IsDAG returns true if and only if there is no sequence of edges forming a directed cycle. Formally: there is no sequence v0, v1, ..., vk where each (vi, vi+1) is an edge and v0 == vk.

### Topological order correctness
- **Completeness**: The output contains every vertex exactly once (it is a permutation of [0, |graph|)).
- **Ordering correctness**: For every edge (u, v) in the graph, u appears before v in the output sequence. Formally: for all u, v where v in graph[u], indexOf(output, u) < indexOf(output, v).
- **No fabrication**: Every element in the output is a valid vertex index.

### Algorithm properties
- **Termination**: The algorithm terminates on all DAG inputs.
- **Ghost state**: The DFS-based algorithm requires tracking a visited set and a finish-order stack as ghost state. The visited set must satisfy: once a vertex is marked visited, it is never unmarked. The finish order must satisfy: a vertex is pushed to the stack only after all its descendants have been pushed.
- **DFS invariant**: At any point during DFS, for every visited vertex u and every edge (u, v), either v is already visited or v is currently on the DFS stack (being processed). This invariant is needed to prove cycle detection and ordering correctness.
