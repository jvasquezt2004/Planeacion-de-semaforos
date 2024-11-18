import osmnx as ox
import networkx as nx
import numpy as np
import random
import matplotlib.pyplot as plt


# Función para cargar la red vial y dividir San Francisco en zonas
def cargar_red_vial_zonas(ciudad="Tlaxcala de Xicohténcatl, Tlaxcala, Mexico", zonas=3):
    G = ox.graph_from_place(ciudad, network_type="drive")
    nodos = list(G.nodes)
    zona_size = len(nodos) // zonas
    return [nodos[i * zona_size : (i + 1) * zona_size] for i in range(zonas)], G


# Función para agregar tráfico simulado con patrones de hora pico y no pico
def agregar_trafico_simulado_complejo(G, hora_pico=False):
    for u, v, data in G.edges(data=True):
        if u % 2 == 0 and v % 2 == 0:  # Arterias principales
            data["traffic"] = (
                random.randint(70, 100) if hora_pico else random.randint(40, 70)
            )
        elif u % 5 == 0 or v % 5 == 0:  # Calles secundarias
            data["traffic"] = (
                random.randint(50, 80) if hora_pico else random.randint(20, 50)
            )
        else:
            data["traffic"] = (
                random.randint(30, 60) if hora_pico else random.randint(10, 30)
            )
    return G


# Función para preparar los datos de tráfico en cada zona
def preparar_datos_zona(G, nodos_zona):
    intersecciones = [nodo for nodo in G.nodes if nodo in nodos_zona]
    trafico = {}
    for u, v, data in G.edges(data=True):
        if u in intersecciones and v in intersecciones:
            trafico[(u, v)] = data.get("traffic", 0)
    return intersecciones, trafico


# Función de fitness con ajuste de penalización y bonificación
def calcular_flujo_total(
    individual,
    intersecciones,
    trafico,
    G,
    penalizacion_semaforos=1,
    sincronizacion=False,
):
    penalizacion = 100
    flujo_total = 0
    distancia_minima = 100  # Distancia mínima entre semáforos (en metros)
    rutas_cubiertas = set()

    for idx in range(len(individual) - 1):
        interseccion_actual = individual[idx]
        siguiente_interseccion = individual[idx + 1]
        rutas_cubiertas.add((interseccion_actual, siguiente_interseccion))

        # Verifica si la conexión existe en el dataset de tráfico
        if (interseccion_actual, siguiente_interseccion) in trafico:
            flujo_segmento = trafico[(interseccion_actual, siguiente_interseccion)]
            if sincronizacion and idx > 0 and interseccion_actual % 2 == 0:
                flujo_segmento *= 0.8  # Reducir tráfico si sincronizado en avenida
        elif (siguiente_interseccion, interseccion_actual) in trafico:
            flujo_segmento = trafico[(siguiente_interseccion, interseccion_actual)]
        else:
            flujo_segmento = penalizacion

        # Calcular distancia entre semáforos si están conectados
        if idx > 0:
            nodo_anterior = individual[idx - 1]
            try:
                if nx.has_path(G, nodo_anterior, interseccion_actual):
                    distancia = nx.shortest_path_length(
                        G,
                        source=nodo_anterior,
                        target=interseccion_actual,
                        weight="length",
                    )
                    if distancia < distancia_minima:
                        flujo_segmento += (
                            penalizacion / 2
                        )  # Penalización adicional si están muy cerca
                else:
                    flujo_segmento += (
                        penalizacion  # Penalización completa si no están conectados
                    )
            except nx.NetworkXNoPath:
                flujo_segmento += (
                    penalizacion  # Penalización si no hay ruta entre nodos
                )

        flujo_total += flujo_segmento

    # Bonificación aumentada por cobertura de rutas únicas
    flujo_total -= (
        len(rutas_cubiertas) * 20
    )  # Bonificación por cubrir más rutas, aumentada
    # Penalización reducida por cantidad de semáforos
    flujo_total += (
        penalizacion_semaforos * len(individual) / 2
    )  # Reducida para permitir más semáforos

    return flujo_total


# Crear población variable con mínimo ajustado de semáforos
def create_population(num_intersecciones, PSIZE, min_semaforos=5, max_semaforos=10):
    population = []
    for _ in range(PSIZE):
        num_semaforos = random.randint(min_semaforos, max_semaforos)
        individual = random.sample(range(num_intersecciones), k=num_semaforos)
        population.append(individual)
    return population


