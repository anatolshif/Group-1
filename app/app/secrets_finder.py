# app/secrets_finder.py
import os
import re
import math
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional

# Regex patterns for known providers/token formats
PATTERNS = {
    "aws_access_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "google_api_key": re.compile(r"\bAIza[0-9A-Za-z-_]{35}\b"),
    "stripe_key": re.compile(r"\b(sk_live|sk_test)_[0-9a-zA-Z]{24,}\b"),
    "slack_token": re.compile(r"\b(xox[pboa]-[0-9]{12}-[0-9]{12}-[0-9a-zA-Z]{24})\b"),
    "jwt": re.compile(r"\b([A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+)\b"),
    "uuid": re.compile(r"\b[0-9a-fA-F]{8}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{12}\b"),
    "hex_40": re.compile(r"\b[0-9a-fA-F]{40}\b"),
    "hex_64": re.compile(r"\b[0-9a-fA-F]{64}\b"),
    "generic_api_key": re.compile(r"\b[A-Za-z0-9\-_]{32,}\b"),  # generic long token
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
}

# Key-like XML attribute/element name heuristics
KEY_NAME_KEYWORDS = [
    "key", "api_key", "apikey", "secret", "token", "password", "passwd",
    "client_id", "clientid", "client_secret", "access_key", "auth"
]

def shannon_entropy(s: str) -> float:
    """Compute Shannon entropy of a string."""
    if not s:
        return 0.0
    freq = {}
    for ch in s:
        freq[ch] = freq.get(ch, 0) + 1
    entropy = 0.0
    length = len(s)
    for v in freq.values():
        p = v / length
        entropy -= p * math.log2(p)
    return entropy

def inspect_string_value(name: Optional[str], value: str, file_path: str, lineno: Optional[int]) -> List[Dict]:
    """
    Inspect a single string resource (name and value) and return a findings list.
    """
    findings = []
    if not value or not value.strip():
        return findings

    # Normalize
    value_str = value.strip()

    # 1) Check name contains key-like keywords
    if name:
        lname = name.lower()
        for kw in KEY_NAME_KEYWORDS:
            if kw in lname:
                findings.append({
                    "type": "suspicious_name",
                    "message": f"Resource name contains keyword '{kw}'",
                    "file": file_path,
                    "line": lineno,
                    "evidence": {"name": name, "value": value_str},
                    "confidence": 0.6
                })
                break

    # 2) Run provider-specific regexes first (strong indicators)
    for label, pattern in PATTERNS.items():
        for m in pattern.finditer(value_str):
            findings.append({
                "type": "hardcoded_secret",
                "message": f"Matched pattern {label}",
                "file": file_path,
                "line": lineno,
                "evidence": m.group(0),
                "confidence": 0.95 if label in ("aws_access_key","google_api_key","stripe_key","slack_token") else 0.9
            })

    # 3) Entropy heuristic for long alphanumeric strings
    # Only consider when length >= 20 to avoid false positives on short words
    alnum_only = re.sub(r'[^A-Za-z0-9]', '', value_str)
    if len(alnum_only) >= 20:
        ent = shannon_entropy(alnum_only)
        # threshold: 4.0 is fairly high, tune as needed
        if ent >= 4.0:
            findings.append({
                "type": "high_entropy_string",
                "message": f"High-entropy string (len={len(alnum_only)}, entropy={ent:.2f})",
                "file": file_path,
                "line": lineno,
                "evidence": value_str[:200],
                "confidence": 0.8
            })

    # 4) Generic long token pattern but lower confidence (exclude values that are URLs or sentences)
    if 32 <= len(alnum_only) <= 128 and re.search(r"[A-Za-z0-9]", value_str):
        # avoid URLs
        if not re.search(r"https?://", value_str, re.I):
            findings.append({
                "type": "possible_api_key",
                "message": "Long alphanumeric string (possible API key)",
                "file": file_path,
                "line": lineno,
                "evidence": value_str[:200],
                "confidence": 0.5
            })

    return findings

def find_secrets_in_strings(decompiled_dir: str) -> List[Dict]:
    """
    Scan resources/res/values*/strings*.xml files under the given decompiled_dir
    and return a list of findings.
    """
    findings = []
    # Common resource path root
    res_root = os.path.join(decompiled_dir, "resources", "res")
    if not os.path.isdir(res_root):
        # also consider direct 'res' path if jadx outputs to other layout
        res_root = os.path.join(decompiled_dir, "res")
    if not os.path.isdir(res_root):
        return [{"type": "error", "message": "res folder not found", "path": decompiled_dir}]

    # Walk values directories and find strings.xml or any strings*.xml
    for root, dirs, files in os.walk(res_root):
        # target only values* directories
        if os.path.basename(root).startswith("values"):
            for fname in files:
                if fname.startswith("strings") and fname.endswith(".xml"):
                    fpath = os.path.join(root, fname)
                    try:
                        tree = ET.parse(fpath)
                        root_el = tree.getroot()
                        # ElementTree doesn't preserve line numbers; lineno set to None
                        for el in root_el:
                            tag = el.tag.lower()
                            # typically <string name="...">value</string>
                            if tag.endswith("string"):
                                name = el.attrib.get("name")
                                value = (el.text or "")
                                findings.extend(inspect_string_value(name, value, fpath, None))
                            # handle string-array items
                            elif tag.endswith("string-array"):
                                name = el.attrib.get("name")
                                for item in el.findall("item"):
                                    val = (item.text or "")
                                    findings.extend(inspect_string_value(name, val, fpath, None))
                    except ET.ParseError as e:
                        findings. append({"type": "warning", "message":f"XML parse error: {e}", "file": fpath})
                    except Exception as e:
                        findings. append({"type": "error", "message":f"Failed to process {fpath}: {e}"})
    return findings
