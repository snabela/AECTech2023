from pathlib import Path
import plotly.express as px

from viktor import ViktorController, File
from viktor.geometry import GeoPoint
from viktor.parametrization import ViktorParametrization, Page, GeoPointField, Tab, OptionField, NumberField
from viktor.views import MapView, MapResult, MapPoint, GeometryView, GeometryResult, WebView, WebResult, PlotlyView, \
    PlotlyResult

from optimization.run_optimization import run_optimization


class Parametrization(ViktorParametrization):
    location = Page('Location', views='get_map_view')
    location.center = GeoPointField('Building location', default=GeoPoint(40.7182, -74.0162))

    geometry = Page('Geometry', views='get_geometry_view')
    # TODO add necessary input parameters

    google = Page('Google 3D', views='get_web_view')

    structural = Page('Structural')
    structural.wind = Tab('Wind')
    structural.wind.code = OptionField('Code', options=['ASCE41', 'ACI'])

    optimization = Page('Optimization', views='get_optimization')
    optimization.min_base_radius = NumberField('Min Base Radius', default=60)
    optimization.max_base_radius = NumberField('Max Base Radius', default=200)
    optimization.step_base_radius = NumberField('Step Base Radius', default=10)

    optimization.min_peak_radius = NumberField('Min Peak Radius', default=60)
    optimization.max_peak_radius = NumberField('Max Peak Radius', default=100)
    optimization.step_peak_radius = NumberField('Step Peak Radius', default=10)

    optimization.min_no_floors = NumberField('Min No Floors', default=10)
    optimization.max_no_floors = NumberField('Max No Floors', default=50)
    optimization.step_no_floors = NumberField('Step No Floors', default=5)

    optimization.min_floor_to_floor = NumberField('Min Floor to Floor', default=8)
    optimization.max_floor_to_floor = NumberField('Max Floor to Floor', default=15)
    optimization.step_floor_to_floor = NumberField('Step Floor to Floor', default=1)

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

        geometry = File.from_url(
            "https://github.com/KhronosGroup/glTF-Sample-Models/raw/master/2.0/CesiumMilkTruck/glTF-Binary/CesiumMilkTruck.glb")
        return GeometryResult(geometry)

    @WebView('3D Map page-Wen', duration_guess=1)
    def get_web_view(self, params, **kwargs):
        html_path = Path(__file__).parent / 'detailedmap_3d.html'
        return WebResult.from_path(html_path)

    @PlotlyView("Result", duration_guess=1)
    def get_optimization(self, params, **kwargs):
        dimensions = ['Base Radius', 'Peak Radius', 'No Floors', 'Floor to Floor', 'Cost', 'Embodied Carbon']
        df = run_optimization(params, dimensions)
        fig = px.parallel_coordinates(df, color="Embodied Carbon",
                                      dimensions=dimensions,
                                      color_continuous_scale=px.colors.diverging.Tealrose,
                                      color_continuous_midpoint=2)
        return PlotlyResult(fig.to_json())
