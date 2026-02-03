# create_demo_data.py

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
import os

def create_demo_gpkg(dataset_name: str):
    """
    Creates a mock GPKG file. For 'xView1', it generates a specific temporal
    scenario. For others, it creates an empty file.
    """
    print(f"Generating demo data for {dataset_name}...")

    output_dir = os.path.join("datasets", "gpkgs", "geeo25")
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, f"{dataset_name.lower()}_images.gpkg")

    if dataset_name == "xView1":
        # A controlled set of data points around India Gate, New Delhi
        # to demonstrate changes over time.
        demo_data = [
            # January 2024: Two events start
            {'date': '2024-01-15', 'lat': 28.6129, 'lon': 77.2295, 'status': 'Monitoring Point A Activated', 'id': 1},
            {'date': '2024-01-20', 'lat': 28.6125, 'lon': 77.2290, 'status': 'Monitoring Point B Activated', 'id': 2},
            
            # February 2024: A new event starts
            {'date': '2024-02-10', 'lat': 28.6133, 'lon': 77.2300, 'status': 'New Anomaly Detected', 'id': 3},

            # March 2024: A final event appears
            {'date': '2024-03-05', 'lat': 28.6120, 'lon': 77.2285, 'status': 'Final Checkpoint Established', 'id': 4},
        ]
        
        # Convert the list of dictionaries to a pandas DataFrame
        df = pd.DataFrame(demo_data)
        num_records = len(df)
        
        # Add the other required columns
        df['dataset'] = dataset_name
        df['uoi'] = [f'{dataset_name}_{i}' for i in range(num_records)]
        
        # Create the GeoDataFrame
        geometry = gpd.points_from_xy(df['lon'], df['lat'])
        gdf = gpd.GeoDataFrame(df, geometry=geometry)

    else:
        # For other datasets, create an empty GeoDataFrame with the correct columns
        gdf = gpd.GeoDataFrame({
            'image_id': [], 'date': [], 'dataset': [], 'uoi': [], 'status': [], 'geometry': []
        })

    # Set the Coordinate Reference System (CRS)
    gdf.set_crs("EPSG:4326", inplace=True)

    # Save to a GeoPackage file
    gdf.to_file(file_path, driver='GPKG', layer=f'{dataset_name.lower()}_images')
    print(f"Successfully created demo file at: {file_path}\n")


if __name__ == "__main__":
    required_datasets = ["xView1", "FAIR1M", "BigEarthNet"]

    for ds in required_datasets:
        create_demo_gpkg(ds)
        
    print("All demo data files have been generated!")