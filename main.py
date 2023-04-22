import traci
import sumolib
import networkx as nx
import math

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
        weight = bpr_travel_time(k)
        G.add_edge(k.getFromNode().getID(), k.getToNode().getID(), weight=weight, id=k.getID())
    return G

def update_edge_weights(G, net):
    for u,v,data in G.edges(data=True):
        edge_id = data['id']
        edge = net.getEdge(edge_id)
        new_weight = bpr_travel_time(edge)
        G.edges[(u,v)]['weight'] = new_weight

traci.start(["sumo-gui", "-c", "yastra.sumocfg"])
net = sumolib.net.readNet("yastra.net.xml")
graph = generate("yastra.net.xml")

step = 0
while step < 1000:
    traci.simulationStep()

    if step % 10 == 0:
        update_edge_weights(graph, net)

    step += 1

traci.close()
