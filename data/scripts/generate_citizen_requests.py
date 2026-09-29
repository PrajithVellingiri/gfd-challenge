#!/usr/bin/env python3
"""
Citizen Demand & Grievances Dataset Generator (Synthetic)
Generates 8,000 realistic, geographically-grounded citizen requests across 7 infrastructure categories.
Embeds intentional demand hotspots aligned with demographic and infrastructure realities.
Outputs to data/processed/citizen_requests_normalized.json.
"""
import json
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from shapely.geometry import shape, Point

PROCESSED_DIR = Path(__file__).parent.parent / "processed"
DISTRICTS_FILE = PROCESSED_DIR / "districts_normalized.json"

CATEGORIES = [
    "healthcare",
    "education",
    "roads",
    "water",
    "transportation",
    "electricity",
    "digital infrastructure"
]

LANGUAGES = ["en", "hi", "ta", "kn", "bn", "mr", "as"]
SOURCE_TYPES = ["mobile_app", "web", "ivr", "sms"]
URGENCIES = ["low", "medium", "high", "critical"]

# Realistic description templates per category
DESCRIPTIONS_BY_CATEGORY = {
    "healthcare": [
        "Primary Health Centre (PHC) lacks emergency doctor on duty; patients forced to travel 40km to district hospital.",
        "Essential medicines including insulin and pediatric antibiotics out of stock for over three weeks at local clinic.",
        "Maternal healthcare facility has no functioning sonography or ultrasound equipment; pregnant mothers delayed for scans.",
        "Community Health Centre ambulance is broken down and unserviceable for emergency patient transfers.",
        "Primary health sub-centre closed for 5 days consecutively due to acute auxiliary nurse midwife shortage.",
        "Anti-rabies and anti-snake venom vaccines completely unavailable at CHC following multiple stray animal incidents."
    ],
    "water": [
        "Jal Jeevan piped water supply pipeline damaged during road widening; 200 households without tap water for 9 days.",
        "Village handpump is pumping heavily turbid and muddy water; risk of waterborne illness among children.",
        "Piped water arrives only once in 4 days with extremely low pressure for barely 25 minutes.",
        "Primary school borehole pump motor burnt out; mid-day meal preparation severely disrupted without drinking water.",
        "Community overhead water tank overflowing into street due to broken float valve; massive drinking water wastage.",
        "Water supply line contaminated by adjacent open sewage drain seepage; foul smell and yellow discoloration."
    ],
    "roads": [
        "Severe deep potholes spanning 3km stretch on main district link road causing frequent two-wheeler accidents.",
        "Bridge approach slab cracked and sinking dangerously following recent heavy rain; heavy vehicles stranded.",
        "Unpaved earthen village road completely waterlogged and slushy, preventing ambulances and school buses from entering.",
        "Dangerous blind curve on hillside stretch lacks guardrails and convex mirrors, causing recurring accidents.",
        "Culvert across agricultural canal collapsed, disconnecting 4 surrounding hamlets from main highway.",
        "Street tarmac completely stripped off after sewer line excavation 6 months ago, creating severe dust and road hazards."
    ],
    "education": [
        "Government Higher Secondary School roof tiles broken, water pouring directly into class 6 and 7 classrooms.",
        "Only 2 teachers appointed for 165 students across 5 grades; classes left unattended throughout the afternoon.",
        "Girls secondary school toilet block non-functional due to lack of running water and missing door latches.",
        "School perimeter boundary wall collapsed, allowing stray cattle and vehicles into children play area.",
        "High school science and mathematics laboratory locked and disused due to complete lack of basic lab equipment.",
        "Desks and benches severely deficient; more than 60 students forced to sit on bare damp concrete floor."
    ],
    "transportation": [
        "State transport bus service reduced from 4 trips to 1 trip daily; college students and office workers stranded.",
        "Bus stop passenger shelter roof blown off; commuters waiting under scorching heat and downpour without protection.",
        "No direct public bus service from suburban residential wards to central railway station; auto rickshaws overcharging.",
        "Bus drivers refusing to halt at designated rural school bus stop, leaving small children stranded along highway.",
        "Feeder mini-bus route abruptly terminated leaving senior citizens without transit access to government hospital.",
        "Overcrowding in morning commuter bus with passengers hanging on footboard due to lack of additional morning frequency."
    ],
    "electricity": [
        "Distribution transformer blown out 5 days ago; 80 households in dark with domestic water motors non-functional.",
        "Extreme voltage fluctuation (dropping to 140V) continuously burning irrigation submersible pump motors and fans.",
        "High tension overhead power line sagging dangerously within 6 feet of agricultural pathway; critical hazard.",
        "Unscheduled power cuts exceeding 8 hours daily during crucial board exam preparation and nighttime.",
        "Damaged electric pole tilting precariously over main street after tractor collision; risk of imminent collapse.",
        "Streetlights in entire residential cluster burned out for two months, leading to theft and safety concerns."
    ],
    "digital infrastructure": [
        "Common Service Centre (CSC) optical fiber link offline for 3 weeks; citizens unable to apply for pensions or certificates.",
        "Village has complete zero-signal cellular dead zone; residents must walk 2km to hilltop for mobile verification OTPs.",
        "Gram Panchayat digital seva portal server constantly timing out during DBT subsidy application submission.",
        "Broadband internet line severed during drainage trenching and telecom department has not repaired line.",
        "Aadhaar biometric authentication kiosk scanner malfunctioning, preventing elderly citizens from ration disbursement.",
        "Public Wi-Fi access point installed under smart city initiative has been non-operational since installation."
    ]
}

