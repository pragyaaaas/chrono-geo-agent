# geoapps/change_detection/detect_changes.py

import numpy as np
from PIL import Image
import io
import base64
import cv2 # Import OpenCV

def run_rgb_change_detection(before_image_np, after_image_np):
    """
    Takes two RGB NumPy arrays, finds the difference, thresholds it,
    and returns a Base64 encoded change map.
    """
    # 1. Convert images to grayscale for easier comparison
    before_gray = cv2.cvtColor(before_image_np, cv2.COLOR_RGB2GRAY)
    after_gray = cv2.cvtColor(after_image_np, cv2.COLOR_RGB2GRAY)

    # 2. Compute the absolute difference between the two images
    diff = cv2.absdiff(before_gray, after_gray)

    # 3. Apply a threshold to get a binary map of significant changes
    # This value may need tuning for different image pairs
    threshold_value = 50 
    _, thresholded_diff = cv2.threshold(diff, threshold_value, 255, cv2.THRESH_BINARY)
    
    # 4. Convert the black and white change map to a Base64 string
    img = Image.fromarray(thresholded_diff, 'L') # 'L' mode for grayscale
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    encoded_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    return f"data:image/png;base64,{encoded_image}"