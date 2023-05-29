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

def makeevehicletype(network):
	A = sumolib.vehicletype.CreateVehTypeDistribution(name="electDist",size=1)
	Attr = [sumolib.vehicletype.VehAttribute("id",False,attribute_value="electric"),
			sumolib.vehicletype.VehAttribute("has.battery.device",True,attribute_value="true"),
			sumolib.vehicletype.VehAttribute("maximumBatteryCapacity",True,attribute_value="2000"),
			sumolib.vehicletype.VehAttribute("stoppingThreshold",True,attribute_value="0.1")]
	for i in Attr:
		A.add_attribute(i)
	A.to_xml(network)

def get_node_from_edge_id(graph, edge_id):
    for u, v, data in graph.edges(data=True):
        if data['id'] == edge_id:
            return v
    return None

def shortest_path_to_station(graph, start_edge):
    start_node = get_node_from_edge_id(graph, start_edge)
    charging_nodes = {v for u, v, d in graph.edges(data=True) if d.get('charging_station')}
    if not charging_nodes:
        return None  
    target_node = min(charging_nodes, key=lambda node: nx.dijkstra_path_length(graph, start_node, node))
    path = nx.dijkstra_path(graph, start_node, target_node)
    edges = [(path[i], path[i+1]) for i in range(len(path)-1)]
    edge_ids = [graph[path[i]][path[i+1]]['id'] for i in range(len(path)-1)]
    print([start_edge]+ edge_ids)
    return [start_edge]+ edge_ids 


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
    battery_level = traci.vehicle.getParameter(vehicle_id, 'device.battery.actualBatteryCapacity')
    if float(battery_level) <= 0.25:
        traci.vehicle.setRoute(vehicle_id,shortest_path_to_station(graph,current_edge_id))
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
	return a_vehicles

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

def get_nodes_from_edge_id(graph, edge_id):
    for u, v, data in graph.edges(data=True):
        if data['id'] == edge_id:
            return u, v
    return None, None





xml = "charge.net.xml"
cfg = "charge.sumocfg"
makeevehicletype(xml)

traci.start(["sumo-gui", "-c", cfg])
net = sumolib.net.readNet(xml)
graph = generate(xml)



CHARGING_STATIONS = ['E63', 'E62'] 

for edge_id in CHARGING_STATIONS:
    u, v = get_nodes_from_edge_id(graph, edge_id)
    if u is not None and v is not None:
        graph[u][v]['charging_station'] = True

simulacion_a= makenevehicles(1000,"J53","J60",1)


step = 0


while step < 1000:
	traci.simulationStep()
	update_edge_weights(graph, net)
	simulation(simulacion_a,"J60")

	step += 1


traci.close()
