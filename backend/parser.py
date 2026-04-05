import re
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def parse_email_headers(raw_headers: str) -> Dict[str, Any]:
    """
    Parse raw email headers into structured forensic data
    """
    result = {
        "from_address": None,
        "to_address": None,
        "subject": None,
        "date": None,

        "sender_domain": None,

        "spf_result": "none",
        "dkim_present": False,
        "dmarc_present": False,

        "received_hops": [],
        "ip_addresses": []
    }

    try:
        lines = raw_headers.replace("\r", "").split("\n")
        current = ""

        for line in lines:
            if line.startswith((" ", "\t")):
                current += " " + line.strip()
            else:
                if current:
                    _process_header(current, result)
                current = line.strip()

        if current:
            _process_header(current, result)

        # Reverse hops → origin → destination
        result["received_hops"].reverse()

        # Deduplicate IPs
        result["ip_addresses"] = list(dict.fromkeys(result["ip_addresses"]))

    except Exception as e:
        logger.exception("Header parsing failed")

    return result


# -------------------------------------------------
# HEADER PROCESSING
# -------------------------------------------------

def _process_header(line: str, result: Dict[str, Any]) -> None:
    lower = line.lower()

    if lower.startswith("received:"):
        _parse_received(line, result)

    elif lower.startswith("from:"):
        result["from_address"] = line[5:].strip()
        result["sender_domain"] = _extract_domain(result["from_address"])

    elif lower.startswith("to:"):
        result["to_address"] = line[3:].strip()

    elif lower.startswith("subject:"):
        result["subject"] = line[8:].strip()

    elif lower.startswith("date:"):
        result["date"] = line[5:].strip()

    elif lower.startswith("authentication-results:"):
        _parse_authentication_results(line, result)

    elif lower.startswith("received-spf:"):
        _parse_spf(line, result)

    elif "dkim-signature:" in lower:
        result["dkim_present"] = True

    elif "dmarc" in lower:
        result["dmarc_present"] = True


# -------------------------------------------------
# RECEIVED HOP PARSING
# -------------------------------------------------

def _parse_received(line: str, result: Dict[str, Any]) -> None:
    hop = {
        "from_host": None,
        "by_host": None,
        "ip": None,
        "timestamp": None,
        "raw": line
    }

    from_match = re.search(r"from\s+([^\s\(\);]+)", line, re.I)
    by_match = re.search(r"by\s+([^\s\(\);]+)", line, re.I)
    time_match = re.search(r";\s*(.+)$", line)

    if from_match:
        hop["from_host"] = from_match.group(1)

    if by_match:
        hop["by_host"] = by_match.group(1)

    if time_match:
        hop["timestamp"] = time_match.group(1).strip()
    else:
        hop["timestamp"] = None

    # IPv4
    ips = re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", line)
    for ip in ips:
        if _is_valid_public_ip(ip):
            hop["ip"] = ip
            result["ip_addresses"].append(ip)
            break

    result["received_hops"].append(hop)


# -------------------------------------------------
# AUTH RESULTS
# -------------------------------------------------

def _parse_authentication_results(line: str, result: Dict[str, Any]) -> None:
    lower = line.lower()

    spf = re.search(r"spf=(pass|fail|softfail|neutral|none)", lower)
    if spf:
        result["spf_result"] = spf.group(1)

    if "dkim=pass" in lower:
        result["dkim_present"] = True

    if "dmarc=pass" in lower:
        result["dmarc_present"] = True


def _parse_spf(line: str, result: Dict[str, Any]) -> None:
    lower = line.lower()

    if "pass" in lower:
        result["spf_result"] = "pass"
    elif "softfail" in lower:
        result["spf_result"] = "softfail"
    elif "fail" in lower:
        result["spf_result"] = "fail"
    elif "neutral" in lower:
        result["spf_result"] = "neutral"


# -------------------------------------------------
# HELPERS
# -------------------------------------------------

def _extract_domain(email_string: str) -> str | None:
    if not email_string:
        return None
    match = re.search(r"@([a-zA-Z0-9.-]+)", email_string)
    return match.group(1).lower() if match else None


def _is_valid_public_ip(ip: str) -> bool:
    try:
        parts = list(map(int, ip.split(".")))
        if len(parts) != 4:
            return False

        if parts[0] in (0, 10, 127):
            return False
        if parts[0] == 192 and parts[1] == 168:
            return False
        if parts[0] == 172 and 16 <= parts[1] <= 31:
            return False
        if parts[0] >= 224:
            return False

        return all(0 <= p <= 255 for p in parts)

    except Exception:
        return False
