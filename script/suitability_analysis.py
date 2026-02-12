import pandas as pd
import geopandas as gpd
import folium
import numpy as np
from shapely.geometry import Point, Polygon
from os import path

# ==========================================
# 1. SETUP & DATA LOADING
# ==========================================
# Load the output from the previous step (Conceptually)
# In practice, we reload the CSVs to keep this script standalone
base_dir = path.dirname(path.abspath(__file__))

df_flood = pd.read_csv(path.join(base_dir, '..', 'data' ,'flood_zones.csv'))
df_villages = pd.read_csv(path.join(base_dir, '..', 'data' ,'villages.csv')) 

# Define the District Boundary (Extent of our analysis)
min_lon, max_lon = df_villages.longitude.min(), df_villages.longitude.max()
min_lat, max_lat = df_villages.latitude.min(), df_villages.latitude.max()

# Convert Flood Data to Polygon Geometries
# We create circular buffers around the flood points to simulate "Risk Zones"
flood_geoms = []
for _, row in df_flood.iterrows():
    # Create a point and buffer it by its radius (convert km to degrees roughly)
    # 1 degree approx 111km, so radius_km / 111
    center = Point(row['longitude'], row['latitude'])
    radius_deg = row['radius_km'] / 111.0 
    flood_geoms.append(center.buffer(radius_deg))

gdf_flood = gpd.GeoDataFrame(geometry=flood_geoms, crs="EPSG:4326")
flood_union = gdf_flood.unary_union  # Combine all flood zones into one shape

# ==========================================
# 2. GENERATE CANDIDATE GRID
# ==========================================
# Instead of checking infinite points, we create a "Grid" of potential sites
# This answers: "Where CAN we build?"
GRID_SPACING = 0.01  # Approx 1km spacing between points
candidate_sites = []

# Generate a meshgrid of points across the district
lon_vals = np.arange(min_lon, max_lon, GRID_SPACING)
lat_vals = np.arange(min_lat, max_lat, GRID_SPACING)

for lon in lon_vals:
    for lat in lat_vals:
        candidate_sites.append(Point(lon, lat))

gdf_candidates = gpd.GeoDataFrame(geometry=candidate_sites, crs="EPSG:4326")
print(f"Generated {len(gdf_candidates)} potential construction sites.")

# ==========================================
# 3. SUITABILITY FILTERING
# ==========================================
# Rule: Exclude sites inside Flood Zones
# "Unsuitable land areas such as flood-prone regions... are excluded"
safe_mask = ~gdf_candidates.geometry.within(flood_union)
gdf_safe_sites = gdf_candidates[safe_mask]
gdf_risky_sites = gdf_candidates[~safe_mask]

print(f"Safe Sites: {len(gdf_safe_sites)}")
print(f"Risky Sites (Discarded): {len(gdf_risky_sites)}")

# ==========================================
# 4. VISUALIZATION
# ==========================================
m = folium.Map(location=[(min_lat + max_lat)/2, (min_lon + max_lon)/2], zoom_start=11)

# Layer 1: Flood Zones (Blue Areas)
folium.GeoJson(
    flood_union,
    name='Flood Risk Zones',
    style_function=lambda x: {'fillColor': '#3186cc', 'color': '#3186cc', 'fillOpacity': 0.4}
).add_to(m)

# Layer 2: Safe Candidate Sites (Green Dots)
# We only plot a subset if there are too many to avoid lag
for _, row in gdf_safe_sites.iloc[::2].iterrows(): # Plot every 2nd point for speed
    folium.CircleMarker(
        location=[row.geometry.y, row.geometry.x],
        radius=2,
        color='green',
        fill=True,
        fill_color='green',
        popup="Safe Site"
    ).add_to(m)

# Layer 3: Risky Sites (Red X or Dots - Optional, for debugging)
for _, row in gdf_risky_sites.iterrows():
    folium.CircleMarker(
        location=[row.geometry.y, row.geometry.x],
        radius=2,
        color='red',
        fill=True,
        fill_color='red',
        popup="RISK: Flood Zone"
    ).add_to(m)

folium.LayerControl().add_to(m)
save_path = path.join(base_dir, '..', 'out', 'gram_drishti_suitability.html')
m.save(save_path)
print("✅ Map saved as 'gram_drishti_suitability.html'")

# Save Safe Sites for the Next Step (Ranking)
safe_sites_save_path = path.join(base_dir, '..', 'out', "safe_sites.geojson")
gdf_safe_sites.to_file(safe_sites_save_path, driver="GeoJSON")