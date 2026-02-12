import osmnx as ox
import networkx as nx
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, Polygon
import matplotlib.pyplot as plt
from os import path

BASE_DIR = path.dirname(path.abspath(__file__))

def calculate_isochrones(place_name="Narayanpet, Telangana, India", trip_time_min=15):
    print(f"🚗 STARTING DRIVE-TIME ANALYSIS for {place_name}...")
    
    # 1. Load the Graph (Saved in Step 1)
    # If the file exists, load it. If not, re-download (safety check).
    try:
        network_file_path = path.join(BASE_DIR, '..', 'data', 'narayanpet_district', 'district_network.graphml')
        G = ox.load_graphml(network_file_path)
        print("   ✅ Loaded road network from cache.")
    except:
        print("   ⚠️ Cache not found. Downloading fresh network...")
        G = ox.graph_from_place(place_name, network_type='drive')
        network_file_save_path = path.join(BASE_DIR, '..', 'data', 'narayanpet_district', 'district_network.graphml')
        ox.save_graphml(G, network_file_save_path)

    # 2. Impute Speeds and Travel Times
    # This function guesses speed limits based on road type (e.g., 'primary', 'residential')
    # Use 'kilometers per hour' (kph)
    G = ox.add_edge_speeds(G) 
    G = ox.add_edge_travel_times(G)
    print("   ✅ Calculated travel times for all road segments.")

    # 3. Load Hospitals
    hospitals_file_path = path.join(BASE_DIR, '..', 'data', 'narayanpet_district', 'hospitals.csv')
    df_h = pd.read_csv(hospitals_file_path)
    
    # 4. Generate Isochrones
    isochrone_polys = []
    
    print(f"   ⏳ Calculating {trip_time_min}-min drive zones for {len(df_h)} hospitals...")
    
    for _, row in df_h.iterrows():
        # Find the nearest network node to the hospital
        center_node = ox.distance.nearest_nodes(G, row['longitude'], row['latitude'])
        
        # Create a subgraph of nodes reachable within trip_time (in seconds)
        subgraph = nx.ego_graph(G, center_node, radius=trip_time_min*60, distance='travel_time')
        
        # Convert the subgraph of nodes into a Polygon (Shape)
        node_points = [Point((data['x'], data['y'])) for node, data in subgraph.nodes(data=True)]
        if len(node_points) > 2: # Need at least 3 points to make a polygon
            # We use a convex hull for simplicity in this demo (or a buffer for more detail)
            # A 'unary_union' of buffered points is more accurate but slower.
            # For hackathon speed, we'll buffer the points and merge.
            merged_poly = gpd.GeoSeries(node_points).buffer(0.005).unary_union # 0.005 deg ~ 500m width
            isochrone_polys.append(merged_poly)

    # 5. Save the Result
    if isochrone_polys:
        # Combine all hospital zones into one big "Served Area"
        total_coverage = gpd.GeoSeries(isochrone_polys).unary_union
        
        # Save as GeoJSON for the App
        drive_time_coverage_file_save_path = path.join(BASE_DIR, '..', 'out', 'narayanpet_district', 'drive_time_coverage.geojson')
        gpd.GeoSeries([total_coverage], crs="EPSG:4326").to_file(drive_time_coverage_file_save_path, driver="GeoJSON")
        print(f"   ✅ SUCCESS! Saved drive-time coverage map to 'data/drive_time_coverage.geojson'")
    else:
        print("   ⚠️ No reachable areas found. Check data.")

if __name__ == "__main__":
    calculate_isochrones()