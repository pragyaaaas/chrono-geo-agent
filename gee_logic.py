import ee
import geemap
import os

# --- 1. Initialize GEE ---
try:
    ee.Initialize()
except Exception:
    ee.Authenticate()
    ee.Initialize()

# --- 2. Helper Functions ---

def get_roi_from_name(place_name):
    print(f"Searching for location: {place_name}...")
    place_name = place_name.title() 
    
    # Use FAO GAUL for global administrative boundaries
    level1 = ee.FeatureCollection("FAO/GAUL/2015/level1")
    level2 = ee.FeatureCollection("FAO/GAUL/2015/level2")
    
    # Try exact match on State/Province
    roi_feat = level1.filter(ee.Filter.eq('ADM1_NAME', place_name))
    
    # If not found, try Partial Match on District/City
    if roi_feat.size().getInfo() == 0:
        roi_feat = level2.filter(ee.Filter.stringContains('ADM2_NAME', place_name))
        
    if roi_feat.size().getInfo() > 0:
        return roi_feat.first().geometry()
    else:
        return None

def analyze_deforestation(place_name, start_year, end_year):
    """ Detects vegetation loss using Hansen Global Forest Change. """
    roi = get_roi_from_name(place_name)
    if not roi: return f"Could not find location '{place_name}'.", None

    # Updated to 2024 version to fix Deprecation Warning
    hansen = ee.Image('UMD/hansen/global_forest_change_2024_v1_12')
    
    start_idx = int(start_year) - 2000
    end_idx = int(end_year) - 2000
    lossyear = hansen.select('lossyear')
    loss_mask = lossyear.gte(start_idx).And(lossyear.lte(end_idx))
    
    # Scale=30 for faster processing
    area = loss_mask.multiply(ee.Image.pixelArea()).reduceRegion(
        reducer=ee.Reducer.sum(), geometry=roi, scale=30, maxPixels=1e10
    )
    loss_ha = area.get('lossyear').getInfo()
    if loss_ha is None: loss_ha = 0
    loss_ha = loss_ha / 10000

    # FIX: Use Esri Satellite Map
    m = geemap.Map(basemap='Esri.WorldImagery')
    m.centerObject(roi, 10)
    m.addLayer(roi, {'color': 'blue'}, 'Sector Boundary', True, 0.1)
    m.addLayer(loss_mask.selfMask(), {'palette': ['red']}, f'Clearing {start_year}-{end_year}')
    
    filename = "map_deforestation.html"
    output_path = os.path.join(os.getcwd(), "assets", filename)
    m.to_html(output_path)
    
    return f"Vegetation density analysis complete. {loss_ha:.2f} hectares cleared between {start_year}-{end_year}.", filename

def analyze_urbanization(place_name, year1, year2):
    """ Detects new infrastructure using Dynamic World. """
    roi = get_roi_from_name(place_name)
    if not roi: return f"Could not find location '{place_name}'.", None

    dw = ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1')
    
    def get_lulc(year):
        return dw.filterBounds(roi).filterDate(f'{year}-01-01', f'{year}-12-31') \
                 .select('label').mode().clip(roi)

    lulc_t1 = get_lulc(year1)
    lulc_t2 = get_lulc(year2)

    # Class 6 is Built-up
    new_built = lulc_t1.neq(6).And(lulc_t2.eq(6))
    
    area = new_built.multiply(ee.Image.pixelArea()).reduceRegion(
        reducer=ee.Reducer.sum(), geometry=roi, scale=30, maxPixels=1e10
    )
    built_ha = area.get('label').getInfo()
    if built_ha is None: built_ha = 0
    built_ha = built_ha / 10000

    # FIX: Use Esri Satellite Map
    m = geemap.Map(basemap='Esri.WorldImagery')
    m.centerObject(roi, 12)
    m.addLayer(roi, {'color': 'blue'}, 'Sector Boundary', True, 0.1)
    m.addLayer(new_built.selfMask(), {'palette': ['ff0000']}, f'New Infrastructure {year1}-{year2}')
    
    filename = "map_urbanization.html"
    output_path = os.path.join(os.getcwd(), "assets", filename)
    m.to_html(output_path)

    return f"Infrastructure scan complete. Detected {built_ha:.2f} hectares of new structural signatures.", filename

