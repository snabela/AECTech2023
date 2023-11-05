import pandas as pd
from viktor.core import Storage, progress_message

from carbon_and_cost.calculate_carbon_and_cost import calculate_carbon_and_cost
from shapediver.ShapeDiverComputation import ShapeDiverComputation, ShapeDiverComputationForOptimization

from typing import List, Tuple
import asyncio
from concurrent.futures import ThreadPoolExecutor


async def batch_run(models_input: List[dict], max_workers) -> Tuple[dict]:
    """
    :param models_input: [{"name": <name>, "x": <x>, "y": <y>}, ...]
    """
    loop = asyncio.get_running_loop()
    # define the maximum number of operations possible per batch
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        # The method `blocking_method` runs in parallel within this asynchronous method.
        results = await asyncio.gather(*[loop.run_in_executor(pool, recalculate_cost_and_carbon, *run.values()) for run in models_input])
    return results


def recalculate_cost_and_carbon(params, base_radius, peak_radius, no_floors, floor_to_floor, i, n):
    params['ShapeDiverParams']['ff31e6cb-2c58-4d73-b6b1-10e63ba346bb'] = base_radius
    params['ShapeDiverParams']['5b127d95-8792-4225-ad73-6d958e9fa6ce'] = peak_radius
    params['ShapeDiverParams']['f86e2cec-4b10-44ca-b42c-e7615be7e784'] = no_floors
    params['ShapeDiverParams']['1125c8f7-8ba9-4b4c-8d17-4a5f2afcea01'] = floor_to_floor

    # Run ShapeDiver based on the updated parameters
    building_structure, building_floor_elv_area = ShapeDiverComputationForOptimization(params.ShapeDiverParams)
    fig, data, cost, carbon = calculate_carbon_and_cost(params, building_structure, building_floor_elv_area)

    message = f"Iteration {i}/{n}. \n " \
              f"Input parameters: \n " \
              f"Base radius: {base_radius}, Peak radius: {peak_radius}, No Floors: {no_floors} Floor to Floor: {floor_to_floor} \n " \
              f"Output parameters: \n " \
              f"Carbon footprint: {round(carbon)} tonnes CO2 \n Costs: $ {round(cost)}K "

    progress_message(message=message, percentage=(i / n) * 100)
    return cost, carbon


def run_optimization(params, dimensions):
    df = pd.DataFrame(columns=dimensions)
    o = params.global_optimization
    list_cost = []
    list_embodied_carbon = []

    options = []
    i = 0
    for base_radius in range(o.min_base_radius, o.max_base_radius+1, o.step_base_radius):
        for peak_radius in range(o.min_peak_radius, o.max_peak_radius+1, o.step_peak_radius):
            for no_floors in range(o.min_no_floors, o.max_no_floors+1, o.step_no_floors):
                for floor_to_floor in range(o.min_floor_to_floor, o.max_floor_to_floor+1, o.step_floor_to_floor):
                    i += 1
                    options.append({'params': params,
                                    'base_radius': base_radius,
                                    'peak_radius': peak_radius,
                                    'no_floors': no_floors,
                                    'floor_to_floor': floor_to_floor,
                                    'i': i})

    n = len(options)
    for option in options:
        option['n'] = n
    i = 0

    if params.global_optimization.run_async:
        test_results = asyncio.run(batch_run(options, params.global_optimization.number_of_workers))
        for test_result in test_results:
            list_cost.append(test_result[0])
            list_embodied_carbon.append(test_result[1])
    else:
        for o in options:
            cost, carbon = recalculate_cost_and_carbon(params, o['base_radius'], o['peak_radius'], o['no_floors'], o['floor_to_floor'], o['i'], o['n'])
            list_cost.append(cost)
            list_embodied_carbon.append(carbon)

    df['Base Radius'] = [o['base_radius'] for o in options]
    df['Peak Radius'] = [o['peak_radius'] for o in options]
    df['No Floors'] = [o['no_floors'] for o in options]
    df['Floor to Floor'] = [o['floor_to_floor'] for o in options]
    df['Cost'] = list_cost
    df['Embodied Carbon'] = list_embodied_carbon
    return df
