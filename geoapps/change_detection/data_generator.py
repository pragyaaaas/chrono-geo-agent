# geoapps/change_detection/data_generator.py

import numpy as np
from PIL import Image
import io
import base64
import os

def load_and_encode_images(before_path, after_path):
    """Loads two images from file, converts them to NumPy and Base64."""
    
    def image_to_base64_and_numpy(path):
        # Open the image
        img = Image.open(path)
        
        # Convert to NumPy array for processing
        numpy_array = np.array(img)
        
        # Encode to Base64 string for display
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        encoded_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return f"data:image/png;base64,{encoded_image}", numpy_array

    # Load the "before" image
    before_b64, before_np = image_to_base64_and_numpy(before_path)
    
    # Load the "after" image
    after_b64, after_np = image_to_base64_and_numpy(after_path)

    return before_b64, after_b64, before_np, after_np