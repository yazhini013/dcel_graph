"""
app.py
======
Interactive Streamlit Academic Dashboard:
Space-Time Trade-off in Planar Graph Topology (Pointer DCEL vs. Compact Array AHF/CHE).

Project Framing (Theoretical & Empirical Cost Model):
---------------------------------------------------
Pointer DCEL vs Compact Array DCEL has identical asymptotic bounds in the standard RAM model:
Theta(V+E+F) space, O(k) face traversal, O(d) vertex star traversal.
The scientific contribution is a rigorous data-structural cost model:
compact 1D flat arrays eliminate Python object overheads, pointer indirection,
and redundant topology fields via closed-form modulo-3 arithmetic (Lage et al. 2005)
and parallel indexing (Garimella et al. 2013), achieving ~85-93% empirical RAM reduction.

Tabs:
1. 🔍 Small-Scale Visualization: Interactive planar topology, face walks, and vertex star proofs.
2. 📈 Performance Analytics: Memory and latency profiling across 3 layouts (Pointer, 5-Array, 2-Array Minimal).
3. 📐 Theory vs Measurement: Mathematical derivation from Euler's formula and finite-size boundary correction.
4. ⚖️ Trade-offs & Analysis: Honest algorithmic analysis of dynamic editing vs. static traversal.

Author: MSc Theoretical Computer Science (DAA Project)
"""

from __future__ import annotations
import math
import os
import time
from typing import Tuple, List, Dict, Any, Optional
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle
import networkx as nx

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
    run_benchmarks,
    PointerDCEL,
    CompactDCEL,
    MinimalCHE,
)
from analysis_model import predicted_reduction


# ============================================================================
# STREAMLIT PAGE CONFIGURATION & THEME
# ============================================================================

