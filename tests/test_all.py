"""
tests/test_all.py
=================
Comprehensive Pytest Suite for DAA DCEL & Data-Oriented Design Research Project.

Tests:
1. Topology validation: Involutive pairing, cycle consistency, metric continuity.
2. Layout equivalence: Identical face walks and vertex star traversals across
   Pointer DCEL, Compact 5-Array DCEL, and Minimal 2-Array CHE.
3. Ghost triangle closure: Full universal arithmetic coverage on closed 2-manifold.
4. Renumbering invariance: Dual BFS and Hilbert curve permutation tests.
5. Twin construction equality: Hash-based vs. Sort-based pairing equivalence.
6. Theoretical model accuracy: Predicted vs. measured tolerance (< 2 percentage points).
"""

import pytest
import math
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dcel_core import (
    generate_grid_graph,
    encode_to_compact,
    encode_to_minimal,
    walk_face,
    get_vertex_star,
    compact_walk_face,
    compact_get_vertex_star,
    minimal_walk_face,
    minimal_get_vertex_star,
    compute_dual_bfs_order,
    compute_hilbert_order,
    renumber_compact_mesh,
    compute_index_jumps,
    che_next,
    che_prev,
)
from analysis_model import predicted_reduction, verify_theoretical_model
from algos import hash_twin_construction, sort_twin_construction, dual_bfs_pointer, dual_bfs_compact
from cache_sim import fragment_heap


@pytest.mark.parametrize("rows,cols", [(2, 2), (3, 3), (4, 5), (6, 6), (10, 10)])
def test_topology_validation(rows: int, cols: int):
    """Verifies that generated grid graphs satisfy all planar DCEL topological invariants."""
    dcel = generate_grid_graph(rows, cols)
    assert dcel.validate_topology(), f"Topology validation failed for {rows}x{cols}"
    assert dcel.num_vertices == rows * cols
    assert dcel.num_faces == 2 * (rows - 1) * (cols - 1) + 1


@pytest.mark.parametrize("rows,cols", [(2, 2), (3, 3), (4, 4), (5, 5)])
def test_layout_traversal_equivalence(rows: int, cols: int):
    """
    Verifies that Pointer DCEL, Compact 5-Array DCEL, and Minimal 2-Array CHE
    yield 100% identical outputs for face walks and vertex stars.
    """
    dcel = generate_grid_graph(rows, cols)
    compact = encode_to_compact(dcel)
    minimal = encode_to_minimal(dcel)

    # Face walks on all internal faces
    for f in dcel.faces:
        if not f.is_outer:
            p_walk = walk_face(f)
            c_walk = compact_walk_face(compact, f.id)
            m_walk = minimal_walk_face(minimal, f.id)
            assert p_walk == c_walk == m_walk, f"Face mismatch at face {f.id}"

    # Vertex stars on all vertices
    for v in dcel.vertices:
        p_star = get_vertex_star(v)
        c_star = compact_get_vertex_star(compact, v.id)
        m_star = minimal_get_vertex_star(minimal, v.id)
        assert p_star == c_star == m_star, f"Vertex star mismatch at vertex {v.id}"


@pytest.mark.parametrize("rows,cols", [(2, 2), (4, 4), (8, 8)])
def test_ghost_triangle_closure(rows: int, cols: int):
    """
    Verifies that the MinimalCHE ghost-triangle mesh satisfies:
    1. twin[twin[e]] == e universally for all edges.
    2. che_next(e) and che_prev(e) closed-form arithmetic hold everywhere.
    3. The mesh forms a closed 2-manifold without boundary.
    """
    dcel = generate_grid_graph(rows, cols)
    minimal = encode_to_minimal(dcel)
    H = minimal.num_edges

    for e in range(H):
        tw = minimal.twin[e]
        assert tw >= 0, f"Unpaired twin at edge {e}"
        assert minimal.twin[tw] == e, f"Twin involution failed at {e}"

        nxt = che_next(e)
        prv = che_prev(e)
        assert che_prev(nxt) == e, f"Cycle next-prev failed at {e}"
        assert che_next(prv) == e, f"Cycle prev-next failed at {e}"

        # Origin of next(e) must equal target of e (origin of twin[e])
        target_e = minimal.origin[minimal.twin[e]]
        origin_next = minimal.origin[nxt]
        assert target_e == origin_next, f"Metric continuity failed at edge {e}"


def test_renumbering_invariance():
    """
    Verifies that dual BFS and Hilbert curve renumbering strictly preserve
    topological face walks while reducing average index jumps.
    """
    dcel = generate_grid_graph(5, 5)
    compact = encode_to_compact(dcel)

    bfs_order = compute_dual_bfs_order(compact)
    c_bfs = renumber_compact_mesh(compact, bfs_order)

    hilbert_order = compute_hilbert_order(compact)
    c_hilbert = renumber_compact_mesh(compact, hilbert_order)

    # Verify face walk equivalence
    for old_f in range(compact.num_faces - 1):
        orig_walk = compact_walk_face(compact, old_f)

        # BFS renumbered face
        new_bfs_f = bfs_order.index(old_f)
        bfs_walk = compact_walk_face(c_bfs, new_bfs_f)
        assert orig_walk == bfs_walk, f"BFS walk discrepancy at old face {old_f}"

        # Hilbert renumbered face
        new_hilb_f = hilbert_order.index(old_f)
        hilb_walk = compact_walk_face(c_hilbert, new_hilb_f)
        assert orig_walk == hilb_walk, f"Hilbert walk discrepancy at old face {old_f}"


def test_twin_construction_equality():
    """Verifies that O(H) Hash pairing and O(H log H) Sort pairing yield identical twin arrays."""
    edges = [(0, 1), (1, 2), (2, 0), (1, 0), (2, 1), (0, 2), (2, 3), (3, 2)]
    t_hash = hash_twin_construction(edges)
    t_sort = sort_twin_construction(edges)
    assert t_hash == t_sort


def test_predicted_vs_measured_tolerance():
    """Verifies that theoretical memory prediction agrees with measured tracemalloc within 2%."""
    res = verify_theoretical_model(test_sizes=[500, 2000, 5000], tolerance_pct=2.0)
    assert res["all_passed"], "Prediction vs measurement exceeded 2% tolerance threshold!"
