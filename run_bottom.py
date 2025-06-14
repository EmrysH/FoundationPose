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
import numpy as np
import cv2
import os
import logging
import trimesh
import imageio
from Utils import *

def calculate_slot_poses(object_pose, slot_coords):
    """
    Calculate 6D poses of slots based on object pose and slot coordinates
    @param object_pose: 4x4 transformation matrix of the object
    @param slot_coords: Nx2 array of slot coordinates (X,Y) in object frame
    @return: Nx4x4 array of slot poses in camera frame
    """
    slot_poses = []
    for coord in slot_coords:
        # Create slot pose in object frame (assuming slots are on top surface)
        slot_pose = np.eye(4)
        slot_pose[:2, 3] = coord  # Set X,Y coordinates
        slot_pose[2, 3] = 0  # Z coordinate (assuming slots are on surface)
        
        # Transform slot pose to camera frame
        slot_pose_cam = object_pose @ slot_pose
        slot_poses.append(slot_pose_cam)
    
    return np.array(slot_poses)

if __name__=='__main__':
  parser = argparse.ArgumentParser()
  code_dir = os.path.dirname(os.path.realpath(__file__))
  parser.add_argument('--mesh_file', type=str, default=f'{code_dir}/demo_data/bottom/mesh/Frame_bottom.obj')
  # parser.add_argument('--mesh_file', type=str, default=f'{code_dir}/demo_data/test/mesh/Frame2_110.obj')

  parser.add_argument('--test_scene_dir', type=str, default=f'{code_dir}/demo_data/bottom')
  # parser.add_argument('--test_scene_dir', type=str, default=f'{code_dir}/demo_data/test')
  parser.add_argument('--est_refine_iter', type=int, default=5)
  parser.add_argument('--track_refine_iter', type=int, default=2)
  parser.add_argument('--debug', type=int, default=1)
  parser.add_argument('--debug_dir', type=str, default=f'{code_dir}/debug')
  parser.add_argument('--slot_coords', type=str, default='[[-0.07,-0.06], [0.07,-0.06], [0.07,0.06], [-0.07,0.06]]', 
                    help='JSON string of slot coordinates [[x1,y1], [x2,y2], ...]')
  args = parser.parse_args()

  # Parse slot coordinates
  import json
  slot_coords = np.array(json.loads(args.slot_coords))

  set_logging_format()
  set_seed(0)

  mesh = trimesh.load(args.mesh_file)

  debug = args.debug
  debug_dir = args.debug_dir
  os.system(f'rm -rf {debug_dir}/* && mkdir -p {debug_dir}/track_vis {debug_dir}/ob_in_cam {debug_dir}/slot_poses')

  to_origin, extents = trimesh.bounds.oriented_bounds(mesh)
  bbox = np.stack([-extents/2, extents/2], axis=0).reshape(2,3)

  scorer = ScorePredictor()
  refiner = PoseRefinePredictor()
  glctx = dr.RasterizeCudaContext()
  est = FoundationPose(model_pts=mesh.vertices, model_normals=mesh.vertex_normals, mesh=mesh, scorer=scorer, refiner=refiner, debug_dir=debug_dir, debug=debug, glctx=glctx)
  logging.info("estimator initialization done")

  reader = YcbineoatReader(video_dir=args.test_scene_dir, shorter_side=None, zfar=np.inf)

  for i in range(len(reader.color_files)):
    logging.info(f'i:{i}')
    color = reader.get_color(i)
    depth = reader.get_depth(i)
    if i==0:
      mask = reader.get_mask(0).astype(bool)
      pose = est.register(K=reader.K, rgb=color, depth=depth, ob_mask=mask, iteration=args.est_refine_iter)
      print(f"Predicted 6D pose for frame {i}:")
      print(pose)

      if debug>=3:
        m = mesh.copy()
        m.apply_transform(pose)
        m.export(f'{debug_dir}/model_tf.obj')
        xyz_map = depth2xyzmap(depth, reader.K)
        valid = depth>=0.001
        pcd = toOpen3dCloud(xyz_map[valid], color[valid])
        o3d.io.write_point_cloud(f'{debug_dir}/scene_complete.ply', pcd)
    else:
      pose = est.track_one(rgb=color, depth=depth, K=reader.K, iteration=args.track_refine_iter)
      print(f"Predicted 6D pose for frame {i}:")
      print(pose)

    # Calculate slot poses
    slot_poses = calculate_slot_poses(pose, slot_coords)
    
    # Save slot poses
    os.makedirs(f'{debug_dir}/slot_poses', exist_ok=True)
    for j, slot_pose in enumerate(slot_poses):
      np.savetxt(f'{debug_dir}/slot_poses/{reader.id_strs[i]}_slot{j}.txt', slot_pose.reshape(4,4))

    os.makedirs(f'{debug_dir}/ob_in_cam', exist_ok=True)
    np.savetxt(f'{debug_dir}/ob_in_cam/{reader.id_strs[i]}.txt', pose.reshape(4,4))

    if debug>=1:
      center_pose = pose@np.linalg.inv(to_origin)
      vis = draw_posed_3d_box(reader.K, img=color, ob_in_cam=center_pose, bbox=bbox)
      vis = draw_xyz_axis(color, ob_in_cam=center_pose, scale=0.1, K=reader.K, thickness=3, transparency=0, is_input_rgb=True)
      
      # Visualize slot poses
      for slot_pose in slot_poses:
        slot_center_pose = slot_pose@np.linalg.inv(to_origin)
        vis = draw_xyz_axis(vis, ob_in_cam=slot_center_pose, scale=0.05, K=reader.K, thickness=2, transparency=0, is_input_rgb=True)
      
      cv2.imshow('1', vis[...,::-1])
      cv2.waitKey(1)

    if debug>=2:
      os.makedirs(f'{debug_dir}/track_vis', exist_ok=True)
      imageio.imwrite(f'{debug_dir}/track_vis/{reader.id_strs[i]}.png', vis)

