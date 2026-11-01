#!/usr/bin/env bash
set -e

echo "=== Compiling C++ Benchmark (clang++ -O2 -std=c++17) ==="
clang++ -O2 -std=c++17 cpp/bench.cpp -o cpp/bench_bin

echo "=== Running Traversal Latency Benchmark across mesh scales ==="
./cpp/bench_bin 500 2000 10000 50000 150000 > cpp_results.csv

echo "=== Benchmark Results CSV ==="
cat cpp_results.csv

echo "=== Plotting Log-Log Scaling Curves ==="
python3 cpp/plot_cpp.py cpp_results.csv

echo "=== Done! Plot saved to figures/cpp_benchmark.png ==="

