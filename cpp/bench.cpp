/**
 * bench.cpp
 * =========
 * High-Performance C++17 Traversal Benchmarks:
 * Layout A: Fragmented Pointer DCEL (struct HalfEdge* on heap)
 * Layout B: Contiguous 3-Array Compact DCEL (std::vector<int>)
 * Layout C: Contiguous 2-Array Minimal CHE (Arithmetic next)
 *
 * Grounding:
 * Models the memory hierarchy (I/O) cost model:
 * Pointer walk = Theta(k) cache misses; Contiguous walk = Theta(1 + k/B) cache misses.
 */

#include <iostream>
#include <vector>
#include <chrono>
#include <algorithm>
#include <random>
#include <numeric>
#include <cmath>
#include <fstream>
#include <cstdint>

// ============================================================================
// DATA STRUCTURE LAYOUTS
// ============================================================================

// Layout A: Pointer DCEL
struct HalfEdge {
    HalfEdge* twin{nullptr};
    HalfEdge* next{nullptr};
    int origin{-1};
};

// ============================================================================
// TOPOLOGY GENERATOR (Identical to Python generate_grid_graph)
// ============================================================================

struct MeshData {
    int num_vertices;
    int num_faces;
    int num_edges;
    std::vector<int> twin;
    std::vector<int> next;
    std::vector<int> origin;
    std::vector<int> vertex_incident;
    std::vector<int> face_edge;
};

MeshData generate_grid(int rows, int cols) {
    int n_v = rows * cols;
    int n_int_f = 2 * (rows - 1) * (cols - 1);
    int B = 2 * (rows - 1) + 2 * (cols - 1);
    int n_f = n_int_f + 1; // including outer face
    int n_e = 3 * n_int_f + B;

    MeshData m;
    m.num_vertices = n_v;
    m.num_faces = n_f;
    m.num_edges = n_e;
    m.twin.assign(n_e, -1);
    m.next.assign(n_e, -1);
    m.origin.assign(n_e, -1);
    m.vertex_incident.assign(n_v, -1);
    m.face_edge.assign(n_f, -1);

    // Map directed edge (u, v) -> edge ID
    std::vector<std::pair<int, int>> edges(n_e);
    int e_cnt = 0;
    int f_cnt = 0;

    auto add_he = [&](int u, int v, int fid) {
        int eid = e_cnt++;
        m.origin[eid] = u;
        edges[eid] = {u, v};
        if (m.vertex_incident[u] == -1) m.vertex_incident[u] = eid;
        return eid;
    };

    // Internal quads
    for (int r = 0; r < rows - 1; ++r) {
        for (int c = 0; c < cols - 1; ++c) {
            int bl = r * cols + c;
            int br = r * cols + (c + 1);
            int tl = (r + 1) * cols + c;
            int tr = (r + 1) * cols + (c + 1);

            // Triangle A
            int fa = f_cnt++;
            int a0 = add_he(bl, br, fa);
            int a1 = add_he(br, tr, fa);
            int a2 = add_he(tr, bl, fa);
            m.next[a0] = a1; m.next[a1] = a2; m.next[a2] = a0;
            m.face_edge[fa] = a0;

            // Triangle B
            int fb = f_cnt++;
            int b0 = add_he(bl, tr, fb);
            int b1 = add_he(tr, tl, fb);
            int b2 = add_he(tl, bl, fb);
            m.next[b0] = b1; m.next[b1] = b2; m.next[b2] = b0;
            m.face_edge[fb] = b0;
        }
    }

    // Pair internal twins
    std::vector<std::tuple<int, int, int>> sort_edges;
    sort_edges.reserve(3 * n_int_f);
    for (int e = 0; e < 3 * n_int_f; ++e) {
        int u = edges[e].first;
        int v = edges[e].second;
        sort_edges.push_back({std::min(u, v), std::max(u, v), e});
    }
    std::sort(sort_edges.begin(), sort_edges.end());

    std::vector<int> boundary_internal;
    for (size_t i = 0; i < sort_edges.size(); ) {
        if (i + 1 < sort_edges.size() &&
            std::get<0>(sort_edges[i]) == std::get<0>(sort_edges[i+1]) &&
            std::get<1>(sort_edges[i]) == std::get<1>(sort_edges[i+1])) {
            int e1 = std::get<2>(sort_edges[i]);
            int e2 = std::get<2>(sort_edges[i+1]);
            m.twin[e1] = e2;
            m.twin[e2] = e1;
            i += 2;
        } else {
            boundary_internal.push_back(std::get<2>(sort_edges[i]));
            i += 1;
        }
    }

    // Outer face
    int f_outer = f_cnt++;
    std::vector<int> outer_edges;
    for (int int_e : boundary_internal) {
        int u = edges[int_e].first;
        int v = edges[int_e].second;
        int out_e = add_he(v, u, f_outer);
        m.twin[int_e] = out_e;
        m.twin[out_e] = int_e;
        outer_edges.push_back(out_e);
    }
    m.face_edge[f_outer] = outer_edges.empty() ? -1 : outer_edges[0];

    // Link outer next pointers
    std::vector<int> out_start(n_v, -1);
    for (int out_e : outer_edges) {
        out_start[m.origin[out_e]] = out_e;
    }
    for (int out_e : outer_edges) {
        int target = m.origin[m.twin[out_e]];
        m.next[out_e] = out_start[target];
    }

    return m;
}

// ============================================================================
// MAIN BENCHMARK ENGINE
// ============================================================================