def analyze_flood_sar(place_name, year):
    """
    Uses Sentinel-1 SAR (Radar) to detect floods.
    HIGH PRECISION VERSION: Filters out general wetness to find deep water.
    """
    roi = get_roi_from_name(place_name)
    if not roi: return f"Could not find location '{place_name}'.", None

    print(f"📡 Activating Sentinel-1 Radar for Flood Scan in {place_name}...")

    # Get Sentinel-1 Data
    s1 = ee.ImageCollection('COPERNICUS/S1_GRD') \
        .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV')) \
        .filter(ee.Filter.eq('instrumentMode', 'IW')) \
        .filterBounds(roi)

    start_date = f'{year}-01-01'
    end_date = f'{year}-12-31'
    
    # 1. Baseline: Median (Normal Year)
    baseline = s1.filterDate(start_date, end_date).select('VV').median().clip(roi)
    
    # 2. Flood Event: 5th Percentile (The absolute darkest/wettest moment of the year)
    flood_img = s1.filterDate(start_date, end_date).select('VV').reduce(ee.Reducer.percentile([5])).rename('VV').clip(roi)

    # 3. Calculate Difference
    # We remove smoothing to get sharper edges
    diff = baseline.subtract(flood_img)

    # 4. STRICT THRESHOLD (The Magic Number)
    # Raised to 3.5. Only VERY distinct changes (Land -> Deep Water) will pass.
    flood_mask = diff.gt(3.5).selfMask()

    # Visualization - FIX: Use Esri Satellite Map
    m = geemap.Map(basemap='Esri.WorldImagery')
    m.centerObject(roi, 10)
    m.addLayer(roi, {'color': 'grey'}, 'Region', True, 0.1)
    
    # Cyan for water
    m.addLayer(flood_mask, {'palette': ['00FFFF'], 'opacity': 0.8}, f'Detected Flood Water ({year})')

    filename = "map_flood.html"
    output_path = os.path.join(os.getcwd(), "assets", filename)
    m.to_html(output_path)
    
    # Calculate Area
    area = flood_mask.multiply(ee.Image.pixelArea()).reduceRegion(
        reducer=ee.Reducer.sum(), geometry=roi, scale=100, maxPixels=1e10
    )
    flood_ha = area.get('VV').getInfo()
    if flood_ha is None: flood_ha = 0
    flood_ha = flood_ha / 10000

    return f"Sentinel-1 SAR Scan Complete. Detected {flood_ha:.2f} hectares of significant inundation.", filename

def analyze_fire_optical(place_name, year):
    """
    Uses Sentinel-2 NBR with a FOREST MASK to prevent false positives.
    """
    roi = get_roi_from_name(place_name)
    if not roi: return f"Could not find location '{place_name}'.", None
    
    print(f"🔥 Activating Sentinel-2 for Burn Scar Analysis in {place_name}...")

    s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
            .filterDate(f'{year}-01-01', f'{year}-12-31') \
            .filterBounds(roi) \
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))

    def calc_nbr(image):
        return image.normalizedDifference(['B8', 'B12']).rename('NBR')

    # 1. Get the "Healthiest" view of the year (Pre-fire state)
    max_nbr = s2.map(calc_nbr).max().clip(roi)
    
    # 2. Get the "Burnt" view (Post-fire state)
    min_nbr = s2.map(calc_nbr).min().clip(roi)

    # 3. INTELLIGENT FOREST MASK
    # Only analyze pixels that started as healthy vegetation (NBR > 0.4)
    # This ignores cities, dirt, and dry grass that confuse the sensor.
    forest_mask = max_nbr.gt(0.4)

    # 4. Calculate Burn Severity (dNBR) only in forest areas
    dnbr = max_nbr.subtract(min_nbr)
    
    # 5. Strict Threshold + Forest Check
    # We look for a massive drop in vegetation health (> 0.5) inside the forest mask
    burn_mask = dnbr.gt(0.5).And(forest_mask).selfMask()

    # FIX: Use Esri Satellite Map
    m = geemap.Map(basemap='Esri.WorldImagery')
    m.centerObject(roi, 10)
    m.addLayer(roi, {'color': 'grey'}, 'Region', True, 0.1)
    # Use bright Red/Orange to visualize the scar
    m.addLayer(burn_mask, {'palette': ['FF4500', 'FF0000']}, f'Verified Fire Scar ({year})')

    filename = "map_fire.html"
    output_path = os.path.join(os.getcwd(), "assets", filename)
    m.to_html(output_path)
    
    # Area Calc
    area = burn_mask.multiply(ee.Image.pixelArea()).reduceRegion(
        reducer=ee.Reducer.sum(), geometry=roi, scale=100, maxPixels=1e10
    )
    burn_ha = area.get('NBR').getInfo()
    if burn_ha is None: burn_ha = 0
    burn_ha = burn_ha / 10000

    return f"Sentinel-2 Spectral Analysis Complete. Identified {burn_ha:.2f} hectares of confirmed forest fire damage.", filename