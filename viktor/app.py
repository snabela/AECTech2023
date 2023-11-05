from pathlib import Path

from viktor import ViktorController, File
from viktor.geometry import GeoPoint
from viktor.parametrization import ViktorParametrization, Page, GeoPointField, Tab, OptionField
from viktor.views import MapView, MapResult, MapPoint, GeometryView, GeometryResult, WebView, WebResult
#from goog_map import create_html
#import requests, os


class Parametrization(ViktorParametrization):
    location = Page('Location', views='get_map_view')
    location.center = GeoPointField('Building location', default=GeoPoint(40.7182, -74.0162))

    geometry = Page('Geometry', views='get_geometry_view')

    google = Page('Google 3D', views='get_web_view')

    structural = Page('Structural')
    structural.wind = Tab('Wind')
    structural.wind.code = OptionField('Code', options=['ASCE41', 'ACI'])

    optimization = Page('Optimization')


class Controller(ViktorController):
    label = 'Building'
    parametrization = Parametrization

    @MapView('Map', duration_guess=1)
    def get_map_view(self, params, **kwargs):
        lat = params.location.center.lat
        lon = params.location.center.lon

        # Visualize point on map
        center_marker = MapPoint.from_geo_point(params.location.center)
        features = [center_marker]
        return MapResult(features)

    @GeometryView('Geometry view', duration_guess=1)
    def get_geometry_view(self, params, **kwargs):
        # TODO integrate with ShapeDiver

        geometry = File.from_url(
            "https://github.com/KhronosGroup/glTF-Sample-Models/raw/master/2.0/CesiumMilkTruck/glTF-Binary"
            "/CesiumMilkTruck.glb")
        return GeometryResult(geometry)

    @WebView('3D Map page-Wen', duration_guess=1)
    def get_web_view(self, params, **kwargs):
        """
        # if you want to use a dynamic html file with variable lon and lat
        lat = params.location.center.lat
        lon = params.location.center.lon
        #  = Path(__file__).parent / 'goog_map/create_html.py'

        # generate html content and create the WebResult
        html_content = create_html.create_html(lon, lat)
        return WebResult(html=html_content)
        """

        # if you want to use a static html file with hardcoded lon and lat
        html_path = Path(__file__).parent / 'goog_map/map_3d.html'
        return WebResult.from_path(html_path)
