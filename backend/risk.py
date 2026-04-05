import logging
from typing import Any

logger = logging.getLogger(__name__)

SUSPICIOUS_KEYWORDS = [
    "urgent", "verify", "suspend", "blocked",
    "confirm", "reset", "security", "alert", "unauthorized"
]

FREE_EMAIL_DOMAINS = {
    "gmail.com", "yahoo.com", "outlook.com", "hotmail.com"
}

SUSPICIOUS_TLDS = {
    ".xyz", ".top", ".click", ".link", ".work", ".date"
}


def calculate_risk_score(
    parsed_headers: dict[str, Any],
    geo_results: list[dict[str, Any]]
) -> dict[str, Any]:

    # 🔑 Slightly lower baseline to avoid clustering
    score = 45
    findings = []

    # --------------------------------------------------
    # SPF
    # --------------------------------------------------
    spf = parsed_headers.get("spf_result", "none")

    if spf == "pass":
        score -= 18
        findings.append(_f("SPF passed", -18, "low"))
    elif spf == "fail":
        score += 25
        findings.append(_f("SPF failed", +25, "high"))
    elif spf == "softfail":
        score += 12
        findings.append(_f("SPF softfail", +12, "medium"))
    else:
        score += 6
        findings.append(_f("No SPF record", +6, "low"))

    # --------------------------------------------------
    # DKIM
    # --------------------------------------------------
    if parsed_headers.get("dkim_present"):
        score -= 12
        findings.append(_f("DKIM signature present", -12, "low"))
    else:
        score += 18
        findings.append(_f("Missing DKIM signature", +18, "medium"))

    # --------------------------------------------------
    # DMARC
    # --------------------------------------------------
    if parsed_headers.get("dmarc_present"):
        score -= 8
        findings.append(_f("DMARC alignment present", -8, "low"))
    else:
        score += 12
        findings.append(_f("No DMARC policy", +12, "low"))

    # --------------------------------------------------
    # Auth Strength Normalization (NO NEW FEATURE)
    # --------------------------------------------------
    if (
        spf == "pass"
        and parsed_headers.get("dkim_present")
        and parsed_headers.get("dmarc_present")
    ):
        score -= 3
        findings.append(_f(
            "Strong authentication alignment",
            -3,
            "low"
        ))

    # --------------------------------------------------
    # Sender Domain Analysis
    # --------------------------------------------------
    sender_domain = parsed_headers.get("sender_domain")

    if sender_domain:
        if sender_domain in FREE_EMAIL_DOMAINS:
            score += 8
            findings.append(_f("Free email domain used", +8, "medium"))

        for tld in SUSPICIOUS_TLDS:
            if sender_domain.endswith(tld):
                score += 15
                findings.append(_f(
                    f"Suspicious domain TLD ({tld})",
                    +15,
                    "medium"
                ))
                break

    # --------------------------------------------------
    # Keyword Heuristics
    # --------------------------------------------------
    text = (
        (parsed_headers.get("subject") or "") +
        (parsed_headers.get("from_address") or "")
    ).lower()

    hits = [k for k in SUSPICIOUS_KEYWORDS if k in text]
    if hits:
        kw_score = min(len(hits) * 6, 18)
        score += kw_score
        findings.append(_f(
            "Suspicious language detected",
            +kw_score,
            "medium",
            f"Keywords: {', '.join(hits)}"
        ))

    # --------------------------------------------------
    # Routing Analysis
    # --------------------------------------------------
    hops = parsed_headers.get("received_hops", [])
    if len(hops) > 5:
        extra = min((len(hops) - 5) * 3, 12)
        score += extra
        findings.append(_f(
            "Extended routing path",
            +extra,
            "medium",
            f"{len(hops)} hops detected"
        ))

    countries = {
        g.get("country")
        for g in geo_results
        if g.get("country") and not g.get("is_private")
    }

    if len(countries) > 1:
        geo_score = min((len(countries) - 1) * 7, 15)
        score += geo_score
        findings.append(_f(
            "Cross-border email routing",
            +geo_score,
            "medium",
            f"Routed through {len(countries)} countries"
        ))



    # --------------------------------------------------
    # HEADER ENTROPY DIFFERENTIATION (ADDITIVE)
    # --------------------------------------------------
    header_length = len(
        (parsed_headers.get("subject") or "") +
        (parsed_headers.get("from_address") or "") +
        (parsed_headers.get("to_address") or "")
    )

    entropy_adjust = min(header_length // 120, 5)
    if entropy_adjust:
        score += entropy_adjust
        findings.append(_f(
            "Header structural variance",
            +entropy_adjust,
            "low",
            f"Header length entropy: {header_length}"
        ))

        # --------------------------------------------------
        # ROUTING ENTROPY (ADDITIVE)
        # --------------------------------------------------
        unique_hosts = {
            h.get("from_host")
            for h in parsed_headers.get("received_hops", [])
            if h.get("from_host")
        }

        if len(unique_hosts) > 1:
            route_entropy = min(len(unique_hosts), 4)
            score += route_entropy
            findings.append(_f(
                "Routing path diversity",
                +route_entropy,
                "low",
                f"{len(unique_hosts)} distinct relay hosts"
            ))


    # --------------------------------------------------
    # Finalize
    # --------------------------------------------------
    score = max(0, min(100, score))

    if score >= 75:
        verdict = "THREAT"
    elif score >= 45:
        verdict = "SUSPICIOUS"
    else:
        verdict = "SAFE"

    return {
        "risk_score": score,
        "verdict": verdict,
        "findings": findings,
        "summary": _summary(score, verdict, findings)
    }


# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def _f(rule, score, severity, details=None):
    return {
        "rule": rule,
        "impact": score,
        "severity": severity,
        "details": details
    }


def _summary(score, verdict, findings):
    if verdict == "SAFE":
        return f"Low risk detected ({score}/100). Authentication and routing indicators look normal."
    if verdict == "SUSPICIOUS":
        top = ", ".join(f["rule"] for f in findings[:2])
        return f"Moderate risk detected ({score}/100). Notable issues: {top}."
    top = ", ".join(f["rule"] for f in findings[:2])
    return f"High risk detected ({score}/100). Critical indicators: {top}."
