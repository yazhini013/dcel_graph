"""
algos.py
========
Algorithmic Comparisons: Primal/Dual Graph Algorithms & Deterministic Topology Construction.

Project Framing & Cost-Model Grounding:
---------------------------------------
In the RAM model, hash-based twin pairing has expected O(H) time complexity, whereas
sort-based pairing has O(H log H) deterministic time complexity.
However, in high-performance computing (DOD), sort-based construction requires zero
dynamic hash tables or bucket linked lists, operating in contiguous memory buffers.

Furthermore, this module benchmarks downstream geometric algorithms executed
identically across both Pointer DCEL and Compact Array DCEL:
1. Dual Graph Breadth-First Search (BFS): Computes topological geodesic distances across faces.
2. Laplacian Mesh Smoothing: Iteratively diffuses vertex coordinates over 1-ring vertex stars.

Author: MSc Theoretical Computer Science (DAA Project)
"""

from __future__ import annotations
import array
from collections import deque
import math
import timeit
from typing import List, Tuple, Dict, Any, Optional

from dcel_core import (
    Vertex,
    Face,
    HalfEdge,
    PointerDCEL,
    CompactDCEL,
    generate_grid_graph,
    encode_to_compact,
    walk_face,
    get_vertex_star,
    compact_walk_face,
    compact_get_vertex_star,
)
from cache_sim import SimpleLRUCache, fragment_heap


# ============================================================================
# 1. TWIN CONSTRUCTION ALGORITHMS: HASH-BASED VS. SORT-BASED
# ============================================================================

def hash_twin_construction(directed_edges: List[Tuple[int, int]]) -> array.array:
    """
    Constructs twin half-edge pairing using an expected O(H) hash table (dict).

    Algorithm:
    For each directed edge e = (u, v):
      If reverse key (v, u) exists in lookup:
        Pair e and lookup[(v, u)]. Remove key.
      Else:
        Insert lookup[(u, v)] = e.
    """
    n_edges = len(directed_edges)
    twin = array.array('i', [-1] * n_edges)
    lookup: Dict[Tuple[int, int], int] = {}

    for e_id, (u, v) in enumerate(directed_edges):
        rev = (v, u)
        if rev in lookup:
            partner = lookup[rev]
            twin[e_id] = partner
            twin[partner] = e_id
            del lookup[rev]
        else:
            lookup[(u, v)] = e_id

    return twin


def sort_twin_construction(directed_edges: List[Tuple[int, int]]) -> array.array:
    """
    Constructs twin half-edge pairing using an O(H log H) deterministic, array-oriented sort.

    Algorithm:
    1. Map each directed edge e = (u, v) to a canonical key (min(u, v), max(u, v)).
    2. Sort records by undirected edge key.
    3. Contiguous matching pairs represent anti-parallel twins. Pair adjacent entries.
    """
    n_edges = len(directed_edges)
    twin = array.array('i', [-1] * n_edges)

    # Records: (min_v, max_v, edge_id, is_forward)
    records: List[Tuple[int, int, int, bool]] = [
        (min(u, v), max(u, v), e_id, u < v)
        for e_id, (u, v) in enumerate(directed_edges)
    ]

    # Deterministic O(H log H) sort
    records.sort(key=lambda r: (r[0], r[1]))

    i = 0
    num_records = len(records)
    while i < num_records - 1:
        r1 = records[i]
        r2 = records[i + 1]
        if r1[0] == r2[0] and r1[1] == r2[1]:
            e1 = r1[2]
            e2 = r2[2]
            twin[e1] = e2
            twin[e2] = e1
            i += 2
        else:
            i += 1

    return twin


