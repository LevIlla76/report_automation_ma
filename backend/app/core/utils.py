import re

def normalize_number(value):
    """
    Normalize string numbers for comparison.
    Handles '63.0G' vs '63G', removals of commas, units, etc.
    """
    if value is None:
        return ""
    if isinstance(value, (int, float)):
        return str(float(value)).rstrip('0').rstrip('.')
    
    # Remove commas and units (G, M, K, %)
    clean = re.sub(r'[^\d.]', '', str(value))
    try:
        return str(float(clean)).rstrip('0').rstrip('.')
    except ValueError:
        return str(value).strip()

def cells_match(val1, val2):
    """
    Check if two values match after normalization.
    """
    return normalize_number(val1) == normalize_number(val2)
