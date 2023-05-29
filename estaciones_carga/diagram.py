import osmnx as ox
from scipy.spatial import Voronoi, voronoi_plot_2d
import matplotlib.pyplot as plt


graph = ox.graph_from_xml("export.osm", simplify=True)


nodes = ox.graph_to_gdfs(graph, nodes=True, edges=False)
coordinates = list(nodes["geometry"].apply(lambda point: (point.y, point.x)))


vor = Voronoi(coordinates)


fig, ax = plt.subplots(figsize=(10, 10))
voronoi_plot_2d(vor, ax=ax, show_vertices=False, line_colors="blue", line_width=0.5)
plt.axis("off")
plt.savefig("voronoi_diagram.png", format="png")
plt.show()

