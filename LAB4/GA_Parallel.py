import numpy as np
import random
import time
import os
from multiprocessing import Pool, cpu_count

TSP_FILE_PATH = "att48.tsp"

# Parametry GA
POPULATION_SIZE = 500
GENERATIONS = 1000
TURNEY_SIZE = 2
MUTATION_RATE = 0.08
ELITE_SIZE = 2

APPLY_2OPT_PROB = 0.25
MAX_2OPT_IMPROV_PER_CHILD = 1

SEED = None

global_dist_matrix = None


def calculate_distance_matrix(coords, edge_weight_type):
    diff = coords[:, np.newaxis, :] - coords[np.newaxis, :, :]
    squared_dist = np.sum(diff ** 2, axis=2)
    if edge_weight_type == 'ATT':
        return np.round(np.sqrt(squared_dist)).astype(int)
    else:
        return np.sqrt(squared_dist)


def load_and_process_tsp_data(file_path):
    coords = []
    dimension = 0
    edge_weight_type = None
    reading_coords = False
    try:
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line: continue
                if line.upper().startswith('DIMENSION'):
                    dimension = int(line.split(':')[1].strip())
                elif line.upper().startswith('EDGE_WEIGHT_TYPE'):
                    edge_weight_type = line.split(':')[1].strip()
                elif line.upper().startswith('NODE_COORD_SECTION'):
                    reading_coords = True
                elif line.upper().startswith('EOF'):
                    break
                elif reading_coords:
                    parts = line.split()
                    if len(parts) >= 3:
                        try:
                            coords.append((float(parts[1]), float(parts[2])))
                        except ValueError:
                            continue
    except FileNotFoundError:
        print(f"Błąd: Nie znaleziono pliku {file_path}")
        raise SystemExit(1)

    if len(coords) != dimension:
        # Fallback if parsing fails or header mismatch
        pass

    coords_array = np.array(coords)
    dist_matrix = calculate_distance_matrix(coords_array, edge_weight_type)
    return dimension, dist_matrix


def path_distance(path, dist_matrix):
    total = dist_matrix[path[:-1], path[1:]].sum()
    total += dist_matrix[path[-1], path[0]]
    return float(total)


def order_crossover(p1, p2):
    n = len(p1)
    child = np.full(n, -1, dtype=int)
    a, b = sorted(random.sample(range(n), 2))
    child[a:b] = p1[a:b]
    p2_idx = 0
    for i in range(n):
        if child[i] == -1:
            while p2[p2_idx] in child:
                p2_idx += 1
            child[i] = p2[p2_idx]
            p2_idx += 1
    return child


def inversion_mutation(path):
    p = path.copy()
    i, j = sorted(random.sample(range(len(p)), 2))
    p[i:j] = p[i:j][::-1]
    return p


def swap_mutation(path):
    p = path.copy()
    i, j = random.sample(range(len(p)), 2)
    p[i], p[j] = p[j], p[i]
    return p


def mutate(path):
    if random.random() < MUTATION_RATE:
        if random.random() < 0.7:
            return inversion_mutation(path)
        else:
            return swap_mutation(path)
    else:
        return path.copy()


def two_opt_improve_once(path, dist_matrix):
    n = len(path)
    best = path
    best_distance = path_distance(path, dist_matrix)
    for i in range(1, n - 2):
        for j in range(i + 1, n):
            if j - i == 1: continue
            new_route = best.copy()
            new_route[i:j] = best[j - 1:i - 1:-1]
            new_dist = path_distance(new_route, dist_matrix)
            if new_dist < best_distance - 1e-12:
                return new_route, True
    return best, False


def two_opt(path, dist_matrix, max_improvements=MAX_2OPT_IMPROV_PER_CHILD):
    current = path.copy()
    improvements = 0
    while improvements < max_improvements:
        new_path, improved = two_opt_improve_once(current, dist_matrix)
        if not improved:
            break
        current = new_path
        improvements += 1
    return current

# Workery
def init_worker(dist_matrix):
    global global_dist_matrix
    global_dist_matrix = dist_matrix

    random.seed(os.getpid() + time.time())
    np.random.seed(int(os.getpid() + time.time()) % 2 ** 32)


