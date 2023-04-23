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
		#weight = k.getLength()
		weight = bpr_travel_time(k)
		G.add_edge(k.getFromNode().getID(), k.getToNode().getID(), weight=weight, id=k.getID())
	return G

def update_edge_weights(G, net):
	for u,v,data in G.edges(data=True):
		edge_id = data['id']
		edge = net.getEdge(edge_id)
		#new_weight = edge.getLength()
		new_weight = bpr_travel_time(edge)
		G.edges[(u,v)]['weight'] = new_weight

def update_vehicle_route(graph,vehicle_id,to_node):
	current_edge_id = traci.vehicle.getRoadID(vehicle_id)
	try:
		current_edge = net.getEdge(current_edge_id)
	except:
		return 0
	from_node = current_edge.getFromNode().getID()
	new_route = shortest_path(graph, from_node, to_node)
	try:
		traci.vehicle.setRoute(vehicle_id, new_route)
	except:
		pass


def shortest_path(graph, start_node, end_node):
    # Find the shortest path between the start and end nodes
    path = nx.shortest_path(graph, start_node, end_node, weight='weight')

    # Get the list of edges along the shortest path
    edges = [(path[i], path[i+1]) for i in range(len(path)-1)]
    edge_ids = [graph[path[i]][path[i+1]]['id'] for i in range(len(path)-1)]

    # Return the list of edge IDs along the shortest path
    return edge_ids

def makenvehicles(n,s,e,count=0):
	for i in range(n):
		new_route = shortest_path(graph, s, e)
		vehicle_id = f"vehicle_{i+count}"
		route_id = f"route_{i+count}"
		traci.route.add(route_id, new_route)
		traci.vehicle.add(vehicle_id, route_id)
		print(traci.vehicle.getElectricityConsumption(vehicle_id))
		count+=1
	return count

def makenevehicles(n,s,e,initial_battery=1000,count=0):
	for i in range(n):
		vehicle_id = f"electric_vehicle_{i+count}"
		new_route = shortest_path(graph, s,e)
		route_id = f"route_{i+count}"
		traci.route.add(route_id, new_route)
		traci.vehicle.add(vehicle_id, route_id,typeID="electric")
		traci.vehicle.setParameter(vehicle_id, "device.battery.actualBatteryCapacity", str(initial_battery))
		
		count += 1
	return count

traci.start(["sumo-gui", "-c", "yastra.sumocfg"])
net = sumolib.net.readNet("yastra.net.xml")
graph = generate("yastra.net.xml")


makenevehicles(1,"A","C",1)


step = 0
while step < 1000:
	print(traci.vehicle.getParameter("electric_vehicle_0", "device.battery.actualBatteryCapacity"))
	traci.simulationStep()
	update_edge_weights(graph, net)
	for i in traci.vehicle.getIDList():
		update_vehicle_route(graph,i,"C")
	step += 1

traci.close()

