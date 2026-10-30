"""
baseline_dcel.py
----------------
This is the baseline Object-Oriented Doubly Connected Edge List (DCEL).
It serves as the "Ground Truth" for the DAA project.
"""

# ==========================================
# 1. CORE OOP CLASSES
# ==========================================

class Vertex:
    def __init__(self, v_id):
        self.id = v_id
        # Points to ONE outgoing HalfEdge from this vertex
        self.incident_edge = None  

    def __repr__(self):
        return f"Vertex({self.id})"

class Face:
    def __init__(self, f_id):
        self.id = f_id
        # Points to ONE HalfEdge on the boundary of this face
        self.inner_component = None  

    def __repr__(self):
        return f"Face({self.id})"

class HalfEdge:
    def __init__(self, e_id):
        self.id = e_id
        self.origin = None  # The Vertex where this edge starts
        self.twin = None    # The reverse HalfEdge
        self.next = None    # The next HalfEdge around the face
        self.prev = None    # The previous HalfEdge around the face
        self.face = None    # The Face this edge bounds

    def __repr__(self):
        return f"Edge({self.id})"


# ==========================================
# 2. GROUND TRUTH GRAPH GENERATOR
# ==========================================

def create_two_triangle_graph():
    """
    Creates a square split by a diagonal line.
    
    Vertices:
    V0 (top-left) ----- V3 (top-right)
      |                / |
      |  Face 1 (F1)  /  |
      |              /   |
      |             /    | Face 0 (Outer)
      |            /     |
      |  Face 2   /      |
      |   (F2)   /       |
      |         /        |
    V1 (bot-left) ----- V2 (bot-right)
    """
    
    # 1. Create Vertices
    v0 = Vertex("V0")
    v1 = Vertex("V1")
    v2 = Vertex("V2")
    v3 = Vertex("V3")
    vertices = [v0, v1, v2, v3]

    # 2. Create Faces
    f1 = Face("F1") # Top-left triangle
    f2 = Face("F2") # Bottom-right triangle
    f0 = Face("F0") # The infinite outer face
    faces = [f1, f2, f0]

    # 3. Create Half-Edges (10 total: 5 physical edges * 2 directions)
    e1   = HalfEdge("e1 (V0->V1)")
    e1_t = HalfEdge("e1_t (V1->V0)")
    
    e2   = HalfEdge("e2 (V1->V2)")
    e2_t = HalfEdge("e2_t (V2->V1)")
    
    e3   = HalfEdge("e3 (V2->V0)")   # The diagonal
    e3_t = HalfEdge("e3_t (V0->V2)") # The diagonal reverse
    
    e4   = HalfEdge("e4 (V2->V3)")
    e4_t = HalfEdge("e4_t (V3->V2)")
    
    e5   = HalfEdge("e5 (V3->V0)")
    e5_t = HalfEdge("e5_t (V0->V3)")

    edges = [e1, e1_t, e2, e2_t, e3, e3_t, e4, e4_t, e5, e5_t]

    # 4. Wire up Twins (Easy part)
    e1.twin, e1_t.twin = e1_t, e1
    e2.twin, e2_t.twin = e2_t, e2
    e3.twin, e3_t.twin = e3_t, e3
    e4.twin, e4_t.twin = e4_t, e4
    e5.twin, e5_t.twin = e5_t, e5

    # 5. Wire up Face 1 (V0 -> V1 -> V2 -> V0) - Counter-clockwise
    e1.origin, e1.face, e1.next, e1.prev = v0, f1, e2, e3
    e2.origin, e2.face, e2.next, e2.prev = v1, f1, e3, e1
    e3.origin, e3.face, e3.next, e3.prev = v2, f1, e1, e2
    f1.inner_component = e1

    # 6. Wire up Face 2 (V0 -> V2 -> V3 -> V0) - Counter-clockwise
    e3_t.origin, e3_t.face, e3_t.next, e3_t.prev = v0, f2, e4, e5
    e4.origin, e4.face, e4.next, e4.prev = v2, f2, e5, e3_t
    e5.origin, e5.face, e5.next, e5.prev = v3, f2, e3_t, e4
    f2.inner_component = e3_t

    # 7. Wire up Face 0 (Outer Face) (V0 -> V3 -> V2 -> V1 -> V0) - Clockwise
    e5_t.origin, e5_t.face, e5_t.next, e5_t.prev = v0, f0, e4_t, e1_t
    e4_t.origin, e4_t.face, e4_t.next, e4_t.prev = v3, f0, e2_t, e5_t
    e2_t.origin, e2_t.face, e2_t.next, e2_t.prev = v2, f0, e1_t, e4_t
    e1_t.origin, e1_t.face, e1_t.next, e1_t.prev = v1, f0, e5_t, e2_t
    f0.inner_component = e5_t

    # 8. Set Vertex Incident Edges (Any outgoing edge works)
    v0.incident_edge = e1
    v1.incident_edge = e2
    v2.incident_edge = e3
    v3.incident_edge = e5

    return {"vertices": vertices, "faces": faces, "edges": edges}


# ==========================================
# 3. TRAVERSAL ALGORITHMS
# ==========================================

def walk_face(face):
    """
    Finds all vertices that make up the boundary of a given face.
    It loops by following the 'next' pointer until it hits the start.
    """
    start_edge = face.inner_component
    current_edge = start_edge
    
    bounding_vertices = []
    
    while True:
        bounding_vertices.append(current_edge.origin.id)
        current_edge = current_edge.next
        
        if current_edge == start_edge:
            break # We completed the circle!
            
    return bounding_vertices

def get_vertex_star(vertex):
    """
    Finds all edges pointing AWAY from a vertex.
    It loops by jumping to the 'twin' (which points IN), 
    then taking the 'next' edge (which points OUT again).
    """
    start_edge = vertex.incident_edge
    current_edge = start_edge
    
    outgoing_edges = []
    
    while True:
        outgoing_edges.append(current_edge.id)
        # To spin around a vertex: jump to the twin, then take the next edge
        current_edge = current_edge.twin.next
        
        if current_edge == start_edge:
            break # We completed the circle!
            
    return outgoing_edges


# ==========================================
# 4. MAIN EXECUTION (Proof that it works)
# ==========================================

if __name__ == "__main__":
    print("--- DAA Project: Baseline DCEL Loaded ---")
    
    # Generate the graph
    graph = create_two_triangle_graph()
    
    # Extract pieces for testing
    f1 = graph["faces"][0] # Face 1
    v0 = graph["vertices"][0] # Vertex 0
    
    print("\n[Test 1] Face Traversal:")
    print(f"Vertices bounding {f1.id}:", walk_face(f1))
    # Expected: ['V0', 'V1', 'V2']
    
    print("\n[Test 2] Vertex Star Traversal:")
    print(f"Edges leaving {v0.id}:", get_vertex_star(v0))
    # Expected: ['e1 (V0->V1)', 'e5_t (V0->V3)', 'e3_t (V0->V2)']
    
    print("\nReady for Member 2 to encode!")