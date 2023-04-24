import traci
import sumolib
import networkx as nx
from networkx.algorithms.flow import maximum_flow
import math
import itertools

print("guh")

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

def makeevehicletype(network):
	A = sumolib.vehicletype.CreateVehTypeDistribution(name="electDist",size=1)
	Attr = [sumolib.vehicletype.VehAttribute("id",False,attribute_value="electric"),
			sumolib.vehicletype.VehAttribute("has.battery.device",True,attribute_value="true"),
			sumolib.vehicletype.VehAttribute("maximumBatteryCapacity",True,attribute_value="2000"),
			sumolib.vehicletype.VehAttribute("stoppingThreshold",True,attribute_value="0.1")]
	for i in Attr:
		A.add_attribute(i)
	A.to_xml(network)

def update_edge_weights(G, net):
	for u,v,data in G.edges(data=True):
		edge_id = data['id']
		edge = net.getEdge(edge_id)
		#new_weight = edge.getLength()
		new_weight = bpr_travel_time(edge)
		G.edges[(u,v)]['weight'] = new_weight
		G.edges[(u,v)]['flow'] = G.edges[(u,v)]['capacity'] / new_weight

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
    path = nx.shortest_path(graph, start_node, end_node, weight='weight')
    edges = [(path[i], path[i+1]) for i in range(len(path)-1)]
    edge_ids = [graph[path[i]][path[i+1]]['id'] for i in range(len(path)-1)]
    return edge_ids

def makenvehicles(n,s,e,count=0):
	for i in range(n):
		new_route = shortest_path(graph, s, e)
		vehicle_id = f"vehicle_{i+count}"
		route_id = f"route_{i+count}"
		traci.route.add(route_id, new_route)
		traci.vehicle.add(vehicle_id, route_id)
		count+=1
	return count

def makenevehicles(n,s,e,initial_battery=1000,count=0):
	a_vehicles = []
	for veh in range(n):
		vehicle_id = f"electric_vehicle_{veh+count}"
		new_route = shortest_path(graph, s,e)
		route_id = f"route_{veh+count}"
		traci.route.add(route_id, new_route)
		traci.vehicle.add(vehicle_id, route_id,typeID="electric")
		traci.vehicle.setParameter(vehicle_id, "device.battery.actualBatteryCapacity", str(initial_battery))
		a_vehicles.append(vehicle_id)
		count += 1
	return count,a_vehicles

def simulation(vehicles,target):
	for  a in vehicles:
		try:
			update_vehicle_route(graph,a,target)	
		except:
			vehicles.remove(a)

def find_most_important_edges(G):
	edge_betweenness = nx.edge_betweenness_centrality(G, weight='weight', normalized=False)
	sorted_edges = sorted(edge_betweenness.items(), key=lambda x: x[1], reverse=True)
	return sorted_edges


xml = "yastra.net.xml"
cfg = "yastra.sumocfg"
makeevehicletype(xml)

traci.start(["sumo-gui", "-c", cfg])
net = sumolib.net.readNet(xml)
graph = generate(xml)



a_count,simulacion_a= makenevehicles(1000,"A","I",10000)

for iteravi in range(1000):
	carro_id = "amogus_{0}".format(iteravi)
	ruta_id = "amogussy_{0}".format(iteravi)
	traci.route.add(ruta_id, ["qwd","qwdqw"])
	traci.vehicle.add(carro_id, ruta_id)

A = []
B = []
step = 0

max_flow,flow_dict = maximum_flow(graph, "A", "I")


while step < 1000:
	traci.simulationStep()
	update_edge_weights(graph, net)
	simulation(simulacion_a,"I")

	step += 1


traci.close()

