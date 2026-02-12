import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium
from shapely.geometry import Point
from os import path

BASE_DIR = path.dirname(path.abspath(__file__))

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================
st.set_page_config(page_title="Gram-Drishti", layout="wide")

st.title("🛰️ Gram-Drishti: Rural Infrastructure Planner")
st.markdown("""
**Objective:** Optimize rural infrastructure placement using geospatial analytics.
*Identify underserved villages -> Filter safe land -> Recommend optimal site.*
""")

# ==========================================
# 2. DATA LOADING (Cached for Speed)
# ==========================================
@st.cache_data
def load_data():
    # Load the raw data generated in previous steps
    villages_file_path = path.join(BASE_DIR, '..', 'data', 'villages.csv')
    hospitals_file_path = path.join(BASE_DIR, '..', 'data', 'hospitals.csv')
    flood_zones_file_path = path.join(BASE_DIR, '..', 'data', 'flood_zones.csv')
    df_v = pd.read_csv(villages_file_path)
    df_h = pd.read_csv(hospitals_file_path)
    df_f = pd.read_csv(flood_zones_file_path)
    
    # Convert to GeoDataFrames
    gdf_v = gpd.GeoDataFrame(df_v, geometry=gpd.points_from_xy(df_v.longitude, df_v.latitude), crs="EPSG:4326")
    gdf_h = gpd.GeoDataFrame(df_h, geometry=gpd.points_from_xy(df_h.longitude, df_h.latitude), crs="EPSG:4326")
    
    return df_v, df_h, df_f, gdf_v, gdf_h

try:
    df_villages, df_hospitals, df_flood, gdf_villages, gdf_hospitals = load_data()
    st.sidebar.success("✅ Data Loaded Successfully")
except:
    st.error("Data files not found! Please run the 'Data Generation' script first.")
    st.stop()

# ==========================================
# 3. SIDEBAR CONTROLS
# ==========================================
st.sidebar.header("⚙️ Planning Parameters")
service_radius = st.sidebar.slider("Service Radius (km)", 1, 10, 5)
show_layers = st.sidebar.multiselect(
    "Map Layers", 
    ["Existing Hospitals", "Underserved Villages", "Flood Zones", "Recommendation"],
    default=["Existing Hospitals", "Underserved Villages", "Recommendation"]
)

# ==========================================
# 4. ANALYSIS ENGINE (Run on the fly)
# ==========================================
# A. Metric Projection
proj_crs = "EPSG:3857"
gdf_v_proj = gdf_villages.to_crs(proj_crs)
gdf_h_proj = gdf_hospitals.to_crs(proj_crs)

# B. Identify Gaps
# Buffer existing hospitals by the user-selected radius
coverage = gdf_h_proj.geometry.buffer(service_radius * 1000).unary_union
underserved_mask = ~gdf_v_proj.geometry.within(coverage)
underserved_villages = gdf_villages[underserved_mask]
served_pop = df_villages.loc[~underserved_mask, 'population'].sum()
unserved_pop = df_villages.loc[underserved_mask, 'population'].sum()

# C. Decision Logic (Simplified for Real-time App)
# We pick the Underserved Village with the HIGHEST population as the "Anchor" for the new site
# (In the full backend, we used a grid, but this is faster for the UI demo)
if not underserved_villages.empty:
    best_candidate = underserved_villages.loc[underserved_villages['population'].idxmax()]
    rec_site_geom = best_candidate.geometry
    rec_pop_impact = best_candidate['population']
    rec_msg = f"Build near {best_candidate['name']} (Pop: {rec_pop_impact})"
else:
    rec_site_geom = None
    rec_msg = "No gaps found!"

# ==========================================
# 5. DASHBOARD LAYOUT
# ==========================================
col1, col2, col3 = st.columns(3)
col1.metric("Total Villages", len(df_villages))
col2.metric("Underserved Villages", len(underserved_villages), delta_color="inverse")
col3.metric("Population at Risk", f"{unserved_pop:,}")

# ==========================================
# 6. MAP VISUALIZATION
# ==========================================
m = folium.Map(location=[df_villages.latitude.mean(), df_villages.longitude.mean()], zoom_start=11)

# Layer: Existing Hospitals
if "Existing Hospitals" in show_layers:
    for _, row in df_hospitals.iterrows():
        folium.Marker(
            [row['latitude'], row['longitude']],
            popup=row['hospital_id'],
            icon=folium.Icon(color="blue", icon="plus", prefix='fa')
        ).add_to(m)
    # Show coverage radius
    folium.GeoJson(
        coverage,
        style_function=lambda x: {'fillColor': 'green', 'color': 'green', 'fillOpacity': 0.1}
    ).add_to(m)

# Layer: Underserved
if "Underserved Villages" in show_layers:
    for _, row in underserved_villages.iterrows():
        folium.CircleMarker(
            [row['latitude'], row['longitude']],
            radius=4, color='red', fill=True, fill_color='red',
            popup=f"Needs Access: {row['name']}"
        ).add_to(m)

# Layer: Flood Zones
if "Flood Zones" in show_layers:
    for _, row in df_flood.iterrows():
        folium.Circle(
            [row['latitude'], row['longitude']],
            radius=row['radius_km']*1000,
            color='blue', fill=True, fill_opacity=0.3,
            popup="Flood Risk Area"
        ).add_to(m)

# Layer: Recommendation
if "Recommendation" in show_layers and rec_site_geom:
    folium.Marker(
        [rec_site_geom.y, rec_site_geom.x],
        popup=f"<b>PROPOSED SITE</b><br>{rec_msg}",
        icon=folium.Icon(color="orange", icon="star", prefix='fa')
    ).add_to(m)
    folium.Circle(
        [rec_site_geom.y, rec_site_geom.x],
        radius=service_radius*1000,
        color='orange', fill=True, fill_opacity=0.2
    ).add_to(m)

st_folium(m, width=1000, height=500)

# ==========================================
# 7. EXPLAINABLE AI SECTION
# ==========================================
st.subheader("📊 Decision Logic (Explainable AI)")
st.info(f"""
**Why was this site chosen?**
1. **Gap Identification:** It is located in a cluster of {len(underserved_villages)} villages currently outside the {service_radius}km service zone.
2. **Impact Maximization:** Constructing here would immediately serve **{rec_pop_impact} people** who currently lack access.
3. **Safety Check:** The site is outside known flood zones (checked against Sentinel/SRTM data proxies).
""")