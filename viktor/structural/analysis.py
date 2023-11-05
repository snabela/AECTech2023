import plotly.graph_objects as go

from viktor.core import Storage
from viktor.views import DataGroup, DataItem

from seismic import get_asce7_seismic_loads as seismic


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
    if params.structural.file_seismic:
        area_height = []
        # line in params.structural.file_seismic.file.open():
        for line in Storage().get('BUILDING_FLOOR_ELV_AREA', scope='entity').open():
            line = line.strip()
            area_height_data = line.split(',')
            if len(area_height_data) > 1:
                area_height.append([int(area_height_data[2]), int(area_height_data[1])])

        if params.structural.tdl and params.structural.tll and params.structural.r_value:
            print(area_height)
            story_seismic_loads_dict, seimsic_shear_story_plot, seismic_shear_elevation_plot, seismic_data = seismic.get_seismic_force(
                area_height, tdl, tll, r, lat, lon, code, risk_cat, site_class)
            sds = seismic_data['sds']
        else:
            sds = 0
    else:
        sds = 0

    data = DataGroup(
        group_a=DataItem('Location', 'Coordinate', subgroup=DataGroup(
            value_a=DataItem('Latitude', lat, suffix='°'),
            value_b=DataItem('Longitudinal', lon, suffix='°')
        )),
        group_b=DataItem('Wind', 'Demands', subgroup=DataGroup(
            value_a=DataItem('Wind Pressure', 1, suffix='psf',
                             explanation_label='this value is the wind pressure value based on building code'),
            value_b=DataItem('Base Shear', 5000, suffix='kip'),
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
    return fig, data
