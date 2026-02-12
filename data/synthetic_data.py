import pandas as pd
import random

# Configuration
NUM_VILLAGES = 50
NUM_HOSPITALS = 5
DISTRICT_CENTER = (17.3850, 78.4867)  # Example: Near Hyderabad

def generate_location(center, spread=0.1):
    """Generates a random lat/lon within a spread of the center."""
    return {
        'latitude': center[0] + random.uniform(-spread, spread),
        'longitude': center[1] + random.uniform(-spread, spread)
    }

# 1. Generate Village Data (Demographics)
# Represents "Village-level demographic information" 
villages = []
for i in range(1, NUM_VILLAGES + 1):
    loc = generate_location(DISTRICT_CENTER)
    villages.append({
        'village_id': i,
        'name': f'Village_{i}',
        'population': random.randint(200, 5000),
        'latitude': loc['latitude'],
        'longitude': loc['longitude']
    })

df_villages = pd.DataFrame(villages)
df_villages.to_csv('villages.csv', index=False)
print("✅ Generated 'villages.csv' with population data.")

# 2. Generate Existing Infrastructure (Hospitals)
# Represents "Existing infrastructure" data [cite: 30]
hospitals = []
for i in range(1, NUM_HOSPITALS + 1):
    loc = generate_location(DISTRICT_CENTER)
    hospitals.append({
        'hospital_id': f'H_{i}',
        'type': 'Primary Health Centre',
        'latitude': loc['latitude'],
        'longitude': loc['longitude']
    })

df_hospitals = pd.DataFrame(hospitals)
df_hospitals.to_csv('hospitals.csv', index=False)
print("✅ Generated 'hospitals.csv' location data.")

# 3. Generate Environmental Constraints (Flood Zones)
# Represents "Flood-prone regions" for exclusion 
# We simulate these as circular zones for simplicity
flood_zones = []
for i in range(1, 4):  # 3 major flood zones
    loc = generate_location(DISTRICT_CENTER)
    flood_zones.append({
        'zone_id': f'Flood_Zone_{i}',
        'risk_level': 'High',
        'latitude': loc['latitude'],
        'longitude': loc['longitude'],
        'radius_km': random.uniform(1.0, 3.0) # Area to avoid
    })

df_flood = pd.DataFrame(flood_zones)
df_flood.to_csv('flood_zones.csv', index=False)
print("✅ Generated 'flood_zones.csv' (risk areas).")