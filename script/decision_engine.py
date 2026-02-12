import pandas as pd
import geopandas as gpd
import folium
from shapely.geometry import Point
from os import path

# ==========================================
# 1. SETUP & DATA LOADING
# ==========================================
# Load safe sites from the previous step
base_dir = path.dirname(path.abspath(__file__))
safe_sites_file_path = path.join(base_dir, '..', 'out', 'safe_sites.geojson')
gdf_safe_sites = gpd.read_file(safe_sites_file_path)

# Load village and hospital data
villages_file_path = path.join(base_dir, '..', 'data', 'villages.csv')
hospitals_file_path = path.join(base_dir, '..', 'data', 'hospitals.csv')
df_villages = pd.read_csv(villages_file_path)
df_hospitals = pd.read_csv(hospitals_file_path)

# Convert to GeoDataFrames
gdf_villages = gpd.GeoDataFrame(
    df_villages, geometry=gpd.points_from_xy(df_villages.longitude, df_villages.latitude), crs="EPSG:4326"
)
gdf_hospitals = gpd.GeoDataFrame(
    df_hospitals, geometry=gpd.points_from_xy(df_hospitals.longitude, df_hospitals.latitude), crs="EPSG:4326"
)

# Reproject to meters (EPSG:3857) for accurate distance calculations
safe_sites_proj = gdf_safe_sites.to_crs(epsg=3857)
villages_proj = gdf_villages.to_crs(epsg=3857)
hospitals_proj = gdf_hospitals.to_crs(epsg=3857)

# Identify strictly UNDERSERVED villages first (Re-running gap logic briefly)
existing_coverage = hospitals_proj.geometry.buffer(5000).unary_union
underserved_mask = ~villages_proj.geometry.within(existing_coverage)
underserved_villages = villages_proj[underserved_mask]

print(f"Analyzing {len(safe_sites_proj)} safe candidate sites...")
print(f"Targeting {len(underserved_villages)} underserved villages.")

# ==========================================
# 2. SCORING ALGORITHM
# ==========================================
scores = []

for idx, site in safe_sites_proj.iterrows():
    # Criteria A: Population Potential
    # Draw a 5km buffer around this candidate site
    potential_coverage = site.geometry.buffer(5000) 
    
    # Find which *underserved* villages fall into this new coverage
    covered_villages = underserved_villages[underserved_villages.geometry.within(potential_coverage)]
    
    # Sum the population of these villages
    # (Note: In the original CSV, 'population' is in df_villages. We map by index or merge.)
    # For MVP speed, we assume the index matches the original gdf_villages
    pop_covered = df_villages.loc[covered_villages.index, 'population'].sum()

    # Criteria B: Distance to Nearest Existing Hospital (Avoid Redundancy)
    # distance() returns meters. We want sites FAR from existing ones.
    dist_to_nearest = hospitals_proj.distance(site.geometry).min()

    # Total Score formula: 
    # Weighted Sum: 70% for Population + 30% for Distance (normalized roughly)
    # We simply add them. High pop + High distance = Good Score.
    # Dividing distance by 10 makes the units roughly comparable to population counts.
    final_score = pop_covered + (dist_to_nearest / 10)

    scores.append({
        'geometry': site.geometry, # Keep the geometry for the final map
        'pop_covered': pop_covered,
        'dist_to_existing': dist_to_nearest,
        'final_score': final_score
    })

# Create a DataFrame of results and sort by score
results_df = pd.DataFrame(scores)
gdf_results = gpd.GeoDataFrame(results_df, geometry='geometry', crs="EPSG:3857")

# GET THE WINNER
best_site = gdf_results.sort_values(by='final_score', ascending=False).iloc[0]
best_site_geo = gpd.GeoSeries([best_site.geometry], crs="EPSG:3857").to_crs(epsg=4326).iloc[0]

print("\n" + "="*30)
print("🏆 RECOMMENDATION GENERATED")
print("="*30)
print(f"Top Site Score: {best_site['final_score']:.2f}")
print(f" - Est. Population Covered: {int(best_site['pop_covered'])} people")
print(f" - Dist. to Nearest Hospital: {best_site['dist_to_existing']/1000:.2f} km")
print(f" - Location: {best_site_geo.y:.4f}, {best_site_geo.x:.4f}")

# ==========================================
# 3. VISUALIZATION (Final Dashboard Output)
# ==========================================
# Center map on the winning site
m = folium.Map(location=[best_site_geo.y, best_site_geo.x], zoom_start=12)

# Layer 1: Existing Hospitals (Grey)
for _, row in df_hospitals.iterrows():
    folium.Marker(
        [row['latitude'], row['longitude']],
        icon=folium.Icon(color="gray", icon="hospital-o", prefix='fa'),
        popup="Existing Hospital"
    ).add_to(m)

# Layer 2: The Recommended New Site (Gold Star)
folium.Marker(
    location=[best_site_geo.y, best_site_geo.x],
    popup=folium.Popup(f"<b>RECOMMENDED SITE</b><br>Pop Coverage: {int(best_site['pop_covered'])}", max_width=300),
    icon=folium.Icon(color="orange", icon="star", prefix='fa')
).add_to(m)

# Layer 3: The New Service Zone (Orange Circle)
folium.Circle(
    location=[best_site_geo.y, best_site_geo.x],
    radius=5000, # 5km
    color="orange",
    fill=True,
    fill_opacity=0.2
).add_to(m)

# Layer 4: Underserved Villages (Red Dots)
# We plot these to visually confirm they are inside the orange circle
underserved_geo = underserved_villages.to_crs(epsg=4326)
for _, row in underserved_geo.iterrows():
    folium.CircleMarker(
        location=[row.geometry.y, row.geometry.x],
        radius=3,
        color='red',
        fill=True,
        popup=f"Village Gap (Pop: {df_villages.loc[row.name, 'population']})"
    ).add_to(m)

save_path = path.join(base_dir, '..', 'out', 'gram_drishti_final_recommendation.html')
m.save(save_path)
print(f"✅ Final Decision Map saved as 'gram_drishti_final_recommendation.html'")