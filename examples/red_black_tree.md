# Red-Black Tree Insert

## Overview
A red-black tree is a self-balancing binary search tree with coloring constraints that guarantee O(log n) height. Insertion requires maintaining four simultaneous invariants through rotation and recoloring operations. This is one of the hardest standard data structure verification problems — AlgoVeri reports near-zero LLM success on advanced data structures with complex invariants.

## Data Structure
An algebraic datatype with two constructors: `Leaf` (empty tree) and `Node(left, key, color, right)`. Each node stores an integer key, a color (red or black), and left and right subtrees. Leaves are considered black for the purpose of the black-height property.

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
- **Black-height property**: For any node, every path from that node to a descendant `Leaf` passes through the same number of black nodes. Leaves themselves do not contribute to the count. This quantity (the "black height") must be uniform across all paths from the root.

### Insertion properties
- **Invariant preservation**: After Insert, all four red-black invariants still hold.
- **Content preservation**: The set of keys in the tree after Insert(key) equals the set of keys before plus {key}. Formally: Elements(Insert(t, k)) == Elements(t) + {k}, where Elements returns the set of all keys in the tree.
- **Idempotence**: Inserting an already-present key does not change the set of keys (since {k} is already in Elements(t)).

### Rotation and fix-up correctness (the hard part)
- **Left rotation preserves BST ordering**: After rotating, the set of keys and their ordering are unchanged.
- **Right rotation preserves BST ordering**: Same for right rotation.
- **Recoloring restores red property**: Insertion of a red node may temporarily violate the red property; fix-up via rotations and recoloring restores it.
- **Fix-up preserves black-height**: Rotations and recoloring do not change the black height of any subtree (except possibly at the root, which may increase by one).
- **Fix-up case coverage**: The fix-up must handle all cases: uncle is red (recolor), uncle is black with zig-zag (double rotation), uncle is black with zig-zig (single rotation) — mirrored for left and right. Each case must independently preserve all invariants.
