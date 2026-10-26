import os
import uuid
import requests as http_requests

# Mapbox Search Box API (replaces slow osmnx — ~200ms vs 3-5s).
# Legacy geocoding v5 no longer returns POIs (e.g. "Navy Pier").
SEARCHBOX_URL = "https://api.mapbox.com/search/searchbox/v1"
CHICAGO_CENTER = '-87.6298,41.8781'
CHICAGO_BBOX = '-87.94,41.644,-87.524,42.023'

_geocode_cache = {}


def geocode_place(place_name, user_coords=None):
    """Convert a place name to [lat, lng].
    suggest+retrieve matches landmarks best; forward is the fallback (handles e.g. "the Loop")."""
    normalized = place_name.strip().lower()
    if normalized in _geocode_cache:
        return _geocode_cache[normalized]
    token = os.environ.get('MAPBOX_TOKEN', '')
    # Use user's location for proximity bias (avoids defaulting to the Loop)
    if user_coords and len(user_coords) == 2:
        proximity = f'{user_coords[1]},{user_coords[0]}'
    else:
        proximity = CHICAGO_CENTER
    params = {
        'access_token': token,
        'proximity': proximity,
        'bbox': CHICAGO_BBOX,
        'limit': 1,
    }
    session = str(uuid.uuid4())
    resp = http_requests.get(f"{SEARCHBOX_URL}/suggest", params={**params, 'q': place_name, 'session_token': session}, timeout=5)
    resp.raise_for_status()
    suggestions = resp.json().get('suggestions', [])
    features = []
    if suggestions:
        resp = http_requests.get(f"{SEARCHBOX_URL}/retrieve/{suggestions[0]['mapbox_id']}",
                                 params={'access_token': token, 'session_token': session}, timeout=5)
        resp.raise_for_status()
        features = resp.json().get('features', [])
    if not features:
        resp = http_requests.get(f"{SEARCHBOX_URL}/forward", params={**params, 'q': f"{place_name}, Chicago, Illinois"}, timeout=5)
        resp.raise_for_status()
        features = resp.json().get('features', [])
    if not features:
        raise ValueError(f"Could not find: {place_name}")
    lng, lat = features[0]['geometry']['coordinates']
    coords = [lat, lng]
    _geocode_cache[normalized] = coords
    return coords