def generate_offspring_task(p1, p2):
    # Krzyżowanie
    child1 = order_crossover(p1, p2)
    child2 = order_crossover(p2, p1)

    # Mutacja
    child1 = mutate(child1)
    child2 = mutate(child2)

    if APPLY_2OPT_PROB > 0 and random.random() < APPLY_2OPT_PROB:
        child1 = two_opt(child1, global_dist_matrix, MAX_2OPT_IMPROV_PER_CHILD)
    if APPLY_2OPT_PROB > 0 and random.random() < APPLY_2OPT_PROB:
        child2 = two_opt(child2, global_dist_matrix, MAX_2OPT_IMPROV_PER_CHILD)

    return [child1, child2]


def initialize_population(pop_size, num_cities):
    pop = [np.random.permutation(num_cities) for _ in range(pop_size)]
    return np.array(pop)


def fitness_all(population, dist_matrix):
    return np.array([path_distance(p, dist_matrix) for p in population])


def tournament_selection(population, distances, tour_size):
    pop_size = len(population)
    parents_idx = []
    for _ in range(pop_size):
        competitors = np.random.choice(pop_size, size=tour_size, replace=False)
        winner = competitors[np.argmin(distances[competitors])]
        parents_idx.append(winner)
    return parents_idx


def GA_parallel_with_2opt(dist_matrix, pop_size, generations):
    num_cities = dist_matrix.shape[0]
    population = initialize_population(pop_size, num_cities)
    fitness = fitness_all(population, dist_matrix)

    best_idx = np.argmin(fitness)
    best_distance = float(fitness[best_idx])
    best_path = population[best_idx].copy()

    # Utworzenie puli procesów (re-używana przez wszystkie generacje)
    # Ustawiamy global_dist_matrix w każdym procesie
    pool_size = cpu_count()
    pool = Pool(processes=pool_size, initializer=init_worker, initargs=(dist_matrix,))

    print(f"Start obliczeń na {pool_size} rdzeniach...")
    start_time = time.time()

    try:
        for gen in range(1, generations + 1):
            fitness = fitness_all(population, dist_matrix)

            sorted_idx = np.argsort(fitness)
            elites = [population[i].copy() for i in sorted_idx[:ELITE_SIZE]]

            if fitness[sorted_idx[0]] < best_distance:
                best_distance = float(fitness[sorted_idx[0]])
                best_path = population[sorted_idx[0]].copy()

            if gen % 100 == 0 or gen == 1 or gen == generations:
                elapsed = time.time() - start_time
                print(f"Gen {gen}/{generations} | Best = {best_distance:.6f} | Time = {elapsed:.2f}s")

            # 2. Selekcja
            parent_indices = tournament_selection(population, fitness, TURNEY_SIZE)


            needed_offspring = pop_size - len(elites)
            pairs_count = (needed_offspring + 1) // 2

            tasks = []
            for i in range(pairs_count):
                p1_idx = parent_indices[(2 * i) % len(parent_indices)]
                p2_idx = parent_indices[(2 * i + 1) % len(parent_indices)]
                tasks.append((population[p1_idx], population[p2_idx]))

            # Równoległe generowanie dzieci (Pool.starmap)
            results = pool.starmap(generate_offspring_task, tasks)

            # Składanie nowej populacji
            new_population = [e.copy() for e in elites]
            for pair in results:
                new_population.extend(pair)

            population = np.array(new_population[:pop_size])

    finally:
        pool.close()
        pool.join()

    total_time = time.time() - start_time
    return best_distance, best_path, total_time


if __name__ == "__main__":
    try:
        NUM_CITIES_GLOBAL, DIST_MATRIX_GLOBAL = load_and_process_tsp_data(TSP_FILE_PATH)
    except FileNotFoundError as e:
        print(e)
        raise SystemExit(1)

    if SEED is not None:
        random.seed(SEED)
        np.random.seed(SEED)

    print("\n--- Parallel GA (OX) + 2-OPT ---")
    print(f"Plik: {TSP_FILE_PATH} ({NUM_CITIES_GLOBAL} miast)")
    print(f"POP_SIZE={POPULATION_SIZE}, GENERATIONS={GENERATIONS}")
    print(f"APPLY_2OPT_PROB={APPLY_2OPT_PROB}")

    best_dist, best_path, elapsed = GA_parallel_with_2opt(DIST_MATRIX_GLOBAL, POPULATION_SIZE, GENERATIONS)

    print("\n--- WYNIK KOŃCOWY ---")
    print(f"Czas całkowity: {elapsed:.2f}s")
    print(f"Najlepsza odległość: {best_dist:.6f}")
    print("Najlepsza trasa:", best_path)