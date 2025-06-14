# Copyright (c) 2023, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

from estimater import *
from datareader import *
import argparse
import cv2
import numpy as np
import trimesh
import os
import logging
import imageio


def set_logging_format():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def cleanup():
    """Cleanup function to close all windows and release resources."""
    cv2.destroyAllWindows()
    logging.info("Cleanup completed")


if __name__=='__main__':
    try:
        parser = argparse.ArgumentParser()
        code_dir = os.path.dirname(os.path.realpath(__file__))
        parser.add_argument('--mesh_file', type=str, default=f'{code_dir}/demo_data/bottom/mesh/Frame_bottom.obj',
                          help='Path to the object mesh file (.obj)')
        parser.add_argument('--image_file', type=str, default=f'{code_dir}/demo_data/bottom/rgb/1749024958297536434.png',
                          help='Path to the input RGB image')
        parser.add_argument('--depth_file', type=str, default=f'{code_dir}/demo_data/bottom/depth/1749024958297536434.png',
                          help='Path to the input depth image')
        parser.add_argument('--mask_file', type=str, default=f'{code_dir}/demo_data/bottom/masks/1749024958297536434.png',
                          help='Path to the object mask image')
        parser.add_argument('--camera_matrix', type=str, default=f'{code_dir}/demo_data/bottom/cam_K.txt',
                          help='Path to camera matrix file (4x4 matrix in txt format)')
        parser.add_argument('--est_refine_iter', type=int, default=5)
        parser.add_argument('--debug', type=int, default=1)
        parser.add_argument('--debug_dir', type=str, default=f'{code_dir}/debug')
        args = parser.parse_args()

        set_logging_format()
        set_seed(0)

        # Load mesh
        mesh = trimesh.load(args.mesh_file)

        # Setup debug directory
        debug = args.debug
        debug_dir = args.debug_dir
        os.system(f'rm -rf {debug_dir}/* && mkdir -p {debug_dir}/track_vis {debug_dir}/ob_in_cam')

        # Calculate bounding box
        to_origin, extents = trimesh.bounds.oriented_bounds(mesh)
        bbox = np.stack([-extents/2, extents/2], axis=0).reshape(2,3)

        # Initialize predictors
        scorer = ScorePredictor()
        refiner = PoseRefinePredictor()
        glctx = dr.RasterizeCudaContext()
        est = FoundationPose(model_pts=mesh.vertices, 
                            model_normals=mesh.vertex_normals, 
                            mesh=mesh, 
                            scorer=scorer, 
                            refiner=refiner, 
                            debug_dir=debug_dir, 
                            debug=debug, 
                            glctx=glctx)
        logging.info("estimator initialization done")

        # Load input data
        color = cv2.imread(args.image_file)
        if color is None:
            raise ValueError(f"Could not load image from {args.image_file}")
        color = cv2.cvtColor(color, cv2.COLOR_BGR2RGB)
        
        depth = cv2.imread(args.depth_file, cv2.IMREAD_UNCHANGED)
        if depth is None:
            raise ValueError(f"Could not load depth from {args.depth_file}")
        depth = depth.astype(np.float32) / 1000.0  # Convert to float32 and scale to meters
        
        mask = cv2.imread(args.mask_file, cv2.IMREAD_GRAYSCALE)
        if mask is None:
            raise ValueError(f"Could not load mask from {args.mask_file}")
        mask = mask.astype(bool)

        # Load camera matrix
        K = np.loadtxt(args.camera_matrix)

        # Predict pose
        pose = est.register(K=K, rgb=color, depth=depth, ob_mask=mask, iteration=args.est_refine_iter)
        print("Predicted 6D pose:")
        print(pose)

        # Save results
        os.makedirs(f'{debug_dir}/ob_in_cam', exist_ok=True)
        np.savetxt(f'{debug_dir}/ob_in_cam/predicted_pose.txt', pose.reshape(4,4))

        # Visualization
        if debug >= 1:
            center_pose = pose @ np.linalg.inv(to_origin)
            vis = draw_posed_3d_box(K, img=color, ob_in_cam=center_pose, bbox=bbox)
            vis = draw_xyz_axis(color, ob_in_cam=center_pose, scale=0.1, K=K, thickness=3, transparency=0, is_input_rgb=True)
            cv2.imshow('Prediction Result', vis[...,::-1])
            cv2.waitKey(0)

        if debug >= 2:
            os.makedirs(f'{debug_dir}/track_vis', exist_ok=True)
            imageio.imwrite(f'{debug_dir}/track_vis/prediction_result.png', vis)

        if debug >= 3:
            m = mesh.copy()
            m.apply_transform(pose)
            m.export(f'{debug_dir}/model_tf.obj')
            xyz_map = depth2xyzmap(depth, K)
            valid = depth >= 0.001
            pcd = toOpen3dCloud(xyz_map[valid], color[valid])
            o3d.io.write_point_cloud(f'{debug_dir}/scene_complete.ply', pcd)

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        raise
    finally:
        cleanup() 