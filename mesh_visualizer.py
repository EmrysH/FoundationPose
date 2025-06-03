import trimesh
import numpy as np
import open3d as o3d
import argparse
import os

def visualize_mesh(mesh_path):
    # Load the mesh
    mesh = trimesh.load(mesh_path)
    
    # Convert trimesh to open3d for visualization
    vertices = np.array(mesh.vertices)
    faces = np.array(mesh.faces)
    
    # Create Open3D mesh
    o3d_mesh = o3d.geometry.TriangleMesh()
    o3d_mesh.vertices = o3d.utility.Vector3dVector(vertices)
    o3d_mesh.triangles = o3d.utility.Vector3iVector(faces)
    
    # Compute vertex normals for better visualization
    o3d_mesh.compute_vertex_normals()
    
    # Create visualization window
    vis = o3d.visualization.Visualizer()
    vis.create_window()
    
    # Add mesh to visualizer
    vis.add_geometry(o3d_mesh)
    
    # Set up camera view
    vis.get_view_control().set_zoom(0.8)
    vis.get_view_control().set_front([0, 0, -1])
    vis.get_view_control().set_lookat([0, 0, 0])
    vis.get_view_control().set_up([0, -1, 0])
    
    # Run visualization
    vis.run()
    vis.destroy_window()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--mesh_file', type=str, required=True,
                      help='Path to the mesh file (supports .obj, .ply, etc.)')
    args = parser.parse_args()
    
    visualize_mesh(args.mesh_file) 