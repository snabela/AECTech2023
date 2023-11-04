import requests
from pyproj import Transformer

WGS84 = "EPSG:4326"  # World Geodetic System 1984 (latitude, longitude)
WEB_MERCATOR = "EPSG:3857"  # Pseudo Web Mercator (meters)

def get_wind_speed(latitude, longitude, server_url):
    """
    Fetch wind speed for given latitude and longitude from the provided server URL.
    
    Parameters:
    - latitude (float): Latitude of the location.
    - longitude (float): Longitude of the location.
    - server_url (str): URL of the wind speed service.
    
    Returns:
    - dict: Dictionary of wind speed values for different return periods.
    """
    
    # Wind return periods (years)
    return_periods = [10, 25, 50, 100, 300, 700, 1700, 3000]
    
    # Initialize transformer for coordinate transformation
    transformer = Transformer.from_crs(WGS84, WEB_MERCATOR)
    
    # Convert latitude and longitude to Web Mercator projection
    x_coordinate, y_coordinate = transformer.transform(latitude, longitude)
    
    params = {
        "geometry": "{},{}".format(x_coordinate, y_coordinate),
        "geometryType": "esriGeometryPoint",
        "returnGeometry": "false",
        "pixelSize": "1000,1000",
        "f": "json",
    }

    wind_speeds = {}

    for period in return_periods:
        service_name = "ASCE/wind2016_{}".format(period)
        identify_url = "{}/arcgis/rest/services/{}/ImageServer/identify".format(server_url, service_name)

        response = requests.get(identify_url, params=params)

        if response.status_code == 200:
            data = response.json()
            if "value" in data:
                wind_speeds[period] = data["value"]
            else:
                raise ValueError("No wind speed value found in service response for return period: {}".format(period))
        else:
            raise ConnectionError("Failed to connect to service with status code: {}".format(response.status_code))
    
    return wind_speeds
