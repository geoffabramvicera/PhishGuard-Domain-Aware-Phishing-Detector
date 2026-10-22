"""Domain-aware and URL-structure feature extraction.

This module is intentionally offline. It parses the hostname and URL text; it does
not contact the website, query DNS, or verify live reputation.
"""
from __future__ import annotations

import ipaddress
import math
import re
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

BASE_DIR = Path(__file__).resolve().parent
PSL_PATH = BASE_DIR / "public_suffix_list.dat"

# These are weak features, not rules that automatically mark a URL as malicious.
SUSPICIOUS_TERMS = frozenset({
    "account", "activate", "auth", "bank", "billing", "bonus", "captcha",
    "confirm", "credential", "crypto", "gift", "invoice", "login", "logon",
    "payment", "password", "recover", "recovery", "secure", "security",
    "signin", "support", "unlock", "update", "validate", "verification",
    "verify", "wallet", "webscr", "webscr", "session", "confirmidentity",
})

# Feature lexicon used to detect brand terms placed in a suspicious hostname.
# It is not an allowlist and never automatically approves arbitrary URLs on these sites.
BRAND_TOKENS = frozenset({
    "adobe", "amazon", "apple", "bankofamerica", "binance", "chase", "coinbase",
    "discord", "dropbox", "facebook", "github", "google", "instagram", "linkedin",
    "microsoft", "netflix", "office", "outlook", "paypal", "steam", "telegram",
    "tiktok", "twitter", "wellsfargo", "whatsapp", "yahoo", "youtube", "zoom",
})

KNOWN_MAJOR_HOME_DOMAINS = frozenset({
    "adobe.com", "amazon.com", "apple.com", "brave.com", "cloudflare.com",
    "duckduckgo.com", "facebook.com", "github.com", "google.com", "instagram.com",
    "linkedin.com", "microsoft.com", "mozilla.org", "netflix.com", "openai.com",
    "paypal.com", "python.org", "reddit.com", "stackoverflow.com", "wikipedia.org",
    "yahoo.com", "youtube.com", "zoom.us",
})

COMMON_PUBLIC_SUFFIXES = frozenset({
    "com", "org", "net", "edu", "gov", "mil", "int", "co.uk", "org.uk",
    "ac.uk", "gov.uk", "com.au", "net.au", "org.au", "co.nz", "com.br",
    "com.ph", "com.sg", "co.in", "co.jp", "co.kr", "com.mx", "com.tr",
})

_TOKEN_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)
_HEX_ESCAPE_RE = re.compile(r"%[0-9a-fA-F]{2}")
_SUSPICIOUS_EXTENSIONS = frozenset({
    ".apk", ".bat", ".cmd", ".com", ".exe", ".hta", ".iso", ".jar", ".js",
    ".msi", ".ps1", ".scr", ".vbs",
})


def _idna_ascii(host: str) -> str:
    """Return a lower-case ASCII form when IDNA encoding is possible."""
    host = (host or "").strip().rstrip(".").lower()
    if not host:
        return ""
    try:
        return host.encode("idna").decode("ascii").lower()
    except (UnicodeError, ValueError):
        return host


def _load_public_suffix_rules() -> tuple[set[str], set[str], set[str]]:
    """Load exact, wildcard, and exception rules from the bundled PSL snapshot."""
    exact: set[str] = set()
    wildcard: set[str] = set()
    exceptions: set[str] = set()
    if not PSL_PATH.exists():
        return exact, wildcard, exceptions

    for raw_line in PSL_PATH.read_text(encoding="utf-8").splitlines():
        rule = raw_line.strip()
        if not rule or rule.startswith("//"):
            continue
        if rule.startswith("!"):
            exceptions.add(_idna_ascii(rule[1:]))
        elif rule.startswith("*."):
            wildcard.add(_idna_ascii(rule[2:]))
        else:
            exact.add(_idna_ascii(rule))
    return exact, wildcard, exceptions


_PSL_EXACT, _PSL_WILDCARD, _PSL_EXCEPTIONS = _load_public_suffix_rules()


