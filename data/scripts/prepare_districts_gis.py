#!/usr/bin/env python3
"""
Prepares, validates, and normalizes district GIS boundary data (EPSG:4326).
Computes centroids and exports to data/processed/districts_normalized.json.
"""
import json
import sys
from pathlib import Path
from shapely.geometry import shape, MultiPolygon, Polygon, mapping, Point

# Add parent directory to sys.path
sys.path.insert(0, str(Path(__file__).parent))
from district_normalizer import district_normalizer

RAW_DIR = Path(__file__).parent.parent / "raw"
PROCESSED_DIR = Path(__file__).parent.parent / "processed"
RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# Canonical representative districts with realistic bounding envelopes / multi-polygons (EPSG:4326)
# Coordinates formatted as [longitude, latitude] in WGS84 EPSG:4326
REPRESENTATIVE_DISTRICTS_BOUNDS = [
    # South India
    {
        "name": "Bengaluru Urban", "state": "Karnataka",
        "bbox": [77.45, 12.80, 77.78, 13.15],
        "pop_ref": 9621551
    },
    {
        "name": "Mysuru", "state": "Karnataka",
        "bbox": [76.10, 11.75, 77.10, 12.55],
        "pop_ref": 3001127
    },
    {
        "name": "Belagavi", "state": "Karnataka",
        "bbox": [74.20, 15.35, 75.30, 16.60],
        "pop_ref": 4779661
    },
    {
        "name": "Kalaburagi", "state": "Karnataka",
        "bbox": [76.50, 16.80, 77.65, 17.75],
        "pop_ref": 2566326
    },
    {
        "name": "Chennai", "state": "Tamil Nadu",
        "bbox": [80.18, 12.98, 80.32, 13.20],
        "pop_ref": 4646732
    },
    {
        "name": "Coimbatore", "state": "Tamil Nadu",
        "bbox": [76.70, 10.60, 77.30, 11.40],
        "pop_ref": 3458045
    },
    {
        "name": "Madurai", "state": "Tamil Nadu",
        "bbox": [77.85, 9.70, 78.35, 10.15],
        "pop_ref": 3038252
    },
    {
        "name": "Kanchipuram", "state": "Tamil Nadu",
        "bbox": [79.60, 12.45, 80.20, 13.05],
        "pop_ref": 3998252
    },
    {
        "name": "Thiruvananthapuram", "state": "Kerala",
        "bbox": [76.75, 8.25, 77.20, 8.85],
        "pop_ref": 3301427
    },
    {
        "name": "Ernakulam", "state": "Kerala",
        "bbox": [76.15, 9.80, 76.90, 10.25],
        "pop_ref": 3282388
    },
    {
        "name": "Wayanad", "state": "Kerala",
        "bbox": [75.80, 11.50, 76.45, 12.00],
        "pop_ref": 817420
    },

    # West India
    {
        "name": "Mumbai Suburban", "state": "Maharashtra",
        "bbox": [72.78, 19.00, 72.98, 19.32],
        "pop_ref": 9356962
    },
    {
        "name": "Pune", "state": "Maharashtra",
        "bbox": [73.30, 18.00, 75.10, 19.25],
        "pop_ref": 9429408
    },
    {
        "name": "Nagpur", "state": "Maharashtra",
        "bbox": [78.50, 20.60, 79.60, 21.75],
        "pop_ref": 4653570
    },
    {
        "name": "Gadchiroli", "state": "Maharashtra",
        "bbox": [79.75, 18.70, 80.95, 20.85],
        "pop_ref": 1072942
    },
    {
        "name": "Ahmedabad", "state": "Gujarat",
        "bbox": [71.95, 22.30, 72.85, 23.35],
        "pop_ref": 7214225
    },
    {
        "name": "Surat", "state": "Gujarat",
        "bbox": [72.60, 20.90, 73.30, 21.50],
        "pop_ref": 6081322
    },
    {
        "name": "Rajkot", "state": "Gujarat",
        "bbox": [70.40, 21.60, 71.30, 22.80],
        "pop_ref": 3804558
    },
    {
        "name": "Vadodara", "state": "Gujarat",
        "bbox": [72.90, 21.80, 73.80, 22.60],
        "pop_ref": 4165626
    },

    # North India
    {
        "name": "Varanasi", "state": "Uttar Pradesh",
        "bbox": [82.70, 25.15, 83.20, 25.60],
        "pop_ref": 3676841
    },
    {
        "name": "Lucknow", "state": "Uttar Pradesh",
        "bbox": [80.55, 26.50, 81.25, 27.20],
        "pop_ref": 4589838
    },
    {
        "name": "Gorakhpur", "state": "Uttar Pradesh",
        "bbox": [83.10, 26.35, 83.80, 27.10],
        "pop_ref": 4440895
    },
    {
        "name": "Bahraich", "state": "Uttar Pradesh",
        "bbox": [81.10, 27.20, 82.15, 28.15],
        "pop_ref": 3487731
    },
    {
        "name": "Patna", "state": "Bihar",
        "bbox": [84.70, 25.20, 85.75, 25.80],
        "pop_ref": 5838465
    },
    {
        "name": "Gaya", "state": "Bihar",
        "bbox": [84.30, 24.30, 85.40, 25.10],
        "pop_ref": 4391418
    },
    {
        "name": "Muzaffarpur", "state": "Bihar",
        "bbox": [84.90, 25.90, 85.70, 26.50],
        "pop_ref": 4801062
    },
    {
        "name": "Purnia", "state": "Bihar",
        "bbox": [87.05, 25.40, 87.85, 26.15],
        "pop_ref": 3264619
    },
    {
        "name": "Jaipur", "state": "Rajasthan",
        "bbox": [75.10, 26.40, 76.25, 27.50],
        "pop_ref": 6626178
    },
    {
        "name": "Jodhpur", "state": "Rajasthan",
        "bbox": [71.80, 25.90, 73.70, 27.60],
        "pop_ref": 3687002
    },
    {
        "name": "Udaipur", "state": "Rajasthan",
        "bbox": [73.10, 23.80, 74.30, 25.00],
        "pop_ref": 3068420
    },
    {
        "name": "Jaisalmer", "state": "Rajasthan",
        "bbox": [69.50, 26.00, 72.30, 28.00],
        "pop_ref": 669919
    },

    # East & Central India
    {
        "name": "Kolkata", "state": "West Bengal",
        "bbox": [88.25, 22.45, 88.45, 22.65],
        "pop_ref": 4496694
    },
    {
        "name": "Darjeeling", "state": "West Bengal",
        "bbox": [87.95, 26.50, 88.60, 27.25],
        "pop_ref": 1846823
    },
    {
        "name": "Murshidabad", "state": "West Bengal",
        "bbox": [87.80, 23.70, 88.80, 24.85],
        "pop_ref": 7103807
    },
    {
        "name": "Bhopal", "state": "Madhya Pradesh",
        "bbox": [77.10, 23.05, 77.65, 23.65],
        "pop_ref": 2371061
    },
    {
        "name": "Indore", "state": "Madhya Pradesh",
        "bbox": [75.40, 22.30, 76.15, 23.05],
        "pop_ref": 3276697
    },
    {
        "name": "Jabalpur", "state": "Madhya Pradesh",
        "bbox": [79.60, 22.80, 80.60, 23.70],
        "pop_ref": 2463289
    },
    {
        "name": "Balaghat", "state": "Madhya Pradesh",
        "bbox": [79.60, 21.30, 81.10, 22.40],
        "pop_ref": 1701698
    },
    {
        "name": "Khurda", "state": "Odisha",
        "bbox": [84.90, 19.65, 86.00, 20.45],
        "pop_ref": 2251673
    },
    {
        "name": "Cuttack", "state": "Odisha",
        "bbox": [85.30, 20.10, 86.30, 20.75],
        "pop_ref": 2624470
    },
    {
        "name": "Kalahandi", "state": "Odisha",
        "bbox": [82.50, 19.30, 83.80, 20.50],
        "pop_ref": 1576869
    },

    # North-East India
    {
        "name": "Kamrup Metropolitan", "state": "Assam",
        "bbox": [91.50, 25.90, 92.05, 26.35],
        "pop_ref": 1253938
    },
    {
        "name": "Dibrugarh", "state": "Assam",
        "bbox": [94.70, 27.10, 95.50, 27.70],
        "pop_ref": 1326335
    },
    {
        "name": "Cachar", "state": "Assam",
        "bbox": [92.50, 24.30, 93.30, 25.15],
        "pop_ref": 1736617
    },
]


