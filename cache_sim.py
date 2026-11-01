"""
cache_sim.py
============
Trace-Driven Cache Simulator for Planar Graph & Mesh Topology Traversals.

Project Framing & Memory-Hierarchy (I/O) Model:
-----------------------------------------------
In the memory hierarchy, traversal cost is dominated not by arithmetic instructions,
but by cache line transfers between RAM, L2/L3, and L1 data caches:
- Pointer Layout: Traversal incurs Theta(k) cache line misses, as each pointer hop
  dereferences an isolated, non-contiguous heap object.
- Compact Array Layout: Traversal incurs Theta(1 + k/B) cache line misses (where B
  is the cache line capacity: 64 B / 4 B = 16 int32 elements per line). Contiguous
  buffers allow the CPU hardware prefetcher to load subsequent elements ahead of execution.

Heap Fragmentation Control:
In CPython, a freshly instantiated pointer mesh is allocated sequentially within
contiguous PyMalloc memory arenas, looking artificially cache-friendly.
The `fragment_heap()` function introduces realistic heap fragmentation by randomizing
object creation order and interleaving dummy allocations, modeling a production mesh
subject to dynamic topological edits.

Author: MSc Theoretical Computer Science (DAA Project)
"""

from __future__ import annotations
from collections import OrderedDict
import math
import random
import sys
from typing import List, Tuple, Dict, Any, Optional, Set

from dcel_core import (
    Vertex,
    Face,
    HalfEdge,
    PointerDCEL,
    CompactDCEL,
    MinimalCHE,
    generate_grid_graph,
    encode_to_compact,
    encode_to_minimal,
    compute_dual_bfs_order,
    compute_hilbert_order,
    renumber_compact_mesh,
    che_next,
)


# ============================================================================
# 1. LRU CACHE SIMULATOR (SET-ASSOCIATIVE-FREE / FULLY ASSOCIATIVE MODEL)
# ============================================================================

class SimpleLRUCache:
    """
    Configurable trace-driven LRU cache model.
    Default parameters:
      - line_size = 64 bytes (standard x86_64 / ARM64 cache line)
      - n_lines = 512 (32 KB total capacity, standard L1 Data Cache)
      - L2 preset = 4096 lines (256 KB total capacity)
    """

    def __init__(self, n_lines: int = 512, line_size: int = 64):
        self.n_lines: int = n_lines
        self.line_size: int = line_size
        self.cache: OrderedDict[int, bool] = OrderedDict()
        self.accesses: int = 0
        self.misses: int = 0
        self.dependent_loads: int = 0
        self.unique_lines_touched: Set[int] = set()

    def access(self, byte_addr: int, is_dependent_load: bool = False) -> bool:
        """
        Simulates access to a memory address.
        Returns True on cache HIT, False on cache MISS.
        """
        self.accesses += 1
        if is_dependent_load:
            self.dependent_loads += 1

        tag = byte_addr // self.line_size
        self.unique_lines_touched.add(tag)

        if tag in self.cache:
            self.cache.move_to_end(tag)
            return True  # Cache Hit
        else:
            self.misses += 1
            if len(self.cache) >= self.n_lines:
                self.cache.popitem(last=False)  # Evict oldest LRU line
            self.cache[tag] = True
            return False  # Cache Miss

    @property
    def miss_rate(self) -> float:
        return (self.misses / self.accesses) * 100.0 if self.accesses > 0 else 0.0

    def reset(self) -> None:
        self.cache.clear()
        self.accesses = 0
        self.misses = 0
        self.dependent_loads = 0
        self.unique_lines_touched.clear()


# ============================================================================
# 2. HEAP FRAGMENTATION CONTROLLER
# ============================================================================

