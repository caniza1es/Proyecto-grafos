import sumolib
import networkx as nx

def generate(network):
    net = sumolib.net.readNet(network)
    edges = net.getEdges()
    G = nx.DiGraph()
    for k in edges:
        G.add_edge(k.getFromNode().getID(),k.getToNode().getID(), weight=k.getLength(), id=k._id)
    return G

def shortest_path(graph, start_node, end_node):
    # Find the shortest path between the start and end nodes
    path = nx.shortest_path(graph, start_node, end_node, weight='weight')

    # Get the list of edges along the shortest path
    edges = [(path[i], path[i+1]) for i in range(len(path)-1)]
    edge_ids = [graph[path[i]][path[i+1]]['id'] for i in range(len(path)-1)]

    # Return the list of edge IDs along the shortest path
    return edge_ids