# Demand hotspot profiles
# Maps district names to category weight multipliers
HOTSPOT_PROFILES = {
    # High Healthcare Demand
    "Bahraich": {"healthcare": 4.5, "water": 1.2, "education": 1.5},
    "Purnia": {"healthcare": 4.0, "education": 1.8, "water": 1.2},
    "Gadchiroli": {"healthcare": 4.2, "roads": 2.0, "digital infrastructure": 1.8},
    "Kalahandi": {"healthcare": 3.8, "water": 2.2, "education": 1.5},

    # High Water & Sanitation Demand
    "Jaisalmer": {"water": 5.0, "electricity": 2.0, "healthcare": 1.0},
    "Jodhpur": {"water": 4.5, "roads": 1.5, "electricity": 1.5},
    "Gaya": {"water": 4.0, "healthcare": 2.0, "education": 1.5},
    "Kalaburagi": {"water": 4.0, "healthcare": 2.2, "electricity": 1.5},

    # High Roads & Transportation Demand
    "Wayanad": {"roads": 4.5, "transportation": 3.5, "healthcare": 1.5},
    "Darjeeling": {"roads": 4.2, "transportation": 3.8, "water": 1.5},
    "Coimbatore": {"roads": 3.5, "transportation": 3.0, "electricity": 1.2},
    "Pune": {"roads": 3.2, "transportation": 3.5, "water": 1.5},

    # High Education & Digital Infrastructure Demand
    "Balaghat": {"education": 3.8, "digital infrastructure": 3.5, "roads": 2.0},
    "Cachar": {"education": 3.5, "digital infrastructure": 3.2, "healthcare": 2.0},
    "Muzaffarpur": {"education": 3.5, "digital infrastructure": 3.0, "water": 1.5},
}

RANDOM_SEED = 12345
TOTAL_RECORDS = 8000


def get_random_point_in_bbox(bbox, rng):
    min_x, min_y, max_x, max_y = bbox
    # Generate point strictly inside bounding box with a 5% margin
    margin_x = (max_x - min_x) * 0.08
    margin_y = (max_y - min_y) * 0.08
    lon = rng.uniform(min_x + margin_x, max_x - margin_x)
    lat = rng.uniform(min_y + margin_y, max_y - margin_y)
    return round(lat, 6), round(lon, 6)


