# geoapps/geeo/database.py
import os
import geopandas as gpd
from shapely.geometry import box
from typing import Optional
from agent_core.modules.toolset import agent_tool
from geoplatform.utils import build_where_date_clause
from geoapps.geeo.constants import (
    IMGS_NONE_MSG, IMGS_EMPTY_MSG, 
    DATASET_ERROR_MSG,
    DATASETS_INFO, DATASETS_KEYS, GPKG_FOLDER
)
from .data_manager import DataManager

class Database:
    """Lightweight toolset for database operations. Accesses the DataManager."""
    
    def __init__(self, data_manager: DataManager):
        self.name = "database"
        self.data_manager = data_manager

    def reset_database(self):
        self.data_manager.reset_data()

    def _load_gpkg_images(self, dataset, start_date=None, end_date=None):
        where_clause = build_where_date_clause(start_date, end_date, DATASETS_INFO[dataset].get("images_date_column", "date"))
        gpkg_path = os.path.join(GPKG_FOLDER, DATASETS_INFO[dataset]["images_file"])
        gpkg_layer = DATASETS_INFO[dataset]["images_layer"]
        return gpd.read_file(gpkg_path, layer=gpkg_layer, where=where_clause)

    @agent_tool
    def query_dataset_images(self, dataset: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
        """
        Loads images from a GeoPackage dataset (like xView1, FAIR1M) into memory.
        """
        if dataset not in DATASETS_INFO: return DATASET_ERROR_MSG.format(dataset=dataset, datasets=DATASETS_KEYS)
        _gdf = self._load_gpkg_images(dataset, start_date, end_date)
        self.data_manager.update_gdf(dataset, _gdf)
        return f"Successfully loaded {len(_gdf)} images from {dataset}."

    @agent_tool
    def query_images_by_aoi_coords(self, dataset: str, lat_min: float, lat_max: float, lon_min: float, lon_max: float, start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
        """
        Loads images from a GeoPackage dataset (like xView1, FAIR1M) that intersect
        with a specified Area of Interest (AOI) and date range.
        """
        if dataset not in DATASETS_INFO: return DATASET_ERROR_MSG.format(dataset=dataset, datasets=DATASETS_KEYS)
        _gdf = self._load_gpkg_images(dataset, start_date, end_date)
        if _gdf.empty: return IMGS_EMPTY_MSG
        
        aoi = box(lon_min, lat_min, lon_max, lat_max)
        _gdf = _gdf[_gdf.geometry.intersects(aoi)]
        
        self.data_manager.update_gdf(dataset, _gdf)
        return f"Successfully loaded {len(_gdf)} images from {dataset} within the specified AOI."
    
    @agent_tool
    def list_available_datasets(self) -> str:
        """Returns a list of all currently loaded dataset names."""
        dataset_names = list(self.data_manager.images_gdf.keys())
        return f"Available datasets are: {', '.join(dataset_names)}"

    @agent_tool
    def list_whu_image_ids(self) -> str:
        """
        Returns a summary of available 'WHU-Building' dataset image IDs.
        """
        dataset_name = 'WHU-Building'
        gdf = self.data_manager.get_gdf(dataset_name)
        if gdf.empty:
            return f"Error: The {dataset_name} dataset is not loaded or is empty."

        count = len(gdf)
        sample_ids = ", ".join(gdf['image_id'].tolist()[:5])
        return f"Found {count} images in '{dataset_name}'. Example IDs: {sample_ids}, ..."