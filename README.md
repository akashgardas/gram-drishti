# 🛰️ Gram-Drishti: Rural Infrastructure Intelligence

![Status](https://img.shields.io/badge/Status-Prototype-green) ![Python](https://img.shields.io/badge/Python-3.9+-blue) ![Streamlit](https://img.shields.io/badge/Deployed%20on-Streamlit-ff4b4b)

**Gram-Drishti** is a geospatial decision-support system designed to optimize the placement of rural infrastructure (hospitals, schools) using AI and satellite intelligence.



## 🚨 The Problem
Traditional rural planning relies on manual surveys and straight-line distance (radius) assumptions. This often leads to:
* **Service Gaps:** Villages that *look* covered but are actually cut off by rivers or lack of roads.
* **Inefficient Spending:** New facilities built in redundant locations.
* **Environmental Risk:** Construction in flood-prone zones.

## 💡 The Solution
Gram-Drishti replaces "gut feeling" with **Data-Driven Logic**:
1.  **Real-World Connectivity:** Uses **15-minute Drive-Time Isochrones** (via OpenStreetMap) instead of simple circles.
2.  **Risk Awareness:** Automatically detects and avoids flood zones/water bodies.
3.  **Multi-Objective Optimization:** Algorithms recommend a strategic "Rollout Plan" (e.g., top 5 sites) that maximizes population coverage.

## 🛠️ Tech Stack
* **Core Engine:** Python, Pandas, GeoPandas, Shapely
* **Geospatial Data:** OpenStreetMap (via `osmnx`), NetworkX (Routing)
* **Visualization:** Folium, Streamlit
* **Logic:** Iterative Greedy Optimization (Maximum Coverage Problem)

## 📂 Project Structure
```text
├── app/
│   └── app.py              # Main Dashboard Application
├── data/
│   ├── villages.csv        # Demographic data (Narayanpet)
│   ├── hospitals.csv       # Existing infrastructure
│   ├── drive_time.geojson  # Calculated isochrone layer
│   └── final_rec.geojson   # AI-generated recommendation
├── script/
│   ├── real_data_loader.py # Fetches live OSM data
│   ├── isochrone_analysis.py # Calculates drive-time zones
│   └── decision_engine.py  # Runs the optimization logic
└── requirements.txt        # Dependencies

## 🚀 How to Run Locally

1.  **Clone the Repo:**
    
    Bash
    
    ```
    git clone [https://github.com/your-username/gram-drishti.git](https://github.com/your-username/gram-drishti.git)
    cd gram-drishti
    ```
    
2.  **Install Dependencies:**
    
    Bash
    
    ```
    pip install -r requirements.txt
    ```
    
3.  **Run the App:**
    
    Bash
    
    ```
    streamlit run app/app.py
    ```
    

## 🌍 Deployment

This project is deployment-ready for **Streamlit Cloud**.

1.  Push code to GitHub.
    
2.  Connect repository to Streamlit Cloud.
    
3.  The app reads pre-computed geospatial data from the `data/` folder for high performance.
    

* * *

*Built for Tech Savishkaar 4.0 Hackathon*

```
---

### **5. `packages.txt` (Optional but Recommended)**
Sometimes `geopandas` or `rtree` need system-level libraries on Linux (which Streamlit Cloud runs on). Create a file named `packages.txt`.

```text
libspatialindex-dev
libgdal-dev
```

* * *
