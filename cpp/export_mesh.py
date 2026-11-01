"""
cpp/export_mesh.py
==================
Exports Python DCEL topology to binary format for the C++ benchmarking harness.
Guarantees byte-level topological identity between Python and C++ test runs.
"""

import struct
from dcel_core import generate_grid_graph, encode_to_compact


def export_mesh_binary(dcel, filepath: str = "cpp/mesh_exported.bin"):
    compact = encode_to_compact(dcel)
    n_v = compact.num_vertices
    n_f = compact.num_faces
    n_e = compact.num_edges

    # Checksum: sum of origin array elements
    chk = sum(compact.origin)

    with open(filepath, "wb") as f:
        # 4 x int32 header
        f.write(struct.pack("<4i", n_v, n_f, n_e, chk))
        # Arrays
        compact.twin.tofile(f)
        compact.next.tofile(f)
        compact.origin.tofile(f)
        compact.vertex_incident.tofile(f)
        compact.face_edge.tofile(f)

    print(f"Exported mesh (V={n_v}, F={n_f}, HE={n_e}) to {filepath}")


if __name__ == "__main__":
    dcel = generate_grid_graph(20, 20)
    export_mesh_binary(dcel)

