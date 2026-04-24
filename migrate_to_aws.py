import psycopg2
import os
from dotenv import load_dotenv
from simulation.city_graph import CityGrid

load_dotenv()

def migrate():
    # 1. Connect to AWS RDS
    print("Connecting to Amazon RDS...")
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASS'),
        port=os.getenv('DB_PORT')
    )
    cur = conn.cursor()

    # 2. Create Tables (The Schema)
    print("Creating logistics tables...")
    cur.execute("DROP TABLE IF EXISTS city_nodes;")
    cur.execute("""
        CREATE TABLE city_nodes (
            id SERIAL PRIMARY KEY,
            node_coord VARCHAR(20),
            node_type VARCHAR(20) -- 'HUB', 'CUSTOMER', or 'INTERSECTION'
        );
    """)
    
    # 3. Generate our local city and push to Cloud
    city = CityGrid(grid_size=6, num_hubs=2, num_riders=5)
    
    for node in city.nodes:
        node_type = 'INTERSECTION'
        if node in city.hubs: node_type = 'HUB'
        
        cur.execute(
            "INSERT INTO city_nodes (node_coord, node_type) VALUES (%s, %s)",
            (str(node), node_type)
        )

    conn.commit()
    print("✅ Migration Successful! Your city grid now lives in the AWS Cloud.")
    cur.close()
    conn.close()

if __name__ == "__main__":
    migrate()