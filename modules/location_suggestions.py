import requests
from .utils import get_env_var

def get_location_suggestions(query):
    if not query or len(query) < 3:
        return []
        
    api_key = get_env_var("RAPIDAPI_KEY")
    if not api_key:
        # Fallback to returning just the query if no API key
        return [query]
        
    url = "https://wft-geo-db.p.rapidapi.com/v1/geo/cities"
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "wft-geo-db.p.rapidapi.com"
    }
    params = {
        "namePrefix": query,
        "limit": 5,
        "sort": "-population"
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        suggestions = []
        for city in data.get("data", []):
            name = city.get("city")
            country = city.get("country")
            suggestions.append(f"{name}, {country}")
        return suggestions
    except Exception as e:
        print(f"Error fetching location suggestions: {e}")
        return [query]