int main(int argc, char** argv) {
    std::cout << "N,layout,ns_per_halfedge,bytes,checksum\n";

    std::vector<int> target_V = {500, 2000, 5000, 20000, 100000};
    if (argc > 1) {
        target_V.clear();
        for (int i = 1; i < argc; ++i) target_V.push_back(std::stoi(argv[i]));
    }

    std::mt19937 rng(42);

    for (int V_target : target_V) {
        int r = std::max(2, (int)std::sqrt(V_target));
        int c = std::max(2, V_target / r);
        MeshData mesh = generate_grid(r, c);
        int H = mesh.num_edges;

        // --------------------------------------------------------------------
        // Layout A: Fragmented Pointer DCEL
        // --------------------------------------------------------------------
        std::vector<HalfEdge*> ptr_edges(H);
        std::vector<int> alloc_order(H);
        std::iota(alloc_order.begin(), alloc_order.end(), 0);
        std::shuffle(alloc_order.begin(), alloc_order.end(), rng);

        // Allocate in shuffled order
        for (int idx : alloc_order) {
            ptr_edges[idx] = new HalfEdge();
            ptr_edges[idx]->origin = mesh.origin[idx];
        }
        for (int i = 0; i < H; ++i) {
            ptr_edges[i]->twin = ptr_edges[mesh.twin[i]];
            ptr_edges[i]->next = ptr_edges[mesh.next[i]];
        }

        std::vector<HalfEdge*> ptr_v_inc(mesh.num_vertices);
        for (int v = 0; v < mesh.num_vertices; ++v) {
            ptr_v_inc[v] = ptr_edges[mesh.vertex_incident[v]];
        }

        // Benchmark Layout A Vertex Star Walk (7 runs, median)
        std::vector<double> runs_ptr;
        int64_t chk_ptr = 0;

        for (int run = 0; run < 8; ++run) {
            auto t0 = std::chrono::high_resolution_clock::now();
            chk_ptr = 0;
            for (int v = 0; v < mesh.num_vertices; ++v) {
                HalfEdge* start = ptr_v_inc[v];
                if (!start) continue;
                HalfEdge* cur = start;
                while (true) {
                    chk_ptr += cur->origin;
                    cur = cur->twin->next;
                    if (cur == start) break;
                }
            }
            auto t1 = std::chrono::high_resolution_clock::now();
            if (run > 0) {
                double ns = std::chrono::duration_cast<std::chrono::nanoseconds>(t1 - t0).count();
                runs_ptr.push_back(ns / H);
            }
        }
        std::sort(runs_ptr.begin(), runs_ptr.end());
        double ns_ptr = runs_ptr[runs_ptr.size() / 2];
        size_t bytes_ptr = H * sizeof(HalfEdge) + H * sizeof(HalfEdge*);
        std::cout << H << ",Pointer," << ns_ptr << "," << bytes_ptr << "," << chk_ptr << "\n";

        // Cleanup Layout A
        for (int i = 0; i < H; ++i) delete ptr_edges[i];

        // --------------------------------------------------------------------
        // Layout B: Compact 3-Array (twin, next, origin)
        // --------------------------------------------------------------------
        std::vector<int>& tw = mesh.twin;
        std::vector<int>& nx = mesh.next;
        std::vector<int>& og = mesh.origin;
        std::vector<int>& vi = mesh.vertex_incident;

        std::vector<double> runs_cmp;
        int64_t chk_cmp = 0;

        for (int run = 0; run < 8; ++run) {
            auto t0 = std::chrono::high_resolution_clock::now();
            chk_cmp = 0;
            for (int v = 0; v < mesh.num_vertices; ++v) {
                int start = vi[v];
                if (start < 0) continue;
                int cur = start;
                while (true) {
                    chk_cmp += og[cur];
                    cur = nx[tw[cur]];
                    if (cur == start) break;
                }
            }
            auto t1 = std::chrono::high_resolution_clock::now();
            if (run > 0) {
                double ns = std::chrono::duration_cast<std::chrono::nanoseconds>(t1 - t0).count();
                runs_cmp.push_back(ns / H);
            }
        }
        std::sort(runs_cmp.begin(), runs_cmp.end());
        double ns_cmp = runs_cmp[runs_cmp.size() / 2];
        size_t bytes_cmp = H * 3 * sizeof(int);
        std::cout << H << ",Compact3Array," << ns_cmp << "," << bytes_cmp << "," << chk_cmp << "\n";

        // --------------------------------------------------------------------
        // Layout C: MinimalCHE 2-Array (twin, origin; arithmetic next)
        // --------------------------------------------------------------------
        // For internal triangle edges: next(e) = 3*(e/3) + (e+1)%3
        int n_int_f = 2 * (r - 1) * (c - 1);
        int max_internal_e = 3 * n_int_f;

        std::vector<double> runs_min;
        int64_t chk_min = 0;

        for (int run = 0; run < 8; ++run) {
            auto t0 = std::chrono::high_resolution_clock::now();
            chk_min = 0;
            for (int v = 0; v < mesh.num_vertices; ++v) {
                int start = vi[v];
                if (start < 0) continue;
                int cur = start;
                while (true) {
                    chk_min += og[cur];
                    int t = tw[cur];
                    // Fast arithmetic next for triangles, fallback to array for boundary
                    cur = (t < max_internal_e) ? (3 * (t / 3) + (t + 1) % 3) : nx[t];
                    if (cur == start) break;
                }
            }
            auto t1 = std::chrono::high_resolution_clock::now();
            if (run > 0) {
                double ns = std::chrono::duration_cast<std::chrono::nanoseconds>(t1 - t0).count();
                runs_min.push_back(ns / H);
            }
        }
        std::sort(runs_min.begin(), runs_min.end());
        double ns_min = runs_min[runs_min.size() / 2];
        size_t bytes_min = H * 2 * sizeof(int);
        std::cout << H << ",MinimalCHE2Array," << ns_min << "," << bytes_min << "," << chk_min << "\n";
    }

    return 0;
}

