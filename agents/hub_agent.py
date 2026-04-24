class HubAgent:
    def __init__(self, hub_id, location):
        self.hub_id = hub_id
        self.location = location

    def broadcast_order(self, city, customer_location, order_value, riders):
        """
        Sends an order out to the swarm and collects bids.
        Now includes the Order Value (ROI) in the broadcast.
        """
        print(f"\n[Hub {self.hub_id}] 📢 Broadcasting order to {customer_location} | Order Value: ₹{order_value}")
        
        bids = []
        for rider in riders:
            # We now pass order_value to the rider
            success, reasoning, cost = rider.evaluate_order(city, self.location, customer_location, order_value)
            
            if success:
                print(f"   ✅ {rider.rider_id} accepted: {reasoning}")
                bids.append({'rider': rider, 'cost': cost})
            else:
                print(f"   ❌ {rider.rider_id} rejected: {reasoning}")

        # Dispatch the most efficient rider among those who accepted
        if bids:
            best_bid = min(bids, key=lambda x: x['cost'])
            winner = best_bid['rider']
            print(f"🏆 Dispatching {winner.rider_id} for the delivery!")
            winner.is_busy = True # Mark rider as busy
            return winner
        else:
            print("⚠️ No riders available or willing to take this order!")
            return None