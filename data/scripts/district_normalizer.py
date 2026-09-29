import re
import uuid
from typing import Optional, Dict, Any, Tuple

# Deterministic namespace for generating canonical district UUIDs
DISTRICT_NAMESPACE = uuid.UUID("a3b8d142-76e9-4e02-8a9d-5f8e12c4b789")


class DistrictNormalizer:
    """
    Normalizes district and state names across varying source spellings, historical names,
    and capitalization, resolving them to canonical names and deterministic UUIDs.
    """

    # Mapping of (raw_clean_district, raw_clean_state) or raw_clean_district to canonical (District, State)
    CANONICAL_DISTRICTS = {
        # Karnataka
        "bengaluru urban": ("Bengaluru Urban", "Karnataka"),
        "bengaluru": ("Bengaluru Urban", "Karnataka"),
        "bangalore": ("Bengaluru Urban", "Karnataka"),
        "bangalore urban": ("Bengaluru Urban", "Karnataka"),
        "mysuru": ("Mysuru", "Karnataka"),
        "mysore": ("Mysuru", "Karnataka"),
        "belagavi": ("Belagavi", "Karnataka"),
        "belgaum": ("Belagavi", "Karnataka"),
        "kalaburagi": ("Kalaburagi", "Karnataka"),
        "gulbarga": ("Kalaburagi", "Karnataka"),

        # Tamil Nadu
        "chennai": ("Chennai", "Tamil Nadu"),
        "madras": ("Chennai", "Tamil Nadu"),
        "coimbatore": ("Coimbatore", "Tamil Nadu"),
        "kovai": ("Coimbatore", "Tamil Nadu"),
        "madurai": ("Madurai", "Tamil Nadu"),
        "kanchipuram": ("Kanchipuram", "Tamil Nadu"),
        "kancheepuram": ("Kanchipuram", "Tamil Nadu"),

        # Kerala
        "thiruvananthapuram": ("Thiruvananthapuram", "Kerala"),
        "trivandrum": ("Thiruvananthapuram", "Kerala"),
        "ernakulam": ("Ernakulam", "Kerala"),
        "cochin": ("Ernakulam", "Kerala"),
        "kochi": ("Ernakulam", "Kerala"),
        "wayanad": ("Wayanad", "Kerala"),

        # Maharashtra
        "mumbai suburban": ("Mumbai Suburban", "Maharashtra"),
        "mumbai": ("Mumbai Suburban", "Maharashtra"),
        "bombay": ("Mumbai Suburban", "Maharashtra"),
        "pune": ("Pune", "Maharashtra"),
        "poona": ("Pune", "Maharashtra"),
        "nagpur": ("Nagpur", "Maharashtra"),
        "gadchiroli": ("Gadchiroli", "Maharashtra"),

        # Gujarat
        "ahmedabad": ("Ahmedabad", "Gujarat"),
        "ahmadabad": ("Ahmedabad", "Gujarat"),
        "surat": ("Surat", "Gujarat"),
        "rajkot": ("Rajkot", "Gujarat"),
        "vadodara": ("Vadodara", "Gujarat"),
        "baroda": ("Vadodara", "Gujarat"),

        # Uttar Pradesh
        "varanasi": ("Varanasi", "Uttar Pradesh"),
        "benares": ("Varanasi", "Uttar Pradesh"),
        "kashi": ("Varanasi", "Uttar Pradesh"),
        "lucknow": ("Lucknow", "Uttar Pradesh"),
        "gorakhpur": ("Gorakhpur", "Uttar Pradesh"),
        "bahraich": ("Bahraich", "Uttar Pradesh"),

        # Bihar
        "patna": ("Patna", "Bihar"),
        "gaya": ("Gaya", "Bihar"),
        "muzaffarpur": ("Muzaffarpur", "Bihar"),
        "purnia": ("Purnia", "Bihar"),
        "purnea": ("Purnia", "Bihar"),

        # Rajasthan
        "jaipur": ("Jaipur", "Rajasthan"),
        "jodhpur": ("Jodhpur", "Rajasthan"),
        "udaipur": ("Udaipur", "Rajasthan"),
        "jaisalmer": ("Jaisalmer", "Rajasthan"),

        # West Bengal
        "kolkata": ("Kolkata", "West Bengal"),
        "calcutta": ("Kolkata", "West Bengal"),
        "darjeeling": ("Darjeeling", "West Bengal"),
        "darjiling": ("Darjeeling", "West Bengal"),
        "murshidabad": ("Murshidabad", "West Bengal"),

        # Madhya Pradesh
        "bhopal": ("Bhopal", "Madhya Pradesh"),
        "indore": ("Indore", "Madhya Pradesh"),
        "jabalpur": ("Jabalpur", "Madhya Pradesh"),
        "balaghat": ("Balaghat", "Madhya Pradesh"),

        # Odisha
        "khurda": ("Khurda", "Odisha"),
        "khordha": ("Khurda", "Odisha"),
        "bhubaneswar": ("Khurda", "Odisha"),
        "cuttack": ("Cuttack", "Odisha"),
        "kalahandi": ("Kalahandi", "Odisha"),

        # Assam
        "kamrup metropolitan": ("Kamrup Metropolitan", "Assam"),
        "kamrup metro": ("Kamrup Metropolitan", "Assam"),
        "guwahati": ("Kamrup Metropolitan", "Assam"),
        "dibrugarh": ("Dibrugarh", "Assam"),
        "cachar": ("Cachar", "Assam"),
        "silchar": ("Cachar", "Assam"),
    }

    # State normalization
    CANONICAL_STATES = {
        "karnataka": "Karnataka",
        "ka": "Karnataka",
        "tamil nadu": "Tamil Nadu",
        "tn": "Tamil Nadu",
        "kerala": "Kerala",
        "kl": "Kerala",
        "maharashtra": "Maharashtra",
        "mh": "Maharashtra",
        "gujarat": "Gujarat",
        "gj": "Gujarat",
        "uttar pradesh": "Uttar Pradesh",
        "up": "Uttar Pradesh",
        "bihar": "Bihar",
        "br": "Bihar",
        "rajasthan": "Rajasthan",
        "rj": "Rajasthan",
        "west bengal": "West Bengal",
        "wb": "West Bengal",
        "madhya pradesh": "Madhya Pradesh",
        "mp": "Madhya Pradesh",
        "odisha": "Odisha",
        "orissa": "Odisha",
        "or": "Odisha",
        "assam": "Assam",
        "as": "Assam",
    }

    @classmethod
    def clean_string(cls, s: Optional[str]) -> str:
        if not s:
            return ""
        s = s.strip().lower()
        # Remove punctuation except spaces
        s = re.sub(r'[^a-z0-9\s]', '', s)
        # Remove district suffix if present
        s = re.sub(r'\b(district|dist)\b', '', s).strip()
        # Collapse multiple spaces
        return re.sub(r'\s+', ' ', s)

    @classmethod
    def generate_district_id(cls, country: str, state: str, district: str) -> uuid.UUID:
        """
        Generates a deterministic UUID5 for a given canonical (country, state, district) tuple.
        """
        key = f"{cls.clean_string(country)}_{cls.clean_string(state)}_{cls.clean_string(district)}"
        return uuid.uuid5(DISTRICT_NAMESPACE, key)

    @classmethod
    def normalize(
        cls,
        raw_district: str,
        raw_state: Optional[str] = None,
        country: str = "India"
    ) -> Dict[str, Any]:
        """
        Resolves raw district and state names to a canonical record with deterministic UUID.
        """
        clean_dist = cls.clean_string(raw_district)
        clean_st = cls.clean_string(raw_state)

        # 1. Direct dictionary match
        if clean_dist in cls.CANONICAL_DISTRICTS:
            canonical_name, canonical_state = cls.CANONICAL_DISTRICTS[clean_dist]
            dist_id = cls.generate_district_id(country, canonical_state, canonical_name)
            return {
                "district_id": dist_id,
                "district_name": canonical_name,
                "state": canonical_state,
                "country": country,
                "matched": True,
                "confidence": 1.0
            }

        # 2. State normalized fallback
        norm_state = cls.CANONICAL_STATES.get(clean_st, raw_state.strip().title() if raw_state else "Unknown")
        norm_district = raw_district.strip().title()
        dist_id = cls.generate_district_id(country, norm_state, norm_district)

        return {
            "district_id": dist_id,
            "district_name": norm_district,
            "state": norm_state,
            "country": country,
            "matched": False,
            "confidence": 0.5
        }


district_normalizer = DistrictNormalizer()