st.set_page_config(
    page_title="DAA Research: DCEL vs. Compact Half-Edge (DOD)",
    page_icon="📐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom academic styling with enhanced tab headers
st.markdown(
    """
    <style>
    .main-header {
        font-family: 'Charter', 'Georgia', serif;
        font-size: 2.1rem;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 0.1rem;
    }
    .sub-header {
        font-family: 'system-ui', sans-serif;
        font-size: 0.95rem;
        color: #475569;
        margin-bottom: 0.9rem;
    }
    .metric-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 0.8rem;
        text-align: center;
    }
    .metric-value {
        font-size: 1.65rem;
        font-weight: 700;
        color: #0f172a;
    }
    .metric-label {
        font-size: 0.8rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .citation-box {
        background-color: #f1f5f9;
        border-left: 4px solid #3b82f6;
        padding: 0.8rem 1.2rem;
        margin: 0.8rem 0;
        border-radius: 0 6px 6px 0;
        font-size: 0.95rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 2px solid #e2e8f0;
    }
    .stTabs [data-baseweb="tab"] {
        height: 44px;
        white-space: pre-wrap;
        background-color: #f8fafc;
        border-radius: 6px 6px 0 0;
        padding: 6px 14px;
        font-weight: 600;
        font-size: 0.9rem;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ffffff !important;
        border-top: 2px solid #2563eb !important;
        color: #1d4ed8 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================================
# CACHED DATA LOADERS
# ============================================================================

@st.cache_data(show_spinner=True)
def get_cached_benchmarks(sizes_tuple: Tuple[int, ...], runs: int = 3) -> Dict[str, Any]:
    return run_benchmarks(list(sizes_tuple), runs=runs)


@st.cache_data(show_spinner=True)
def get_cached_prediction_curve(min_v: int = 100, max_v: int = 10000, steps: int = 40):
    sizes = [int(min_v + (max_v - min_v) * (i / steps)) for i in range(steps + 1)]
    records = []
    for s in sizes:
        pred_pct, _, _, asymp_pct = predicted_reduction(s)
        records.append({"V": s, "predicted_reduction": pred_pct, "asymptote": asymp_pct})
    return pd.DataFrame(records)


# ============================================================================
# HEADER & OVERVIEW
# ============================================================================

st.markdown('<div class="main-header">Space-Time Trade-offs in Planar Graph Topology</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">'
    'MSc Theoretical Computer Science | Design and Analysis of Algorithms (DAA) | '
    '<b>Pointer DCEL vs. Compact Array Half-Edge (Data-Oriented Design)</b>'
    '</div>',
    unsafe_allow_html=True,
)


# ============================================================================
# SIDEBAR CONTROLS
# ============================================================================

st.sidebar.header("🕹️ Configuration Panel")

st.sidebar.subheader("Visualization Parameters")
grid_rows = st.sidebar.slider("Grid Rows (r)", min_value=2, max_value=6, value=3, step=1)
grid_cols = st.sidebar.slider("Grid Columns (c)", min_value=2, max_value=6, value=3, step=1)

total_small_nodes = grid_rows * grid_cols
st.sidebar.caption(f"Small Graph Nodes: **{total_small_nodes}** (Safety Limit: ≤ 100)")

st.sidebar.divider()

st.sidebar.subheader("Benchmarking Parameters")
bench_preset = st.sidebar.selectbox(
    "Graph Scale Preset",
    options=["Standard Suite (500, 2000, 5000)", "Extended Suite (250, 500, 1000, 2500, 5000)", "Quick Suite (300, 1000)", "Custom Selection"],
    index=0,
    help="Select a benchmark scale preset or define custom vertex counts."
)

if bench_preset == "Standard Suite (500, 2000, 5000)":
    default_sizes = [500, 2000, 5000]
elif bench_preset == "Extended Suite (250, 500, 1000, 2500, 5000)":
    default_sizes = [250, 500, 1000, 2500, 5000]
elif bench_preset == "Quick Suite (300, 1000)":
    default_sizes = [300, 1000]
else:
    default_sizes = [500, 2000]

selected_sizes = st.sidebar.multiselect(
    "Benchmark Graph Scales (|V|)",
    options=[100, 200, 250, 300, 500, 800, 1000, 1500, 2000, 2500, 3000, 4000, 5000, 7500],
    default=default_sizes,
    help="Add or remove specific mesh vertex counts to benchmark live."
)

if not selected_sizes:
    selected_sizes = [500, 2000]

timing_runs = st.sidebar.slider(
    "Benchmark Timing Runs",
    min_value=1,
    max_value=5,
    value=3,
    step=1,
    help="Number of traversal repetitions averaged for runtime speed measurement."
)

benchmark_sizes = tuple(sorted(selected_sizes))

if st.sidebar.button("🔄 Force Re-run Benchmarks", help="Clears cache and forces immediate re-computation"):
    st.cache_data.clear()
    st.rerun()


# ============================================================================
# TABULAR INTERFACE: 4 FOCUSED TABS
# ============================================================================

tab_viz, tab_perf, tab_theory, tab_tradeoffs = st.tabs([
    "🔍 Small-Scale Visualization",
    "📈 Performance Analytics",
    "📐 Theory vs Measurement",
    "⚖️ Trade-offs & Analysis"
])


# ============================================================================
# TAB 1: SMALL-SCALE GRAPH VISUALIZATION & TOPOLOGICAL PROOF
# ============================================================================

with tab_viz:
    st.markdown(
        """
        Interactive topological verification on a triangulated planar grid.
        Select an internal face or a vertex to observe CCW boundary walking and 1-ring star traversal.
        """
    )

    small_dcel = generate_grid_graph(grid_rows, grid_cols)
    small_compact = encode_to_compact(small_dcel)
    small_minimal = encode_to_minimal(small_dcel)

    col_ctrl1, col_ctrl2 = st.columns(2)

    with col_ctrl1:
        internal_faces = [f.id for f in small_dcel.faces if not f.is_outer]
        selected_face_id = st.selectbox(
            "Select Face to Highlight (CCW Boundary Walk):",
            options=internal_faces if internal_faces else [0],
            index=0,
            help="Traverses face boundary via next pointers vs. next_array indexing vs. arithmetic."
        )

    with col_ctrl2:
        selected_vertex_id = st.selectbox(
            "Select Vertex to Highlight (1-Ring Star Orbit):",
            options=[v.id for v in small_dcel.vertices],
            index=min(4, len(small_dcel.vertices) - 1),
            help="Orbits outgoing half-edges around vertex."
        )

    # Execute traversals on all 3 models
    selected_face_obj = small_dcel.faces[selected_face_id]
    selected_vertex_obj = small_dcel.vertices[selected_vertex_id]

    ptr_face_walk = walk_face(selected_face_obj)
    ptr_vertex_star = get_vertex_star(selected_vertex_obj)

    cmp_face_walk = compact_walk_face(small_compact, selected_face_id)
    cmp_vertex_star = compact_get_vertex_star(small_compact, selected_vertex_id)

    min_face_walk = minimal_walk_face(small_minimal, selected_face_id)
    min_vertex_star = minimal_get_vertex_star(small_minimal, selected_vertex_id)

    # Plot planar graph using NetworkX and Matplotlib
    fig, ax = plt.subplots(figsize=(6.5, 4.8), dpi=130)

    G = nx.DiGraph()
    pos = {v.id: (v.x, v.y) for v in small_dcel.vertices}
    for v in small_dcel.vertices:
        G.add_node(v.id)

    for e in small_dcel.half_edges:
        if not e.face.is_outer:
            G.add_edge(e.origin.id, e.twin.origin.id)

    nx.draw_networkx_edges(G, pos, ax=ax, edge_color="#94a3b8", width=1.1, arrows=False, alpha=0.7)
    nx.draw_networkx_nodes(G, pos, ax=ax, node_color="#e2e8f0", edgecolors="#64748b", node_size=340, linewidths=1.2)
    nx.draw_networkx_labels(G, pos, ax=ax, font_size=8.5, font_family="sans-serif", font_weight="bold", font_color="#1e293b")

    if ptr_face_walk:
        face_pts = [pos[vid] for vid in ptr_face_walk]
        face_patch = Polygon(
            face_pts, closed=True, facecolor="#3b82f6", alpha=0.35, edgecolor="#1d4ed8",
            linewidth=2.5, label=f"Face {selected_face_id} Boundary"
        )
        ax.add_patch(face_patch)

    star_edges = []
    for eid in ptr_vertex_star:
        he = small_dcel.half_edges[eid]
        star_edges.append((he.origin.id, he.twin.origin.id))

    nx.draw_networkx_nodes(
        G, pos, nodelist=[selected_vertex_id], ax=ax,
        node_color="#ef4444", edgecolors="#991b1b", node_size=480, linewidths=2.0,
        label=f"Central Vertex {selected_vertex_id}"
    )

    if star_edges:
        nx.draw_networkx_edges(
            G, pos, edgelist=star_edges, ax=ax, edge_color="#dc2626", width=2.2,
            arrows=True, arrowsize=14, arrowstyle="-|>", label=f"Vertex Star Outgoing"
        )

    ax.set_title(f"Planar DCEL ({grid_rows}×{grid_cols} | |V|={small_dcel.num_vertices}, |F|={small_dcel.num_faces}, |HE|={small_dcel.num_half_edges})", fontsize=10, fontweight="bold", pad=8)
    ax.set_xlim(-0.6, grid_cols - 0.4)
    ax.set_ylim(-0.6, grid_rows - 0.4)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), frameon=True, fontsize=8)
    plt.tight_layout()

    col_viz, col_proof = st.columns([1.1, 0.9])
    with col_viz:
        st.pyplot(fig)
        plt.close(fig)

    with col_proof:
        st.markdown("#### 3-Layout Topological Equivalence Proof")
        st.markdown("**Face Traversal (`walk_face`):**")
        st.code(f"Pointer DCEL:    {ptr_face_walk}\nCompact 5-Array: {cmp_face_walk}\nMinimal 2-Array: {min_face_walk}", language="python")
        if ptr_face_walk == cmp_face_walk == min_face_walk:
            st.success("✅ Identical Bounding Vertices Traversed Across All 3 Layouts")

        st.markdown("**Vertex Star Traversal (`get_vertex_star`):**")
        st.code(f"Pointer DCEL:    {ptr_vertex_star}\nCompact 5-Array: {cmp_vertex_star}\nMinimal 2-Array: {min_vertex_star}", language="python")
        if ptr_vertex_star == cmp_vertex_star == min_vertex_star:
            st.success("✅ Identical 1-Ring Outgoing Edge IDs Traversed Across All 3 Layouts")


# ============================================================================
# TAB 2: LARGE-SCALE PERFORMANCE & MEMORY ANALYTICS
# ============================================================================

with tab_perf:
    st.markdown(
        """
        Byte-level memory profiling (`tracemalloc`) and traversal speed profiling (`timeit`)
        comparing **Pointer DCEL vs. Compact 5-Array DCEL vs. Minimal 2-Array CHE**.
        """
    )

    st.info(
        f"⚙️ **Active Benchmark Configuration:** Evaluating **{len(benchmark_sizes)}** graph scales: "
        f"`{list(benchmark_sizes)}` with **{timing_runs}** timing runs per layout."
    )

    with st.spinner(f"Running benchmarks for sizes {list(benchmark_sizes)}..."):
        benchmarks_data = get_cached_benchmarks(benchmark_sizes, runs=timing_runs)

    records = benchmarks_data["records"]
    df_bench = pd.DataFrame(records)

    avg_reduction_5 = df_bench["ram_reduction_pct"].mean()
    avg_reduction_2 = df_bench["minimal_ram_reduction_pct"].mean()
    avg_savings_factor = df_bench["minimal_savings_ratio"].mean()
    max_vertices = df_bench["vertex_count"].max()

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.markdown(f'<div class="metric-card"><div class="metric-value" style="color: #2563eb;">{avg_reduction_5:.1f}%</div><div class="metric-label">5-Array RAM Reduction</div></div>', unsafe_allow_html=True)
    with kpi2:
        st.markdown(f'<div class="metric-card"><div class="metric-value" style="color: #16a34a;">{avg_reduction_2:.1f}%</div><div class="metric-label">2-Array RAM Reduction</div></div>', unsafe_allow_html=True)
    with kpi3:
        st.markdown(f'<div class="metric-card"><div class="metric-value" style="color: #9333ea;">{avg_savings_factor:.1f}×</div><div class="metric-label">Max Savings Factor</div></div>', unsafe_allow_html=True)
    with kpi4:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{max_vertices:,}</div><div class="metric-label">Max Mesh Vertices</div></div>', unsafe_allow_html=True)

    st.write("")
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.markdown("##### 3-Layout Memory Footprint Comparison (MB)")
        mem_chart = df_bench.set_index("vertex_count")[["pointer_memory_mb", "compact_memory_mb", "minimal_memory_mb"]]
        mem_chart.columns = ["Pointer DCEL (MB)", "Compact 5-Array (MB)", "Minimal 2-Array (MB)"]
        st.line_chart(mem_chart, height=310)

    with chart_col2:
        st.markdown("##### RAM Reduction Percentage vs. Mesh Size (%)")
        red_chart = df_bench.set_index("vertex_count")[["ram_reduction_pct", "minimal_ram_reduction_pct"]]
        red_chart.columns = ["5-Array AHF (%)", "2-Array CHE (%)"]
        st.line_chart(red_chart, height=310)

    st.markdown("##### Detailed Experimental Metrics")
    st.dataframe(df_bench, width="stretch", hide_index=True)


# ============================================================================
# TAB 3: THEORY VS MEASUREMENT (PHASE 1 INTEGRATION)
# ============================================================================

with tab_theory:
    st.markdown("### Theoretical Derivation & Convergence to the 85.6% Asymptote")
    st.markdown(
        r"""
        #### 1. Planar Triangulation Topology (Euler's Formula)
        By Euler's polyhedral formula, for any planar embedding with $V$ vertices, $E$ edges, and $F$ faces:
        $$V - E + F = 2$$
        On an $R \times C$ triangulated grid where $V = R \cdot C$:
        * Undirected Edges: $E = 3V - 2(R + C) + 1 = 3V - O(\sqrt{V})$
        * Directed Half-Edges: $H = 2E = 6V - 4(R + C) + 2 = 6V - O(\sqrt{V})$
        * Faces: $F = 2(R - 1)(C - 1) + 1 = 2V - 2(R + C) + 3 = 2V - O(\sqrt{V})$

        In the asymptotic limit ($V \to \infty$):
        $$\lim_{V \to \infty} \frac{E}{V} = 3, \quad \lim_{V \to \infty} \frac{H}{V} = 6, \quad \lim_{V \to \infty} \frac{F}{V} = 2$$

        #### 2. Exact Empirical Object Costs (CPython 64-bit)
        * $\text{Cost}(\text{Vertex}) = 64\text{ B (base struct)} + 28\text{ B (id)} + 48\text{ B (x, y floats)} + 8\text{ B (list ptr)} = 148\text{ B}$
        * $\text{Cost}(\text{Face}) = 56\text{ B (base struct)} + 28\text{ B (id)} + 8\text{ B (list ptr)} = 92\text{ B}$
        * $\text{Cost}(\text{HalfEdge}) = 80\text{ B (base struct)} + 28\text{ B (id)} + 8\text{ B (list ptr)} = 116\text{ B}$

        #### 3. Compact Buffer Cost per Vertex
        $$\text{Cost}_{\text{Compact}}(V) = \underbrace{6 \times 20\text{ B}}_{\text{5 int32 arrays for } H} + \underbrace{20\text{ B}}_{v_{\text{inc}} + \text{coords}} + \underbrace{2 \times 4\text{ B}}_{f_{\text{edge}}} = 148\text{ B / vertex}$$

        #### 4. Asymptotic RAM Reduction Limit
        $$\text{Asymptote} = \frac{(148 + 2 \times 92 + 6 \times 116) - 148}{148 + 2 \times 92 + 6 \times 116} = \frac{1028 - 148}{1028} \approx \mathbf{85.60\%}$$
        """
    )

    pred_curve_df = get_cached_prediction_curve()
    st.markdown("##### Finite-Size Boundary Convergence Curve")

    fig_th, ax_th = plt.subplots(figsize=(8, 4.2), dpi=130)
    ax_th.plot(pred_curve_df["V"], pred_curve_df["predicted_reduction"], label="Theoretical Prediction (with Boundary Correction)", color="#2563eb", linewidth=2.2)
    ax_th.axhline(y=85.60, color="#dc2626", linestyle="--", linewidth=1.8, label="V -> inf Asymptote (85.60%)")

    # Plot empirical measured points from cached benchmark
    meas_records = benchmarks_data["records"]
    meas_v = [r["vertex_count"] for r in meas_records]
    meas_y = [r["ram_reduction_pct"] for r in meas_records]
    ax_th.scatter(meas_v, meas_y, color="#0f172a", s=65, zorder=5, label="Empirical Measurements (tracemalloc)")

    ax_th.set_xlabel("Vertex Count (|V|)", fontsize=9.5, fontweight="bold")
    ax_th.set_ylabel("RAM Reduction (%)", fontsize=9.5, fontweight="bold")
    ax_th.set_ylim(84.0, 87.0)
    ax_th.grid(True, linestyle=":", alpha=0.5)
    ax_th.legend(frameon=True, fontsize=8.5)
    plt.tight_layout()
    st.pyplot(fig_th)
    plt.close(fig_th)


# ============================================================================
# TAB 4: TRADE-OFFS & ANALYSIS
# ============================================================================

with tab_tradeoffs:
    st.markdown("### Algorithmic & Structural Trade-Offs")
    st.markdown(
        r"""
        In adherence to rigorous algorithm analysis, we document the fundamental limitations and trade-offs
        of Compact Array-Based representations versus traditional Object-Oriented Pointer DCEL:

        | Criterion | Object-Oriented Pointer DCEL (Muller & Preparata 1978) | Compact 5-Array DCEL (Garimella et al. 2013 AHF) | Minimal 2-Array CHE (Lage et al. 2005 CHE) |
        | :--- | :--- | :--- | :--- |
        | **Memory Model Footprint** | $\\Theta(V + E + F)$ with high constant ($\\approx 148\\text{ B}/V + 116\\text{ B}/H$) | $\\Theta(V + E + F)$ with reduced constant ($\\approx 148\\text{ B}/V$ total) | $\\Theta(V + E + F)$ with minimal constant ($\\approx 60\\text{ B}/V$ total) |
        | **Memory Organization** | Fragmented dynamic heap allocations (pointers to objects) | Contiguous parallel 1D integer arrays | Contiguous 1D integer arrays (`twin`, `origin`) |
        | **Next/Prev Navigation** | Explicit stored pointers (`e.next`, `e.prev`) | Explicit array lookup (`next_arr[e]`, `prev_arr[e]`) | Closed-form arithmetic (zero-cost mod 3 formulas) |
        | **Edge Flips** | $O(1)$ pointer rewiring across affected objects | $O(1)$ array index assignment | $O(1)$ array index assignment |
        | **Vertex / Face Insertion** | **$O(1)$ isolated heap allocation** | Amortized $O(1)$ array dynamic reallocation | Amortized $O(1)$ array dynamic reallocation |
        | **Entity Deletion** | **$O(1)$ isolated deallocation** | Leaves index holes or requires compaction | Leaves index holes or requires compaction |
        | **Arbitrary Polygons** | Arbitrary $n$-gon faces supported natively | Arbitrary $n$-gon faces supported | Purely triangular ($d=3$); polygons require triangulation |
        | **Boundary Closure** | Single external boundary cycle | Explicit boundary half-edge cycle | Requires Ghost-Triangle closure to emulate 2-manifold |

        > **Algorithmic Fit Summary:**
        > * **Compact Array DCEL (AHF / CHE):** Superior for static meshes, simulation meshes, GIS spatial queries, 
        >   and traversal-dominated workloads where memory compactness is paramount.
        > * **Pointer DCEL:** Optimal for interactive CAD geometric modeling, incremental Delaunay triangulation, 
        >   and topological surgery requiring frequent node deletions and additions without bulk array shifting.
        """
    )
    st.markdown("---")
    st.caption("MSc Theoretical Computer Science | Academic Project Artifact | Design and Analysis of Algorithms")
