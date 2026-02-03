# ingest_whu.py
import os
import pandas as pd
import geopandas as gpd
from PIL import Image
import base64
import io

# --- Configuration ---
# This points to the folder created by the organize_whu.py script.
DATASET_BASE_PATH = './datasets/Building change detection dataset_add/test1' 
OUTPUT_FILE = './datasets/whu_dataset_registry.csv'

def encode_image_to_base64(image_path):
    """Reads an image file and returns its Base64 encoded string."""
    try:
        with Image.open(image_path) as img:
            buffer = io.BytesIO()
            # Convert to RGB to ensure consistency and save as JPEG for efficiency
            img.convert('RGB').save(buffer, format="JPEG")
            encoded_string = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return f"data:image/jpeg;base64,{encoded_string}"
    except Exception as e:
        print(f"Error encoding image {image_path}: {e}")
        return None

def create_whu_registry():
    """Scans the organized WHU dataset, encodes images, and creates a registry file."""
    print("\n--- ⚙️ Starting Data Ingestion Script ---")
    image_a_dir = os.path.join(DATASET_BASE_PATH, 'image_A')
    image_b_dir = os.path.join(DATASET_BASE_PATH, 'image_B')
    
    if not os.path.isdir(image_a_dir):
        print(f"❌ ERROR: Directory not found: '{image_a_dir}'")
        print("Please run 'organize_whu.py' first to create the correct file structure.")
        return
        
    image_files = os.listdir(image_a_dir)
    data_records = []
    
    print(f"Found {len(image_files)} image pairs. Processing...")

    for i, filename in enumerate(image_files):
        if not filename.endswith(('.tif', '.png', '.jpg')):
            continue

        pair_id = os.path.splitext(filename)[0]
        
        # --- Process 'Before' Image (A) from 2012 ---
        before_path = os.path.join(image_a_dir, filename)
        before_b64 = encode_image_to_base64(before_path)
        if before_b64:
            data_records.append({
                'image_id': f'WHU-{pair_id}-A',
                'dataset': 'WHU-Building',
                'timestamp': '2012-01-01', # Representative 'before' date
                'image_b64': before_b64,
                'pair_id': pair_id
            })
        
        # --- Process 'After' Image (B) from 2016 ---
        after_path = os.path.join(image_b_dir, filename)
        after_b64 = encode_image_to_base64(after_path)
        if after_b64:
            data_records.append({
                'image_id': f'WHU-{pair_id}-B',
                'dataset': 'WHU-Building',
                'timestamp': '2016-01-01', # Representative 'after' date
                'image_b64': after_b64,
                'pair_id': pair_id
            })
        
        print(f"Processed pair {i+1}/{len(image_files)}: {filename}")

    # Create a Pandas DataFrame
    df = pd.DataFrame(data_records)
    
    # --- Add Placeholder Geometry Data ---
    # WHU images don't have real-world coordinates, so we add placeholders.
    df['latitude'] = 30.5  # Placeholder lat for Wuhan
    df['longitude'] = 114.3 # Placeholder lon for Wuhan
    
    # Convert to a GeoDataFrame
    gdf = gpd.GeoDataFrame(
        df, geometry=gpd.points_from_xy(df.longitude, df.latitude), crs="EPSG:4326"
    )
    
    # Save the registry to a CSV file
    gdf.to_csv(OUTPUT_FILE, index=False)
    print(f"\n--- ✅ Success! Created registry with {len(gdf)} records at {OUTPUT_FILE} ---")


if __name__ == "__main__":
    create_whu_registry()