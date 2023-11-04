import random
import math

# Constants
POPULATION_SIZE = 100  # Total number of individuals in the population
MUTATION_RATE = 0.05  # Probability of a gene mutating
CROSSOVER_RATE = 0.9  # Probability of crossover happening
GENERATIONS = 1000  # Number of iterations/generations the algorithm will run for
GENE_MIN = 0  # Minimum value for a gene (rotation in degrees)
GENE_MAX = 90  # Maximum value for a gene (rotation in degrees)

def fitness(individual):
    # Calculate the fitness of an individual.
    # The fitness function represents the quality of a solution.
    # Here, we use the negative sine product of rotations to simulate the bounding box problem.
    x_rotation, y_rotation = individual
    return -(math.sin(math.radians(x_rotation)) * math.sin(math.radians(y_rotation)))

def crossover(parent1, parent2):
    # Create two children by combining genes from two parents.
    # The crossover point is chosen randomly.
    if random.random() < CROSSOVER_RATE:
        point = random.randint(0, len(parent1)-1)
        child1 = parent1[:point] + parent2[point:]
        child2 = parent2[:point] + parent1[point:]
        return child1, child2
    else:
        # If no crossover, children are clones of parents.
        return parent1, parent2

def mutate(individual):
    # Apply mutations to genes of an individual with a probability of MUTATION_RATE.
    # The mutation is a random value between -1 and 1 added to the original gene value.
    # The gene value is constrained between 0 and 90 using modulo operation.
    return [(gene + (random.uniform(-1, 1) if random.random() < MUTATION_RATE else 0)) % 90 for gene in individual]

def select(population):
    # Select the top half of the population based on fitness.
    # This is a truncation selection method.
    sorted_population = sorted(population, key=fitness)
    return sorted_population[:POPULATION_SIZE//2]

def main():
    # Main loop of the genetic algorithm.
    
    # Initialize a population with random gene values (rotations).
    population = [[random.uniform(GENE_MIN, GENE_MAX) for _ in range(2)] for _ in range(POPULATION_SIZE)]
    
    for generation in range(GENERATIONS):
        # Selection: Choose the top individuals based on fitness.
        selected = select(population)
        
        # Crossover and Mutation: Generate children from selected individuals.
        children = []
        for i in range(0, len(selected), 2):
            child1, child2 = crossover(selected[i], selected[i+1])
            children.append(mutate(child1))
            children.append(mutate(child2))
        
        # Combine selected individuals and their children to form the new population.
        population = selected + children
        
        # Print the best individual of the current generation.
        best = min(population, key=fitness)
        print(f"Generation {generation + 1}: Best individual = {best} with fitness = {fitness(best)}")

main()
