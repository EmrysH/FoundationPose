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
    
    # Calculate mesh center and dimensions
    mesh_center = o3d_mesh.get_center()
    mesh_dims = o3d_mesh.get_max_bound() - o3d_mesh.get_min_bound()
    coord_frame_size = np.max(mesh_dims) * 0.2  # 20% of the largest dimension
    
    # Create coordinate frame at mesh center
    coordinate_frame = o3d.geometry.TriangleMesh.create_coordinate_frame(
        size=coord_frame_size,
        origin=mesh_center
    )
    
    # Create visualization window
    vis = o3d.visualization.Visualizer()
    vis.create_window()
    
    # Add mesh and coordinate frame to visualizer
    vis.add_geometry(o3d_mesh)
    vis.add_geometry(coordinate_frame)
    
    # Set up camera view
    vis.get_view_control().set_zoom(0.8)
    vis.get_view_control().set_front([0, 0, -1])
    vis.get_view_control().set_lookat(mesh_center)
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