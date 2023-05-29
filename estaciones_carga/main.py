import traci
import sumolib
import networkx as nx

def edge_capacity(edge, time_headway=2.0):
    num_lanes = traci.edge.getLaneNumber(edge.getID())
    lane_length = edge.getLength()
    speed_limit = edge.getSpeed()
    lane_capacity = (lane_length / time_headway) * (speed_limit / lane_length)
    return num_lanes * lane_capacity

def bpr_travel_time(edge, alpha=0.15, beta=4):
    free_flow_time = edge.getLength() / edge.getSpeed()
    vehicle_ids = traci.edge.getLastStepVehicleIDs(edge.getID())
    volume = len(vehicle_ids)
    capacity = edge_capacity(edge)
    return free_flow_time * (1 + alpha * (volume / capacity) ** beta)

def generate(network):
	net = sumolib.net.readNet(network)
	edges = net.getEdges()
	G = nx.DiGraph()
	for k in edges:
		#weight = k.getLength()
		weight = bpr_travel_time(k)
		G.add_edge(k.getFromNode().getID(), k.getToNode().getID(), weight=weight, id=k.getID(),capacity=edge_capacity(k),flow=0)
	return G

def update_edge_weights(G, net):
	for u,v,data in G.edges(data=True):
		edge_id = data['id']
		edge = net.getEdge(edge_id)
		#new_weight = edge.getLength()
		new_weight = bpr_travel_time(edge)
		G.edges[(u,v)]['weight'] = new_weight
		G.edges[(u,v)]['flow'] = G.edges[(u,v)]['capacity'] / new_weight

def find_most_important_edges(G):
	edge_betweenness = nx.edge_betweenness_centrality(G, weight='weight', normalized=False)
	sorted_edges = sorted(edge_betweenness.items(), key=lambda x: x[1], reverse=True)
	return sorted_edges

xml = "output.net.xml"
cfg = "font.sumocfg"


traci.start(["sumo", "-c", cfg])
net = sumolib.net.readNet(xml)
graph = generate(xml)




traci.simulationStep()
update_edge_weights(graph, net)

subgraph = graph.edge_subgraph([edge[0] for edge in find_most_important_edges(graph)[:20]])
center_nodes = set([u for u, v in subgraph.edges()] + [v for u, v in subgraph.edges()])
cells = nx.voronoi_cells(subgraph, center_nodes)



import matplotlib.pyplot as plt



voronoi_graph = nx.Graph()



for center_node, cell_nodes in cells.items():
    for node in cell_nodes:
        voronoi_graph.add_edge(center_node, node)



pos = nx.spring_layout(subgraph)
plt.figure(figsize=(8, 6))
nx.draw_networkx(subgraph, pos, with_labels=True, node_color='lightgray', edge_color='gray')
nx.draw_networkx_edges(voronoi_graph, pos, edge_color='red', alpha=0.5, width=2.0)
plt.title("Voronoi Cells")
plt.axis("off")



plt.savefig("voronoi_cells.png", format="png")



traci.close()