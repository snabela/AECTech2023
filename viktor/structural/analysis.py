import plotly.graph_objects as go
import json
from viktor.core import Storage
from viktor.views import DataGroup, DataItem

from seismic import get_asce7_seismic_loads as seismic
from wind import get_asce7_wind_loads as wind
from structural import lateral_loads_plot

def base_analysis(params):
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
    sds = -1
    base_shear = -1
    seismic_shear_story_plot = None
    seismic_shear_elevation_plot = None
    wind_shear_story_plot = None
    wind_shear_elevation_plot = None

    if params.structural.file_seismic:
        # data structure: area_height = [[F,1000,40],[F,1200,10]]
        area_height = []
        for line in params.structural.file_seismic.file.open():
            line = line.strip()
            area_height_data = line.split(',')
            if len(area_height_data) > 1:
                area_height.append([int(area_height_data[2]), int(area_height_data[1])])

        if params.structural.tdl and params.structural.tll and params.structural.r_value:
            print(area_height)
            story_seismic_loads_dict, seismic_shear_story_plot, seismic_shear_elevation_plot, seismic_data,base_shear = seismic.get_seismic_force(
                area_height, tdl, tll, r, lat, lon, code, risk_cat, site_class)
            sds = seismic_data['sds']
            # sd1 = seismic_data['sd1']
    else:
        area_height = []
        # datastructure [{}]
        file_content = Storage().get('BUILDING_STRUCTURE', scope='entity')
        building_structure = json.loads(file_content.getvalue())
        print(building_structure)
        for line in Storage().get('BUILDING_FLOOR_ELV_AREA', scope='entity').open():
            print()
            line = line.strip()
            area_height_data = line.split(',')
            if len(area_height_data) > 1:
                area_height.append([int(area_height_data[2]), int(area_height_data[1])])

        if params.structural.tdl and params.structural.tll and params.structural.r_value:
            print(area_height)
            story_seismic_loads_dict, seismic_shear_story_plot, seismic_shear_elevation_plot, seismic_data = seismic.get_seismic_force(
                area_height, tdl, tll, r, lat, lon, code, risk_cat, site_class)
            sds = seismic_data['sds']
            sd1 = seismic_data['sd1']
            base_shear = seismic_data['base_shear']

    if params.structural.file_wind:
        json_file = params.structural.file_wind.file
        floors = wind.get_building_data(json_file)
        wind_speed = wind.get_wind_speed(lat, lon, risk_cat)
        base_x, base_y, story_forces_x, story_forces_y = wind.get_wind_forces(lat, lon, risk_cat, floors)
        wind_story_shear_plot_x = wind.get_story_shear_plot(story_forces_x)
        wind_story_shear_plot_y = wind.get_story_shear_plot(story_forces_y)
        # Use the same elevation plots from seismic
    else:
        wind_speed = -1
        base_x = -1
        base_y = -1

    data = DataGroup(
        group_a=DataItem('Location', 'Coordinate', subgroup=DataGroup(
            value_a=DataItem('Latitude', lat, suffix='°'),
            value_b=DataItem('Longitudinal', lon, suffix='°')
        )),
        group_b=DataItem('Wind', 'Demands', subgroup=DataGroup(
            value_a=DataItem('Wind Speed', wind_speed, suffix='psf',
                             explanation_label='this value is the wind speed value based on building code'),
            value_b=DataItem('Base Shear X', base_x, suffix='kip'),
            value_c=DataItem('Base Shear Y', base_y, suffix='kip-ft'),
            value_d=DataItem('Max Displacement', 5, suffix='in')
        )),
        group_c=DataItem('Seismic', 'Demands', subgroup=DataGroup(
            value_a=DataItem('Sds', sds, suffix='g'),
            value_b=DataItem('Base Shear', base_shear, suffix='kip'),
            value_c=DataItem('Overturning Moment', 5000, suffix='kip-ft'),
            value_d=DataItem('Max Displacement', 5, suffix='in')
        )))
    # fig = go.Figure(
    #     data=[go.Bar(x=[1, 2, 3], y=[1, 3, 2])],
    #     layout=go.Layout(title=go.layout.Title(text="A Figure Specified By A Graph Object"))
    # )
    fig = lateral_loads_plot.plot_lateral_loads(seismic_shear_story_plot,seismic_shear_elevation_plot,wind_shear_story_plot,wind_shear_elevation_plot)

    return fig, data
