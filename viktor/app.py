from pathlib import Path

from viktor import ViktorController, File, UserMessage
from viktor.geometry import GeoPoint
from viktor.parametrization import ViktorParametrization, Page, GeoPointField, Tab, OptionField, NumberField, BooleanField
from viktor.views import MapView, MapResult, MapPoint, GeometryView, GeometryResult, WebView, WebResult
from ShapeDiverTinySdkViktorUtils import ShapeDiverTinySessionSdkMemoized
import os

# ShapeDiver ticket and modelViewUrl
ticket = os.getenv("SD_TICKET")
if ticket is None or len(ticket) == 0:
    ticket = "a2dea6109cbcbe3b34906036c1c6bce1763adac8b1e25066af1ab69f5d715bfca562e9559d9f8e28f78756a545e3db3e1e29ea646423be87583ba0cd159b4806f8c26b48d12943be774af5cfd3d1eb5da4dbd19f163e7562cc17d823dcac2375e1446124ba732a36ca93094a1cacd4254ca2adfa222d5418-1c02a1b80a0b39bc36f136303faee4f2"
modelViewUrl = os.getenv("SD_MODEL_VIEW_URL")
if modelViewUrl is None or len(modelViewUrl) == 0:
    modelViewUrl = "https://nsc005.us-east-1.shapediver.com"

class Parametrization(ViktorParametrization):
    location = Page('Location', views='get_map_view')
    location.center = GeoPointField('Building location', default=GeoPoint(40.7182, -74.0162))

    geometry = Page('Geometry', views='get_geometry_view')
    geometry.param0 = NumberField('Base Radius', name='ShapeDiverParams.ff31e6cb-2c58-4d73-b6b1-10e63ba346bb', default=83, min=60, max=200, num_decimals=0, step=1.0, variant='slider')
    geometry.param1 = NumberField('Peak Radius', name='ShapeDiverParams.5b127d95-8792-4225-ad73-6d958e9fa6ce', default=60, min=60, max=100, num_decimals=0, step=1.0, variant='slider')
    geometry.param2 = NumberField('No Floors', name='ShapeDiverParams.f86e2cec-4b10-44ca-b42c-e7615be7e784', default=48, min=10, max=50, num_decimals=0, step=1, variant='slider')
    geometry.param3 = NumberField('Floor to Floor', name='ShapeDiverParams.1125c8f7-8ba9-4b4c-8d17-4a5f2afcea01', default=12, min=8, max=15, num_decimals=0, step=1.0, variant='slider')
    geometry.param4 = NumberField('Grid Spacing', name='ShapeDiverParams.6488bc66-2a0a-4c32-bfaa-e5e26a79ab49', default=18, min=15, max=25, num_decimals=0, step=1.0, variant='slider')
    geometry.param5 = BooleanField('Faces', name='ShapeDiverParams.f4ed86ed-aa01-4ef8-a4a1-d52912fca945', default=True)
    geometry.param6 = BooleanField('Structure', name='ShapeDiverParams.c3d98212-8694-4b6b-9d9a-9fe4fb800670', default=False)
    geometry.param7 = BooleanField('Floor', name='ShapeDiverParams.b04900a4-2d8f-499d-94d7-d1da11d592b0', default=False)

    google = Page('Google 3D', views='get_web_view')

    structural = Page('Structural')
    structural.wind = Tab('Wind')
    structural.wind.code = OptionField('Code', options=['ASCE41', 'ACI'])
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

    @GeometryView('Geometry view', duration_guess=10, up_axis='Y')
    def get_geometry_view(self, params, **kwargs):
        
        # Debug output
        # UserMessage.info(str(params))

        # Get parameter values from section "ShapeDiverParams"
        parameters = params.ShapeDiverParams

        # Initialize a session with the model (memoized)
        shapeDiverSessionSdk = ShapeDiverTinySessionSdkMemoized(ticket, modelViewUrl)

        # compute outputs of ShapeDiver model, get resulting glTF 2 assets
        contentItemsGltf2 = shapeDiverSessionSdk.output(paramDict = parameters).outputContentItemsGltf2()
        
        if len(contentItemsGltf2) < 1:
            raise UserError('Computation did not result in at least one glTF 2.0 asset.')
        
        if len(contentItemsGltf2) > 1: 
            UserMessage.warning(f'Computation resulted in {contentItemsGltf2.count} glTF 2.0 assets, only displaying the first one.')

        glTF_file = File.from_url(contentItemsGltf2[0]['href'])

        return GeometryResult(geometry=glTF_file)


    @WebView('3D Map page-Wen', duration_guess=1)
    def get_web_view(self, params, **kwargs):
        html_path = Path(__file__).parent / 'map_3d.html'
        return WebResult.from_path(html_path)