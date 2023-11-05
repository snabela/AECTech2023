def calculate_embodied_carbon_concrete(concrete_volume):
    '''
    Input: concrete_volume (ft^3)
    Output: embodied_carbon (kgCO2e)
    '''
    # Calculate Concrete Embodied Carbon
    # 600 kg CO2e/m3 based on CLF High Baseline

    embodied_carbon = concrete_volume / 35.3147 * 600 # kgCO2

    return embodied_carbon

def calculate_embodied_carbon_reinforcement(reinforcement_volume):
    '''
    Input: reinforcement_volume (ft^3)
    Output: embodied_carbon (kgCO2e)
    '''
    
    # Calculate Reinforcement Embodied Carbon
    # 2 kg CO2e/kg based on CLF High Baseline
    # rebar density = 490 lb/ft^3

    embodied_carbon = reinforcement_volume * 490  * 0.453 # kgCO2

    return embodied_carbon