def generate_citizen_requests():
    assert DISTRICTS_FILE.exists(), f"Districts file {DISTRICTS_FILE} not found."
    districts = json.loads(DISTRICTS_FILE.read_text(encoding="utf-8"))

    rng = random.Random(RANDOM_SEED)
    requests = []

    # Calculate district base weights based on population
    total_pop = sum(d.get("population_ref", 1000000) for d in districts)
    district_weights = [d.get("population_ref", 1000000) / total_pop for d in districts]

    start_date = datetime(2025, 1, 1, 0, 0, 0)
    end_date = datetime(2026, 9, 28, 23, 59, 59)
    total_seconds = int((end_date - start_date).total_seconds())

    for i in range(TOTAL_RECORDS):
        req_id = str(uuid.uuid4())
        # Select district with demographic population probability
        dist = rng.choices(districts, weights=district_weights, k=1)[0]
        dist_name = dist["name"]
        bbox = dist["bbox"]

        # Category selection with hotspot bias
        hotspot = HOTSPOT_PROFILES.get(dist_name, {})
        category_weights = [hotspot.get(cat, 1.0) for cat in CATEGORIES]
        cat = rng.choices(CATEGORIES, weights=category_weights, k=1)[0]

        # Template description
        desc = rng.choice(DESCRIPTIONS_BY_CATEGORY[cat])

        # Urgency: Hotspot categories have higher urgency
        if cat in hotspot:
            urgency_weights = [0.10, 0.25, 0.40, 0.25]  # Higher high & critical
        else:
            urgency_weights = [0.25, 0.45, 0.20, 0.10]
        urgency = rng.choices(URGENCIES, weights=urgency_weights, k=1)[0]

        # Coordinates
        lat, lon = get_random_point_in_bbox(bbox, rng)

        # Timestamp
        offset_sec = rng.randint(0, total_seconds)
        created_at = (start_date + timedelta(seconds=offset_sec)).isoformat() + "Z"

        # Language selection
        state = dist["state"]
        if state == "Tamil Nadu":
            lang = rng.choices(["ta", "en"], weights=[0.75, 0.25], k=1)[0]
        elif state == "Karnataka":
            lang = rng.choices(["kn", "en"], weights=[0.70, 0.30], k=1)[0]
        elif state == "West Bengal":
            lang = rng.choices(["bn", "en"], weights=[0.75, 0.25], k=1)[0]
        elif state == "Maharashtra":
            lang = rng.choices(["mr", "en", "hi"], weights=[0.55, 0.30, 0.15], k=1)[0]
        elif state == "Assam":
            lang = rng.choices(["as", "en", "bn"], weights=[0.60, 0.25, 0.15], k=1)[0]
        else:
            lang = rng.choices(["hi", "en"], weights=[0.80, 0.20], k=1)[0]

        source_type = rng.choices(SOURCE_TYPES, weights=[0.45, 0.30, 0.15, 0.10], k=1)[0]

        requests.append({
            "id": req_id,
            "district_id": dist["id"],
            "district_name": dist["name"],
            "state": dist["state"],
            "country": dist["country"],
            "category": cat,
            "description": desc,
            "language": lang,
            "urgency": urgency,
            "status": "submitted",
            "latitude": lat,
            "longitude": lon,
            "location_name": f"{dist_name} Ward {rng.randint(1, 45)}",
            "source_type": source_type,
            "is_synthetic": True,
            "data_type": "synthetic",
            "created_at": created_at,
            "updated_at": created_at
        })

    proc_path = PROCESSED_DIR / "citizen_requests_normalized.json"
    proc_path.write_text(json.dumps(requests, indent=2), encoding="utf-8")
    print(f"[OK] Saved processed citizen requests: {proc_path} ({len(requests)} records)")
    return requests


if __name__ == "__main__":
    generate_citizen_requests()
