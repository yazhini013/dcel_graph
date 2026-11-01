# Space-Time Trade-offs in Planar Graph Topology: Data-Oriented Design (DOD) Research

An empirical and theoretical research platform for MSc Theoretical Computer Science (Design and Analysis of Algorithms - DAA), contrasting classical Object-Oriented Doubly Connected Edge Lists (Pointer DCEL) against Compact Array-Based representations (AHF / CHE).

---

## Quickstart & Commands

All commands are strictly reproducible:

```bash
# 1. Headless verification suite & 3-layout benchmark (Pointer vs 5-Array vs 2-Array)
python3 dcel_core.py

# 2. Theoretical Euler model prediction vs. tracemalloc empirical comparison
python3 analysis_model.py

# 3. Trace-driven LRU cache simulator & heap fragmentation benchmark
python3 cache_sim.py

# 4. Twin construction (Hash vs Sort) & downstream algorithm equivalence (Dual BFS, Laplacian smoothing)
python3 algos.py

# 5. Compiled C++17 hardware latency benchmark & log-log scaling plot
bash cpp/run_cpp.sh

# 6. Pytest suite covering all topological invariants and theoretical models
pytest -q

# 7. Launch the interactive 7-tab Streamlit academic dashboard
streamlit run app.py
```

---

## File Architecture

* [`dcel_core.py`](dcel_core.py): Core data structures (`Vertex`, `Face`, `HalfEdge`, `PointerDCEL`, `CompactDCEL`, `MinimalCHE`), triangulated grid generator, ghost-triangle closure, traversal engines, renumbering algorithms, and 3-layout benchmarking.
* [`analysis_model.py`](analysis_model.py): Mathematical derivation of Euler's formula for planar triangulations, empirical per-object `sys.getsizeof` measurement, and convergence to the 85.60% asymptote with finite-size boundary correction.
* [`cache_sim.py`](cache_sim.py): 32 KB L1 and 256 KB L2 trace-driven cache simulator, heap fragmentation modeling (`fragment_heap`), and cache miss comparison.
* [`algos.py`](algos.py): Deterministic twin pairing ($O(H)$ Hash vs. $O(H \log H)$ Sort) and downstream algorithms (Dual BFS and Laplacian smoothing).
* [`cpp/bench.cpp`](cpp/bench.cpp): High-performance C++17 benchmarking harness measuring nanoseconds per half-edge up to $10^6$ half-edges.
* [`cpp/plot_cpp.py`](cpp/plot_cpp.py): Generates log-log scaling curves illustrating the CPU cache inflection point.
* [`app.py`](app.py): Comprehensive 7-tab Streamlit academic dashboard.
* [`tests/test_all.py`](tests/test_all.py): Complete pytest test suite.
* [`REPORT.md`](REPORT.md): Academic research report and 7-slide presentation outline.

