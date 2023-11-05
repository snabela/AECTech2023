import math

import plotly.graph_objects as go
import plotly.subplots as sp

from viktor.views import DataGroup, DataItem


def calculate_carbon_and_cost(params, building_structure, building_floor_elv_area):
    nodes = building_structure['nodes']
    beams = building_structure['beams']
    beam_length = []
    for beam in beams:
        x1, y1, z1 = nodes[beam[0]*3], nodes[beam[0]*3 + 1], nodes[beam[0]*3 + 2]
        x2, y2, z2 = nodes[beam[1]*3], nodes[beam[1]*3 + 1], nodes[beam[1]*3 + 2]
        beam_length.append(math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2))

    total_beam_length = sum(beam_length)
    embodied_carbon_beams = total_beam_length * params.carbon_and_cost.carbon_per_beam_length / 1000 # Convert to tonnes
    cost_beams = total_beam_length * params.carbon_and_cost.cost_per_beam_length / 1000

    total_floor_area = sum([floor['area'] for floor in building_floor_elv_area])
    embodied_carbon_floors = total_floor_area * params.carbon_and_cost.carbon_per_floor_area / 1000 # Convert to tonnes
    cost_floors = total_floor_area * params.carbon_and_cost.cost_per_floor_area / 1000

    total_carbon = embodied_carbon_floors + embodied_carbon_beams
    total_cost = cost_floors + cost_beams

    data = DataGroup(
        DataItem('Total Embodied Carbon', total_carbon, number_of_decimals=0, suffix='tonnes C02', subgroup=DataGroup(
            DataItem('Embodied Carbon Floors', embodied_carbon_floors, number_of_decimals=0, suffix='tonnes C02'),
            DataItem('Embodied Carbon Beams', embodied_carbon_beams, number_of_decimals=0, suffix='tonnes C02')
        )),
        DataItem('Total Cost', total_cost, number_of_decimals=0, prefix='$', suffix='K', subgroup=DataGroup(
            DataItem('Cost Floors', cost_floors, number_of_decimals=0, prefix='$', suffix='K'),
            DataItem('Cost Beams', cost_beams, number_of_decimals=0, prefix='$', suffix='K')
        )),
        DataItem('Total Floor Area', total_floor_area, number_of_decimals=0, suffix='m2'),
        DataItem('Total Beam Length', total_beam_length, number_of_decimals=0, suffix='m'),
    )

    # Create a subplot with two pie charts
    fig = sp.make_subplots(rows=2, cols=1, subplot_titles=['Carbon', 'Cost'], specs=[[{"type": "pie"}], [{"type": "pie"}]])
    fig.add_trace(go.Pie(labels=['Floors', 'Beams'], values=[embodied_carbon_floors, embodied_carbon_beams]), row=1, col=1)
    fig.add_trace(go.Pie(labels=['Floors', 'Beams'], values=[cost_floors, cost_beams]), row=2, col=1)

    return fig, data, total_cost, total_carbon
