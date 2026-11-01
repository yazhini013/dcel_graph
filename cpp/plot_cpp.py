"""
cpp/plot_cpp.py
===============
Parses C++ benchmarking CSV results and plots a log-log scaling chart:
Latency (ns / half-edge) vs. Mesh Size (|H|).
Annotates the hardware cache inflection point (L2/L3 boundary) where pointer chasing bends.
"""

import sys
import os
import pandas as pd
import matplotlib.pyplot as plt

def generate_plot(csv_path: str = "cpp_results.csv", output_png: str = "figures/cpp_benchmark.png"):
    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found at {csv_path}")
        return

    df = pd.read_csv(csv_path)
    os.makedirs(os.path.dirname(output_png), exist_ok=True)

    fig, ax = plt.subplots(figsize=(8, 5.5), dpi=150)

    layouts = df["layout"].unique()
    colors = {"Pointer": "#dc2626", "Compact3Array": "#2563eb", "MinimalCHE2Array": "#16a34a"}
    markers = {"Pointer": "o", "Compact3Array": "s", "MinimalCHE2Array": "^"}

    for layout in layouts:
        sub = df[df["layout"] == layout].sort_values("N")
        ax.plot(
            sub["N"],
            sub["ns_per_halfedge"],
            label=f"{layout}",
            color=colors.get(layout, "#475569"),
            marker=markers.get(layout, "o"),
            linewidth=2.0,
            markersize=6,
        )

    # Annotate Cache Thresholds (Typical Apple Silicon: L1=128KB, L2=4MB/16MB, L3/SLC=32MB)
    # At ~32 bytes/edge, 10^5 half-edges = 3.2 MB (approaching L2 capacity boundary)
    ax.axvline(x=50000, color="#94a3b8", linestyle="--", alpha=0.7)
    ax.text(52000, ax.get_ylim()[1] * 0.5 if ax.get_ylim()[1] > 0 else 10,
            "L2 Cache Boundary (~3 MB)", color="#64748b", fontsize=8.5, rotation=90)

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Mesh Size: Half-Edge Count (|H|)", fontsize=10, fontweight="bold")
    ax.set_ylabel("Traversal Latency (ns / half-edge)", fontsize=10, fontweight="bold")
    ax.set_title("C++17 Traversal Latency: Pointer DCEL vs. Compact Arrays (DOD)", fontsize=11, fontweight="bold", pad=12)
    ax.grid(True, which="both", linestyle=":", alpha=0.4)
    ax.legend(frameon=True, fontsize=9)

    plt.tight_layout()
    plt.savefig(output_png)
    plt.close(fig)
    print(f"Saved C++ scaling plot to {output_png}")


if __name__ == "__main__":
    csv_file = sys.argv[1] if len(sys.argv) > 1 else "cpp_results.csv"
    generate_plot(csv_file)