# Modificar la función de recombinación para tamaños variables
def recombinar_individuos(ind1, ind2, ind3, num_intersecciones):
    min_len = min(len(ind1), len(ind2), len(ind3))
    ind1 = (
        (ind1[:min_len] + random.sample(range(num_intersecciones), min_len - len(ind1)))
        if len(ind1) < min_len
        else ind1[:min_len]
    )
    ind2 = (
        (ind2[:min_len] + random.sample(range(num_intersecciones), min_len - len(ind2)))
        if len(ind2) < min_len
        else ind2[:min_len]
    )
    ind3 = (
        (ind3[:min_len] + random.sample(range(num_intersecciones), min_len - len(ind3)))
        if len(ind3) < min_len
        else ind3[:min_len]
    )
    child = np.add(ind1, (0.5 * (np.subtract(ind2, ind3))))
    child = [int(round(val)) % num_intersecciones for val in child]
    return list(set(child))


# Función principal para ejecutar el algoritmo en cada zona
def optimizar_por_zona(ciudad="San Francisco, California, USA", hora_pico=False):
    zonas, G = cargar_red_vial_zonas(ciudad)
    G = agregar_trafico_simulado_complejo(G, hora_pico)

    FM = 0.5
    CR = 0.5
    NGEN = 500
    PSIZE = 50
    OBJECTIVE = "MIN"
    penalizacion_semaforos = 1  # Penalización reducida para permitir más semáforos
    sincronizacion = True

    resultados = []
    for idx, nodos_zona in enumerate(zonas):
        print(f"\nOptimizando en la zona {idx + 1}")
        intersecciones, trafico = preparar_datos_zona(G, nodos_zona)
        num_intersecciones = len(intersecciones)

        population = create_population(num_intersecciones, PSIZE)

        for n in range(NGEN):
            for i, target in enumerate(population):
                populationEX = [ind for j, ind in enumerate(population) if j != i]
                values = random.sample(populationEX, 3)
                child = recombinar_individuos(
                    values[0], values[1], values[2], num_intersecciones
                )

                if random.random() < 0.5 and len(child) > 5:
                    child.pop(random.randint(0, len(child) - 1))
                elif random.random() < 0.5 and len(child) < 10:
                    nuevo_semaforo = random.choice(
                        list(set(range(num_intersecciones)) - set(child))
                    )
                    child.append(nuevo_semaforo)

                child_value = calcular_flujo_total(
                    [intersecciones[i] for i in child],
                    intersecciones,
                    trafico,
                    G,
                    penalizacion_semaforos,
                    sincronizacion,
                )
                target_value = calcular_flujo_total(
                    [intersecciones[i] for i in target],
                    intersecciones,
                    trafico,
                    G,
                    penalizacion_semaforos,
                    sincronizacion,
                )

                if (
                    child_value < target_value
                    if OBJECTIVE == "MIN"
                    else child_value > target_value
                ):
                    population[i] = child

        min_fitness = float("inf")
        best_individual = None
        for individual in population:
            fitness_value = calcular_flujo_total(
                [intersecciones[i] for i in individual],
                intersecciones,
                trafico,
                G,
                penalizacion_semaforos,
                sincronizacion,
            )
            if fitness_value < min_fitness:
                min_fitness = fitness_value
                best_individual = individual

        resultados.append(
            (
                min_fitness,
                [intersecciones[i] for i in best_individual],
                len(best_individual),
            )
        )
        print(
            f"Zona {idx + 1} - Fitness: {min_fitness}, Semáforos: {len(best_individual)}, Ubicaciones: {[intersecciones[i] for i in best_individual]}"
        )

    return resultados


# Visualización de los semáforos en el mapa
def visualizar_semaforos(G, ubicaciones_optimas):
    fig, ax = ox.plot_graph(G, show=False, close=False)
    for idx, nodo in enumerate(ubicaciones_optimas):
        if nodo in G.nodes:
            x, y = G.nodes[nodo]["x"], G.nodes[nodo]["y"]
            ax.scatter(
                x,
                y,
                color="red",
                s=100,
                label=f"Semáforo Zona {idx + 1}" if idx == 0 else "",
            )
    plt.legend()
    plt.title("Ubicaciones Óptimas de Semáforos en Cada Zona - Tlaxcala")
    plt.show()


if __name__ == "__main__":
    resultados = optimizar_por_zona("Tlaxcala de Xicohténcatl, Tlaxcala, Mexico", hora_pico=True)
    print("\nResumen de Resultados:")
    ubicaciones_optimas = []
    for idx, (fitness, ubicaciones, num_semaforos) in enumerate(resultados):
        ubicaciones_optimas.extend(ubicaciones)
        print(
            f"Zona {idx + 1} - Fitness: {fitness}, Semáforos óptimos: {num_semaforos}, Ubicaciones: {ubicaciones}"
        )
    G_sf = ox.graph_from_place("Tlaxcala de Xicohténcatl, Tlaxcala, Mexico", network_type="drive")
    visualizar_semaforos(G_sf, ubicaciones_optimas)
