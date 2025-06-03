import trimesh
import numpy as np
import open3d as o3d
import argparse
import os

def load_mesh(mesh_path):
    # Load the mesh
    mesh = trimesh.load(mesh_path)
    
    # Convert trimesh to open3d for visualization
    vertices = np.array(mesh.vertices)
    faces = np.array(mesh.faces)
    
    # Create Open3D mesh
    o3d_mesh = o3d.geometry.TriangleMesh()
    o3d_mesh.vertices = o3d.utility.Vector3dVector(vertices)
    o3d_mesh.triangles = o3d.utility.Vector3iVector(faces)
    
    # Center the mesh at origin
    o3d_mesh.compute_vertex_normals()
    o3d_mesh.translate(-o3d_mesh.get_center())
    return o3d_mesh

def print_pose(object_name: str, translation: list, rotation: list):
    print(f"\nObject: {object_name}")
    print(f"Position (x, y, z): [{translation[0]:.3f}, {translation[1]:.3f}, {translation[2]:.3f}]")
    print(f"Rotation (degrees): [{rotation[0]:.3f}, {rotation[1]:.3f}, {rotation[2]:.3f}]")

def visualize_assembly(mesh_paths, translations, rotations):
    # Create visualization window
    vis = o3d.visualization.Visualizer()
    vis.create_window()
    
    # Process each mesh
    for i, (mesh_path, translation, rotation) in enumerate(zip(mesh_paths, translations, rotations)):
        # Load mesh
        mesh = load_mesh(mesh_path)
        center = mesh.get_center()
        
        # Apply transformation
        rotation_rad = np.radians(rotation)
        R = mesh.get_rotation_matrix_from_xyz(rotation_rad)
        mesh.rotate(R, center=[0, 0, 0])
        mesh.translate(translation)
        
        # Create coordinate frame
        frame = o3d.geometry.TriangleMesh.create_coordinate_frame(size=0.1)
        frame.rotate(R, center=[0, 0, 0])
        frame.translate(center + translation)
        
        # Add to visualization
        vis.add_geometry(mesh)
        vis.add_geometry(frame)
        
        # Print pose information
        print_pose(os.path.basename(mesh_path), translation, rotation)
    
    # Set up camera view
    vis.get_view_control().set_zoom(0.8)
    vis.get_view_control().set_front([0, 0, -1])
    vis.get_view_control().set_lookat([0, 0, 0])
    vis.get_view_control().set_up([0, -1, 0])
    
    # Run visualization
    vis.run()
    vis.destroy_window()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Visualize up to 6 3D objects with their poses')
    
    # Add arguments for each object
    for i in range(1, 7):
        parser.add_argument(f'--mesh{i}', type=str,
                          help=f'Path to mesh file {i} (supports .obj, .ply, etc.)')
        parser.add_argument(f'--translation{i}', type=float, nargs=3, default=[0, 0, 0],
                          help=f'Translation vector for mesh {i} [x y z]')
        parser.add_argument(f'--rotation{i}', type=float, nargs=3, default=[0, 0, 0],
                          help=f'Rotation angles in degrees for mesh {i} [rx ry rz]')
    
    args = parser.parse_args()
    
    # Collect mesh paths, translations, and rotations
    mesh_paths = []
    translations = []
    rotations = []
    
    for i in range(1, 7):
        mesh_path = getattr(args, f'mesh{i}')
        if mesh_path:  # Only add if mesh path is provided
            mesh_paths.append(mesh_path)
            translations.append(getattr(args, f'translation{i}'))
            rotations.append(getattr(args, f'rotation{i}'))
    
    if not mesh_paths:
        print("Error: At least one mesh file must be specified")
        exit(1)
    
    visualize_assembly(mesh_paths, translations, rotations)