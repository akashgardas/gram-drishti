import geopandas as gpd
import folium
import pandas as pd
from os import path

BASE_DIR = path.dirname(path.abspath(__file__))

def visualize_impact():
    print("🗺️ Generating Comparison Map (HTML)...")

    # 1. Load Data
    try:
        # The "Reality" (Drive-Time Polygon)
        drive_time_coverage_file_path = path.join(BASE_DIR, '..', 'out', 'narayanpet_district', 'drive_time_coverage.geojson')
        gdf_iso = gpd.read_file(drive_time_coverage_file_path)
        
        # The Hospitals (Points)
        hospitals_file_path = path.join(BASE_DIR, '..', 'data', 'narayanpet_district', 'hospitals.csv')
        df_h = pd.read_csv(hospitals_file_path)
        
        # The Villages (Points)
        villages_file_path = path.join(BASE_DIR, '..', 'data', 'narayanpet_district', 'villages.csv')
        df_v = pd.read_csv(villages_file_path)
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        print("   (Did you run 'real_data_loader.py' and 'isochrone_analysis.py' first?)")
        return

    # 2. Setup Map centered on Narayanpet
    center_lat = df_h.latitude.mean()
    center_lon = df_h.longitude.mean()
    m = folium.Map(location=[center_lat, center_lon], zoom_start=11, tiles="CartoDB positron")

    # 3. Layer A: The "Illusion" (Simple 5km Buffer)
    # We create this on the fly to show what the "old" method looked like
    gdf_h_points = gpd.GeoDataFrame(
        df_h, geometry=gpd.points_from_xy(df_h.longitude, df_h.latitude), crs="EPSG:4326"
    )
    # Buffer in degrees (approx 0.05 deg ~ 5km)
    simple_buffer = gdf_h_points.buffer(0.05).unary_union
    
    folium.GeoJson(
        simple_buffer,
        name='Old Method (5km Radius)',
        style_function=lambda x: {
            'fillColor': 'gray', 'color': 'gray', 'fillOpacity': 0.1, 'dashArray': '5, 5'
        }
    ).add_to(m)

    # 4. Layer B: The "Reality" (15-min Drive Time)
    folium.GeoJson(
        gdf_iso,
        name='New Method (15-min Drive)',
        style_function=lambda x: {
            'fillColor': '#2ecc71', 'color': '#27ae60', 'fillOpacity': 0.4, 'weight': 2
        }
    ).add_to(m)

    # 5. Layer C: Hospitals
    for _, row in df_h.iterrows():
        folium.Marker(
            [row['latitude'], row['longitude']],
            popup=f"<b>{row['name']}</b>",
            icon=folium.Icon(color="blue", icon="plus", prefix='fa')
        ).add_to(m)
        
    # 6. Layer D: Unserved Villages (The Gap)
    # Find villages OUTSIDE the Drive-Time zone
    # Note: 'gdf_iso' is likely a MultiPolygon, we check 'within'
    gdf_v_points = gpd.GeoDataFrame(
        df_v, geometry=gpd.points_from_xy(df_v.longitude, df_v.latitude), crs="EPSG:4326"
    )
    
    # Check if point is inside the drive-time polygon
    iso_polygon = gdf_iso.geometry.iloc[0] # Get the shape
    served_mask = gdf_v_points.within(iso_polygon)
    unserved_villages = df_v[~served_mask]
    
    # Add Red Dots for these Gaps
    for _, row in unserved_villages.iterrows():
        folium.CircleMarker(
            [row['latitude'], row['longitude']],
            radius=3, color='red', fill=True, fill_color='red',
            popup=f"GAP: {row['name']} (Pop: {row['population']})"
        ).add_to(m)

    # Add Layer Control
    folium.LayerControl().add_to(m)

    # Save
    isochrone_comparison_file_save_path = path.join(BASE_DIR, '..', 'out', 'narayanpet_district', 'gram_drishti_isochrone_comparison.html')
    output_file = isochrone_comparison_file_save_path
    m.save(output_file)
    print(f"✅ Map saved to '{output_file}'")
    print("   Open this file in your browser to see the difference!")

if __name__ == "__main__":
    visualize_impact()