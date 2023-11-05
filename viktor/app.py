from pathlib import Path
import plotly.graph_objects as go
from seismic import  get_asce7_seismic_loads as seismic

from viktor import ViktorController, File
from viktor.geometry import GeoPoint
from viktor.parametrization import ViktorParametrization, Page, GeoPointField, Tab, OptionField, LineBreak, FileField,NumberField
from viktor.views import MapView, MapResult, MapPoint, GeometryView, GeometryResult
from viktor.views import DataGroup, DataItem, PlotlyAndDataResult, PlotlyAndDataView

def param_site_class_visible(params, **kwargs):
    if params.structural.code and params.structural.code.lower().startswith('asce7'):
        return True
    else:
        return False


class Parametrization(ViktorParametrization):
    location = Page('Location', views='get_map_view')
    location.center = GeoPointField('Building location', default=GeoPoint(40.7182, -74.0162))

    geometry = Page('Geometry', views='get_geometry_view')
    # TODO add necessary input parameters

    google = Page('Google 3D')
    # TODO add necessary input parameters

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
    