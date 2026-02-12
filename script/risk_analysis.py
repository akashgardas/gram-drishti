import osmnx as ox
import geopandas as gpd
import pandas as pd
from os import path

BASE_DIR = path.dirname(path.abspath(__file__))

def fetch_flood_risks(place_name="Narayanpet, Telangana, India"):
    print(f"🌊 MAPPING FLOOD RISKS (WATER BODIES) FOR: {place_name}")
    
    # 1. Define Water Tags
    # We want everything that is water: lakes, rivers, reservoirs, ponds
    water_tags = {
        'natural': ['water', 'wetland'],
        'waterway': ['riverbank', 'dock', 'canal'],
        'landuse': ['reservoir', 'basin']
    }
    
    print("   1. Downloading water geometries from OpenStreetMap...")
    try:
        # Download the shapes
        gdf_water = ox.features_from_place(place_name, tags=water_tags)
        
        # Filter: We only care about Polygons (shapes), not Points
        gdf_water = gdf_water[gdf_water.geometry.type.isin(['Polygon', 'MultiPolygon'])]
        
        # Data Cleaning: Keep only essential columns to save space
        # If 'name' is missing, label it 'Unnamed Water Body'
        gdf_water['name'] = gdf_water['name'].fillna('Unnamed Water Body')
        gdf_water = gdf_water[['name', 'geometry']]
        
        print(f"      ✅ Found {len(gdf_water)} water bodies (Lakes, Tanks, Reservoirs).")
        
        # 2. Add a 'Safety Buffer'
        # Real flood zones extend beyond the water's edge. 
        # We add a 50-meter buffer zone around every lake.
        # (0.0005 degrees is approx 50-60 meters)
        gdf_water['geometry'] = gdf_water.geometry.buffer(0.0005)
        
        # 3. Save as GeoJSON
        # This replaces our old 'flood_zones.csv' logic
        flood_zones_file_save_path = path.join(BASE_DIR, '..', 'data', 'narayanpet_district', 'flood_zones.geojson')
        output_file = flood_zones_file_save_path
        gdf_water.to_file(output_file, driver='GeoJSON')
        print(f"   2. Saved Flood Risk Map to '{output_file}'")
        print("      ⚠️  Any hospital recommended inside these zones will be rejected.")

    except Exception as e:
        print(f"❌ Error fetching water data: {e}")
        print("   (Note: If the internet is slow, try running it again.)")

if __name__ == "__main__":
    fetch_flood_risks()