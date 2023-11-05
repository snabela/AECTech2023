import pandas as pd


def calculate_cost(base_radius, peak_radius, no_floors, floor_to_floor):
    # TODO: make actual calculation
    cost = base_radius + peak_radius + no_floors + floor_to_floor
    return cost


def calculate_embodied_carbon(base_radius, peak_radius, no_floors, floor_to_floor):
    # TODO: make actual calculation
    embodied_carbon = base_radius*2 + peak_radius/3 + no_floors + floor_to_floor
    return embodied_carbon


def run_optimization(params, dimensions):
    df = pd.DataFrame(columns=dimensions)
    o = params.global_optimization
    list_base_radius = []
    list_peak_radius = []
    list_no_floors = []
    list_floor_to_floor = []
    list_cost = []
    list_embodied_carbon = []
    for base_radius in range(o.min_base_radius, o.max_base_radius, o.step_base_radius):
        for peak_radius in range(o.min_peak_radius, o.max_peak_radius, o.step_peak_radius):
            for no_floors in range(o.min_no_floors, o.max_no_floors, o.step_no_floors):
                for floor_to_floor in range(o.min_floor_to_floor, o.max_floor_to_floor, o.step_floor_to_floor):
                    list_base_radius.append(base_radius)
                    list_peak_radius.append(peak_radius)
                    list_no_floors.append(no_floors)
                    list_floor_to_floor.append(floor_to_floor)

                    cost = calculate_cost(base_radius, peak_radius, no_floors, floor_to_floor)
                    embodied_carbon = calculate_embodied_carbon(base_radius, peak_radius, no_floors, floor_to_floor)
                    list_cost.append(cost)
                    list_embodied_carbon.append(embodied_carbon)

    df['Base Radius'] = list_base_radius
    df['Peak Radius'] = list_peak_radius
    df['No Floors'] = list_no_floors
    df['Floor to Floor'] = list_floor_to_floor
    df['Cost'] = list_cost
    df['Embodied Carbon'] = list_embodied_carbon
    return df
