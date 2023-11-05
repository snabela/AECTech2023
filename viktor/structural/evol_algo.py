def evolutionary_optimizer(story_force_dictionary, min_wall_thickness, max_wall_thickness, min_wall_length, max_wall_length):
    '''
    Input: story_force_dictionary - dictionary of story forces, with keys as story elevations and values as story forces
    Output: optimized_section_dictionary - dictionary of core section, with keys as story elevations and values as core dimensions [length, thickness, reinforcement_ratio]
    '''

    from structural import mdof_simple_model as mdof
    from structural import calculate_embodied_carbon
    import random
    from viktor.core import Storage
    from viktor.views import DataGroup, DataItem

    # Constants
    POPULATION_SIZE = 1000 # Number of individuals in the population
    MUTATION_RATE = 0.05 # Probability of mutation
    CROSSOVER_RATE = 0.9 # Probability of crossover
    GENERATIONS = 100 # Number of generations to run the algorithm
    LENGTH_MIN = min_wall_length  # Core Length min ft
    LENGTH_MAX = max_wall_length  # Core Length max ft
    THICKNESS_MIN = min_wall_thickness  # Core thickness min ft
    THICKNESS_MAX = max_wall_thickness  # Core thickness max ft
    REINFORCEMENT_RATIO_MIN = 0.0025 # Reinforcement ratio min
    REINFORCEMENT_RATIO_MAX = 0.02 # Reinforcement ratio max
    ELEVATIONS = list(story_force_dictionary.keys())
    CONCRETE_IMPACT_WEIGHT = 0.1 # Weight of concrete volume in the fitness function
    REINFORCEMENT_IMPACT_WEIGHT = 1 # Weight of reinforcement volume in the fitness function
    EARLY_STOPPING_GENERATIONS = 20 # Number of generations without improvement to stop the algorithm

    def calculate_concrete_and_reinforcement_volume(section_dict):
        concrete_cumulative_volume = 0
        reinforcement_cumulative_volume = 0
        z_prev = 0
        for z, values in section_dict.items():
            length, thickness, reinforcement_ratio = values
            concrete_area = length * thickness * 2 + (length - 2 * thickness) * thickness * 2

            concrete_cumulative_volume += concrete_area * (z - z_prev)

            reinforcement_cumulative_volume += reinforcement_ratio * concrete_area * (z - z_prev)
            z_prev = z
        
        return concrete_cumulative_volume, reinforcement_cumulative_volume

    def fitness(individual):
        # Extract section_dict from the individual
        section_dict = {z: values[:3] for z, values in individual.items()}

        dcr_results = mdof.mdof_simple_model(story_force_dictionary, section_dict)

        shear_dcr = max(dcr_results['shear_dcr'].values())
        moment_dcr = max(dcr_results['moment_dcr'].values())
        drift_dcr = dcr_results['drift_dcr']

        concrete_cumulative_volume, reinforcement_cumulative_volume = calculate_concrete_and_reinforcement_volume(section_dict)

        if shear_dcr > 1 or moment_dcr > 1 or drift_dcr > 1:
            return max(shear_dcr, moment_dcr, drift_dcr) * 100000 + CONCRETE_IMPACT_WEIGHT * concrete_cumulative_volume + REINFORCEMENT_IMPACT_WEIGHT * reinforcement_cumulative_volume

        return abs(1 - shear_dcr) + abs(1 - moment_dcr) + abs(1 - drift_dcr) + CONCRETE_IMPACT_WEIGHT * concrete_cumulative_volume + REINFORCEMENT_IMPACT_WEIGHT * reinforcement_cumulative_volume

    def crossover(parent1, parent2):
        child1 = {}
        child2 = {}
        for z in ELEVATIONS:
            if random.random() < CROSSOVER_RATE:
                child1[z] = parent1[z]
                child2[z] = parent2[z]
            else:
                child1[z] = parent2[z]
                child2[z] = parent1[z]
        return child1, child2

    def mutate(individual):
        mutated_dict = {}
        for z, values in individual.items():
            length, thickness, reinforcement_ratio = values
            if random.random() < MUTATION_RATE:
                length += random.choice([-2, 2])  # Change by 2 units to keep it even
                length = max(LENGTH_MIN, min(LENGTH_MAX, length))  # Ensure within limits
            if random.random() < MUTATION_RATE:
                thickness += random.choice([-2, 2])  # Change by 2 units to keep it even
                thickness = max(THICKNESS_MIN, min(THICKNESS_MAX, thickness))  # Ensure within limits
            if random.random() < MUTATION_RATE:
                reinforcement_ratio += random.uniform(-0.001, 0.001)
                reinforcement_ratio = max(REINFORCEMENT_RATIO_MIN, min(REINFORCEMENT_RATIO_MAX, reinforcement_ratio))
            mutated_dict[z] = [length, thickness, round(reinforcement_ratio, 4)]
        return mutated_dict

    def select(population):
        sorted_population = sorted(population, key=fitness)
        return sorted_population[:POPULATION_SIZE//2]

    # Initialize a population with random gene values.
    population = []
    for _ in range(POPULATION_SIZE):
        individual = {}
        for z in ELEVATIONS:
            length = random.choice(range(LENGTH_MIN + LENGTH_MIN % 2, LENGTH_MAX + 1, 2))
            thickness = random.choice(range(int(THICKNESS_MIN + THICKNESS_MIN % 2), int(THICKNESS_MAX + 1), 2))
            reinforcement_ratio = random.uniform(REINFORCEMENT_RATIO_MIN, REINFORCEMENT_RATIO_MAX)
            individual[z] = [length, thickness, round(reinforcement_ratio, 4)]
        population.append(individual)

    best_fitness_ever = float('inf')
    generations_without_improvement = 0

    for generation in range(GENERATIONS):
        selected = select(population)
        children = []

        # Generate children by performing crossover and mutation on selected individuals.
        for i in range(0, len(selected), 2):
            child1, child2 = crossover(selected[i], selected[i+1])
            children.append(mutate(child1))
            children.append(mutate(child2))

        population = selected + children

        best = min(population, key=fitness)
        best_fitness_current = fitness(best)
        #print(f"Generation {generation + 1}: Best individual = {best} with fitness = {round(best_fitness_current,2)}")

        # Check if the best fitness has improved.
        if best_fitness_current < best_fitness_ever:
            best_fitness_ever = best_fitness_current
            generations_without_improvement = 0
        else:
            generations_without_improvement += 1

        # If there's no improvement for a predefined number of generations, stop the optimization.
        if generations_without_improvement >= EARLY_STOPPING_GENERATIONS:
            print(f"Stopping early: No improvement for {EARLY_STOPPING_GENERATIONS} generations.")
            break

    concrete_volume = round(calculate_concrete_and_reinforcement_volume(best)[0], 2)
    reinforcement_volume = round(calculate_concrete_and_reinforcement_volume(best)[1], 2)

    concrete_embodied_carbon = calculate_embodied_carbon.calculate_embodied_carbon_concrete(concrete_volume)
    reinforcement_embodied_carbon = calculate_embodied_carbon.calculate_embodied_carbon_reinforcement(reinforcement_volume)      

    best_result = {"Generation": generation + 1, 
                   "Best Section Information": best, 
                   "Best fitness": round(best_fitness_ever, 2), 
                   "Concrete volume": concrete_volume, 
                   "Reinforcement volume": reinforcement_volume,
                   "Concrete Embodied Carbon": round(concrete_embodied_carbon, 2),
                   "Reinforcement Embodied Carbon": round(reinforcement_embodied_carbon, 2)}
    
    
    # Return the best individual found.
    print(best_result)

    data = DataGroup(
        DataItem('Generation', generation+1),
        DataItem('Core Section', best),
        DataItem('Fitness', round(best_fitness_ever, 2)),
        DataItem('Concrete Volume', round(calculate_concrete_and_reinforcement_volume(best)[0], 2), suffix='ft^3'),
        DataItem('Reinforcement Volume', round(calculate_concrete_and_reinforcement_volume(best)[1], 2), suffix='ft^3'),
        DataItem('Concrete Embodied Carbon', round(concrete_embodied_carbon, 2), suffix='kgCO2e'),
        DataItem('Reinforcement Embodied Carbon', round(reinforcement_embodied_carbon, 2), suffix='kgCO2e')
    )
    
    return best_result, data
        

if __name__ == "__main__":
    test_story_forces = {0: 0, 10: 100, 20: 200, 30: 300, 40: 400}
    print(evolutionary_optimizer(test_story_forces, 20, 40))