def _parse_for_analysis(url: str):
    """Parse a URL, adding a scheme only for parsing URLs in imperfect datasets."""
    value = str(url or "").strip()
    candidate = value
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", candidate) and not candidate.startswith("//"):
        candidate = "http://" + candidate
    try:
        parsed = urlsplit(candidate)
        hostname = (parsed.hostname or "").rstrip(".").lower()
        try:
            port = parsed.port
        except ValueError:
            port = None
        return parsed, hostname, port
    except ValueError:
        return urlsplit(""), "", None


def split_domain(hostname: str) -> tuple[str, str, int]:
    """Return (registrable domain, public suffix, subdomain count) using PSL rules.

    A small fallback is used if the bundled list is unavailable. The fallback is
    intentionally described as approximate in the UI and documentation.
    """
    host = _idna_ascii(hostname)
    if not host:
        return "", "", 0
    try:
        ipaddress.ip_address(host)
        return host, "", 0
    except ValueError:
        pass

    labels = [label for label in host.split(".") if label]
    if len(labels) <= 1:
        return host, labels[0] if labels else "", 0

    # Exceptions override wildcard and exact rules, for example !www.ck.
    exception_len = 0
    for start in range(len(labels)):
        candidate = ".".join(labels[start:])
        if candidate in _PSL_EXCEPTIONS:
            exception_len = len(labels) - start - 1
            break

    if exception_len:
        suffix_len = exception_len
    else:
        suffix_len = 1  # PSL's default rule is "*".
        for start in range(len(labels)):
            candidate = ".".join(labels[start:])
            if candidate in _PSL_EXACT:
                suffix_len = max(suffix_len, len(labels) - start)
            if start + 1 < len(labels):
                tail = ".".join(labels[start + 1:])
                if tail in _PSL_WILDCARD:
                    suffix_len = max(suffix_len, len(labels) - start)

    public_suffix = ".".join(labels[-suffix_len:])
    if len(labels) <= suffix_len:
        return host, public_suffix, 0

    registered_domain = ".".join(labels[-(suffix_len + 1):])
    subdomain_count = max(0, len(labels) - suffix_len - 1)
    return registered_domain, public_suffix, subdomain_count


def get_url_parts(url: str) -> dict[str, str | int | bool]:
    """Extract parsed URL fields for the model and result explanation."""
    value = str(url or "").strip()
    parsed, hostname, port = _parse_for_analysis(value)
    hostname_ascii = _idna_ascii(hostname)
    registered_domain, public_suffix, subdomain_count = split_domain(hostname_ascii)
    labels = [part for part in hostname_ascii.split(".") if part]
    is_ip = False
    try:
        ipaddress.ip_address(hostname_ascii)
        is_ip = True
    except ValueError:
        pass

    domain_label = ""
    if registered_domain and not is_ip:
        domain_labels = registered_domain.split(".")
        if len(domain_labels) >= 2:
            domain_label = domain_labels[0]
        else:
            domain_label = domain_labels[0]

    if port is None:
        nonstandard_port = False
    else:
        expected_port = 443 if parsed.scheme.lower() == "https" else 80
        nonstandard_port = port != expected_port

    return {
        "raw_url": value,
        "scheme": parsed.scheme.lower(),
        "hostname": hostname,
        "hostname_ascii": hostname_ascii,
        "registered_domain": registered_domain,
        "domain_label": domain_label,
        "public_suffix": public_suffix,
        "subdomain_count": subdomain_count,
        "labels": labels,
        "path": parsed.path or "",
        "query": parsed.query or "",
        "fragment": parsed.fragment or "",
        "port": port if port is not None else 0,
        "has_port": port is not None,
        "nonstandard_port": nonstandard_port,
        "is_ip_address": is_ip,
        "has_userinfo": parsed.username is not None or parsed.password is not None,
        "path_and_query": (parsed.path or "") + ("?" + parsed.query if parsed.query else "") + ("#" + parsed.fragment if parsed.fragment else ""),
    }


def _entropy(text: str) -> float:
    if not text:
        return 0.0
    counts = Counter(text)
    total = len(text)
    return -sum((count / total) * math.log2(count / total) for count in counts.values())


def _safe_ratio(numerator: int | float, denominator: int | float) -> float:
    return round(float(numerator) / denominator, 4) if denominator else 0.0


