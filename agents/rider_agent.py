import requests
import json
import boto3
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class RiderAgent:
    def __init__(self, rider_id, start_location):
        self.rider_id = rider_id
        self.location = start_location
        self.battery = 100.0
        self.is_busy = False
        self.s3 = boto3.client('s3')
        self.bucket_name = os.getenv('S3_BUCKET_NAME')

    def log_to_blackbox(self, total_cost, order_value, llm_response):
        """Uploads the LLM's thought process to S3 for production auditing."""
        log_entry = {
            "rider_id": self.rider_id,
            "timestamp": datetime.now().isoformat(),
            "environment": {
                "traffic_cost": total_cost,
                "order_value": order_value,
                "battery": self.battery,
                "location": str(self.location)
            },
            "llm_decision": llm_response
        }
        
        file_name = f"logs/{self.rider_id}/{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            self.s3.put_object(
                Bucket=self.bucket_name,
                Key=file_name,
                Body=json.dumps(log_entry, indent=2),
                ContentType='application/json'
            )
        except Exception as e:
            print(f"   ⚠️ S3 Logging Failed: {e}")

    def think(self, total_cost, order_value):
        """
        The Agentic Brain: Uses Chain of Thought to prevent math hallucinations.
        """
        prompt = f"""
        You are an autonomous delivery agent ({self.rider_id}). 
        Traffic cost: {total_cost}
        Order Value: {order_value}

        You must evaluate whether to accept the order based on these rules:
        Rule 1: If Traffic cost is > 40 -> REJECT.
        Rule 2: If Order Value is > 500 -> ACCEPT.
        Rule 3: If Order Value is < 200 AND Traffic cost is > 25 -> REJECT.
        Rule 4: If Order Value is between 200 and 500 AND Traffic cost is > 30 -> REJECT.
        Rule 5: If none of the above REJECT conditions apply -> ACCEPT.

        Before making a final decision, evaluate the rules step-by-step.
        Output your decision STRICTLY in this JSON format:
        {{
            "rule_1_check": "Is traffic > 40? (Yes/No)",
            "rule_2_check": "Is value > 500? (Yes/No)",
            "rule_4_check": "Is value between 200-500 AND traffic > 30? (Yes/No)",
            "accept": true/false,
            "reasoning": "Final conclusion based on the checks above."
        }}
        """
        try:
            response = requests.post('http://localhost:11434/api/generate', 
                json={"model": "llama3", "prompt": prompt, "stream": False, "format": "json"})
            
            result = json.loads(response.json()['response'])
            
            # --- THE BLACK BOX RECORDING ---
            self.log_to_blackbox(total_cost, order_value, result)
            
            # Return the decision and the reasoning
            return result.get('accept', False), result.get('reasoning', "No reasoning provided.")
        except Exception as e:
            return total_cost <= 30, f"Fallback: LLM Offline. Cost: {total_cost}"

    def evaluate_order(self, city, hub_location, customer_location, order_value):
        if self.is_busy:
            return False, "System Override: I am currently on another delivery.", 0
        if self.battery < 15.0:
            return False, "System Override: Battery critically low.", 0

        _, travel_to_hub_cost = city.get_fastest_route(self.location, hub_location)
        _, delivery_cost = city.get_fastest_route(hub_location, customer_location)
        total_cost = travel_to_hub_cost + delivery_cost
        
        accept, reasoning = self.think(total_cost, order_value)
        
        # We now return the cost as well so the Hub can pick the fastest rider among those who accepted
        return accept, reasoning, total_cost
        
    def __str__(self):
        return f"[{self.rider_id} | Loc: {self.location} | Bat: {self.battery}%]"