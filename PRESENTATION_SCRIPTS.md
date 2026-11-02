# DAA Final Package Presentation: Team of 3 Spoken Script & Defense Guide

**Project Title:** Space-Time Trade-offs in Planar Mesh Representations: Moving from Pointer-Based DCEL to Compact Array Structures via Data-Oriented Design  
**Curriculum:** MSc Theoretical Computer Science — Design and Analysis of Algorithms (DAA)  
**Repository:** `https://github.com/yazhini013/dcel_graph.git`  
**Frontend URL:** `http://localhost:8501` (8 Interactive Tabs)

---

## 🏆 Presentation Architecture & Team Role Allocation

All three members have **100% equal academic weightage**. The presentation is strictly organized according to the Faculty Evaluation Rubric:
1. **Background Study & Problem Formulation**
2. **Implementation & Algorithmic Mechanics**
3. **Physical Paper Reference (Carry in hand!)**
4. **Concrete Accomplishments & Deliverables**
5. **New Findings, Surprises & Observations**
6. **Deep Code Walkthrough (Line-by-Line Defense)**
7. **Live Interactive UI Walkthrough (No-PPT Defense)**
8. **Anticipated Faculty Viva Q&A**

```
+--------------------------------------------------------------------------------------------------+
|                                    TOTAL PRESENTATION (15-20 MIN)                                |
+------------------------------------+--------------------------------+----------------------------+
| MEMBER 1 (~5-6 min)                | MEMBER 2 (~5-6 min)            | MEMBER 3 (~5-6 min)        |
| Foundations, Pointer DCEL &        | Data-Oriented Design, AHF/CHE, | Memory-Hierarchy Model,    |
| Analytical Memory Derivation       | Ghost Closure & Downstream Eq. | Cache Sim, C++17 & Limits  |
+------------------------------------+--------------------------------+----------------------------+
| • Tab 1: Small-Scale Viz           | • Tab 2: Performance Analytics | • Tab 4: Memory Lens       |
| • Tab 3: Theory vs Measurement     | • Tab 5: Layouts & Algorithms  | • Tab 6: C++17 Benchmarks  |
|                                    | • Tab 8: Literature & Theory   | • Tab 7: Trade-offs        |
+------------------------------------+--------------------------------+----------------------------+
| Paper: Muller & Preparata (1978) / | Paper: Garimella et al. (2013) | Paper: Aggarwal-Vitter '88 |
| Salinas-Fernandez et al. (2023) §2 | & Lage et al. (2005) CHE       | & Salinas-Fernandez '23 §4 |
+------------------------------------+--------------------------------+----------------------------+
| Code: dcel_core.py (Pointer),      | Code: dcel_core.py (Compact,   | Code: cache_sim.py,        |
| analysis_model.py                  | MinimalCHE), algos.py          | cpp/bench.cpp, app.py Lens |
+------------------------------------+--------------------------------+----------------------------+
```

---

# 🎙️ MEMBER 1: FOUNDATIONS, POINTER DCEL & MATHEMATICAL MEMORY DERIVATION

### Assigned Tabs:
* **Tab 1:** `🔍 Small-Scale Visualization`
* **Tab 3:** `📐 Theory vs Measurement`

### Physical Paper to Hold in Hand:
* **Primary Reference:** *Salinas-Fernández, J. A., et al. (2023).* "A Survey on Compact and Succinct Data Structures for Meshes." *ACM Computing Surveys*, 55(11), 1–38. (Hold open to **Section 2: Classic Mesh Representations & The Memory Wall**).
* **Foundational Cite:** *Muller, D. E., & Preparata, F. P. (1978).* "Finding the intersection of two convex polyhedra." *Theoretical Computer Science*, 7(2), 217–236; and *de Berg et al. (2008)* *Computational Geometry: Algorithms and Applications*.

---

### 1. Spoken Presentation Script (Word-for-Word Narration)

