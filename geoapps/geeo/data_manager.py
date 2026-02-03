# geoapps/geeo/data_manager.py
import pandas as pd
import geopandas as gpd

class DataManager:
    """
    This class is responsible for loading and holding all application data.
    It does not contain any agent tools.
    """
    def __init__(self):
        self.images_gdf = {} # Dictionary to hold all GeoDataFrames
        self.latest_change_mask = None # A spot to store the last change mask
        
        # --- DISABLED: WHU DATASET LOADING ---
        # self.load_whu_dataset_from_csv()

    def load_whu_dataset_from_csv(self):
        """
        Loads the pre-processed WHU dataset registry from its CSV file
        and adds it to the images_gdf dictionary.
        """
        dataset_name = 'WHU-Building'
        registry_path = './datasets/whu_dataset_registry.csv'
        
        print(f"DataManager: Attempting to load {dataset_name} dataset...")
        try:
            df = pd.read_csv(registry_path)
            gdf = gpd.GeoDataFrame(
                df, geometry=gpd.points_from_xy(df.longitude, df.latitude), crs="EPSG:4326"
            )
            self.images_gdf[dataset_name] = gdf
            print(f"✅ DataManager: Successfully loaded {len(gdf)} records for '{dataset_name}'.")
        except FileNotFoundError:
            print(f"❌ WARNING: DataManager could not find '{registry_path}'.")

    def get_gdf(self, dataset: str) -> gpd.GeoDataFrame:
        """Safely gets a GeoDataFrame for a given dataset."""
        return self.images_gdf.get(dataset, gpd.GeoDataFrame())

    def update_gdf(self, dataset: str, gdf: gpd.GeoDataFrame):
        """Updates the GDF for a dataset, merging if it exists."""
        if dataset not in self.images_gdf or self.images_gdf[dataset].empty:
            self.images_gdf[dataset] = gdf.copy()
        else:
            merged_gdf = pd.concat([self.images_gdf[dataset], gdf], ignore_index=True)
            # Use 'image_id' for WHU data, 'uoi' for others
            subset_col = 'image_id' if dataset == 'WHU-Building' else 'uoi'
            if subset_col in merged_gdf.columns:
                merged_gdf = merged_gdf.drop_duplicates(subset=[subset_col])
            self.images_gdf[dataset] = merged_gdf
    
    def reset_data(self):
        """Clears all data."""
        self.images_gdf.clear()
        self.latest_change_mask = None
        
        # --- DISABLED: WHU DATASET RELOADING ---
        # self.load_whu_dataset_from_csv()