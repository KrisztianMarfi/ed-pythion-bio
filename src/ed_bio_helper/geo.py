from math import radians, degrees, sin, cos, sqrt, asin, atan2

_CARDINALS = ('N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW')


def haversine(lat1: float, lon1: float, lat2: float, lon2: float, radius: float) -> float:
    """Great-circle distance in meters between two lat/lon points on a sphere of given radius."""
    phi1, phi2 = radians(lat1), radians(lat2)
    dphi = phi2 - phi1
    dlambda = radians(lon2 - lon1)
    a = sin(dphi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(dlambda / 2) ** 2
    return 2 * radius * asin(sqrt(a))


def bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Initial great-circle bearing in degrees (0-359) from point 1 toward point 2."""
    phi1, phi2 = radians(lat1), radians(lat2)
    dlambda = radians(lon2 - lon1)
    y = sin(dlambda) * cos(phi2)
    x = cos(phi1) * sin(phi2) - sin(phi1) * cos(phi2) * cos(dlambda)
    return (degrees(atan2(y, x)) + 360) % 360


def cardinal(deg: float) -> str:
    """8-point compass label (N, NE, E, ...) for a bearing in degrees."""
    return _CARDINALS[round(deg / 45) % 8]
