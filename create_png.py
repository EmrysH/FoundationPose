from PIL import Image
import numpy as np

def create_rgb_image(r, g, b, output_filename="output.png"):
    """
    Create a 1024x1024 PNG image with specified RGB values.
    
    Args:
        r (int): Red value (0-255)
        g (int): Green value (0-255)
        b (int): Blue value (0-255)
        output_filename (str): Name of the output PNG file
    """
    # Create a 1024x1024 array with the specified RGB values
    # Shape is (1024, 1024, 3) for RGB
    image_array = np.full((1024, 1024, 3), [r, g, b], dtype=np.uint8)
    
    # Convert the array to an image
    image = Image.fromarray(image_array)
    
    # Save the image as PNG
    image.save(output_filename)
    print(f"Image saved as {output_filename}")

if __name__ == "__main__":
    # Example usage: Create a red image (255, 0, 0)
    create_rgb_image(255, 252,250, "material.png")
    