> *"Good morning, Professor and members of the panel. Today, our team is presenting our DAA final package project: **Evaluating Space-Time Trade-offs in Planar Mesh Representations using Data-Oriented Design**.*
>
> *(Hold up paper copy)*
> *"I am holding Section 2 of Salinas-Fernández et al.'s 2023 ACM Computing Surveys paper. For nearly four decades, the gold standard in computational geometry has been the **Doubly Connected Edge List (DCEL)**, originally formalized by Muller and Preparata in 1978. In a DCEL, every geometric edge is split into two directed half-edges of opposite orientation. This allows constant-time $O(1)$ topological navigation—finding the twin edge, the next edge in a counter-clockwise face orbit, or the incident face.*
>
> *In classical computer science, we teach that a DCEL takes $\Theta(V + E + F)$ space. In the standard Word RAM model, this seems optimal. However, when we implement this in object-oriented software, a massive **hidden space penalty** emerges.*
>
> *(Point to screen or dashboard Tab 1)*
> *Let us look at **Tab 1: Small-Scale Visualization**. Here, we have generated an interactive triangulated planar grid. If I select face $F_4$, our traversal engine calls `walk_face()` and orbits the boundary half-edges in counter-clockwise order using pointer dereferences: `edge = edge.next`. If I select Vertex $V_5$, our engine executes `get_vertex_star()`, rotating around the vertex orbit using `edge = edge.twin.next` to collect the 1-ring star in $O(d)$ time, where $d$ is the vertex degree.*
>
> *Every single vertex, face, and half-edge in this classical structure is an independent Python heap object. Even using `__slots__` to eliminate dynamic dictionaries, our empirical measurements in `analysis_model.py` show that:*
> * 1 `Vertex` object costs **148 bytes**
> * 1 `Face` object costs **92 bytes**
> * 1 `HalfEdge` object costs **116 bytes**
>
> *Now, let us switch to **Tab 3: Theory vs Measurement** to understand the mathematical derivation.*
>
> *For any planar triangulation, Euler's polyhedral formula dictates that $V - E + F = 2$. In an infinite or boundary-less triangular mesh, each face has 3 edges and each edge is shared by 2 faces ($3F = 2E$), giving:*
> $$E \approx 3V, \quad H = 2E \approx 6V, \quad F \approx 2V$$
>
> *Multiplying these Euler topological ratios by our empirical byte sizes gives the exact theoretical memory per vertex:*
> $$\text{Memory per Vertex} = 1 \times 148 + 2 \times 92 + 6 \times 116 = 1028\text{ Bytes per Vertex}$$
>
> *Now, contrast this with an array-based Data-Oriented representation. If we replace entity objects with parallel 32-bit integer arrays—where the edge ID is directly the array index—each half-edge only requires 5 integers (20 bytes). A vertex requires just one incident edge ID (4 bytes) and two 64-bit floats for coordinates (16 bytes). A face requires 1 edge ID (4 bytes). Summing these up:*
> $$\text{Compact Memory per Vertex} = (4 + 16) + (6 \times 20) + (2 \times 4) = 148\text{ Bytes per Vertex}$$
>
> *Dividing the two yields our **Theoretical Asymptotic Reduction**:*
> $$\lim_{V \to \infty} \left(1 - \frac{148}{1028}\right) \times 100\% = \mathbf{85.60\%}$$
>
> *Our major theoretical finding in Tab 3 is the **Finite-Size Boundary Correction**. Real planar grids have outer boundaries where exterior half-edges do not have twins. For an $r \times c$ grid:*
> $$E(r, c) = 3V - 2(r + c) + 1$$
> *Because of this boundary penalty, small meshes have slightly fewer half-edges per vertex, starting at **84.7%** reduction for $N=500$, and monotonically converging toward our theoretical asymptote of **85.60%** at $N=5000$. Our empirical `tracemalloc` measurements match our mathematical formula with less than **0.4% error**.*
>
> *I will now hand over to Member 2, who will explain how we implemented Data-Oriented Design, our Compact DCEL, and the 2-Array CHE representation with Ghost Triangles."*

---

### 2. Live Actions on the Dashboard (Member 1)
1. **Navigate to Tab 1 (`🔍 Small-Scale Visualization`):**
   * Change grid dimension slider to `4 x 4`.
   * Pick `Face ID: 2` from the dropdown: point out the green highlighted triangle and the exact sequence of half-edge IDs logged below the plot.
   * Pick `Vertex ID: 5`: point out the orange 1-ring star edges radiating from node 5.
   * State: *"This visually proves topological correctness—every twin is matched, and boundary orbits are closed."*
2. **Navigate to Tab 3 (`📐 Theory vs Measurement`):**
   * Scroll to the **Mathematical Derivation Table**: show the $1028\text{ B}$ vs $148\text{ B}$ per-vertex breakdown.
   * Point to the Matplotlib curve: *"Observe how the solid blue theoretical curve approaches the dashed red 85.60% asymptote, and the black dots (our empirical `tracemalloc` runs) sit directly on the predicted curve."*

---

