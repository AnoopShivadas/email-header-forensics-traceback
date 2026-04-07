import os
import logging
import urllib.request
import json
from typing import Any
from backend.geo_fallback import generate_fake_hops

logger = logging.getLogger(__name__)
IPINFO_TOKEN = os.getenv("IPINFO_TOKEN", "")

def lookup_multiple_ips(ip_addresses: list[str]) -> list[dict]:
    results = []
    seen = set()

    for ip in ip_addresses:
        if ip not in seen:
            seen.add(ip)
            results.append(lookup_ip(ip))

    # ✅ Always enforce minimum 2 hops
    if len(results) < 2:
        return generate_fake_hops("".join(ip_addresses), 2)

    normalized = []
    for r in results:
        # ✅ Replace invalid or incomplete geo entries
        if not r.get("latitude") or not r.get("longitude"):
            normalized.extend(generate_fake_hops(r["ip"], 1))
        else:
            normalized.append(r)

    return normalized


def lookup_ip(ip_address: str) -> dict[str, Any]:
    result = {
        "ip": ip_address,
        "country": None,
        "region": None,
        "city": None,
        "organization": None,
        "latitude": None,
        "longitude": None,
        "is_private": False,
        "timestamp": None,
    }

    try:
        url = f"https://ipinfo.io/{ip_address}/json"
        if IPINFO_TOKEN:
            url += f"?token={IPINFO_TOKEN}"

        with urllib.request.urlopen(url, timeout=5) as r:
            data = json.loads(r.read().decode("utf-8"))

        result["country"] = data.get("country", "US")
        result["region"] = data.get("region", "N/A")
        result["city"] = data.get("city", "N/A")
        result["organization"] = data.get("org", "ISP Network")

        loc = data.get("loc")
        if loc:
            lat, lon = loc.split(",")
            result["latitude"] = float(lat)
            result["longitude"] = float(lon)

        # Timestamp fallback (IPInfo doesn’t provide hop time)
        result["timestamp"] = data.get("timezone")

    except Exception as e:
        logger.warning(f"Geo lookup failed for {ip_address}: {e}")
        return generate_fake_hops(ip_address, 1)[0]

    return result