def fragment_heap(dcel: PointerDCEL, seed: int = 42) -> PointerDCEL:
    """
    Rebuilds a PointerDCEL with randomized allocation order and interleaved junk
    allocations to model a realistic, fragmented heap.

    Scientific Rationale:
    In synthetic benchmarks, freshly created objects occupy contiguous memory blocks,
    masking pointer indirection penalties. Fragmenting the heap disperses objects
    across distinct virtual memory pages and PyMalloc arenas, exposing true pointer
    chasing cache line misses.
    """
    rng = random.Random(seed)
    n_v = dcel.num_vertices
    n_f = dcel.num_faces
    n_he = dcel.num_half_edges

    plan: List[Tuple[str, int]] = (
        [('v', i) for i in range(n_v)] +
        [('f', i) for i in range(n_f)] +
        [('he', i) for i in range(n_he)]
    )
    rng.shuffle(plan)

    junk_buffer: List[bytearray] = []
    new_vertices: List[Optional[Vertex]] = [None] * n_v
    new_faces: List[Optional[Face]] = [None] * n_f
    new_edges: List[Optional[HalfEdge]] = [None] * n_he

    for kind, idx in plan:
        # Interleave dummy heap allocations between 64 and 512 bytes
        junk_buffer.append(bytearray(rng.randint(64, 512)))
        if kind == 'v':
            old_v = dcel.vertices[idx]
            new_vertices[idx] = Vertex(old_v.id, old_v.x, old_v.y)
        elif kind == 'f':
            old_f = dcel.faces[idx]
            new_faces[idx] = Face(old_f.id, old_f.is_outer)
        elif kind == 'he':
            old_he = dcel.half_edges[idx]
            new_edges[idx] = HalfEdge(old_he.id)

    # Wire up pointers identically to original topology
    for i in range(n_v):
        old_inc = dcel.vertices[i].incident_edge
        if old_inc is not None:
            new_vertices[i].incident_edge = new_edges[old_inc.id]

    for i in range(n_f):
        old_he = dcel.faces[i].half_edge
        if old_he is not None:
            new_faces[i].half_edge = new_edges[old_he.id]

    for i in range(n_he):
        old_e = dcel.half_edges[i]
        new_e = new_edges[i]
        new_e.origin = new_vertices[old_e.origin.id]
        new_e.face = new_faces[old_e.face.id]
        new_e.twin = new_edges[old_e.twin.id]
        new_e.next = new_edges[old_e.next.id]
        new_e.prev = new_edges[old_e.prev.id]

    del junk_buffer  # Release junk references

    frag_dcel = PointerDCEL(
        [v for v in new_vertices if v is not None],
        [f for f in new_faces if f is not None],
        [e for e in new_edges if e is not None]
    )
    assert frag_dcel.validate_topology(), "Topology validation failed on fragmented heap!"
    return frag_dcel


# ============================================================================
# 3. TRACE-DRIVEN SIMULATION RUNNERS
# ============================================================================

def simulate_vertex_star_traversal(
    layout_name: str,
    mesh_obj: Any,
    cache: SimpleLRUCache
) -> Dict[str, Any]:
    """
    Simulates a full-mesh 1-ring vertex star traversal across all vertices.
    Records physical memory addresses touched during execution.
    """
    cache.reset()

    if layout_name in ("pointer_fresh", "pointer_fragmented"):
        dcel: PointerDCEL = mesh_obj
        for v in dcel.vertices:
            cache.access(id(v), is_dependent_load=False)
            start_edge = v.incident_edge
            if start_edge is None:
                continue
            cur = start_edge
            while True:
                cache.access(id(cur), is_dependent_load=True)
                cache.access(id(cur.twin), is_dependent_load=True)
                cache.access(id(cur.twin.next), is_dependent_load=True)
                cur = cur.twin.next
                if cur == start_edge or cur is None:
                    break

    elif layout_name.startswith("compact"):
        compact: CompactDCEL = mesh_obj
        tw_buf = compact.twin.buffer_info()[0]
        nx_buf = compact.next.buffer_info()[0]
        vi_buf = compact.vertex_incident.buffer_info()[0]

        for vid in range(compact.num_vertices):
            cache.access(vi_buf + 4 * vid, is_dependent_load=False)
            start_edge = compact.vertex_incident[vid]
            if start_edge < 0:
                continue
            cur = start_edge
            while True:
                cache.access(tw_buf + 4 * cur, is_dependent_load=True)
                tw = compact.twin[cur]
                cache.access(nx_buf + 4 * tw, is_dependent_load=True)
                cur = compact.next[tw]
                if cur == start_edge or cur < 0:
                    break

    elif layout_name == "minimal":
        minimal: MinimalCHE = mesh_obj
        tw_buf = minimal.twin.buffer_info()[0]
        vi_buf = minimal.vertex_incident.buffer_info()[0]

        for vid in range(minimal.num_vertices):
            cache.access(vi_buf + 4 * vid, is_dependent_load=False)
            start_edge = minimal.vertex_incident[vid]
            if start_edge < 0:
                continue
            cur = start_edge
            while True:
                cache.access(tw_buf + 4 * cur, is_dependent_load=True)
                tw = minimal.twin[cur]
                # next(tw) is ARITHMETIC! Zero memory reads!
                cur = che_next(tw)
                if cur == start_edge:
                    break

    return {
        "layout": layout_name,
        "accesses": cache.accesses,
        "misses": cache.misses,
        "miss_rate_pct": round(cache.miss_rate, 2),
        "dependent_loads": cache.dependent_loads,
        "unique_lines_touched": len(cache.unique_lines_touched),
    }