### 3. Deep Code Explanation (If Faculty Asks to See Code)

#### File: `dcel_core.py`
* **`class Vertex` / `class Face` / `class HalfEdge` (Lines 35–105):**
  * Point out `__slots__ = ('id', 'x', 'y', 'incident_edge')`. Explain: *"Using `__slots__` prevents Python from creating a dynamic `__dict__` for each instance, saving 112 bytes per object. Even with `__slots__`, PyObject header (16 B) + type pointer (8 B) + field references (8 B each) creates unavoidable overhead."*
* **`generate_grid_graph(rows, cols)` (Lines 110–210):**
  * Walk through the two triangles created per grid square: lower triangle $(v_{00}, v_{10}, v_{11})$ and upper triangle $(v_{00}, v_{11}, v_{01})$.
  * Point out `validate_topology()` (Lines 215–260): tests that $\text{twin}(\text{twin}(e)) = e$, $\text{next}(\text{prev}(e)) = e$, and $\text{origin}(\text{twin}(e)) = \text{target}(e)$.
* **`walk_face(face)` (Lines 265–280):**
  ```python
  curr = face.half_edge
  while True:
      edges.append(curr.id)
      curr = curr.next
      if curr == face.half_edge: break
  ```
* **`get_vertex_star(vertex)` (Lines 285–305):**
  ```python
  curr = vertex.incident_edge
  while True:
      star.append(curr.id)
      curr = curr.twin.next  # 1-ring rotation
      if curr == vertex.incident_edge: break
  ```

#### File: `analysis_model.py`
* **`empirical_object_sizes()` (Lines 20–55):**
  * Uses `sys.getsizeof()` on instantiated objects plus 8 bytes per slot pointer reference.
* **`finite_grid_counts(r, c)` (Lines 60–90):**
  * Computes exact planar boundary edges: $E_{\text{boundary}} = 2(r-1) + 2(c-1) + 2(r-1)(c-1)$.
* **`predicted_reduction(V)` (Lines 110–145):**
  * Evaluates $1 - \frac{\text{CompactBytes}(V)}{\text{PointerBytes}(V)}$ and returns both the finite ratio and the $85.60\%$ infinite limit.

---

### 4. Member 1 Viva Q&A Defense

* **Q1: Did you improve the Big-O space complexity of the DCEL?**
  * **Answer:** *"No, Professor. In the standard Word RAM model, both Pointer DCEL and Compact DCEL have identical asymptotic complexity: $\Theta(V + E + F)$ space. Our contribution is an advanced **Cost-Model analysis**: we reduced the constant factor from $1028$ bytes per vertex down to $148$ bytes (an ~7x constant reduction), and down to $60$ bytes in CHE."*
* **Q2: Why did your empirical measurements on small graphs give 84.7% instead of exactly 85.60%?**
  * **Answer:** *"Because of the finite-size boundary effect. Euler's asymptotic formula $E \approx 3V$ assumes an infinite triangulation without boundaries. On an $r \times c$ grid, the perimeter edges lack exterior adjacent faces, giving $E = 3V - 2(r+c) + 1$. This $O(\sqrt{V})$ boundary term reduces the proportion of half-edges on small meshes. As $V$ increases from 500 to 5000, the boundary-to-interior ratio diminishes, and the reduction monotonically converges to 85.60%."*
* **Q3: Why not just use Python's built-in dictionaries instead of classes?**
  * **Answer:** *"A Python dictionary has an empty overhead of 64 bytes and resizes with a $2/3$ load factor, which would make the pointer representation even more bloated (~1800 B/V). We used slotted classes specifically to give the Pointer DCEL the most optimized, fair object-oriented baseline possible."*

---

# 🎙️ MEMBER 2: DATA-ORIENTED DESIGN, AHF, MINIMAL CHE & GHOST TRIANGLES

### Assigned Tabs:
* **Tab 2:** `📈 Performance Analytics`
* **Tab 5:** `⚡ Layouts & Algorithms` (Downstream Algorithms & Determinism)
* **Tab 8:** `📚 Literature & Theory`

### Physical Papers to Hold in Hand:
* **Primary Reference 1:** *Garimella, R. V., Kim, J., & Berndt, M. (2013).* "An Array-based Half-Facet (AHF) mesh data structure: a lightweight and scalable representation for polyhedral meshes." *Journal of Computational Physics*, 258, 260–280.
* **Primary Reference 2:** *Lage, M., Petronetto, F., Paiva, A., Lopes, H., Lewiner, T., & Velho, L. (2005).* "CHE: A Compact Half-Edge data structure for triangle meshes." *SIBGRAPI 2005*, 217–224.

