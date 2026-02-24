# Red-Black Tree Insert

## Overview
A red-black tree is a self-balancing binary search tree with coloring constraints that guarantee O(log n) height. Insertion requires maintaining four simultaneous invariants through rotation and recoloring operations. This is one of the hardest standard data structure verification problems — AlgoVeri reports near-zero LLM success on advanced data structures with complex invariants.

## Data Structure
A binary tree where each node stores an integer key, a color (red or black), and references to left and right children. The tree may be represented as an algebraic datatype (Leaf | Node) or with explicit null sentinels.

## Operations
1. **Insert(key)**: Insert a key into the tree, maintaining all red-black invariants. If the key already exists, the tree is unchanged.
2. **Contains(key)**: Return whether the key exists in the tree.
3. **Valid()**: Return whether the tree satisfies all red-black invariants.

## Properties to Prove

### BST invariant
- **Ordering**: For every node, all keys in the left subtree are strictly less than the node's key, and all keys in the right subtree are strictly greater.
- **Contains correctness**: Contains returns true if and only if the key exists in the tree.

### Red-black invariants (all four must hold simultaneously)
- **Node coloring**: Every node is either red or black.
- **Root is black**: The root of the tree is always black.
- **Red property**: A red node has no red children (no two consecutive red nodes on any path).
- **Black-height property**: Every path from any node to a descendant leaf passes through the same number of black nodes. This quantity (the "black height") is uniform across the tree.

### Insertion properties
- **Invariant preservation**: After Insert, all four red-black invariants still hold.
- **Content preservation**: Insert adds exactly the new key. All previously existing keys remain, and no other keys are added.
- **Idempotence**: Inserting an already-present key does not change the tree.

### Rotation correctness (the hard part)
- **Left rotation preserves BST ordering**: After rotating, the in-order traversal is unchanged.
- **Right rotation preserves BST ordering**: Same for right rotation.
- **Recoloring restores red property**: After insertion may temporarily violate the red property; fix-up via rotations and recoloring restores it.
- **Fix-up preserves black-height**: Rotations and recoloring do not change the black height of any subtree (except possibly at the root).
