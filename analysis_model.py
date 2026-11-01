"""
analysis_model.py
=================
Theoretical Memory Model & Asymptotic Space Prediction for DCEL Meshes.

Project Framing (Cost-Model Story):
-----------------------------------
In the standard Random Access Machine (RAM) model, Pointer DCEL and Compact Array DCEL
share IDENTICAL asymptotic complexity:
    Space Complexity:  Theta(V + E + F)
    Traversal Latency: O(k) for k-gon face walk, O(d) for degree-d vertex star.

The true scientific contribution of Data-Oriented Design (DOD) lies in a dual cost-model:
1. Memory Space: A ~7x smaller constant factor (~86% RAM reduction) by eliminating
   per-object PyObject headers, instance dictionaries/slots, and 64-bit reference pointers.
2. Memory Hierarchy (I/O Model): A pointer walk costs Theta(k) cache misses due to
   non-contiguous heap allocations, whereas a contiguous array walk costs Theta(1 + k/B)
   cache misses (where B is the cache line size in elements), saturating CPU stream prefetchers.

This module provides the formal mathematical derivation based on Euler's polyhedral formula
for planar triangulations, empirically measures per-object memory overheads via sys.getsizeof,
and evaluates the finite-size boundary correction against empirical tracemalloc data.

Author: MSc Theoretical Computer Science (DAA Project)
"""

from __future__ import annotations
import math
import sys
from typing import Tuple, Dict, Any, List

from dcel_core import Vertex, Face, HalfEdge, run_benchmarks


# ============================================================================
# 1. EMPIRICAL PER-OBJECT MEMORY MEASUREMENT (NO HARDCODED GUESSES)
# ============================================================================

def measure_object_sizes() -> Dict[str, int]:
    """
    Measures the exact runtime byte consumption of individual CPython objects
    using sys.getsizeof.

    Slotted Object Memory Model:
    In CPython (64-bit), a class with __slots__ has a fixed-size struct allocation:
      sizeof(PyObject_HEAD) [16 B] + num_slots * sizeof(PyObject*) [8 B each].
    In addition, referenced primitives (float coordinates, integer IDs, and list references)
    occupy dedicated heap allocations tracked by Python's memory manager.
    """
    dummy_v = Vertex(0, 0.0, 0.0)
    dummy_f = Face(0)
    dummy_he = HalfEdge(0)

    # Base slotted struct sizes
    sz_v_base = sys.getsizeof(dummy_v)
    sz_f_base = sys.getsizeof(dummy_f)
    sz_he_base = sys.getsizeof(dummy_he)

    # Primitive attribute payload sizes
    sz_int = sys.getsizeof(0)      # int ID allocation (28 bytes in 64-bit CPython)
    sz_float = sys.getsizeof(0.0)  # float coordinate allocation (24 bytes)
    sz_ptr = 8                     # 64-bit reference pointer in Python list (8 bytes)

    # Full retained cost per topological element in a PointerDCEL:
    # Vertex: base + id(int) + x(float) + y(float) + list_ptr(8 B)
    cost_vertex = sz_v_base + sz_int + 2 * sz_float + sz_ptr

    # Face: base + id(int) + list_ptr(8 B)
    cost_face = sz_f_base + sz_int + sz_ptr

    # HalfEdge: base + id(int) + list_ptr(8 B)
    cost_half_edge = sz_he_base + sz_int + sz_ptr

    return {
        "sz_v_base": sz_v_base,
        "sz_f_base": sz_f_base,
        "sz_he_base": sz_he_base,
        "cost_vertex": cost_vertex,
        "cost_face": cost_face,
        "cost_half_edge": cost_half_edge,
    }


# ============================================================================
# 2. EULER'S FORMULA DERIVATION & FINITE-SIZE BOUNDARY CORRECTION
# ============================================================================