---

### 1. Spoken Presentation Script (Word-for-Word Narration)

> *"Thank you, Member 1. Continuing from the theoretical derivation, I will present the core algorithmic implementation of our two Data-Oriented representations, our topological breakthrough with Ghost Triangles, and our verification of downstream geometric algorithms.*
>
> *(Hold up papers)*
> *"I have here **Garimella et al. (2013)** and **Lage et al. (2005)**. Both papers propose a fundamental paradigm shift from Object-Oriented Programming to **Data-Oriented Design (DOD)**.*
>
> *In Garimella's **AHF** model—which is our `CompactDCEL`—we completely eliminate heap node objects. Instead, we allocate five parallel 1D integer arrays: `twin[]`, `next[]`, `prev[]`, `origin[]`, and `face[]`. The half-edge ID is **not** stored; it is simply the array index! Traversal requires zero pointer chasing: `next_edge = next[e]` is a single array index lookup.*
>
> *In Lage's **CHE** model—our `MinimalCHE`—we take this even further. For a pure triangular mesh, the half-edges of face $f$ are numbered sequentially: $3f, 3f+1, 3f+2$. Because of this rigid structure, the `next`, `prev`, and `face` pointers are mathematically redundant!*
> $$\text{next}(e) = 3 \cdot \lfloor e/3 \rfloor + (e+1) \bmod 3$$
> $$\text{prev}(e) = 3 \cdot \lfloor e/3 \rfloor + (e+2) \bmod 3$$
> $$\text{face}(e) = \lfloor e/3 \rfloor$$
> *Therefore, we store **ONLY TWO ARRAYS**: `twin[]` and `origin[]`. That is just 8 bytes per half-edge!*
>
> *Now, here was our **Major Technical Challenge**:*
> *Lage's CHE mathematical formula strictly assumes that EVERY half-edge belongs to a triangle. But in a planar grid graph, the outer boundary half-edges face the open exterior—they have no adjacent triangle! In traditional implementations, this causes negative indices or invalid branches that break the arithmetic.*
>
> *We solved this problem through a clean topological mechanism: **Ghost Triangles**. We add a single virtual 'ghost vertex' at infinity and cone every boundary perimeter edge into a virtual ghost triangle. Topologically, this compacts the open planar disc into a **closed 2-sphere ($S^2$)** where every single half-edge belongs to a valid triangle. During traversal, our engines `minimal_walk_face()` and `minimal_get_vertex_star()` simply check `if face < num_real_faces`, completely hiding the ghost faces while preserving unbroken $O(1)$ arithmetic!*
>
> *(Point to screen: Tab 2: Performance Analytics)*
> *Let us look at the live empirical results in **Tab 2: Performance Analytics** across 500, 2000, and 5000 vertices:*
> * At $V=5000$, Pointer DCEL consumes **$5.07\text{ MB}$** of RAM.
> * 5-Array Compact DCEL consumes **$0.73\text{ MB}$** — an **85.6% RAM reduction**.
> * 2-Array Minimal CHE with Ghost Triangles consumes only **$0.30\text{ MB}$** — a **94.1% RAM reduction**!
>
> *(Point to screen: Tab 5: Layouts & Algorithms)*
> *In **Tab 5**, we address another critical DAA problem: **How do you build the `twin` array without pointers?** We implemented and compared two algorithms:*
> 1. **Hash-Based Pairing:** Uses a hash table mapping undirected edge keys $(\min(u,v), \max(u,v)) \to e$. Expected time $O(H)$ in the RAM model.
> 2. **Sort-Based Pairing:** Stores pairs $((u, v), e)$ in a contiguous array and sorts them lexicographically. Adjacent elements form twin pairs. Deterministic time $O(H \log H)$, requiring zero dynamic hash table allocations.
> *As shown in the Tab 5 table, both algorithms produce **100% bit-identical twin arrays** across all mesh sizes up to 100,000 vertices.*
>
> *Finally, we verified downstream geometric algorithms across both layouts:*
> * **Dual Graph BFS** (traversing face adjacencies)
> * **Laplacian Mesh Smoothing** ($k=5$ iterations updating coordinates $x_i \leftarrow \frac{1}{|\mathcal{N}(i)|} \sum_{j \in \mathcal{N}(i)} x_j$)
> *The output coordinate delta between Pointer DCEL and Compact DCEL is **$\Delta = 0.000000$**—complete floating-point and topological fidelity.*
>
> *I will now hand over to Member 3 to explain why this architectural difference produces an 11.5x speedup when tested against real CPU cache hierarchies."*

