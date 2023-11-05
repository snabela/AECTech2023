import os
import json
from pathlib import Path
import plotly.express as px

from viktor import ViktorController
from viktor.core import Storage, File
from viktor.geometry import GeoPoint

from goog_map import create_html
from viktor.parametrization import ViktorParametrization, Page, GeoPointField, OptionField, NumberField, BooleanField, Tab, \
    IntegerField, ActionButton, LineBreak, FileField, DownloadButton
from viktor.result import DownloadResult
from viktor.views import MapView, MapResult, MapPoint, GeometryView, GeometryResult, WebView, WebResult, \
    PlotlyAndDataResult, PlotlyAndDataView, PlotlyView, PlotlyResult, DataView, DataResult
from viktor.external.generic import GenericAnalysis

from optimization.run_optimization import run_optimization
from shapediver.ShapeDiverComputation import ShapeDiverComputation
from structural import evol_algo, calculate_embodied_carbon
from structural.analysis import base_analysis
from carbon_and_cost.calculate_carbon_and_cost import calculate_carbon_and_cost


def param_site_class_visible(params, **kwargs):
    if params.structural.code and params.structural.code.lower().startswith('asce7'):
        return True
    else:
        return False


class Parametrization(ViktorParametrization):
    location = Page('Location', views='get_map_view')
    location.center = GeoPointField('Building location', default=GeoPoint(40.7182, -74.0162))

    geometry = Page('Geometry', views='get_geometry_view')

    google = Page('Google 3D', views='get_web_view')

    structural = Page('Structural Basic', views = "structural_base_analysis")
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

    optimization = Page('Profile Optimization', views='profile_optimization')
    optimization.story_forces = IntegerField('Story Forces', min=0, default=100)
    optimization.minimum_wall_thickness = IntegerField('Minimum Wall Thickness (ft)', min=1, max=3, default=1)
    optimization.maximum_wall_thickness = IntegerField('Maximum Wall Thickness (ft)', min=1, max=3, default=2)
    optimization.minimum_wall_length = IntegerField('Minimum Wall Length (ft)', min=10, max=30, default=20)
    optimization.maximum_wall_length = IntegerField('Maximum Wall Length (ft)', min=15, max=40, default=30)
    #optimization.button = ActionButton('Perform Preliminary Optimization', method='prelim_optimization')



    #optimization.button2 = ActionButton('Send Optimized Solution to Analysis Model', method='send_to_analysis')

    detailedanalysis = Page('Detailed Analysis')
    detailedanalysis.button = ActionButton('Run etabs', method='run_etabs')

    carbon_and_cost = Page('Carbon & Cost', views='get_carbon_and_cost')
    carbon_and_cost.carbon_per_floor_area = NumberField('Carbon per Floor Area', suffix='CO2/m2', flex=50)
    carbon_and_cost.cost_per_floor_area = NumberField('Cost per Floor Area', suffix='$/m2', flex=50)
    carbon_and_cost.nl = LineBreak()
    carbon_and_cost.carbon_per_beam_length = NumberField('Carbon per Beam Length', suffix='CO2/m', flex=50)
    carbon_and_cost.cost_per_beam_length = NumberField('Cost per Beam Length', suffix='$/m', flex=50)

    global_optimization = Page('Global Optimization', views='get_optimization')
    global_optimization.min_base_radius = NumberField('Min Base Radius', default=60)
    global_optimization.max_base_radius = NumberField('Max Base Radius', default=200)
    global_optimization.step_base_radius = NumberField('Step Base Radius', default=10)
    global_optimization.min_peak_radius = NumberField('Min Peak Radius', default=60)
    global_optimization.max_peak_radius = NumberField('Max Peak Radius', default=100)
    global_optimization.step_peak_radius = NumberField('Step Peak Radius', default=10)
    global_optimization.min_no_floors = NumberField('Min No Floors', default=10)
    global_optimization.max_no_floors = NumberField('Max No Floors', default=50)
    global_optimization.step_no_floors = NumberField('Step No Floors', default=5)
    global_optimization.min_floor_to_floor = NumberField('Min Floor to Floor', default=8)
    global_optimization.max_floor_to_floor = NumberField('Max Floor to Floor', default=15)
    global_optimization.step_floor_to_floor = NumberField('Step Floor to Floor', default=1)
    global_optimization.run_async = BooleanField('Run Asynchronously')
    global_optimization.number_of_workers = NumberField('Number of parallel workers', default=4)


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

    @GeometryView('Geometry view', duration_guess=10, up_axis='Y', update_label='Run ShapeDiver')
    def get_geometry_view(self, params, **kwargs):
        parameters = params.ShapeDiverParams
        glTF_file = ShapeDiverComputation(parameters)
        return GeometryResult(geometry=glTF_file)

    @WebView('3D Tiles Map', duration_guess=1)
    def get_web_view(self, params, **kwargs):
        secret = os.getenv("API_KEY")
        lat = params.location.center.lat
        lon = params.location.center.lon

        # generate html content and create the WebResult
        html_content = create_html.create_html(lon, lat, secret)
        return WebResult(html=html_content)

    
 
    @DataView("OUTPUT", duration_guess=1)
    def profile_optimization(self, params, **kwargs):
        ## TODO remove test_story_forces
        parameters = params.optimization
        #building_forces = Storage().get('building_forces', scope='entity')
        test_story_forces = {0: 0, 10: parameters.story_forces, 20: parameters.story_forces, 30: parameters.story_forces, 40: parameters.story_forces}
        best_result, data = evol_algo.evolutionary_optimizer(test_story_forces, 
                                                parameters.minimum_wall_thickness, 
                                                parameters.maximum_wall_thickness, 
                                                parameters.minimum_wall_length, 
                                                parameters.maximum_wall_length)
        print(best_result)

        return DataResult(data)
        #optimized_corewall = Storage().set('OPTIMIZED_COREWALL', data=data, scope='entity')


    @PlotlyAndDataView("OUTPUT", duration_guess=5)
    def structural_base_analysis(self, params, **kwargs):
        fig, data = base_analysis(params)
        Storage().set('BUILDING_FORCES', data=data, scope='entity')
        return PlotlyAndDataResult(fig.to_json(), data)
    
    def send_to_analysis(self, params, **kwargs):
        ## TODO pass wall_sections to structural analysis
        pass

    @staticmethod
    def download_building_structure():
        file_content = Storage().get('BUILDING_STRUCTURE', scope='entity')
        return DownloadResult(file_content=file_content, file_name='building_structure.json')

    @staticmethod
    def download_building_floor_edge():
        file_content = Storage().get('BUILDING_FLOOR_EDGE', scope='entity')
        return DownloadResult(file_content=file_content, file_name='building_floor_edge.json')

    @staticmethod
    def download_building_floor_elv_area():
        file_content = Storage().get('BUILDING_FLOOR_ELV_AREA', scope='entity')
        return DownloadResult(file_content=file_content, file_name='building_floor_elv_area.json')

    @PlotlyView("Result", duration_guess=10, update_label='RUN OPTIMIZATION')
    def get_optimization(self, params, **kwargs):
        dimensions = ['Base Radius', 'Peak Radius', 'No Floors', 'Floor to Floor', 'Cost', 'Embodied Carbon']
        df = run_optimization(params, dimensions)
        fig = px.parallel_coordinates(df, color="Embodied Carbon",
                                      dimensions=dimensions,
                                      color_continuous_scale=px.colors.diverging.Tealrose,
                                      color_continuous_midpoint=2)
        return PlotlyResult(fig.to_json())

    @PlotlyAndDataView("Result", duration_guess=1)
    def get_carbon_and_cost(self, params, **kwargs):
        building_structure = json.loads(Storage().get('BUILDING_STRUCTURE', scope='entity').getvalue())
        building_floor_elv_area = json.loads(Storage().get('BUILDING_FLOOR_ELV_AREA', scope='entity').getvalue())

        fig, data, total_cost, total_carbon = calculate_carbon_and_cost(params, building_structure, building_floor_elv_area)
        return PlotlyAndDataResult(fig.to_json(), data)

    def run_etabs(self, params, **kwargs):
        file_content1 = Storage().get('BUILDING_STRUCTURE', scope='entity')
        file_content2 = Storage().get('BUILDING_STRUCTURE', scope='entity')

        files = [('building_structure.json', file_content1)]

        # Run the analysis and obtain the output file
        generic_analysis = GenericAnalysis(files=files, executable_key="run_etabs", output_filenames=["output.json"])
        generic_analysis.execute(timeout=6000)
        output_file = generic_analysis.get_output_file("output.json")
        print(output_file)

        # Setting data on a key
        Storage().set('results_etabs', data=File.from_data(output_file), scope='entity')