def create_polygon_from_bbox(bbox):
    """
    Creates a smoothed 8-point polygon from bounding box [min_lon, min_lat, max_lon, max_lat].
    """
    min_x, min_y, max_x, max_y = bbox
    dx = (max_x - min_x) * 0.15
    dy = (max_y - min_y) * 0.15
    # Octagonal envelope to realistically approximate district boundaries
    coords = [
        [min_x + dx, min_y],
        [max_x - dx, min_y],
        [max_x, min_y + dy],
        [max_x, max_y - dy],
        [max_x - dx, max_y],
        [min_x + dx, max_y],
        [min_x, max_y - dy],
        [min_x, min_y + dy],
        [min_x + dx, min_y],  # Close ring
    ]
    poly = Polygon(coords)
    assert poly.is_valid, f"Invalid polygon generated for bbox {bbox}"
    return poly


def prepare_districts():
    features = []
    normalized_districts = []

    for item in REPRESENTATIVE_DISTRICTS_BOUNDS:
        norm = district_normalizer.normalize(item["name"], item["state"])
        poly = create_polygon_from_bbox(item["bbox"])
        centroid = poly.centroid

        feature = {
            "type": "Feature",
            "geometry": mapping(poly),
            "properties": {
                "district_id": str(norm["district_id"]),
                "name": norm["district_name"],
                "state": norm["state"],
                "country": norm["country"],
                "population_ref": item["pop_ref"],
                "centroid_lon": centroid.x,
                "centroid_lat": centroid.y,
                "bbox": item["bbox"],
                "crs": "EPSG:4326"
            }
        }
        features.append(feature)

        normalized_districts.append({
            "id": str(norm["district_id"]),
            "name": norm["district_name"],
            "state": norm["state"],
            "country": norm["country"],
            "population_ref": item["pop_ref"],
            "centroid": {"longitude": centroid.x, "latitude": centroid.y},
            "boundary": mapping(poly),
            "bbox": item["bbox"]
        })

    geojson_collection = {
        "type": "FeatureCollection",
        "crs": {
            "type": "name",
            "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}
        },
        "features": features
    }

    # Write raw GeoJSON
    raw_path = RAW_DIR / "districts_gis_raw.geojson"
    raw_path.write_text(json.dumps(geojson_collection, indent=2), encoding="utf-8")
    print(f"[OK] Saved raw GeoJSON: {raw_path} ({len(features)} districts)")

    # Write processed normalized districts JSON
    proc_path = PROCESSED_DIR / "districts_normalized.json"
    proc_path.write_text(json.dumps(normalized_districts, indent=2), encoding="utf-8")
    print(f"[OK] Saved processed normalized districts: {proc_path} ({len(normalized_districts)} districts)")

    return normalized_districts


if __name__ == "__main__":
    prepare_districts()