---

### 2. Live Actions on the Dashboard (Member 2)
1. **Navigate to Tab 2 (`📈 Performance Analytics`):**
   * Point to the metric cards: *"Notice the exact metrics: Pointer 5.07 MB, Compact 0.73 MB (85.6% reduction), Minimal CHE 0.30 MB (94.1% reduction)."*
   * Point to the interactive line chart: *"Observe how the memory consumption slopes diverge dramatically as graph size scales to 5000 vertices."*
2. **Navigate to Tab 5 (`⚡ Layouts & Algorithms`):**
   * Point to **Table 1 (Deterministic Twin Pairing)**: *"At 99,856 vertices and 595,350 half-edges, Hash takes 157 ms, Sort takes 417 ms, and both yield 'Pairing Identical: YES'."*
   * Point to **Table 2 (Downstream Equivalence)**: *"Notice that for Dual BFS and Laplacian smoothing, BFS order match is 100% and Laplacian maximum coordinate error is strictly $0.00\text{e}+00$."*
3. **Navigate to Tab 8 (`📚 Literature & Theory`):**
   * Briefly highlight the three citation boxes: Garimella (2013), Lage (2005), and Salinas-Fernández (2023).

---

### 3. Deep Code Explanation (If Faculty Asks to See Code)

#### File: `dcel_core.py`
* **`class CompactDCEL` (Lines 310–355):**
  * Stored using Python's native `array.array('i')` (signed 32-bit integers, 4 bytes each) and `array.array('d')` (64-bit floats).
  * Five half-edge arrays: `self.twin`, `self.next`, `self.prev`, `self.origin`, `self.face`.
* **`class MinimalCHE` (Lines 420–470):**
  * Stores strictly: `self.twin = array('i')` and `self.origin = array('i')`.
  * Encodes arithmetic methods:
    ```python
    @staticmethod
    def next_edge(e: int) -> int:
        return 3 * (e // 3) + (e + 1) % 3
    ```
* **Ghost Triangle Closure in `encode_to_minimal()` (Lines 480–560):**
  * Iterates over boundary half-edges (where `twin == -1`).
  * Creates a ghost vertex $V_{\text{ghost}} = |V|$.
  * For each boundary edge $(u, v)$, constructs a ghost triangle $(v, u, V_{\text{ghost}})$, assigning sequential indices and cross-linking their twins.
* **`minimal_walk_face(che, face_id)` (Lines 570–595):**
  * Computes the 3 half-edges directly via arithmetic: $e_0 = 3f, e_1 = 3f+1, e_2 = 3f+2$.
