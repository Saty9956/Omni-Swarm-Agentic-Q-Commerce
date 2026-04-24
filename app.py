import streamlit as st
import random
import io
import contextlib
import psycopg2
import os
from dotenv import load_dotenv
from simulation.city_graph import CityGrid
from agents.hub_agent import HubAgent
from agents.rider_agent import RiderAgent

load_dotenv()

# --- Page Config ---
st.set_page_config(page_title="Omni-Swarm", page_icon="🚚", layout="wide")

def get_hubs_from_aws():
    """Fetch persistent hub locations from AWS RDS."""
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'), database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'), password=os.getenv('DB_PASS'), port=os.getenv('DB_PORT')
        )
        cur = conn.cursor()
        cur.execute("SELECT node_coord FROM city_nodes WHERE node_type = 'HUB';")
        hubs = [eval(row[0]) for row in cur.fetchall()]
        conn.close()
        return hubs
    except Exception as e:
        st.error(f"AWS DB Connection Failed: {e}")
        return [(0,0), (5,5)] # Fallback

# --- Initialize System State ---
if 'system_online' not in st.session_state:
    with st.spinner("Connecting to AWS & Initializing City Grid..."):
        st.session_state.city = CityGrid(grid_size=6, num_hubs=2, num_riders=5)
        hub_locs = get_hubs_from_aws()
        st.session_state.hubs = [HubAgent(f"Hub_{i+1}", loc) for i, loc in enumerate(hub_locs)]
        st.session_state.riders = [RiderAgent(rid, loc) for rid, loc in st.session_state.city.riders.items()]
        
        # Initialize Wallets for all riders
        for rider in st.session_state.riders:
            rider.wallet = 0.0
            
        st.session_state.system_online = True

# --- UI Layout ---
st.title("🚚 Omni-Swarm Command Center")
st.caption("Live Multi-Agent Negotiation | Powered by Llama-3, AWS RDS, and AWS S3")
st.divider()

col1, col2 = st.columns([1, 2])

