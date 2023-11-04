def evolutionary_optimizer(story_force_dictionary):

    import mdof_simple_model as mdof
    import random

    # Constants
    POPULATION_SIZE = 1000
    MUTATION_RATE = 0.15
    CROSSOVER_RATE = 0.9
    GENERATIONS = 100
    LENGTH_MIN = 10  # ft
    LENGTH_MAX = 40  # ft
    THICKNESS_MIN = 1  # ft
    THICKNESS_MAX = 3  # ft
    REINFORCEMENT_RATIO_MIN = 0.0025
    REINFORCEMENT_RATIO_MAX = 0.02
    ELEVATIONS = list(story_force_dictionary.keys())
    CONCRETE_IMPACT_WEIGHT = 0.1
    REINFORCEMENT_IMPACT_WEIGHT = 1

    def fitness(individual):
        # Extract section_dict and reinforcement_ratios
        section_dict = {z: values[:3] for z, values in individual.items()}

        dcr_results = mdof.mdof_simple_model(story_force_dictionary, section_dict)

        shear_dcr = max(dcr_results['shear_dcr'].values())
        moment_dcr = max(dcr_results['moment_dcr'].values())
        drift_dcr = dcr_results['drift_dcr']

        concrete_cumulative_volume = 0
        reinforcement_cumulative_volume = 0
        z_prev = 0
        for z, values in section_dict.items():
            length, thickness, reinforcement_ratio = values
            concrete_area = length * thickness * 2 + (length - 2 * thickness) * thickness * 2
            concrete_cumulative_volume += concrete_area * (z - z_prev)

            reinforcement_cumulative_volume += reinforcement_ratio * concrete_area * (z - z_prev)
            z_prev = z

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

            mutated_dict[z] = [length, thickness, reinforcement_ratio]
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
            individual[z] = [length, thickness, reinforcement_ratio]
        population.append(individual)

    for generation in range(GENERATIONS):
        selected = select(population)
        children = []
        for i in range(0, len(selected), 2):
            child1, child2 = crossover(selected[i], selected[i+1])
            children.append(mutate(child1))
            children.append(mutate(child2))

        population = selected + children

        best = min(population, key=fitness)
        print(f"Generation {generation + 1}: Best individual = {best} with fitness = {fitness(best)}")


if __name__ == "__main__":

    test_story_forces = {0: 0, 10: 100, 20: 200, 30: 300, 40: 400}

    evolutionary_optimizer(test_story_forces)