def _brand_signals(hostname: str, registered_domain: str) -> tuple[int, int, int]:
    """Return exact brand token in root label, in subdomain, and mismatched root."""
    host_labels = [p for p in hostname.split(".") if p]
    root_labels = [p for p in registered_domain.split(".") if p]
    root_label = root_labels[0] if root_labels else ""
    subdomain_labels = host_labels[:max(0, len(host_labels) - len(root_labels))]

    brand_in_root = int(any(brand in root_label for brand in BRAND_TOKENS))
    brand_in_subdomain = int(any(
        brand in label for label in subdomain_labels for brand in BRAND_TOKENS
    ))
    exact_brand_root = any(root_label == brand for brand in BRAND_TOKENS)
    brand_mismatch = int(brand_in_root and not exact_brand_root)
    return brand_in_root, brand_in_subdomain, brand_mismatch


def extract_features(url: str) -> dict[str, int | float]:
    """Extract numeric domain, URL structure, and character-pattern features."""
    value = str(url or "").strip()
    parts = get_url_parts(value)
    hostname = str(parts["hostname"])
    hostname_ascii = str(parts["hostname_ascii"])
    registered_domain = str(parts["registered_domain"])
    public_suffix = str(parts["public_suffix"])
    host_labels = list(parts["labels"])
    is_ip = int(bool(parts["is_ip_address"]))
    host_content = hostname_ascii.replace(".", "").replace("-", "").replace("_", "")
    registered_label = str(parts["domain_label"])
    path = str(parts["path"])
    query = str(parts["query"])
    fragment = str(parts["fragment"])
    path_text = f"{path} {query} {fragment}".lower()

    host_tokens = _TOKEN_RE.findall(hostname_ascii.lower())
    path_tokens = _TOKEN_RE.findall(path_text)
    host_suspicious = min(8, sum(token in SUSPICIOUS_TERMS for token in host_tokens))
    path_suspicious = min(8, sum(token in SUSPICIOUS_TERMS for token in path_tokens))
    brand_root, brand_subdomain, brand_mismatch = _brand_signals(hostname_ascii, registered_domain)

    try:
        is_punycode = int(any(label.startswith("xn--") for label in host_labels))
    except Exception:
        is_punycode = 0
    has_non_ascii = int(any(ord(c) > 127 for c in hostname))

    path_segments = [segment for segment in path.split("/") if segment]
    query_parts = [part for part in query.split("&") if part]
    host_digits = sum(char.isdigit() for char in hostname_ascii)
    host_alpha = sum(char.isalpha() for char in hostname_ascii)
    host_symbols = sum(not (char.isalnum() or char in ".-") for char in hostname_ascii)
    percent_encoded_count = len(_HEX_ESCAPE_RE.findall(value))
    path_lower = path.lower()
    suspicious_extension = int(any(path_lower.endswith(ext) for ext in _SUSPICIOUS_EXTENSIONS))
    double_extension = int(bool(re.search(r"\.(?:pdf|docx?|xlsx?|jpg|png)\.(?:exe|scr|js|bat|msi)$", path_lower)))
    public_suffix_labels = public_suffix.split(".") if public_suffix else []
    common_suffix = int(public_suffix in COMMON_PUBLIC_SUFFIXES)
    port_value = int(bool(parts["nonstandard_port"]))
    url_special = sum(not char.isalnum() for char in value)

    return {
        # Legacy URL-wide character features.
        "url_length": len(value),
        "url_dots": value.count("."),
        "url_hyphens": value.count("-"),
        "url_slashes": value.count("/"),
        "url_underscores": value.count("_"),
        "url_at_signs": value.count("@"),
        "uses_https": int(str(parts["scheme"]) == "https"),
        "uses_http": int(str(parts["scheme"]) == "http"),
        "url_digit_count": sum(char.isdigit() for char in value),
        "url_digit_ratio": _safe_ratio(sum(char.isdigit() for char in value), len(value)),
        "url_special_char_ratio": _safe_ratio(url_special, len(value)),
        "url_entropy": round(_entropy(value), 4),
        "percent_encoded_count": percent_encoded_count,
        "encoded_at_sign": int(bool(re.search(r"%40", value, re.IGNORECASE))),
        "has_double_slash_in_path": int("//" in path),
        "has_query": int(bool(query)),
        "query_length": len(query),
        "query_parameter_count": len(query_parts),
        "has_fragment": int(bool(fragment)),
        "path_length": len(path),
        "path_depth": len(path_segments),
        "suspicious_path_term_count": path_suspicious,
        "suspicious_file_extension": suspicious_extension,
        "double_file_extension": double_extension,
        # Hostname and registrable-domain features.
        "hostname_length": len(hostname_ascii),
        "registered_domain_length": len(registered_domain),
        "registered_label_length": len(registered_label),
        "public_suffix_length": len(public_suffix),
        "public_suffix_label_count": len(public_suffix_labels),
        "public_suffix_is_common": common_suffix,
        "hostname_label_count": len(host_labels),
        "subdomain_count": int(parts["subdomain_count"]),
        "hostname_hyphen_count": hostname_ascii.count("-"),
        "hostname_underscore_count": hostname_ascii.count("_"),
        "hostname_digit_count": host_digits,
        "hostname_digit_ratio": _safe_ratio(host_digits, len(hostname_ascii)),
        "registered_label_digit_ratio": _safe_ratio(sum(c.isdigit() for c in registered_label), len(registered_label)),
        "max_hostname_label_length": max((len(label) for label in host_labels), default=0),
        "avg_hostname_label_length": _safe_ratio(sum(len(label) for label in host_labels), len(host_labels)),
        "hostname_alpha_ratio": _safe_ratio(host_alpha, len(hostname_ascii)),
        "hostname_symbol_ratio": _safe_ratio(host_symbols, len(hostname_ascii)),
        "hostname_entropy": round(_entropy(host_content), 4),
        "registered_label_entropy": round(_entropy(registered_label), 4),
        "hostname_unique_char_ratio": _safe_ratio(len(set(host_content)), len(host_content)),
        "has_ip_address": is_ip,
        "has_punycode": is_punycode,
        "has_non_ascii_hostname": has_non_ascii,
        "has_userinfo": int(bool(parts["has_userinfo"])),
        "has_nonstandard_port": port_value,
        "suspicious_host_term_count": host_suspicious,
        "brand_token_in_registered_label": brand_root,
        "brand_token_in_subdomain": brand_subdomain,
        "brand_mismatch_in_registered_label": brand_mismatch,
        "repeated_hostname_separators": int(bool(re.search(r"[-_]{2,}", hostname_ascii))),
    }


