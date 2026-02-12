import geopandas as gpd
import pandas as pd
import folium
from os import path

BASE_DIR = path.dirname(path.abspath(__file__))

def visualize_master_plan():
    print("🗺️ Generating Strategic Master Plan Map (with Village Details)...")

    # 1. Load All Data Layers
    try:
        # The Core Plan (5 Sites)
        final_recommendation_file_path = path.join(BASE_DIR, '..', 'out', 'narayanpet_district', 'final_recommendation.geojson')
        gdf_rec = gpd.read_file(final_recommendation_file_path)
        
        # Context Data
        drive_time_coverage_file_path = path.join(BASE_DIR, '..', 'out', 'narayanpet_district', 'drive_time_coverage.geojson')
        gdf_iso = gpd.read_file(drive_time_coverage_file_path)
        hospitals_file_path = path.join(BASE_DIR, '..', 'data', 'narayanpet_district', 'hospitals.csv')
        df_h = pd.read_csv(hospitals_file_path)
        villages_file_path = path.join(BASE_DIR, '..', 'data', 'narayanpet_district', 'villages.csv')
        df_v = pd.read_csv(villages_file_path)
        
        # Create GeoDataFrame for Villages (Crucial for the "Within" check)
        gdf_v = gpd.GeoDataFrame(
            df_v, 
            geometry=gpd.points_from_xy(df_v.longitude, df_v.latitude), 
            crs="EPSG:4326"
        )
        
        # Try loading flood zones
        try:
            flood_zones_file_path = path.join(BASE_DIR, '..', 'data', 'narayanpet_district', 'flood_zones.geojson')
            gdf_flood = gpd.read_file(flood_zones_file_path)
        except:
            gdf_flood = gpd.GeoDataFrame()
            
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return

    # 2. Setup Map
    center_lat = df_h.latitude.mean()
    center_lon = df_h.longitude.mean()
    m = folium.Map(location=[center_lat, center_lon], zoom_start=11, tiles="CartoDB positron")

    # 3. Layer A: Environmental Context
    if not gdf_flood.empty:
        folium.GeoJson(
            gdf_flood,
            name='Flood Risks (No-Go)',
            style_function=lambda x: {'fillColor': '#00008b', 'color': 'none', 'fillOpacity': 0.3},
            tooltip="Flood Risk Zone"
        ).add_to(m)

    folium.GeoJson(
        gdf_iso,
        name='Existing Coverage (15m)',
        style_function=lambda x: {'fillColor': '#95a5a6', 'color': '#7f8c8d', 'fillOpacity': 0.2, 'weight': 1}
    ).add_to(m)

    # 4. Layer B: Villages (The Context Layer)
    # We distinguish between "Currently Served" and "Gaps"
    iso_geom = gdf_iso.geometry.iloc[0]
    served_mask = gdf_v.within(iso_geom)
    
    served_villages = gdf_v[served_mask]
    unserved_villages = gdf_v[~served_mask]

    # Plot Served Villages (Small Green Dots)
    for _, row in served_villages.iterrows():
        folium.CircleMarker(
            [row.geometry.y, row.geometry.x],
            radius=2, color='#27ae60', fill=True, fill_opacity=0.3, weight=0,
            popup=f"✅ Served: {row['name']} (Pop: {row['population']})"
        ).add_to(m)

    # Plot Unserved Villages (Red Dots - The Problem)
    # We make these slightly larger/brighter to stand out
    for _, row in unserved_villages.iterrows():
        folium.CircleMarker(
            [row.geometry.y, row.geometry.x],
            radius=3, color='#c0392b', fill=True, fill_color='#c0392b', fill_opacity=0.7, weight=0,
            popup=f"❌ Gap: {row['name']} (Pop: {row['population']})"
        ).add_to(m)

    # 5. Layer C: Existing Hospitals
    for _, row in df_h.iterrows():
        folium.Marker(
            [row['latitude'], row['longitude']],
            popup=f"Existing: {row['name']}",
            icon=folium.Icon(color="gray", icon="plus", prefix='fa')
        ).add_to(m)

    # 6. Layer D: The Strategic Plan (Recommendations)
    for _, row in gdf_rec.iterrows():
        rank = int(row['rank'])
        pop = int(row['pop_covered'])
        
        if rank == 1:
            color = "red"
            z_index = 1000
        elif rank == 2:
            color = "orange"
            z_index = 900
        else:
            color = "green"
            z_index = 800
            
        # The Marker
        folium.Marker(
            [row.geometry.y, row.geometry.x],
            popup=folium.Popup(f"<b>PRIORITY #{rank}</b><br>Impact: +{pop} people", max_width=200),
            icon=folium.Icon(color=color, icon=str(rank), prefix='fa'),
            z_index_offset=z_index
        ).add_to(m)
        
        # The Estimated Impact Zone
        folium.Circle(
            [row.geometry.y, row.geometry.x],
            radius=3000,
            color=color, fill=True, fill_opacity=0.1, weight=2, dash_array='5, 5'
        ).add_to(m)

    folium.LayerControl().add_to(m)

    gram_drishti_final_plan_file_save_path = path.join(BASE_DIR, '..', 'out', 'narayanpet_district', 'gram_drishti_final_plan.html')
    output_file = gram_drishti_final_plan_file_save_path
    m.save(output_file)
    print(f"✅ Updated Master Plan saved to '{output_file}'")

if __name__ == "__main__":
    visualize_master_plan()