def simulate_face_traversal(
    layout_name: str,
    mesh_obj: Any,
    cache: SimpleLRUCache
) -> Dict[str, Any]:
    """
    Simulates a full-mesh face boundary walk across all faces.
    """
    cache.reset()

    if layout_name in ("pointer_fresh", "pointer_fragmented"):
        dcel: PointerDCEL = mesh_obj
        for f in dcel.faces:
            cache.access(id(f), is_dependent_load=False)
            start_edge = f.half_edge
            if start_edge is None:
                continue
            cur = start_edge
            while True:
                cache.access(id(cur), is_dependent_load=True)
                cache.access(id(cur.origin), is_dependent_load=True)
                cache.access(id(cur.next), is_dependent_load=True)
                cur = cur.next
                if cur == start_edge or cur is None:
                    break

    elif layout_name.startswith("compact"):
        compact: CompactDCEL = mesh_obj
        orig_buf = compact.origin.buffer_info()[0]
        nx_buf = compact.next.buffer_info()[0]
        fe_buf = compact.face_edge.buffer_info()[0]

        for fid in range(compact.num_faces):
            cache.access(fe_buf + 4 * fid, is_dependent_load=False)
            start_edge = compact.face_edge[fid]
            if start_edge < 0:
                continue
            cur = start_edge
            while True:
                cache.access(orig_buf + 4 * cur, is_dependent_load=True)
                cache.access(nx_buf + 4 * cur, is_dependent_load=True)
                cur = compact.next[cur]
                if cur == start_edge or cur < 0:
                    break

    elif layout_name == "minimal":
        minimal: MinimalCHE = mesh_obj
        orig_buf = minimal.origin.buffer_info()[0]
        num_int = minimal.num_internal_faces

        for fid in range(num_int):
            b = 3 * fid
            cache.access(orig_buf + 4 * b, is_dependent_load=True)
            cache.access(orig_buf + 4 * (b + 1), is_dependent_load=True)
            cache.access(orig_buf + 4 * (b + 2), is_dependent_load=True)

    return {
        "layout": layout_name,
        "accesses": cache.accesses,
        "misses": cache.misses,
        "miss_rate_pct": round(cache.miss_rate, 2),
        "dependent_loads": cache.dependent_loads,
        "unique_lines_touched": len(cache.unique_lines_touched),
    }


# ============================================================================
# 4. BENCHMARK COMPARISON SUITE ACROSS GRAPH SIZES
# ============================================================================

