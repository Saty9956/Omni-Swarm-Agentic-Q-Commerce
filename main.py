import random
import psycopg2
import os
from dotenv import load_dotenv
from simulation.city_graph import CityGrid
from agents.hub_agent import HubAgent
from agents.rider_agent import RiderAgent

load_dotenv()

def get_hubs_from_aws():
    """Connects to RDS to fetch the persistent world state."""
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASS'),
            port=os.getenv('DB_PORT')
        )
        cur = conn.cursor()
        cur.execute("SELECT node_coord FROM city_nodes WHERE node_type = 'HUB';")
        hubs = [eval(row[0]) for row in cur.fetchall()]
        cur.close()
        conn.close()
        return hubs
    except Exception as e:
        print(f"AWS Error: {e}")
        return [(0,0), (5,5)] # Fallback if DB is offline

def run_production_swarm():
    random.seed(42)
    print("--- 📡 Connecting to AWS Cloud Infrastructure ---")
    
    # 1. Load the physical world
    city = CityGrid(grid_size=6, num_hubs=2, num_riders=5)
    hub_locations = get_hubs_from_aws()
    
    # 2. Spawn Agents
    hubs = [HubAgent(f"Hub_{i+1}", loc) for i, loc in enumerate(hub_locations)]
    riders = [RiderAgent(rid, loc) for rid, loc in city.riders.items()]
    
    print(f"--- 🟢 Swarm Online: {len(hubs)} Hubs found in RDS ---")
    
    # 3. Simulate an order rush (THIS IS THE FOR LOOP)
    for i in range(3):
        print(f"\n========== 📦 ORDER #{i+1} ==========")
        hub_loc = random.choice(hub_locations)
        customer_loc = random.choice([n for n in city.nodes if n not in hub_locations])
        
        # --- GENERATE THE MONEY ---
        order_value = random.randint(100, 1000)
        
        active_hub = next(h for h in hubs if h.location == hub_loc)
        
        # --- PASS THE MONEY TO THE HUB ---
        active_hub.broadcast_order(city, customer_loc, order_value, riders)

if __name__ == "__main__":
    run_production_swarm()