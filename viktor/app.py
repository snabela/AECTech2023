from pathlib import Path
import plotly.graph_objects as go
from seismic import  get_asce7_seismic_loads as seismic

from viktor import ViktorController, File, UserMessage
from viktor.geometry import GeoPoint
from viktor.parametrization import ViktorParametrization, Page, GeoPointField, Tab, OptionField, NumberField, BooleanField, IntegerField, ActionButton, LineBreak, FileField
from viktor.views import MapView, MapResult, MapPoint, GeometryView, GeometryResult, WebView, WebResult, DataView, DataResult, DataGroup, DataItem, PlotlyAndDataResult, PlotlyAndDataView
from ShapeDiverComputation import ShapeDiverComputation
from structural import evol_algo

def param_site_class_visible(params, **kwargs):
    if params.structural.code and params.structural.code.lower().startswith('asce7'):
        return True
    else:
        return False

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

    structural = Page('Structural Basic', views = "structural_base_analysis")
    # structural.wind = Tab('Wind')
    structural.code = OptionField('Code Version', options=['ASCE7-22','ASCE7-16','ASCE41-17','ASCE41-13'])
    structural.line_break1 = LineBreak()
    structural.site_class = OptionField('Site Class', options=['Default','A','B','BC','C','CD', 'D','DE','E'], flex = 30)
    structural.line_break2 = LineBreak()
    structural.risk_cat = OptionField('Risk', options=['I', 'II','III','IV'],visible=param_site_class_visible,flex = 30)
    structural.line_break3 = LineBreak()
    structural.file_seismic = FileField('Floor Area and Elevation', file_types=['.png', '.jpg', '.jpeg','.txt','.json'], max_size=5_000_000)
    structural.tdl = NumberField('Total DL',flex = 20)
    structural.tll = NumberField('Total LL',flex = 20)
    structural.r_value = NumberField('R Value', flex=20)
    structural.line_break4 = LineBreak()
    structural.file_wind = FileField('Wind load input', file_types=['.png', '.jpg', '.jpeg','.txt','.json'], max_size=5_000_000)

    optimization = Page('Optimization')
    optimization.story_forces = IntegerField('Story Forces', min=0, default=100)
    optimization.minimum_wall_thickness = IntegerField('Minimum Wall Thickness (ft)', min=1, max=3, default=1)
    optimization.maximum_wall_thickness = IntegerField('Maximum Wall Thickness (ft)', min=1, max=3, default=2)
    optimization.minimum_wall_length = IntegerField('Minimum Wall Length (ft)', min=10, max=30, default=20)
    optimization.maximum_wall_length = IntegerField('Maximum Wall Length (ft)', min=15, max=40, default=30)
    optimization.button = ActionButton('Perform Preliminary Optimization', method='prelim_optimization')
    optimization.button2 = ActionButton('Send Optimized Solution to Analysis Model', method='send_to_analysis')

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

        # run ShapeDiver computation
        glTF_file = ShapeDiverComputation(parameters)

        return GeometryResult(geometry=glTF_file)


    @WebView('3D Map page-Wen', duration_guess=1)
    def get_web_view(self, params, **kwargs):
        html_path = Path(__file__).parent / 'detailedmap_3d.html'
        return WebResult.from_path(html_path)
    
    def prelim_optimization(self, params, **kwargs):
        ## TODO remove test_story_forces
        parameters = params.optimization

        test_story_forces = {0: 0, 10: parameters.story_forces, 20: parameters.story_forces, 30: parameters.story_forces, 40: parameters.story_forces}
        wall_section = evol_algo.evolutionary_optimizer(test_story_forces, 
                                                        parameters.minimum_wall_thickness, 
                                                        parameters.maximum_wall_thickness, 
                                                        parameters.minimum_wall_length, 
                                                        parameters.maximum_wall_length)
        print(wall_section)
        return wall_section

    @PlotlyAndDataView("OUTPUT", duration_guess=5)
    def structural_base_analysis(self, params, **kwargs):
        lat = params.location.center.lat
        lon = params.location.center.lon
        tdl = params.structural.tdl
        tll = params.structural.tll
        r = params.structural.r_value
        code = params.structural.code
        risk_cat = params.structural.risk_cat
        site_class = params.structural.site_class

        # fetch data from usgs
        # seismic.fetch_usgs_data(params.location.center.lat,params.location.center.lon,params.structural.code,params.structural.risk_cat,params.structural.site_class)
        # with open(params.structural.file_seismic,'r') as file:
        #     for line in file:
        #         print(line.strip())
        if params.structural.file_seismic:
            area_height = []
            for line in params.structural.file_seismic.file.open():
                line = line.strip()
                area_height_data = line.split(',')
                if len(area_height_data)>1:
                    area_height.append([int(area_height_data[2]),int(area_height_data[1])])

            if params.structural.tdl and params.structural.tll and params.structural.r_value:
                print(area_height)
                story_seismic_loads_dict, seimsic_shear_story_plot, seismic_shear_elevation_plot, seismic_data = seismic.get_seismic_force(area_height,tdl,tll,r,lat,lon,code,risk_cat,site_class)
                sds = seismic_data['sds']
            else:
                sds = 0
        else:
            sds=0

        data = DataGroup(
            group_a=DataItem('Location', 'Coordinate', subgroup=DataGroup(
                value_a=DataItem('Latitude',lat, suffix='°'),
                value_b=DataItem('Longitudinal', lon, suffix='°')
            )),
            group_b=DataItem('Wind', 'Demands', subgroup=DataGroup(
                value_a=DataItem('Wind Pressure', 1, suffix='psf',explanation_label='this value is the wind pressure value based on building code'),
                value_b=DataItem('Base Shear',5000,suffix='kip'),
                value_c=DataItem('Overturning Moment', 5000, suffix='kip-ft'),
                value_d=DataItem('Max Displacement', 5, suffix='in')
            )),
            group_c=DataItem('Seismic', 'Demands', subgroup=DataGroup(
                value_a=DataItem('Sds', sds, suffix='g'),
                value_b=DataItem('Base Shear', 5000, suffix='kip'),
                value_c=DataItem('Overturning Moment', 5000, suffix='kip-ft'),
                value_d=DataItem('Max Displacement', 5, suffix='in')
            )))
        fig = go.Figure(
            data=[go.Bar(x=[1, 2, 3], y=[1, 3, 2])],
            layout=go.Layout(title=go.layout.Title(text="A Figure Specified By A Graph Object"))
        )

        return PlotlyAndDataResult(fig.to_json(), data)
    
    def send_to_analysis(self, params, **kwargs):
        ## TODO pass wall_sections to structural analysis
        pass