def domain_character_text(url: str) -> str:
    """Text passed to the hostname character n-gram classifier."""
    parts = get_url_parts(url)
    return " ".join(filter(None, [
        str(parts["registered_domain"]),
        str(parts["hostname_ascii"]),
        str(parts["hostname"]).lower(),
    ]))


def path_character_text(url: str) -> str:
    """Return path, query, and fragment text for URL-level character n-grams."""
    parts = get_url_parts(url)
    path = str(parts["path"]).lower()
    query = str(parts["query"]).lower()
    fragment = str(parts["fragment"]).lower()
    # Mark boundaries so the vectorizer can learn path and query patterns separately.
    return f"path:{path} query:{query} fragment:{fragment}"


def get_group_domain(url: str) -> str:
    """Registered domain used to keep related hostnames in one evaluation split."""
    parts = get_url_parts(url)
    return str(parts["registered_domain"] or parts["hostname_ascii"] or url)


def known_major_domain(url: str) -> str | None:
    """Recognize an exact configured major hostname, including its subpages.

    This is a weak context signal only. The caller must not treat it as a verdict
    that all content hosted on the domain is safe.
    """
    try:
        parsed = urlsplit(str(url or "").strip())
        hostname = (parsed.hostname or "").lower().rstrip(".")
        port = parsed.port
    except ValueError:
        return None
    if parsed.scheme.lower() not in {"http", "https"} or not hostname:
        return None
    if parsed.username is not None or parsed.password is not None:
        return None
    expected_port = 443 if parsed.scheme.lower() == "https" else 80
    if port not in (None, expected_port):
        return None
    canonical_host = hostname[4:] if hostname.startswith("www.") else hostname
    return canonical_host if canonical_host in KNOWN_MAJOR_HOME_DOMAINS else None


def recognized_major_homepage(url: str) -> str | None:
    """Recognize a narrow set of exact HTTPS homepages, not their subpages."""
    try:
        parsed = urlsplit(str(url or "").strip())
        hostname = (parsed.hostname or "").lower().rstrip(".")
        port = parsed.port
    except ValueError:
        return None
    if parsed.scheme.lower() != "https" or not hostname:
        return None
    if parsed.username is not None or parsed.password is not None:
        return None
    if parsed.path not in ("", "/") or parsed.query or parsed.fragment:
        return None
    if port not in (None, 443):
        return None
    canonical_host = hostname[4:] if hostname.startswith("www.") else hostname
    return canonical_host if canonical_host in KNOWN_MAJOR_HOME_DOMAINS else None


