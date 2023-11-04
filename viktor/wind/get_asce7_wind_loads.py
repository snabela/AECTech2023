"""
get_asce7_wind_loads.py takes a given building geometry and location to determine the wind load on the building

Inputs:
latitude
longitude
risk category
list of 2d floor elements

Outputs:
base shear x
base shear y
story forces x
story forces y
"""
import requests
from pyproj import Transformer

WGS84 = "EPSG:4326"  # World Geodetic System 1984 (latitude, longitude)
WEB_MERCATOR = "EPSG:3857"  # Pseudo Web Mercator (meters)


def get_wind_forces(latitude, longitude, risk_category, floors):
    """
    Get the base shear data for a building given information about it's location, risk category and geometry

    Parameters:
    - latitude (float): The latitude the building is located at
    - longitude (float): The lognitude the building is located at
    - risk_category (int): The risk category of the building (1, 2, 3, or 4)
    - floors (list[list[list[float]]]): The list of floors in the building

    Returns:
    - tuple: containing the following
        base_x float: Base shear in the X direction
        base_y float: Base shear in the Y direction        
        story_forces_x dict[float]: dict of story forces in X direction, key = height (z) and val = story force
        story_forces_y dict[float]: dict of story forces in Y direction, key = height (z) and val = story force
    """
    h = 0
    story_forces_x = {}
    story_forces_y = {}
    base_x = 0
    base_y = 0
    V = get_wind_speed_for_risk(latitude, longitude, risk_category)
    Kzt = 1 #Kzt can be adjusted for local topography, future implementation
    Kd = 0.85
    Ke = 1 #Don't take advantage of elevation factor, future implementation
    for floor in floors[1:]:
        z = floor[0][2] #Z coordinate of first node in floor area
        Kz = get_Kz(z)
        qz = 0.00256*Kz*Kzt*Kd*Ke*V*V #Wind pressure
        width_x, width_y = get_widths(floor)
        h = z - h
        area_x = width_x * h
        area_y = width_y * h
        force_x = qz*area_x/1000
        force_y = qz*area_y/1000
        story_forces_x[z] = force_x
        story_forces_y[z] = force_y
        base_x += force_x
        base_y += force_y
    return base_x, base_y, story_forces_x, story_forces_y
        

def get_widths(floor):
    """
    Given the list of floor nodes, return the maximum width in the x and y projections

    Parameters:
    - floor list[list[float]]: List of nodes that make up floor perimeter that are x, y and z coordinates

    Output:
    - tuple: containing the following
        width_x float: Width of the X projection of the floor
        width_y float: Width of the Y projection of the floor
    """
    x_min = floor[0][0]
    x_max = floor[0][0]
    y_min = floor[0][1]
    y_max = floor[0][1]
    for node in floor:
        if node[0] < x_min:
            x_min = node[0]
        elif node[0] > x_max:
            x_max = node[0]
        if node[1] < y_min:
            y_min = node[0]
        elif node[1] > y_max:
            y_max = node[1]
    width_x = x_max - x_min
    width_y = y_max - y_min
    return width_x, width_y


def get_Kz(z):
    """
    Get the Kz factor for a given floor elevation.

    Parameters:
    - z (float): Elevation of the floor

    Returns:
    - float: The Kz factor
    """
    a = 7 #This could be a variable in the future depending on exposure category
    zg = 1200 #This could be a variable in the future depending on exposure category
    if z < 15:
        return 2.01*(15/zg)**(2/a)
    else:
        return 2.01*(z/zg)**(2/a)
    

def get_wind_speed_for_risk(latitude, longitude, risk_category):
    """
    Get the ultimate wind speed based on the latitude, longitude and the risk category

    Parameters:
    - latitude (float): Latitude of the location.
    - longitude (float): Longitude of the location.
    - risk_category (int): The risk category of the building (1, 2, 3, or 4)

    Returns:
    - float: Design wind speed
    """
    wind_speed_dict = get_wind_speed(latitude, longitude)
    if risk_category == 1:
        return_period = 300
    elif risk_category == 2:
        return_period = 700
    elif risk_category == 3:
        return_period = 1700
    else:
        return_period = 3000
    return wind_speed_dict[return_period]


def get_wind_speed(latitude, longitude, server_url='https://gis.asce.org'):
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


def main(latitude, longitude, risk_category, floors):
    base_x, base_y, story_forces_x, story_forces_y = get_wind_forces(latitude, longitude, risk_category, floors)
    return 0