def euler_mesh_counts(V_target: int) -> Tuple[int, int, int, int, int]:
    """
    Computes exact topological entity counts for an R x C planar triangulated grid.

    Derivation from Euler's Polyhedral Formula:
    For any planar graph embedded in R^2:
        V - E + F = 2

    For an R x C grid with V = R * C vertices:
      - Horizontal edges: R * (C - 1)
      - Vertical edges:   (R - 1) * C
      - Diagonal edges:   (R - 1) * (C - 1)
      Total undirected edges:
        E = R(C - 1) + (R - 1)C + (R - 1)(C - 1)
          = 3RC - 2(R + C) + 1
          = 3V - 2(R + C) + 1

    Total directed half-edges:
        H = 2E = 6V - 4(R + C) + 2

    Total faces (including the 1 outer unbounded face):
        F_internal = 2 * (R - 1) * (C - 1)
        F_outer = 1
        F = 2(R - 1)(C - 1) + 1 = 2V - 2(R + C) + 3

    Finite-Size Boundary Correction:
    On a square-like grid where R ~= C ~= sqrt(V), the perimeter term (R + C) is 2*sqrt(V).
    Hence:
        E = 3V - O(sqrt(V))
        H = 6V - O(sqrt(V))
        F = 2V - O(sqrt(V))

    As V -> infinity:
        E / V -> 3
        H / V -> 6
        F / V -> 2
    """
    R = max(2, int(math.isqrt(V_target)))
    C = max(2, V_target // R)
    V = R * C

    E = 3 * V - 2 * (R + C) + 1
    H = 2 * E
    F = 2 * (R - 1) * (C - 1) + 1

    return V, R, C, H, F


def predicted_reduction(V_target: int) -> Tuple[float, int, int, float]:
    """
    Calculates the theoretically predicted RAM reduction for a mesh of V vertices,
    incorporating the finite-size boundary correction and returning the V -> infinity asymptote.

    Returns:
      (predicted_pct, predicted_ptr_bytes, predicted_cmp_bytes, asymptotic_limit_pct)
    """
    sizes = measure_object_sizes()
    V, R, C, H, F = euler_mesh_counts(V_target)

    # 1. Theoretical Pointer DCEL Memory:
    ptr_bytes = (
        V * sizes["cost_vertex"] +
        F * sizes["cost_face"] +
        H * sizes["cost_half_edge"]
    )

    # 2. Theoretical Compact Array DCEL Memory:
    # 5 contiguous int32 arrays for H: twin, next, prev, origin, face (5 * 4 = 20 B per H)
    # 1 int32 array for V: vertex_incident (4 B per V)
    # 2 float64 arrays for V: vertex_x, vertex_y (2 * 8 = 16 B per V)
    # 1 int32 array for F: face_edge (4 B per F)
    cmp_bytes = (
        H * 20 +       # 5 int32 arrays * 4 B
        V * (4 + 16) + # vertex_incident + coords
        F * 4          # face_edge
    )

    predicted_pct = ((ptr_bytes - cmp_bytes) / ptr_bytes) * 100.0

    # 3. Asymptotic Limit as V -> infinity:
    # Per-vertex costs as H -> 6V, F -> 2V:
    asymp_ptr_per_v = (
        sizes["cost_vertex"] +
        2 * sizes["cost_face"] +
        6 * sizes["cost_half_edge"]
    )
    # Compact per-vertex cost:
    # 6 * 20 (half-edge arrays) + (4 + 16) (vertex arrays) + 2 * 4 (face array)
    asymp_cmp_per_v = (6 * 20) + (4 + 16) + (2 * 4) # exactly 148 B / V

    asymptotic_limit_pct = (
        (asymp_ptr_per_v - asymp_cmp_per_v) / asymp_ptr_per_v
    ) * 100.0

    return predicted_pct, ptr_bytes, cmp_bytes, asymptotic_limit_pct


# ============================================================================
# 3. VERIFICATION & COMPARISON SUITE
# ============================================================================

def verify_theoretical_model(
    test_sizes: List[int] = [500, 2000, 5000],
    tolerance_pct: float = 2.0
) -> Dict[str, Any]:
    """
    Verifies that the theoretical model's predicted RAM reduction matches
    the empirical measurements from run_benchmarks within the specified tolerance.
    """
    sizes = measure_object_sizes()
    _, _, _, asymp_pct = predicted_reduction(10000)

    print("=" * 80)
    print("PHASE 1: THEORETICAL PREDICTION OF THE ~86% RAM REDUCTION")
    print("MSc Theoretical Computer Science | Data-Oriented Design Cost Model")
    print("=" * 80)
    print(f"Empirical Object Costs: Vertex={sizes['cost_vertex']} B, Face={sizes['cost_face']} B, HalfEdge={sizes['cost_half_edge']} B")
    print(f"Euler Triangulation Asymptotes: E ~ 3V, H ~ 6V, F ~ 2V")
    print(f"Compact Buffer Layout: 6*20 B (HE) + 20 B (V) + 8 B (F) = 148 B per vertex")
    print(f"Theoretical V -> inf Asymptote: {asymp_pct:.2f}% RAM reduction\n")

    # Run empirical benchmark
    empirical_results = run_benchmarks(test_sizes, runs=1)
    records = empirical_results["records"]

    comparison_table: List[Dict[str, Any]] = []
    all_within_tolerance = True

    print(f"{'Mesh Size (V)':<14} | {'Predicted %':<13} | {'Measured %':<12} | {'Delta (%)':<10} | {'Status'}")
    print("-" * 65)

    for rec in records:
        v = rec["vertex_count"]
        pred_pct, pred_ptr, pred_cmp, _ = predicted_reduction(v)
        meas_pct = rec["ram_reduction_pct"]
        diff = abs(pred_pct - meas_pct)

        status = "PASSED" if diff <= tolerance_pct else "FAILED"
        if diff > tolerance_pct:
            all_within_tolerance = False

        print(f"V = {v:<10} | {pred_pct:>10.2f}%   | {meas_pct:>9.2f}%   | {diff:>7.2f}%   | [ {status} ]")

        comparison_table.append({
            "vertex_count": v,
            "predicted_pct": round(pred_pct, 2),
            "measured_pct": round(meas_pct, 2),
            "delta_pct": round(diff, 2),
            "passed": diff <= tolerance_pct
        })

    print("-" * 65)
    print(f"All predictions within {tolerance_pct} percentage points: {all_within_tolerance}\n")

    return {
        "asymptotic_pct": asymp_pct,
        "comparison_table": comparison_table,
        "all_passed": all_within_tolerance
    }


if __name__ == "__main__":
    result = verify_theoretical_model()
    assert result["all_passed"], "Theoretical model verification failed tolerance check!"

