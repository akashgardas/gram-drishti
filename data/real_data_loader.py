import osmnx as ox
import geopandas as gpd
import pandas as pd
import random 
from os import path

BASE_DIR = path.dirname(path.abspath(__file__))

def fetch_real_district_data(place_name="Narayanpet, Telangana, India"):
    print(f"\n🌍 STARTING DATA PIPELINE FOR: {place_name}")
    print("="*50)
    
    # ==========================================
    # STEP 1: Fetch the Road Network (The "Skeleton")
    # ==========================================
    print(f"   1. Downloading Driveable Road Network...")
    print("      (This might take 1-2 mins depending on your connection)")
    
    # Narayanpet has good road coverage, so 'drive' network will be clean
    G = ox.graph_from_place(place_name, network_type='drive')
    
    # Save the graph for Challenge 2 (Accessibility)
    # We save as GraphML to preserve the complex node/edge structure
    network_file_save_path = path.join(BASE_DIR, 'narayanpet_district', 'district_network.graphml')
    ox.save_graphml(G, network_file_save_path)
    print(f"      ✅ Saved road network graph.")

    # ==========================================
    # STEP 2: Fetch Hospitals (The "Existing Infra")
    # ==========================================
    print(f"   2. Downloading Existing Hospitals...")
    # Fetching hospitals, clinics, and doctors
    tags = {'amenity': ['hospital', 'clinic', 'doctors']}
    gdf_hospitals = ox.features_from_place(place_name, tags=tags)
    
    # Data Cleaning: Keep only Points 
    # (If OSM returns a building polygon, we take its centroid)
    gdf_hospitals['geometry'] = gdf_hospitals.geometry.centroid
    
    # Handle missing names
    gdf_hospitals['name'] = gdf_hospitals['name'].fillna('Local Medical Center')
    
    # Create the CSV 
    df_h = pd.DataFrame({
        'hospital_id': range(len(gdf_hospitals)),
        'name': gdf_hospitals['name'],
        'type': gdf_hospitals['amenity'],
        'latitude': gdf_hospitals.geometry.y,
        'longitude': gdf_hospitals.geometry.x
    })
    hospitals_file_save_path = path.join(BASE_DIR, 'narayanpet_district', 'hospitals.csv')
    df_h.to_csv(hospitals_file_save_path, index=False)
    print(f"      ✅ Found {len(df_h)} hospitals in Narayanpet.")

    # ==========================================
    # STEP 3: Fetch Villages (The "Demand Points")
    # ==========================================
    print(f"   3. Downloading Villages & Clusters...")
    # 'place' tag is used for settlements
    village_tags = {'place': ['village', 'town', 'hamlet']}
    gdf_villages = ox.features_from_place(place_name, tags=village_tags)
    
    # Data Cleaning: Keep only Points
    gdf_villages['geometry'] = gdf_villages.geometry.centroid
    gdf_villages['name'] = gdf_villages['name'].fillna('Unnamed Settlement')
    
    # SIMULATING POPULATION 
    # Since Narayanpet is rural/semi-developed, we adjust the population model slightly
    print("      ⚠️  Simulating census data for demo purposes...")
    population_data = []
    for _, row in gdf_villages.iterrows():
        if row['place'] == 'town':
            pop = random.randint(8000, 35000) # Larger towns
        else:
            pop = random.randint(300, 2500)   # Smaller rural clusters
        population_data.append(pop)
        
    df_v = pd.DataFrame({
        'village_id': range(len(gdf_villages)),
        'name': gdf_villages['name'],
        'population': population_data,
        'latitude': gdf_villages.geometry.y,
        'longitude': gdf_villages.geometry.x
    })
    villages_file_save_path = path.join(BASE_DIR, 'narayanpet_district', 'villages.csv')
    df_v.to_csv(villages_file_save_path, index=False)
    print(f"      ✅ Found {len(df_v)} settlements.")
    
    print("\n✅ NARAYANPET DATA READY.")

if __name__ == "__main__":
    fetch_real_district_data("Narayanpet, Telangana, India")