def run_cache_benchmarks(
    sizes: List[int] = [100, 400, 900, 1600],
    cache_lines: int = 512
) -> Dict[str, Any]:
    """
    Executes trace-driven simulation across graph sizes for all topological layouts:
    1. Fresh Pointer DCEL
    2. Fragmented Pointer DCEL
    3. Compact 5-Array DCEL (Row-major)
    4. Compact 5-Array DCEL (Dual BFS renumbered)
    5. Compact 5-Array DCEL (Hilbert curve renumbered)
    6. Minimal 2-Array CHE (Implicit Arithmetic)

    Asserts: misses(compact) < misses(fragmented pointer).
    """
    cache = SimpleLRUCache(n_lines=cache_lines, line_size=64)
    results: List[Dict[str, Any]] = []

    print("=" * 80)
    print("PHASE 3: TRACE-DRIVEN CACHE SIMULATION (32 KB L1 CACHE)")
    print("Memory Hierarchy (I/O) Model: Pointer Theta(k) vs. Compact Theta(1 + k/B)")
    print("=" * 80)

    for target_v in sizes:
        r = max(2, int(math.isqrt(target_v)))
        c = max(2, target_v // r)
        v_actual = r * c

        # Generate layouts
        p_fresh = generate_grid_graph(r, c)
        p_frag = fragment_heap(p_fresh, seed=42)
        compact_orig = encode_to_compact(p_fresh)
        minimal_che = encode_to_minimal(p_fresh)

        # Locality-improving permutations (Phase 4)
        bfs_order = compute_dual_bfs_order(compact_orig)
        compact_bfs = renumber_compact_mesh(compact_orig, bfs_order)

        hilbert_order = compute_hilbert_order(compact_orig)
        compact_hilbert = renumber_compact_mesh(compact_orig, hilbert_order)

        # Simulate Vertex Star Traversal
        sim_p_fresh = simulate_vertex_star_traversal("pointer_fresh", p_fresh, cache)
        sim_p_frag = simulate_vertex_star_traversal("pointer_fragmented", p_frag, cache)
        sim_cmp_orig = simulate_vertex_star_traversal("compact_orig", compact_orig, cache)
        sim_cmp_bfs = simulate_vertex_star_traversal("compact_bfs", compact_bfs, cache)
        sim_cmp_hilbert = simulate_vertex_star_traversal("compact_hilbert", compact_hilbert, cache)
        sim_minimal = simulate_vertex_star_traversal("minimal", minimal_che, cache)

        # Scientific assertion: Compact must incur significantly fewer cache misses than fragmented pointer
        assert sim_cmp_orig["misses"] < sim_p_frag["misses"], (
            f"Assertion Failed: Compact misses ({sim_cmp_orig['misses']}) >= "
            f"Fragmented Pointer misses ({sim_p_frag['misses']}) at V={v_actual}"
        )

        entry = {
            "vertices": v_actual,
            "grid": f"{r}x{c}",
            "pointer_fresh_misses": sim_p_fresh["misses"],
            "pointer_frag_misses": sim_p_frag["misses"],
            "compact_orig_misses": sim_cmp_orig["misses"],
            "compact_bfs_misses": sim_cmp_bfs["misses"],
            "compact_hilbert_misses": sim_cmp_hilbert["misses"],
            "minimal_misses": sim_minimal["misses"],
            "pointer_frag_lines": sim_p_frag["unique_lines_touched"],
            "compact_lines": sim_cmp_orig["unique_lines_touched"],
        }
        results.append(entry)

        print(f"Mesh {entry['grid']} (|V|={v_actual}):")
        print(f"  Frag Pointer Misses: {sim_p_frag['misses']:>5} (Lines: {sim_p_frag['unique_lines_touched']:>4}) | Dependent Loads: {sim_p_frag['dependent_loads']}")
        print(f"  Fresh Pointer Misses: {sim_p_fresh['misses']:>5} (Lines: {sim_p_fresh['unique_lines_touched']:>4})")
        print(f"  Compact Orig Misses:  {sim_cmp_orig['misses']:>5} (Lines: {sim_cmp_orig['unique_lines_touched']:>4})")
        print(f"  Compact BFS Misses:   {sim_cmp_bfs['misses']:>5} (Lines: {sim_cmp_bfs['unique_lines_touched']:>4})")
        print(f"  Compact Hilbert Miss: {sim_cmp_hilbert['misses']:>5} (Lines: {sim_cmp_hilbert['unique_lines_touched']:>4})")
        print(f"  Minimal CHE Misses:   {sim_minimal['misses']:>5} (Lines: {sim_minimal['unique_lines_touched']:>4})")
        print(f"  => Cache Miss Reduction Factor (Frag Ptr / Compact): {sim_p_frag['misses'] / sim_cmp_orig['misses']:.2f}x\n")

    return {"records": results, "cache_size_kb": (cache_lines * 64) // 1024}


if __name__ == "__main__":
    benchmark_data = run_cache_benchmarks()
    print("Phase 3 Cache Simulation successfully verified!")

