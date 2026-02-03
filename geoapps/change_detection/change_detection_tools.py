# geoapps/change_detection/change_detection_tools.py

from agent_core.modules.toolset import agent_tool
from geoapps.geeo.data_manager import DataManager
import numpy as np
from PIL import Image
import io
import base64
from .detect_changes import run_rgb_change_detection

class ChangeDetectionTools:
    """Lightweight toolset for change detection. Accesses the DataManager."""

    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
        self.name = "ChangeDetectionTools"

    def _decode_b64_to_np(self, b64_string: str) -> np.ndarray:
        if ',' in b64_string:
            b64_string = b64_string.split(',')[1]
        img_bytes = base64.b64decode(b64_string)
        img = Image.open(io.BytesIO(img_bytes)).convert('RGB')
        return np.array(img)

    @agent_tool
    def detect_changes_in_images_by_id(self, before_image_id: str, after_image_id: str) -> str:
        """
        Runs change detection using two image IDs.
        The resulting change mask is saved to memory, not returned.
        """
        dataset_name = 'WHU-Building'
        gdf = self.data_manager.get_gdf(dataset_name)
        if gdf.empty:
            return f"Error: The {dataset_name} dataset is not loaded."

        before_row = gdf[gdf['image_id'] == before_image_id]
        after_row = gdf[gdf['image_id'] == after_image_id]

        if before_row.empty or after_row.empty:
            return f"Error: One or both image IDs ('{before_image_id}', '{after_image_id}') were not found."

        before_b64 = before_row.iloc[0]['image_b64']
        after_b64 = after_row.iloc[0]['image_b64']
        
        before_np = self._decode_b64_to_np(before_b64)
        after_np = self._decode_b64_to_np(after_b64)

        change_mask_b64 = run_rgb_change_detection(before_np, after_np)
        
        # --- THIS IS THE FIX ---
        # Save the result to the DataManager instead of returning it
        self.data_manager.latest_change_mask = change_mask_b64
        
        print(f"✅ Successfully generated and saved change mask for {before_image_id} and {after_image_id}.")
        # Return a short, safe message
        return f"Change mask generated for {before_image_id} and {after_image_id}. It is ready to be displayed."