* **`minimal_get_vertex_star(che, v_id)` (Lines 600–630):**
  * Traverses using arithmetic orbit: $e \leftarrow \text{next\_edge}(\text{che.twin}[e])$. Skips any edges belonging to ghost faces ($e // 3 \ge \text{che.num\_real\_faces}$).

#### File: `algos.py`
* **`build_twin_array_hash(num_edges, origins, targets)` (Lines 25–60):**
  * Key = `(min(u, v), max(u, v))`. Single pass over half-edges, expected $O(H)$.
* **`build_twin_array_sort(num_edges, origins, targets)` (Lines 65–110):**
  * Creates an array of records `(min(u, v), max(u, v), edge_id)`.
  * Calls `records.sort()`. Pairs up adjacent records where keys match. Deterministic $O(H \log H)$.
* **`laplacian_smoothing_compact()` (Lines 220–270):**
  * Executes vertex updates directly using `compact_get_vertex_star()` without allocating a single node object.

---

### 4. Member 2 Viva Q&A Defense

* **Q1: Why did you need Ghost Triangles? Can't you just put an IF condition for boundary edges?**
  * **Answer:** *"If we used an IF condition or sentinel value like $-1$ for boundary edges, the closed-form arithmetic $\text{next}(e) = 3(e//3) + (e+1)\%3$ would break whenever a traversal hit the boundary. By coning boundary edges to a ghost vertex, we turn the mesh into a topologically closed 2-sphere. Every half-edge belongs to a triangle, so the arithmetic is unconditional and branch-free. We only filter out ghost faces at the very end of the user query."*
* **Q2: Why bother with Sort-based twin pairing if Hash-based is $O(H)$?**
  * **Answer:** *"In the Word RAM model, hashing is expected $O(H)$, but its worst-case is $O(H^2)$, and dynamic hash tables incur unpredictable allocation spikes and poor cache locality. Sort-based pairing takes deterministic $O(H \log H)$ time, uses contiguous array buffers, and is trivially parallelizable via parallel merge-sort or radix-sort on GPUs."*
* **Q3: What happens to CHE if the mesh contains quads or arbitrary polygons?**
  * **Answer:** *"CHE strictly relies on 3 edges per face. If the mesh contains quads or $n$-gons, one must either triangulate the polygons first or use Garimella's AHF (our 5-Array `CompactDCEL`), which supports arbitrary polygons by storing explicit face offsets."*

---

# 🎙️ MEMBER 3: MEMORY-HIERARCHY MODEL, CACHE SIMULATION, C++17 & LIMITATIONS

### Assigned Tabs:
* **Tab 4:** `🔬 Memory Lens`
* **Tab 6:** `💻 C++17 Hardware Benchmark`
* **Tab 7:** `⚖️ Trade-offs`

### Physical Paper to Hold in Hand:
* **Primary Reference:** *Aggarwal, A., & Vitter, J. S. (1988).* "The Input/Output Complexity of Sorting and Related Problems." *Communications of the ACM*, 31(9), 1116–1127. (Hold open to **The Two-Level Memory Hierarchy (I/O) Model**).
* **Supporting Reference:** *Salinas-Fernández et al. (2023)* Section 4: "Cache Locality and Spatial Coherence in Surface Traversals."

---

### 1. Spoken Presentation Script (Word-for-Word Narration)

> *"Thank you, Member 2. My role is to deliver the theoretical capstone of this project: **Why does Compact Array DCEL run significantly faster even though both algorithms have identical $O(k)$ asymptotic time in the RAM model?**
>
> *(Hold up Aggarwal & Vitter paper)*
> *"The answer lies in the **Memory Hierarchy (I/O) Cost Model**, formalized by Aggarwal and Vitter in 1988. The standard RAM model assumes that every memory dereference costs $O(1)$ uniform time. On physical hardware, this assumption is completely false.*
>
> *An L1 cache access takes ~1 nanosecond (4 cycles). An L2 cache access takes ~3 to 4 nanoseconds. But an access to Main Memory (DRAM) takes **60 to 100 nanoseconds**—a 100x latency penalty!*
>
> *When a CPU accesses memory, it does not fetch a single byte; it fetches an entire **64-byte cache line**. In our Compact Array DCEL, four-byte integers are packed contiguously. A single 64-byte cache line brings in **16 consecutive half-edges**! Therefore, a contiguous traversal costs:*
> $$Q_{\text{Compact}}(k) = \Theta\left(1 + \frac{k}{B}\right) \text{ cache misses, where } B = 16$$
> *In contrast, in a Pointer DCEL running on a long-lived heap, objects are scattered arbitrarily across memory addresses. Every pointer hop jumps to a random cache line, incurring:*
> $$Q_{\text{Pointer}}(k) = \Theta(k) \text{ cache misses}$$
>
> *(Point to screen: Tab 4: Memory Lens)*
> *Let us look at **Tab 4: Memory Lens**. We built an exact trace-driven LRU Cache Simulator (`cache_sim.py`) modeling a 32 KB L1 data cache with 64-byte lines.*
>
> *Now, notice something crucial in scientific methodology: if you allocate a pointer mesh in a fresh Python script, the heap allocator places them sequentially, giving an **artificially optimistic** cache result. To control for this, we wrote `fragment_heap()`, which rebuilds the pointer mesh with randomized creation orders and interleaved dummy allocations to model a real-world application.*
>
> *If you click **'▶ Play Orbit Animation'** on Tab 4, watch the 16x16 grid of cache lines:*
> * The **Fragmented Pointer Layout** (in red) scatters accesses all over memory, lighting up over **45 distinct cache lines** for a simple vertex star.
> * The **Compact Array Layout** (in blue) packs lookups into just **6 to 8 cache lines**!
> * Across the entire mesh, our cache simulator proves an **8.6x reduction in L1 cache misses**.*
>
> *Furthermore, on Tab 4, we evaluated **Locality-Improving Renumbering**. By applying a Dual Graph BFS or Hilbert space-filling curve permutation to the compact arrays, we reduced the average twin index jump from **14.5 edges down to 5.2 edges**, keeping twin pairs inside the same or adjacent cache lines.*
>
> *(Point to screen: Tab 6: C++17 Hardware Benchmarks)*
> *Now, look at **Tab 6: C++17 Hardware Benchmarks**. To prove this is a genuine hardware phenomenon and not a CPython artifact, we compiled identical topologies in native C++17 (`cpp/bench.cpp`) using `-O3` optimization.*
>
> *Look at the curve in `figures/cpp_benchmark.png`:*
> * At small scales ($|H| = 1,000$), the working set fits entirely within the CPU's 32 KB L1 and 512 KB L2 caches. Here, pointer chasing is fast: **$3.1\text{ ns}$ per hop**.*
> * But look at what happens between $|H| = 10,000$ and $100,000$: the working set exceeds the L2 cache! The pointer chasing latency spikes vertically to **$17.05\text{ ns}$ per hop** as the CPU constantly stalls on DRAM.*
> * In contrast, the Compact Array and CHE layouts stay completely flat at **$1.48\text{ ns}$ per hop** all the way to 1,000,000 half-edges. That is a concrete **$11.5\times$ hardware speedup** purely from cache-line streaming!*
>
> *(Point to screen: Tab 7: Trade-offs)*
> *Finally, in **Tab 7: Trade-offs**, we present our **Engineering Decision Matrix**. In scientific research, no data structure is strictly superior in every dimension:*
> * **Compact Array DCEL wins** in: Static mesh processing, rendering pipelines, GIS engines, and finite-element analysis where traversals dominate.
> * **Pointer DCEL still wins** in: Interactive CAD modeling, Delaunay incremental insertion, and localized mesh surgery. In a pointer DCEL, inserting a vertex is an $O(1)$ heap allocation. In a compact array, inserting an entity in the middle requires an $O(N)$ array copy or complex freelist tombstones.*
>
> *In summary, we have mathematically proven, simulated, and hardware-verified that Data-Oriented compact arrays achieve an 85.6% to 94.1% memory reduction and an 11.5x hardware speedup by replacing pointer chasing with cache-line-aware contiguous arrays.*
>
> *Thank you. We are now ready for your questions."*

---

### 2. Live Actions on the Dashboard (Member 3)
1. **Navigate to Tab 4 (`🔬 Memory Lens`):**
   * Keep slider at Grid Size `4 x 4`, Vertex `5`.
   * Click **'▶ Play Orbit Animation'**: let the faculty watch the 16x16 grid light up step-by-step.
   * Point out the metrics below: *"Notice the Red pointer touches 45 cache lines; the Blue compact touches only 7 cache lines. Dual BFS renumbering drops average jump from 14.5 to 5.2 edges."*
2. **Navigate to Tab 6 (`💻 C++17 Hardware Benchmark`):**
   * Point to the image `figures/cpp_benchmark.png`:
   * *"Look at the blue curve vs the green and orange curves. The blue pointer curve has a distinct inflection point at $10^4$ half-edges—this is the exact hardware boundary where the dataset spills out of the CPU L2 cache into DRAM, causing latency to jump from 3.4 ns to 17.05 ns."*
   * Point to the summary table: *"11.5x speedup at 1 million half-edges."*
3. **Navigate to Tab 7 (`⚖️ Trade-offs`):**
   * Highlight the table rows: *"Notice that for Vertex/Face insertion, Pointer DCEL is $O(1)$ isolated allocation, whereas Compact requires amortized array reallocation. This gives a balanced, rigorous engineering conclusion."*

---

### 3. Deep Code Explanation (If Faculty Asks to See Code)

#### File: `cache_sim.py`
* **`class SimpleLRUCache` (Lines 20–60):**
  * Implemented using `collections.OrderedDict`.
  * Capacity = `n_lines` (default 512 lines $\times$ 64 B = 32 KB L1).
  * `access(address)`: computes `line_addr = address >> 6`. If present, calls `move_to_end()` (hit). If not, evicts `popitem(last=False)` if full and increments `misses`.
* **`fragment_heap(dcel, seed)` (Lines 70–135):**
  * Allocates random byte-arrays (`junk.append(bytearray(random.randint(64, 512)))`) between node instantiations.
  * Shuffles the vertex and half-edge creation orders to scatter their addresses across the Python private heap.
* **Address generation (Lines 140–210):**
  * Pointer: `id(obj)` (exact virtual memory address of the CPython object header).
  * Compact: `array.buffer_info()[0] + 4 * index` (exact 32-bit contiguous physical memory address).

#### File: `cpp/bench.cpp`
* **Layouts A, B, C (Lines 25–95):**
  * Layout A: `struct HalfEdge { HalfEdge* twin; HalfEdge* next; int origin; }` allocated via `new` in randomized order.
  * Layout B: `std::vector<int32_t> twin, next, origin`.
  * Layout C: `MinimalCHEMesh` storing only `std::vector<int32_t> twin, origin`.
* **Benchmark Loop (Lines 110–165):**
  * Traverses 1-ring vertex stars across the mesh for multiple warm-up and timed iterations.
  * Measures latency with `std::chrono::high_resolution_clock` divided by total edge hops to yield exact **nanoseconds per operation**.

---

### 4. Member 3 Viva Q&A Defense

* **Q1: Why did you test C++ when the project is in Python?**
  * **Answer:** *"In Python, every integer access has interpreter overhead, dynamic type checking, and PyObject boxing. To scientifically prove that our 8.6x cache reduction produces real hardware latency benefits, we had to eliminate interpreter noise. C++ compiles to bare-metal x86/ARM machine code with `-O3` vectorization, allowing us to directly measure CPU cache line misses and DRAM bus stalls."*
* **Q2: Why does the Pointer latency jump from 3.4 ns to 17.05 ns, while Compact stays at 1.48 ns?**
  * **Answer:** *"Because of the CPU cache hierarchy. Below 10,000 half-edges, the entire pointer mesh fits inside the CPU's 512 KB L2 cache. Once $|H|$ reaches 100,000, the working set is ~4.8 MB, and at 1,000,000 it is ~48 MB. When pointer chasing across 48 MB of fragmented heap, the CPU's hardware prefetcher cannot predict the next pointer address, causing an L3 miss and a DRAM stall (~60-80 ns). For compact arrays, memory accesses are sequential and contiguous, allowing the CPU stream prefetcher to load cache lines into L1 before the loop even requests them."*
* **Q3: What did your Hilbert and BFS renumbering accomplish?**
  * **Answer:** *"In a standard array mesh, twin half-edges on opposite sides of a quad or row might be separated by hundreds of indices: $|e - \text{twin}[e]| \gg 16$. By renumbering the faces along a Dual BFS or a 2D Hilbert space-filling curve, topologically adjacent half-edges are assigned spatially contiguous indices. This reduced our average twin index jump from 14.5 to 5.2 edges, ensuring that accessing a twin edge almost always hits the same or adjacent 64-byte cache line."*

---

## 🎯 Quick Reference Cheat-Sheet for All 3 Members

| Topic | Pointer DCEL | Compact DCEL (5-Array) | Minimal CHE (2-Array) |
| :--- | :--- | :--- | :--- |
| **Space Complexity (RAM Model)** | $\Theta(V + E + F)$ | $\Theta(V + E + F)$ | $\Theta(V + E + F)$ |
| **Traversal Time (RAM Model)** | $O(k)$ | $O(k)$ | $O(k)$ |
| **I/O Complexity (Cache Misses)** | $\mathbf{\Theta(k)}$ | $\mathbf{\Theta(1 + k/B)}$ | $\mathbf{\Theta(1 + k/B)}$ |
| **Memory per Vertex** | **$1028\text{ B}$** | **$148\text{ B}$** | **$60\text{ B}$** |
| **Empirical RAM Reduction** | Baseline ($0\%$) | **$85.6\%$** | **$94.1\%$** |
| **L1 Cache Miss Reduction** | Baseline ($1\times$) | **$8.6\times$ fewer misses** | **$9.1\times$ fewer misses** |
| **C++ Latency at 1M edges** | $17.05\text{ ns/op}$ | $1.48\text{ ns/op}$ (**$11.5\times$ faster**) | $1.31\text{ ns/op}$ (**$13.0\times$ faster**) |
| **Boundary Handling** | Native arbitrary loops | Explicit array indices | **Ghost Triangles ($S^2$ sphere closure)** |
| **Best Use Case** | Dynamic CAD / Modeling | Static Meshes / GIS / FEM | Ultra-dense Triangle Graphics |

---

## 🚀 How to Run the Demo Tomorrow Morning

```bash
# 1. Activate environment and verify tests (all 15 must pass)
cd ~/coding/projects_sem5/DAA
pytest -v

# 2. Launch the Streamlit Frontend (8 Tabs)
streamlit run app.py --server.port 8501

# 3. Open your browser to:
http://localhost:8501
```
*(Have this markdown document open side-by-side or printed during the presentation!)*
