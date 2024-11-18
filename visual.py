import osmnx as ox
import matplotlib.pyplot as plt

# Cargar la red vial completa para visualización
ciudad = "Manhattan, New York, USA"
G = ox.graph_from_place(ciudad, network_type="drive")

# Ubicaciones óptimas para semáforos en cada zona
ubicaciones_optimas = [42428094, 42446013, 9166213997]  # IDs obtenidos del algoritmo

# Dibujar el grafo con los semáforos óptimos
fig, ax = ox.plot_graph(G, show=False, close=False)

# Añadir puntos para los semáforos óptimos en cada zona
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
plt.title("Ubicaciones Óptimas de Semáforos en Cada Zona")
plt.show()
