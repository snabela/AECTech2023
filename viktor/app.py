from pathlib import Path
import plotly.graph_objects as go

from viktor import ViktorController, File
from viktor.geometry import GeoPoint
from viktor.parametrization import ViktorParametrization, Page, GeoPointField, Tab, OptionField
from viktor.views import MapView, MapResult, MapPoint, GeometryView, GeometryResult
from viktor.views import DataGroup, DataItem, PlotlyAndDataResult, PlotlyAndDataView


class Parametrization(ViktorParametrization):
    location = Page('Location', views='get_map_view')
    location.center = GeoPointField('Building location', default=GeoPoint(40.7182, -74.0162))

    geometry = Page('Geometry', views='get_geometry_view')
    # TODO add necessary input parameters

    google = Page('Google 3D')
    # TODO add necessary input parameters

    structural = Page('Structural', views = "visualize_data")
    # structural.wind = Tab('Wind')
    structural.code = OptionField('Code Version', options=['ASCE7-22','ASCE7-16','ASCE41-17','ASCE41-13'])

    # TODO add necessary input parameters

    optimization = Page('Optimization')
    # TODO add necessary input parameters


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

        geometry = File.from_url("https://github.com/KhronosGroup/glTF-Sample-Models/raw/master/2.0/CesiumMilkTruck/glTF-Binary/CesiumMilkTruck.glb")
        return GeometryResult(geometry)

    @PlotlyAndDataView("OUTPUT", duration_guess=1)
    def visualize_data(self, params, **kwargs):

        fig = go.Figure(
            data=[go.Bar(x=[1, 2, 3], y=[1, 3, 2])],
            layout=go.Layout(title=go.layout.Title(text="A Figure Specified By A Graph Object"))
        )

        lat = params.location.center.lat + 3
        print(params.structural.code)
        data = DataGroup(
            group_a=DataItem('Location', 'Coordinate', subgroup=DataGroup(
                value_a=DataItem('Latitude',params.location.center.lat, suffix='°'),
                value_b=DataItem('Longitudinal', params.location.center.lon, suffix='°')
            )),
            group_b=DataItem('Wind', 'some result', subgroup=DataGroup(
                sub_group=DataItem('Result', 1, suffix='N')
            )),
            group_c=DataItem('Seismic', '', subgroup=DataGroup(
                sub_group=DataItem('Sub group', 6, prefix='€', subgroup=DataGroup(
                    value_a=DataItem('Value A', 5, prefix='€'),
                    value_b=DataItem('Value B', 4, prefix='€',
                                     explanation_label='this value is a result of multiplying Value A by 2')
                ))
            )))

        return PlotlyAndDataResult(fig.to_json(), data)
    