import pandas as pd
import geopandas as gpd
import numpy as np
from shapely.geometry import Point
from os import path

BASE_DIR = path.dirname(path.abspath(__file__))

# ==========================================
# CONFIGURATION
# ==========================================
NUM_SITES_TO_RECOMMEND = 5  # We want a plan for 5 new hospitals
SERVICE_RADIUS_DEG = 0.03   # Approx 3km service radius for new sites

def optimize_multi_site():
    print(f"🚀 STARTING MULTI-SITE OPTIMIZATION (Target: {NUM_SITES_TO_RECOMMEND} Sites)")
    print("="*50)

    # 1. Load Data
    try:
        # Load Villages
        villages_file_path = path.join(BASE_DIR, '..', 'data', 'narayanpet_district', 'villages.csv')
        df_v = pd.read_csv(villages_file_path)
        gdf_v = gpd.GeoDataFrame(
            df_v, 
            geometry=gpd.points_from_xy(df_v.longitude, df_v.latitude), 
            crs="EPSG:4326"
        )
        
        # Load Drive-Time Coverage (Existing Access)
        drive_time_coverage_file_path = path.join(BASE_DIR, '..', 'out', 'narayanpet_district', 'drive_time_coverage.geojson')
        gdf_iso = gpd.read_file(drive_time_coverage_file_path)
        existing_coverage = gdf_iso.geometry.iloc[0] # The big "amoeba" shape
        
        # Load Flood Zones (Constraint)
        # Handle case where file might not exist yet
        try:
            flood_zones_file_path = path.join(BASE_DIR, '..', 'data', 'narayanpet_district', 'flood_zones.geojson')
            gdf_flood = gpd.read_file(flood_zones_file_path)
            flood_zone = gdf_flood.unary_union
            print("   ✅ Loaded Flood Risk Zones.")
        except:
            flood_zone = None
            print("   ⚠️ No flood zones found. Proceeding without risk analysis.")
            
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return

    # 2. Identify Initial Gaps
    # Find villages strictly OUTSIDE existing drive-time coverage
    unserved_mask = ~gdf_v.within(existing_coverage)
    current_unserved_villages = gdf_v[unserved_mask].copy()
    
    initial_gap_pop = current_unserved_villages['population'].sum()
    print(f"   📉 Initial Unserved Population: {initial_gap_pop:,}")
    print(f"   📍 Unserved Villages Count: {len(current_unserved_villages)}")

    # 3. Generate Candidate Grid (Potential Build Sites)
    print("   🏗️  Generating Candidate Grid...")
    min_lon, max_lon = df_v.longitude.min(), df_v.longitude.max()
    min_lat, max_lat = df_v.latitude.min(), df_v.latitude.max()
    
    candidates = []
    # Create a grid (0.01 deg is approx 1km)
    for x in np.arange(min_lon, max_lon, 0.01):
        for y in np.arange(min_lat, max_lat, 0.01):
            p = Point(x, y)
            # Filter Flood Zones immediately (Don't even consider them)
            if flood_zone is None or not p.within(flood_zone):
                candidates.append(p)
                
    gdf_candidates = gpd.GeoDataFrame(geometry=candidates, crs="EPSG:4326")
    print(f"      Analyzed {len(gdf_candidates)} safe locations.")

    # 4. THE OPTIMIZATION LOOP
    recommended_sites = []
    
    for i in range(NUM_SITES_TO_RECOMMEND):
        print(f"\n   🔄 Finding Optimal Site #{i+1}...")
        
        best_score = 0
        best_site_geom = None
        best_covered_indices = []

        # Iterate through every candidate site
        # We simulate placing a hospital at each candidate point
        # A simple buffer approximates the new service area
        # (For higher precision, we'd recalc isochrones, but that's too slow for live demo)
        candidate_buffers = gdf_candidates.buffer(SERVICE_RADIUS_DEG)
        
        # We need to find which candidate covers the MOST 'current_unserved_villages'
        # Spatial Join is faster than looping
        joined = gpd.sjoin(current_unserved_villages, 
                           gpd.GeoDataFrame(geometry=candidate_buffers, crs="EPSG:4326"), 
                           how="inner", predicate="within")
        
        # 'joined' now has village data linked to candidate index (index_right)
        # Group by candidate index and sum the population
        candidate_scores = joined.groupby('index_right')['population'].sum()
        
        if not candidate_scores.empty:
            best_candidate_idx = candidate_scores.idxmax()
            best_score = candidate_scores.max()
            best_site_geom = gdf_candidates.iloc[best_candidate_idx].geometry
            
            # Identify which villages were covered by this winner
            best_covered_indices = joined[joined['index_right'] == best_candidate_idx].index.tolist()
        
        # Check if we found anything useful
        if best_site_geom is None or best_score == 0:
            print("      ⚠️ No more gaps can be covered efficiently. Stopping early.")
            break
            
        # 5. Lock in the Winner
        print(f"      ✅ Found Site #{i+1}! Covers {int(best_score)} people.")
        recommended_sites.append({
            'rank': i+1,
            'pop_covered': int(best_score),
            'geometry': best_site_geom,
            'status': 'Proposed'
        })
        
        # 6. CRITICAL STEP: Remove these villages from the 'Unserved' pool
        # This prevents Site #2 from covering the same people as Site #1
        current_unserved_villages = current_unserved_villages.drop(best_covered_indices)
        remaining_pop = current_unserved_villages['population'].sum()
        print(f"      📉 Remaining Gap: {remaining_pop:,} people")

    # 7. Save Results
    if recommended_sites:
        gdf_results = gpd.GeoDataFrame(recommended_sites, crs="EPSG:4326")
        final_recommendation_file_save_path = path.join(BASE_DIR, '..', 'out', 'narayanpet_district', 'final_recommendation.geojson')
        output_file = final_recommendation_file_save_path
        gdf_results.to_file(output_file, driver='GeoJSON')
        print("\n" + "="*50)
        print(f"🏆 PLAN GENERATED: Saved {len(recommended_sites)} sites to '{output_file}'")
        print("="*50)
    else:
        print("❌ No sites recommended.")

if __name__ == "__main__":
    optimize_multi_site()