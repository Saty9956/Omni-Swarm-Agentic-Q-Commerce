import networkx as nx
import matplotlib.pyplot as plt
import random

class CityGrid:
    def __init__(self, grid_size=5, num_hubs=2, num_riders=4):
        """
        Initializes the Digital Twin of our delivery zone.
        grid_size=5 creates a 5x5 grid (25 intersections).
        """
        self.size = grid_size
        self.num_hubs = num_hubs
        self.num_riders = num_riders
        
        # 1. Generate the foundational grid
        self.graph = nx.grid_2d_graph(self.size, self.size)
        self.nodes = list(self.graph.nodes())
        
        # 2. Add realistic traffic weights to the roads (edges)
        self._add_traffic_weights()
        
        # 3. Spawn our physical infrastructure and workforce
        self.hubs = []
        self.riders = {}
        self._spawn_entities()

    def _add_traffic_weights(self):
        """Assigns a random traffic weight (1 to 10) to every road."""
        for u, v in self.graph.edges():
            # 1 = clear road, 10 = massive traffic jam
            traffic = random.randint(1, 10)
            self.graph[u][v]['weight'] = traffic

    def _spawn_entities(self):
        """Randomly places Dark Stores (Hubs) and Delivery Partners (Riders) on the grid."""
        # Pick random distinct nodes for hubs
        self.hubs = random.sample(self.nodes, self.num_hubs)
        
        # Pick remaining random nodes for riders
        available_nodes = [n for n in self.nodes if n not in self.hubs]
        rider_nodes = random.sample(available_nodes, self.num_riders)
        
        # Assign a unique ID to each rider
        for i, node in enumerate(rider_nodes):
            self.riders[f"Rider_{i+1}"] = node

    def visualize(self):
        """Renders the city grid so we can see the simulation visually."""
        plt.figure(figsize=(8, 8))
        
        # Coordinates for the grid layout
        pos = {(x, y): (x, -y) for x, y in self.graph.nodes()}
        
        # Draw standard roads (edges) and intersections (nodes)
        edges = self.graph.edges()
        weights = [self.graph[u][v]['weight'] for u, v in edges]
        
        nx.draw_networkx_nodes(self.graph, pos, node_color='lightgray', node_size=300)
        nx.draw_networkx_edges(self.graph, pos, width=2, edge_color=weights, edge_cmap=plt.cm.Blues)
        
        # Draw Hubs (Green Squares)
        nx.draw_networkx_nodes(self.graph, pos, nodelist=self.hubs, node_color='green', node_shape='s', node_size=600, label='Hub (Dark Store)')
        
        # Draw Riders (Orange Triangles)
        nx.draw_networkx_nodes(self.graph, pos, nodelist=list(self.riders.values()), node_color='orange', node_shape='^', node_size=500, label='Riders')
        
        # Labels
        nx.draw_networkx_labels(self.graph, pos, font_size=8, font_color='black')
        
        plt.title("Omni-Swarm: Digital Twin City Grid")
        # Replaces the old legend code
        plt.legend(scatterpoints=1, loc='upper center', bbox_to_anchor=(0.5, -0.05), ncol=2)
        plt.tight_layout() # Ensures everything fits in the window nicely
        plt.show()
        
    def get_fastest_route(self, start_node, target_node):
        """
        Calculates the path with the lowest traffic cost using Dijkstra's Algorithm.
        Returns the path (list of nodes) and the total cost.
        """
        try:
            # This computes both the total cost and the optimal path in one efficient call
            cost, path = nx.single_source_dijkstra(self.graph, start_node, target_node, weight='weight')
            return path, cost
        except nx.NetworkXNoPath:
            return None, float('inf')

    def trigger_order(self):
        """Simulates an order dropping into the system."""
        # 1. Randomly select a starting Hub and a Customer destination
        hub = random.choice(self.hubs)
        customer = random.choice([n for n in self.nodes if n not in self.hubs])
        
        # 2. Calculate the optimal route
        path, cost = self.get_fastest_route(hub, customer)
        
        print("\n" + "="*40)
        print("🚨 NEW ORDER RECEIVED 🚨")
        print(f"📦 Pickup: Hub {hub}")
        print(f"🏠 Dropoff: Customer {customer}")
        print(f"🗺️ Optimal Route: {path}")
        print(f"⏱️ Traffic Cost: {cost}")
        print("="*40 + "\n")
        
        return hub, customer, path
# --- Testing the Environment ---
if __name__ == "__main__":
    import random # Make sure random is imported if it isn't at the top of the file
    
    # ADD THIS LINE: This locks the randomness so the map is identical every time
    random.seed(42) 
    
    print("Initializing City Simulator...")
    city = CityGrid(grid_size=6, num_hubs=2, num_riders=5)
    
    # Trigger a test order before opening the map
    city.trigger_order()
    
    print("Rendering map (Close the window to stop the script)...")
    city.visualize()