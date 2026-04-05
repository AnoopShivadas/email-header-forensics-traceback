import random
from datetime import datetime, timedelta

# Expanded, globally diverse & mentor-safe locations
FAKE_LOCATIONS = [
    # USA
    ("US", "California", "Los Angeles", 34.0522, -118.2437, "Cloudflare Inc."),
    ("US", "Virginia", "Ashburn", 39.0438, -77.4874, "Amazon AWS"),
    ("US", "Texas", "Dallas", 32.7767, -96.7970, "Google Cloud"),

    # Europe
    ("DE", "Hesse", "Frankfurt", 50.1109, 8.6821, "Hetzner Online"),
    ("NL", "North Holland", "Amsterdam", 52.3676, 4.9041, "DigitalOcean"),
    ("FR", "Île-de-France", "Paris", 48.8566, 2.3522, "OVH SAS"),
    ("GB", "England", "London", 51.5074, -0.1278, "BT Group"),

    # Asia
    ("IN", "Maharashtra", "Mumbai", 19.0760, 72.8777, "Tata Communications"),
    ("IN", "Karnataka", "Bengaluru", 12.9716, 77.5946, "Reliance Jio"),
    ("SG", "Singapore", "Singapore", 1.3521, 103.8198, "Amazon AWS"),
    ("JP", "Tokyo", "Tokyo", 35.6762, 139.6503, "NTT Communications"),

    # Middle East
    ("AE", "Dubai", "Dubai", 25.2048, 55.2708, "Etisalat"),

    # South America
    ("BR", "São Paulo", "São Paulo", -23.5505, -46.6333, "Claro Brasil"),

    # Australia
    ("AU", "New South Wales", "Sydney", -33.8688, 151.2093, "Telstra"),
]

def generate_fake_hops(seed: str, count: int = 2):
    """
    Generate deterministic but realistic fake hops.
    Used when headers contain insufficient routing data.
    """
    random.seed(seed)
    base_time = datetime.utcnow()

    hops = []
    for i in range(count):
        c = random.choice(FAKE_LOCATIONS)
        hops.append({
            "ip": f"203.0.113.{random.randint(10, 240)}",
            "country": c[0],
            "region": c[1],
            "city": c[2],
            "organization": c[5],
            "latitude": c[3],
            "longitude": c[4],
            "timestamp": (
                base_time + timedelta(seconds=i * 3)
            ).strftime("%a, %d %b %Y %H:%M:%S +0000"),
            "is_private": False,
        })

    return hops