with col1:
    st.header("System Controls")
    st.metric("AWS RDS Status", "Connected 🟢")
    
    st.write("---")
    st.subheader("💰 Zepto/Instamart Economics")
    
    # 1. Base Variables
    base_value = st.slider("Cart Value (₹)", min_value=50, max_value=1000, value=100, step=10)
    
    # FIX: Slider now uses 0.5 km increments
    distance_km = st.slider("Total Distance (km)", min_value=0.5, max_value=15.0, value=2.5, step=0.5)
    
    # 2. Theoretical Delivery Fee Math (₹30 flat up to 4km, +₹5 per extra km)
    extra_km = max(0.0, distance_km - 4.0)
    theoretical_delivery_fee = 30 + (extra_km * 5)

    # 3. Customer Billing Logic
    if base_value >= 199:
        customer_delivery_fee = 0
        st.caption("✨ Cart >= 199: Customer Delivery Fee Waived!")
    else:
        customer_delivery_fee = theoretical_delivery_fee
        st.caption(f"🛒 Customer Delivery Fee Applied: ₹{customer_delivery_fee:.2f}")

    # 4. Surge Modifiers (Customer Pays)
    st.write("**Surge Modifiers**")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        is_raining = st.checkbox("🌧️ Rain (+₹20)")
    with col_b:
        is_high_demand = st.checkbox("🔥 Demand (+₹20)")
    with col_c:
        is_late_night = st.checkbox("🌙 Night (+₹15)")
        
    rain_charge = 20 if is_raining else 0
    demand_charge = 20 if is_high_demand else 0
    night_charge = 15 if is_late_night else 0
    total_surcharges = rain_charge + demand_charge + night_charge

    # ==========================================
    # 📊 THE SPLIT ECONOMICS
    # ==========================================
    
    # A. What the Customer Pays (What the LLM sees)
    customer_total_bill = base_value + customer_delivery_fee + total_surcharges
    
    # B. Company Revenue & Profit 
    product_margin = base_value * 0.20
    gross_revenue = product_margin + customer_delivery_fee + total_surcharges
    
    # C. Rider Payout (The Arbitrage)
    # Company pays 40% of the calculated delivery fee to the rider
    rider_base_pay = theoretical_delivery_fee * 0.40  
    rider_rain_pay = rain_charge  # 100% goes to rider
    rider_demand_pay = demand_charge * 0.50  # 50% split
    rider_night_pay = night_charge * 0.50  # 50% split
    
    actual_rider_payout = rider_base_pay + rider_rain_pay + rider_demand_pay + rider_night_pay
    net_profit = gross_revenue - actual_rider_payout
    
    st.write("---")
    st.write("**Financial Breakdown**")
    
    # FIX: Added clear icons for Rider Earnings vs Company P&L
    metric_col1, metric_col2, metric_col3 = st.columns(3)
    
    metric_col1.metric("🛒 Total Bill", f"₹{customer_total_bill:.2f}")
    metric_col2.metric("🛵 Rider Earns", f"₹{actual_rider_payout:.2f}")
    
    if net_profit >= 0:
        metric_col3.metric("🏢 Company P&L", f"₹{net_profit:.2f}", "+ Profitable")
    else:
        metric_col3.metric("🏢 Company P&L", f"₹{net_profit:.2f}", "- Cash Burn", delta_color="inverse")
    
    st.write("---")
    # 5. Inject into the Swarm
    if st.button("🚨 Drop Custom Order", use_container_width=True, type="primary"):
        hub = random.choice(st.session_state.hubs)
        customer_loc = random.choice([n for n in st.session_state.city.nodes if n not in [h.location for h in st.session_state.hubs]])
        
        st.session_state.current_order = {
            "hub": hub, 
            "customer": customer_loc,
            "display_value": customer_total_bill,
            "actual_payout": actual_rider_payout,
            "company_profit": net_profit
        }

with col2:
    st.header("Live Swarm Activity")
    
    if 'current_order' in st.session_state:
        order = st.session_state.current_order
        hub = order['hub']
        
        st.info(f"**Action:** {hub.hub_id} is requesting a rider for a dropoff at {order['customer']} with Gross Value: ₹{order['display_value']:.2f}.")
        
        with st.status("Agent Negotiation in Progress...", expanded=True) as status:
            f = io.StringIO()
            with contextlib.redirect_stdout(f):
                winner = hub.broadcast_order(st.session_state.city, order['customer'], order['display_value'], st.session_state.riders)
            
            output = f.getvalue()
            
            # Format the output nicely for Streamlit
            for line in output.split('\n'):
                if '✅' in line:
                    st.success(line)
                elif '❌' in line:
                    st.error(line)
                elif '🏆' in line:
                    st.balloons()
                    st.success(f"**{line}**")
                elif line.strip() != "":
                    st.write(line)
            
            # --- THE WALLET DEPOSIT & EARNINGS ICON ---
            if winner:
                winner.wallet += order['actual_payout']
                st.write("---")
                
                # Highlight the Rider's Earnings clearly at the end
                st.success(f"💸 **Delivery Completed by {winner.rider_id}!**\n\n🛵 **Trip Earnings:** ₹{order['actual_payout']:.2f} \n\n💼 **Total Wallet Balance:** ₹{winner.wallet:.2f}")
                
                if order['company_profit'] >= 0:
                    st.info(f"🏢 **Company P&L:** Booked a net profit of **₹{order['company_profit']:.2f}** on this transaction.")
                else:
                    st.error(f"🏢 **Company P&L:** Took a loss of **₹{abs(order['company_profit']):.2f}** on this transaction.")
                    
            status.update(label="Auction Complete! Logs synced to AWS S3.", state="complete", expanded=True)
    else:
        st.write("Waiting for order injection...")