def explain_domain(url: str) -> dict[str, object]:
    """Return user-facing domain details and observable structural indicators."""
    parts = get_url_parts(url)
    features = extract_features(url)
    indicators: list[str] = []
    if features["has_ip_address"]:
        indicators.append("The hostname is an IP address rather than a domain name.")
    if features["has_punycode"] or features["has_non_ascii_hostname"]:
        indicators.append("The hostname uses internationalized or encoded characters. Check for lookalike letters.")
    if int(features["subdomain_count"]) >= 3:
        indicators.append("The hostname has several subdomain levels. This can be legitimate, but inspect the registered domain carefully.")
    if features["brand_token_in_subdomain"]:
        indicators.append("A recognizable brand term appears in a subdomain, not necessarily in the registered domain.")
    if features["brand_mismatch_in_registered_label"]:
        indicators.append("The registered domain includes a recognizable brand term alongside other text.")
    if int(features["hostname_hyphen_count"]) >= 2 or float(features["hostname_digit_ratio"]) >= 0.25:
        indicators.append("The hostname contains multiple hyphens or a relatively high proportion of digits.")
    if int(features["suspicious_host_term_count"]) > 0:
        indicators.append("The hostname contains wording commonly used in account or verification lures.")
    if not indicators:
        indicators.append("No obvious domain-structure flags were found. This does not verify ownership or safety.")

    return {
        "hostname": str(parts["hostname"]),
        "registered_domain": str(parts["registered_domain"]),
        "public_suffix": str(parts["public_suffix"]),
        "subdomain_count": int(parts["subdomain_count"]),
        "is_ip_address": bool(parts["is_ip_address"]),
        "indicators": indicators,
    }


def explain_url_structure(url: str) -> dict[str, object]:
    """Return path/query observations distinct from domain-name analysis."""
    features = extract_features(url)
    indicators: list[str] = []
    if int(features["url_length"]) > 120:
        indicators.append("The URL is unusually long.")
    if int(features["suspicious_path_term_count"]) > 0:
        indicators.append("The path or query contains account, login, verification, or similar wording.")
    if int(features["percent_encoded_count"]) >= 3:
        indicators.append("The URL uses multiple percent-encoded character sequences.")
    if int(features["has_userinfo"]) or int(features["url_at_signs"]) > 0:
        indicators.append("The URL contains user-information syntax or an at sign, which can obscure the destination.")
    if int(features["has_nonstandard_port"]):
        indicators.append("The URL specifies a nonstandard port.")
    if int(features["suspicious_file_extension"]):
        indicators.append("The path ends with a file extension often associated with executable downloads.")
    if int(features["double_file_extension"]):
        indicators.append("The path has a double extension that can be used to disguise a file type.")
    if not indicators:
        indicators.append("No obvious path or query flags were found. This does not verify the page content.")
    return {
        "path_depth": int(features["path_depth"]),
        "query_parameter_count": int(features["query_parameter_count"]),
        "indicators": indicators,
    }


def validate_url(url: str) -> str | None:
    """Return a friendly validation error, or None if URL syntax looks acceptable."""
    if not isinstance(url, str) or not url.strip():
        return "Enter a URL to analyze."
    value = url.strip()
    if len(value) > 2048:
        return "This URL is too long. Please enter a URL under 2,048 characters."
    if any(character.isspace() for character in value):
        return "The URL contains spaces. Remove them or encode them before trying again."
    try:
        parsed = urlsplit(value)
        hostname = parsed.hostname
        _ = parsed.port
    except ValueError:
        return "This URL format is invalid. Check its brackets, hostname, or port."
    if parsed.scheme.lower() not in {"http", "https"}:
        return "Include http:// or https:// at the beginning of the URL."
    if not parsed.netloc or not hostname:
        return "Enter a complete URL with a hostname, such as https://example.com."
    if hostname.startswith(".") or hostname.endswith("."):
        return "Check the hostname and try again."
    return None
