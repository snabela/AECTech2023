import json
import time

import pandas as pd
from viktor.core import Storage, progress_message

from carbon_and_cost.calculate_carbon_and_cost import calculate_carbon_and_cost
from shapediver.ShapeDiverComputation import ShapeDiverComputation


def recalculate_cost_and_carbon(params, base_radius, peak_radius, no_floors, floor_to_floor):
    params['ShapeDiverParams']['ff31e6cb-2c58-4d73-b6b1-10e63ba346bb'] = base_radius
    params['ShapeDiverParams']['5b127d95-8792-4225-ad73-6d958e9fa6ce'] = peak_radius
    params['ShapeDiverParams']['f86e2cec-4b10-44ca-b42c-e7615be7e784'] = no_floors
    params['ShapeDiverParams']['1125c8f7-8ba9-4b4c-8d17-4a5f2afcea01'] = floor_to_floor

    # Run ShapeDiver based on the updated parameters
    # ShapeDiverComputation(params.ShapeDiverParams)
    time.sleep(0.5)

    # Load the storage files and update the cost and carbon calculation
    building_structure = json.loads(Storage().get('BUILDING_STRUCTURE', scope='entity').getvalue())
    building_floor_elv_area = json.loads(Storage().get('BUILDING_FLOOR_ELV_AREA', scope='entity').getvalue())

    fig, data, cost, carbon = calculate_carbon_and_cost(params, building_structure, building_floor_elv_area)
    return cost, carbon


def run_optimization(params, dimensions):
    df = pd.DataFrame(columns=dimensions)
    o = params.global_optimization
    list_base_radius = []
    list_peak_radius = []
    list_no_floors = []
    list_floor_to_floor = []
    list_cost = []
    list_embodied_carbon = []

    n = 0
    for base_radius in range(o.min_base_radius, o.max_base_radius, o.step_base_radius):
        for peak_radius in range(o.min_peak_radius, o.max_peak_radius, o.step_peak_radius):
            for no_floors in range(o.min_no_floors, o.max_no_floors, o.step_no_floors):
                for floor_to_floor in range(o.min_floor_to_floor, o.max_floor_to_floor, o.step_floor_to_floor):
                    n += 1

    i = 0
    for base_radius in range(o.min_base_radius, o.max_base_radius, o.step_base_radius):
        for peak_radius in range(o.min_peak_radius, o.max_peak_radius, o.step_peak_radius):
            for no_floors in range(o.min_no_floors, o.max_no_floors, o.step_no_floors):
                for floor_to_floor in range(o.min_floor_to_floor, o.max_floor_to_floor, o.step_floor_to_floor):
                    i += 1
                    list_base_radius.append(base_radius)
                    list_peak_radius.append(peak_radius)
                    list_no_floors.append(no_floors)
                    list_floor_to_floor.append(floor_to_floor)

                    cost, carbon = recalculate_cost_and_carbon(params, base_radius, peak_radius, no_floors, floor_to_floor)

                    message = f"Iteration {i}/{n}. \n " \
                              f"Base radius: {base_radius} \n " \

                    progress_message(message=message, percentage=(i / n) * 100)

                    list_cost.append(cost)
                    list_embodied_carbon.append(carbon)

    df['Base Radius'] = list_base_radius
    df['Peak Radius'] = list_peak_radius
    df['No Floors'] = list_no_floors
    df['Floor to Floor'] = list_floor_to_floor
    df['Cost'] = list_cost
    df['Embodied Carbon'] = list_embodied_carbon
    return df