def benchmark_twin_construction(
    test_scales: List[int] = [1000, 10000, 50000, 100000]
) -> List[Dict[str, Any]]:
    """
    Benchmarks Hash-based vs. Sort-based twin pairing up to 100k vertices.
    Validates that both algorithms yield 100% identical twin pairings.
    """
    records: List[Dict[str, Any]] = []

    print("=" * 80)
    print("PHASE 5: TWIN PAIRING BENCHMARK (HASH O(H) VS. SORT O(H log H))")
    print("=" * 80)
    print(f"{'Vertices (|V|)':<14} | {'Half-Edges (|H|)':<16} | {'Hash Time (ms)':<16} | {'Sort Time (ms)':<16} | {'Identical?'}")
    print("-" * 75)

    for v_target in test_scales:
        r = max(2, int(math.isqrt(v_target)))
        c = max(2, v_target // r)
        v_actual = r * c

        # Generate directed edges for grid
        directed_edges: List[Tuple[int, int]] = []
        for row in range(r - 1):
            for col in range(c - 1):
                bl = row * c + col
                br = row * c + (col + 1)
                tl = (row + 1) * c + col
                tr = (row + 1) * c + (col + 1)

                # Triangle A
                directed_edges.extend([(bl, br), (br, tr), (tr, bl)])
                # Triangle B
                directed_edges.extend([(bl, tr), (tr, tl), (tl, bl)])

        n_edges = len(directed_edges)

        # Time Hash-based
        t_hash = timeit.timeit(lambda: hash_twin_construction(directed_edges), number=3) / 3.0 * 1000.0

        # Time Sort-based
        t_sort = timeit.timeit(lambda: sort_twin_construction(directed_edges), number=3) / 3.0 * 1000.0

        # Verify equivalence
        res_hash = hash_twin_construction(directed_edges)
        res_sort = sort_twin_construction(directed_edges)
        is_identical = (res_hash == res_sort)
        assert is_identical, f"Twin construction discrepancy detected at V={v_actual}!"

        print(f"V = {v_actual:<10} | H = {n_edges:<12} | {t_hash:>12.2f} ms | {t_sort:>12.2f} ms | [ {'YES' if is_identical else 'NO'} ]")

        records.append({
            "vertex_count": v_actual,
            "edge_count": n_edges,
            "hash_time_ms": round(t_hash, 2),
            "sort_time_ms": round(t_sort, 2),
            "identical": is_identical
        })

    print("-" * 75)
    return records


# ============================================================================
# 2. DOWNSTREAM ALGORITHMS: DUAL BFS & LAPLACIAN SMOOTHING
# ============================================================================

def dual_bfs_pointer(dcel: PointerDCEL, start_face_id: int = 0) -> List[int]:
    """
    Executes Breadth-First Search on the dual graph of faces using Pointer DCEL.
    Returns: distances array where dist[f] is geodesic hop distance from start_face.
    """
    num_f = dcel.num_faces
    dist = [-1] * num_f
    queue = deque([start_face_id])
    dist[start_face_id] = 0

    while queue:
        curr_fid = queue.popleft()
        curr_face = dcel.faces[curr_fid]
        start_edge = curr_face.half_edge
        if start_edge is None:
            continue
        cur = start_edge
        while True:
            twin_face = cur.twin.face
            if twin_face is not None:
                twin_fid = twin_face.id
                if dist[twin_fid] == -1:
                    dist[twin_fid] = dist[curr_fid] + 1
                    queue.append(twin_fid)
            cur = cur.next
            if cur == start_edge or cur is None:
                break

    return dist


def dual_bfs_compact(compact: CompactDCEL, start_face_id: int = 0) -> List[int]:
    """
    Executes Breadth-First Search on the dual graph of faces using Compact 5-Array DCEL.
    Returns: distances array where dist[f] is geodesic hop distance from start_face.
    """
    num_f = compact.num_faces
    dist = [-1] * num_f
    queue = deque([start_face_id])
    dist[start_face_id] = 0

    twin_arr = compact.twin
    next_arr = compact.next
    face_arr = compact.face
    face_edge_arr = compact.face_edge

    while queue:
        curr_fid = queue.popleft()
        start_edge = face_edge_arr[curr_fid]
        if start_edge < 0:
            continue
        cur = start_edge
        while True:
            tw = twin_arr[cur]
            if tw >= 0:
                nbr_fid = face_arr[tw]
                if nbr_fid >= 0 and dist[nbr_fid] == -1:
                    dist[nbr_fid] = dist[curr_fid] + 1
                    queue.append(nbr_fid)
            cur = next_arr[cur]
            if cur == start_edge or cur < 0:
                break

    return dist


def laplacian_smoothing_pointer(
    dcel: PointerDCEL,
    iterations: int = 5,
    lam: float = 0.5
) -> List[Tuple[float, float]]:
    """
    Executes iterative Laplacian mesh smoothing on Pointer DCEL.
    Formula: x_{new}(v) = (1 - lam)*x(v) + lam * (1 / deg(v)) * sum_{u in N(v)} x(u)
    """
    coords = [(v.x, v.y) for v in dcel.vertices]

    for _ in range(iterations):
        new_coords: List[Tuple[float, float]] = []
        for v in dcel.vertices:
            star_edges = get_vertex_star(v)
            if not star_edges:
                new_coords.append(coords[v.id])
                continue

            # Accumulate neighbor coordinates
            sum_x = 0.0
            sum_y = 0.0
            count = 0
            for eid in star_edges:
                nbr_v = dcel.half_edges[eid].twin.origin.id
                sum_x += coords[nbr_v][0]
                sum_y += coords[nbr_v][1]
                count += 1

            if count > 0:
                nx = (1.0 - lam) * coords[v.id][0] + lam * (sum_x / count)
                ny = (1.0 - lam) * coords[v.id][1] + lam * (sum_y / count)
                new_coords.append((nx, ny))
            else:
                new_coords.append(coords[v.id])

        coords = new_coords

    return coords


def laplacian_smoothing_compact(
    compact: CompactDCEL,
    iterations: int = 5,
    lam: float = 0.5
) -> List[Tuple[float, float]]:
    """
    Executes iterative Laplacian mesh smoothing on Compact 5-Array DCEL.
    """
    coords_x = list(compact.vertex_x)
    coords_y = list(compact.vertex_y)
    num_v = compact.num_vertices

    twin_arr = compact.twin
    origin_arr = compact.origin

    for _ in range(iterations):
        new_x = [0.0] * num_v
        new_y = [0.0] * num_v

        for vid in range(num_v):
            star_edges = compact_get_vertex_star(compact, vid)
            if not star_edges:
                new_x[vid] = coords_x[vid]
                new_y[vid] = coords_y[vid]
                continue

            sum_x = 0.0
            sum_y = 0.0
            count = 0
            for eid in star_edges:
                nbr_v = origin_arr[twin_arr[eid]]
                sum_x += coords_x[nbr_v]
                sum_y += coords_y[nbr_v]
                count += 1

            if count > 0:
                new_x[vid] = (1.0 - lam) * coords_x[vid] + lam * (sum_x / count)
                new_y[vid] = (1.0 - lam) * coords_y[vid] + lam * (sum_y / count)
            else:
                new_x[vid] = coords_x[vid]
                new_y[vid] = coords_y[vid]

        coords_x = new_x
        coords_y = new_y

    return list(zip(coords_x, coords_y))


def run_downstream_benchmarks(
    sizes: List[int] = [500, 2000, 5000]
) -> List[Dict[str, Any]]:
    """
    Executes downstream algorithm benchmarks and asserts equivalence between
    Pointer DCEL and Compact Array DCEL.
    """
    records: List[Dict[str, Any]] = []

    print("\n" + "=" * 80)
    print("DOWNSTREAM ALGORITHMS BENCHMARK (DUAL BFS & LAPLACIAN SMOOTHING)")
    print("=" * 80)

    for target_v in sizes:
        r = max(2, int(math.isqrt(target_v)))
        c = max(2, target_v // r)
        v_actual = r * c

        p_dcel = generate_grid_graph(r, c)
        c_dcel = encode_to_compact(p_dcel)

        # 1. Dual BFS Benchmark
        t_ptr_bfs = timeit.timeit(lambda: dual_bfs_pointer(p_dcel, 0), number=5) / 5.0 * 1000.0
        t_cmp_bfs = timeit.timeit(lambda: dual_bfs_compact(c_dcel, 0), number=5) / 5.0 * 1000.0

        dist_ptr = dual_bfs_pointer(p_dcel, 0)
        dist_cmp = dual_bfs_compact(c_dcel, 0)
        assert dist_ptr == dist_cmp, f"Dual BFS mismatch at V={v_actual}!"

        # 2. Laplacian Smoothing Benchmark (5 iterations)
        t_ptr_smooth = timeit.timeit(lambda: laplacian_smoothing_pointer(p_dcel, iterations=5), number=3) / 3.0 * 1000.0
        t_cmp_smooth = timeit.timeit(lambda: laplacian_smoothing_compact(c_dcel, iterations=5), number=3) / 3.0 * 1000.0

        smooth_ptr = laplacian_smoothing_pointer(p_dcel, iterations=5)
        smooth_cmp = laplacian_smoothing_compact(c_dcel, iterations=5)

        max_err = max(
            math.hypot(p[0] - c[0], p[1] - c[1])
            for p, c in zip(smooth_ptr, smooth_cmp)
        )
        assert max_err < 1e-6, f"Laplacian smoothing coordinate mismatch (max_err={max_err})!"

        print(f"Mesh {r}x{c} (|V|={v_actual}, |F|={p_dcel.num_faces}):")
        print(f"  Dual BFS Time:       Pointer={t_ptr_bfs:>6.2f} ms | Compact={t_cmp_bfs:>6.2f} ms | Verified: Identical Distances")
        print(f"  Laplacian Smoothing: Pointer={t_ptr_smooth:>6.2f} ms | Compact={t_cmp_smooth:>6.2f} ms | Max Coord Delta: {max_err:.2e}\n")

        records.append({
            "vertex_count": v_actual,
            "grid": f"{r}x{c}",
            "ptr_bfs_ms": round(t_ptr_bfs, 2),
            "cmp_bfs_ms": round(t_cmp_bfs, 2),
            "ptr_smooth_ms": round(t_ptr_smooth, 2),
            "cmp_smooth_ms": round(t_cmp_smooth, 2),
            "max_coord_delta": max_err,
        })

    return records


if __name__ == "__main__":
    benchmark_twin_construction()
    run_downstream_benchmarks()

