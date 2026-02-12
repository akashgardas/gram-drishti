import pandas as pd
import geopandas as gpd
import folium
from shapely.geometry import Point
from os import path

# ==========================================
# 1. SETUP & DATA LOADING
# ==========================================
# Load the datasets we created in the previous step
base_dir = path.dirname(path.abspath(__file__))
df_villages = pd.read_csv(path.join(base_dir, '..', 'data', 'villages.csv'))
df_hospitals = pd.read_csv(path.join(base_dir, '..', 'data', 'hospitals.csv'))

# Convert standard DataFrames to GeoDataFrames (spatial data)
# We tell GeoPandas that Longitude is X and Latitude is Y
gdf_villages = gpd.GeoDataFrame(
    df_villages, 
    geometry=gpd.points_from_xy(df_villages.longitude, df_villages.latitude),
    crs="EPSG:4326"  # Standard Lat/Lon coordinate system
)

gdf_hospitals = gpd.GeoDataFrame(
    df_hospitals, 
    geometry=gpd.points_from_xy(df_hospitals.longitude, df_hospitals.latitude),
    crs="EPSG:4326"
)

# ==========================================
# 2. SPATIAL ANALYSIS (The "Gap" Logic)
# ==========================================
# Project to a metric CRS (EPSG:3857) to calculate distance in meters
# (Lat/Lon is in degrees, which makes buffer calculations difficult)
villages_proj = gdf_villages.to_crs(epsg=3857)
hospitals_proj = gdf_hospitals.to_crs(epsg=3857)

# Define Service Radius (e.g., 5 Kilometers)
SERVICE_RADIUS_METERS = 5000 

# Create "Service Buffers" around hospitals
# This draws a 5km circle around each hospital
hospital_buffers = hospitals_proj.geometry.buffer(SERVICE_RADIUS_METERS)

# Create a single "Served Zone" polygon by merging all buffers
served_zone = hospital_buffers.unary_union

# Identify Underserved Villages
# We check if each village point is 'within' the served zone polygon
# The '~' operator negates the result (i.e., finds those NOT in the zone)
underserved_mask = ~villages_proj.geometry.within(served_zone)
underserved_villages = gdf_villages[underserved_mask]
served_villages = gdf_villages[~underserved_mask]

print(f"Total Villages: {len(gdf_villages)}")
print(f"Served Villages: {len(served_villages)}")
print(f"Underserved Villages (GAPS): {len(underserved_villages)}")

# ==========================================
# 3. VISUALIZATION (Streamlit/Folium Ready)
# ==========================================
# Create a base map centered on the district
center_lat = df_villages['latitude'].mean()
center_lon = df_villages['longitude'].mean()
m = folium.Map(location=[center_lat, center_lon], zoom_start=11)

# Layer 1: The Service Zone (Green Area)
# We must re-project back to Lat/Lon (4326) for plotting on the map
if not served_zone.is_empty:
    # Handle both MultiPolygon and Polygon cases
    zone_geo = gpd.GeoSeries([served_zone], crs="EPSG:3857").to_crs(epsg=4326)
    folium.GeoJson(
        zone_geo,
        name='Service Coverage (5km)',
        style_function=lambda x: {'fillColor': 'green', 'color': 'green', 'fillOpacity': 0.2}
    ).add_to(m)

# Layer 2: Hospitals (Blue Plus Icons)
for _, row in df_hospitals.iterrows():
    folium.Marker(
        location=[row['latitude'], row['longitude']],
        popup=f"Hospital: {row['hospital_id']}",
        icon=folium.Icon(color="blue", icon="plus", prefix='fa')
    ).add_to(m)

# Layer 3: Underserved Villages (Red Dots) - The Critical "Gap"
for _, row in underserved_villages.iterrows():
    folium.CircleMarker(
        location=[row['latitude'], row['longitude']],
        radius=5,
        color='red',
        fill=True,
        fill_color='red',
        popup=f"UNDERSERVED: {row['name']} (Pop: {row['population']})"
    ).add_to(m)

# Layer 4: Served Villages (Green Dots)
for _, row in served_villages.iterrows():
    folium.CircleMarker(
        location=[row['latitude'], row['longitude']],
        radius=3,
        color='green',
        fill=True,
        fill_color='green',
        popup=f"Served: {row['name']}"
    ).add_to(m)

# Add Layer Control to toggle views
folium.LayerControl().add_to(m)

# Save the map

output_file = path.join(base_dir, '..', 'out', 'gram_drishti_gap_analysis.html')
m.save(output_file)
print(f"✅ Map saved as '{output_file}'. Open this file in your browser to see the results.")