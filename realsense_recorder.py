import pyrealsense2 as rs
import numpy as np
import cv2
import os
import time

def create_folders():
    # Create timestamp for folder names
    timestamp = int(time.time())
    
    # Create folders for RGB and depth images
    rgb_folder = "data/rgb"
    depth_folder = "data/depth"
    
    os.makedirs(rgb_folder, exist_ok=True)
    os.makedirs(depth_folder, exist_ok=True)
    
    return rgb_folder, depth_folder, timestamp

def save_camera_intrinsics(pipeline, folder):
    # Get the depth sensor's intrinsics
    depth_sensor = pipeline.get_active_profile().get_device().first_depth_sensor()
    depth_intrinsics = depth_sensor.as_video_stream_profile().get_intrinsics()
    
    # Create the camera matrix in the specified format
    K = np.array([
        [depth_intrinsics.fx, 0, depth_intrinsics.ppx],
        [0, depth_intrinsics.fy, depth_intrinsics.ppy],
        [0, 0, 1]
    ])
    
    # Save to file with the specified format
    with open(os.path.join(folder, 'Cam_K.txt'), 'w') as f:
        for row in K:
            f.write(' '.join([f'{x:.18e}' for x in row]) + '\n')

def main():
    # Create folders
    rgb_folder, depth_folder, timestamp = create_folders()
    
    # Configure depth and color streams
    pipeline = rs.pipeline()
    config = rs.config()
    
    # Configure streams
    config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
    config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
    
    # Start streaming
    pipeline.start(config)
    
    # Save camera intrinsics
    save_camera_intrinsics(pipeline, "data")
    
    try:
        frame_count = 0
        print("Recording started. Press 'q' to stop.")
        
        while True:
            # Wait for a coherent pair of frames: depth and color
            frames = pipeline.wait_for_frames()
            depth_frame = frames.get_depth_frame()
            color_frame = frames.get_color_frame()
            
            if not depth_frame or not color_frame:
                continue
            
            # Convert images to numpy arrays
            depth_image = np.asanyarray(depth_frame.get_data())
            color_image = np.asanyarray(color_frame.get_data())
            
            # Get current timestamp in nanoseconds
            current_time = int(time.time_ns())
            
            # Save images with timestamp
            cv2.imwrite(f"{rgb_folder}/{current_time}.png", color_image)
            cv2.imwrite(f"{depth_folder}/{current_time}.png", depth_image)
            
            # Display images (depth image is shown as is)
            cv2.imshow('RGB Stream', color_image)
            cv2.imshow('Depth Stream', depth_image)
            
            frame_count += 1
            
            # Break the loop if 'q' is pressed
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    finally:
        # Stop streaming
        pipeline.stop()
        cv2.destroyAllWindows()
        print(f"Recording stopped. Saved {frame_count} frames.")
        print(f"RGB images saved in: {rgb_folder}")
        print(f"Depth images saved in: {depth_folder}")

if __name__ == "__main__":
    main() 