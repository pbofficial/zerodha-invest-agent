import os
import json
import sys
import math
import time
from datetime import datetime

import streamlit as st
import pandas as pd
import subprocess
from google.cloud import firestore
from kiteconnect import KiteConnect

# Resolve absolute paths first!
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
if project_root not in sys.path:
    sys.path.append(project_root)

from src.functions.market_data.main import is_market_open

# --- 🚀 GLOBAL LOGGING CONFIG ---
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger("Dashboard")
logger.info("🎬 Dashboard Application Powering Up...")

# Handle Project Discovery
from src.utils.project import get_project_id, get_dashboard_url
project_id = get_project_id()
if project_id:
    os.environ["PROJECT_ID"] = project_id
else:
    st.warning("⚠️ PROJECT_ID not found in environment, config, or via ADC. Cloud features may fail.")

dashboard_url = get_dashboard_url()

# Set up page config
st.set_page_config(page_title="Intelligent Investment Agent", page_icon="📈", layout="wide")

# Market Status Check
is_open, status_reason = is_market_open()
status_emoji = "🟢" if is_open else "🔴"
st.sidebar.markdown(f"### Market Status: {status_emoji} **{status_reason}**")
st.sidebar.divider()

# --- 🎨 Custom Theme Injection ---
st.markdown("""
    <style>
    /* Global Background & Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    
    .stApp {
        background-color: #0B0E14 !important;
        background-image: 
            radial-gradient(at 0% 0%, rgba(255, 87, 34, 0.1) 0, transparent 50%), 
            radial-gradient(at 50% 0%, rgba(212, 175, 55, 0.05) 0, transparent 50%),
            radial-gradient(at 100% 100%, rgba(255, 87, 34, 0.05) 0, transparent 50%);
        font-family: 'Inter', sans-serif;
    }

    /* 🔐 Global Login Styles */
    .login-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 60px;
        background: rgba(255, 255, 255, 0.03) !important;
        backdrop-filter: blur(20px) !important;
        border: 1px solid rgba(212, 175, 55, 0.3) !important;
        border-radius: 32px !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.8), 0 0 15px rgba(212, 175, 55, 0.1) !important;
        max-width: 550px;
        margin: 100px auto;
        text-align: center;
    }

    .login-header {
        color: #D4AF37 !important;
        font-weight: 800 !important;
        font-size: 2.5rem !important;
        margin-bottom: 10px !important;
        letter-spacing: -1px !important;
    }

    .login-subtitle {
        color: rgba(255, 255, 255, 0.6) !important;
        font-size: 1.1rem !important;
        margin-bottom: 40px !important;
    }

    .login-button {
        display: inline-block !important;
        background: linear-gradient(135deg, #FF8F00 0%, #FF5722 50%, #D4AF37 100%) !important;
        color: white !important;
        padding: 18px 52px !important;
        border-radius: 16px !important;
        font-weight: 800 !important;
        font-size: 1.3rem !important;
        text-decoration: none !important;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        box-shadow: 0 10px 30px rgba(255, 87, 34, 0.4), 0 0 15px rgba(212, 175, 55, 0.2) !important;
        border: none !important;
        outline: none !important;
        text-align: center !important;
        min-width: 280px !important;
    }

    .login-button:hover {
        transform: translateY(-3px) scale(1.02) !important;
        box-shadow: 0 8px 25px rgba(255, 87, 34, 0.5) !important;
        color: white !important;
    }

    /* 📊 Glassmorphic Metrics */
    [data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.03) !important;
        backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 20px !important;
        padding: 24px !important;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3) !important;
    }

    [data-testid="stMetricValue"] {
        color: #D4AF37 !important;
        font-size: 2rem !important;
        font-weight: 800 !important;
    }

    /* 📦 Table & Data Editor Modernization */
    .stDataFrame, .stDataEditor {
        background: rgba(255, 255, 255, 0.02) !important;
        border-radius: 16px !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
    }

    /* 🧭 Navigation Tab Refinement */
    .stTabs [data-baseweb="tab-list"] {
        gap: 32px !important;
        padding: 0 20px !important;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: transparent !important;
        color: rgba(255, 255, 255, 0.5) !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
        border: none !important;
        padding: 12px 0 !important;
    }

    .stTabs [aria-selected="true"] {
        color: #D4AF37 !important;
        border-bottom: 3px solid #D4AF37 !important;
        text-shadow: 0 0 10px rgba(212, 175, 55, 0.4) !important;
    }

    /* Hide Streamlit elements */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# Helper to load secrets for Login
def get_secrets():
    try:
        from src.utils.secrets import get_secret
        return get_secret("KITE_API_KEY"), get_secret("KITE_API_SECRET")
    except: return None, None

# --- DATABASE INITIALIZATION (Moved up for Remote Actions) ---
@st.cache_resource
def get_db():
    try:
        project_id = os.environ.get("PROJECT_ID")
        return firestore.Client(project=project_id)
    except Exception as e:
        st.error(f"Firestore Initialization Failed: {e}")
        return None

db = get_db()

# --- Authenticated App Flows (Helpers) ---
def handle_remote_actions():
    params = st.query_params.to_dict()
    logger.info(f"🔄 Checking for remote actions. Current params: {params}")
    
    # Handle potentially multi-valued 'action' param (Zerodha often appends ?action=login)
    all_actions = st.query_params.get_all("action") 
    action = None
    if "approve_batch" in all_actions: action = "approve_batch"
    elif "reject_batch" in all_actions: action = "reject_batch"
    
    if action:
        logger.info(f"🎯 Action identified: {action}")
        try:
            pending_ref = db.collection("pending_orders").document("latest")
            pending_doc = pending_ref.get()
            pending_data = pending_doc.to_dict() if pending_doc.exists else {}
            orders = pending_data.get("orders", [])
            total_amt = sum((o.get("quantity", 0) * o.get("price", 0)) for o in orders)
            order_summary = f"({len(orders)} symbols, ~₹{total_amt:,.0f})"

            if action == "approve_batch":
                pending_ref.update({"status": "APPROVED", "approved_at": firestore.SERVER_TIMESTAMP})
                st.session_state["remote_feedback"] = ("success", f"✅ Batch Approved {order_summary}")
            elif action == "reject_batch":
                pending_ref.update({"status": "DRAFT"})
                st.session_state["remote_feedback"] = ("warning", f"🛑 Batch Reset to Draft {order_summary}")
            
            # CLEAR ALL action params to prevent replay
            if "action" in st.query_params:
                del st.query_params["action"]
            # Rerun to clean UI
            st.rerun()
        except Exception as e:
            st.error(f"Remote Action Failed: {e}")

    # Display feedback if exists
    if "remote_feedback" in st.session_state:
        type_str, msg = st.session_state.pop("remote_feedback")
        if type_str == "success": st.success(msg)
        else: st.warning(msg)
        st.toast(msg, icon="🛰️")

# --- 🔐 Authentication Flow ---
api_key, api_secret = get_secrets()

if "kite_token" not in st.session_state:
    # Check for callback
    query_params = st.query_params.to_dict()
    logger.info(f"🔑 Auth Flow Init. URL Params: {query_params}")
    req_token = query_params.get("request_token")
    
    if req_token:
        logger.info(f"🎟️ Detected request_token. Converting to session... (Action: {query_params.get('action')})")
        try:
            kite = KiteConnect(api_key=api_key)
            data = kite.generate_session(req_token, api_secret=api_secret)
            
            # --- USER PINNING ---
            from src.utils.secrets import get_secret
            allowed_user = get_secret("ALLOWED_USER_ID")
            actual_user = data.get("user_id")
            
            if allowed_user and actual_user != allowed_user:
                st.error("⛔ Access Denied: This dashboard is pinned to a specific Zerodha account.")
                st.stop()
            
            st.session_state["kite_token"] = data["access_token"]
            st.session_state["user_id"] = actual_user
            
            # --- PERSIST TOKEN FOR BACKGROUND JOBS ---
            from src.utils.secrets import save_secret
            success = save_secret("KITE_ACCESS_TOKEN", data["access_token"])
            if success:
                st.toast("✅ Session Synced to Cloud Secret Manager", icon="🛰️")
                logger.info("🔐 Kite session synced to Cloud Secret Manager successfully.")
            else:
                st.error("⚠️ Failed to sync session to Cloud. Background trades may fail.")
                logger.error("❌ Failed to sync Kite session to Cloud Secret Manager.")
            
            # --- COMPREHENSIVE URL CLEANUP ---
            # Remove Zerodha callback noise (request_token, status, type)
            # but preserve our 'action' if it was part of the original request
            for k in ["request_token", "status", "type"]:
                if k in st.query_params:
                    del st.query_params[k]
            
            # Special case: Zerodha sometimes appends action=login. Clear ONLY that specific value.
            all_actions = st.query_params.get_all("action")
            if "login" in all_actions:
                # If it's a list, remove just 'login'
                remaining = [a for a in all_actions if a != "login"]
                if remaining:
                    st.query_params["action"] = remaining
                else:
                    del st.query_params["action"]

            # Streamlit rerun will reflect new state
            st.rerun()
        except Exception as e:
            # Store error and force refresh to clear URL params
            st.session_state["login_error"] = str(e)
            st.query_params.clear()
            st.rerun()
    else:
        # Show Modern Login Screen
        kite = KiteConnect(api_key=api_key)
        
        # --- DYNAMIC REDIRECT (Local vs Cloud) ---
        
        # Determine redirect base
        if not os.environ.get("K_SERVICE"):
            redirect_base = "http://localhost:8501/"
        else:
            # Ensure trailing slash for Zerodha registration consistency
            redirect_base = dashboard_url if dashboard_url.endswith("/") else f"{dashboard_url}/"

        # Build final login URL with preserved parameters
        final_login_url = kite.login_url()
        action = st.query_params.get("action")
        
        # Append redirect_url to kite login URL
        redirect_param = redirect_base
        if action:
            redirect_param = f"{redirect_base}?action={action}"
        
        import urllib.parse
        logger.info(f"🔗 Constructing Login URL. Base: {redirect_base} | Action: {action} | Full Redirect: {redirect_param}")
        
        if "?" in final_login_url:
            final_login_url += f"&redirect_url={urllib.parse.quote(redirect_param)}"
        else:
            final_login_url += f"?redirect_url={urllib.parse.quote(redirect_param)}"
             
        login_html = f"""
<div class="login-container">
<div style="font-size: 4rem; margin-bottom: 20px;">⚡</div>
<div class="login-header">Intelligent Investment Agent</div>
<div class="login-subtitle">A secure, AI-powered gateway to your Private Allocation Desk.</div>
{"<div style='color: #ff4b4b; background: rgba(255,75,75,0.1); padding: 10px; border-radius: 8px; margin-bottom: 20px;'>⚠️ " + st.session_state['login_error'] + "</div>" if "login_error" in st.session_state else ""}
<a href="{final_login_url}" target="_self" class="login-button">
🔐 Login via Zerodha Kite
</a>
<div style="margin-top: 30px; font-size: 0.8rem; color: rgba(255,255,255,0.4);">
Powered by Vertex AI & Zerodha Kite Connect
</div>
</div>
"""
        st.markdown(login_html, unsafe_allow_html=True)
        
        if "login_error" in st.session_state:
            del st.session_state["login_error"]
            
        st.stop() # Stop here until logged in

# Authenticated App Starts Here
# Database initialized globably at top of file
universe_ref = db.collection("config").document("universe") if db else None

# Handle Actions only AFTER authentication is established
handle_remote_actions()

def load_universe():
    """Uses the Unified Cloud Loader for all data fetch."""
    from src.utils.config_loader import config as cloud_config
    return cloud_config.get_universe(force_refresh=True)

def save_universe(data):
    """Saves universe data directly to Cloud Firestore."""
    if universe_ref:
        try: universe_ref.set(data)
        except: pass

def paginate_dataframe(df, key, items_per_page=10):
    if df.empty: return df, 1, 1
    total_pages = math.ceil(len(df) / items_per_page)
    page_key = f"page_{key}"
    if page_key not in st.session_state: st.session_state[page_key] = 1
    col_p1, col_p2 = st.columns([1, 4])
    page = col_p1.selectbox(f"Page ({key})", range(1, total_pages + 1), index=st.session_state[page_key]-1, key=page_key)
    start_idx = (page - 1) * items_per_page
    return df.iloc[start_idx : start_idx + items_per_page], page, total_pages

# --- ADVISOR INTEGRATION ---
def get_advisor():
    from src.agent.advisor import InvestmentAdvisor
    return InvestmentAdvisor()

def format_agent_logs(raw_logs):
    """Parses raw subprocess logs into a clean, markdown 'Logic Stream'."""
    if not raw_logs: return "No logs available."
    
    clean_lines = []
    lines = raw_logs.split("\n")
    
    for line in lines:
        # 1. Extract Model Thoughts
        if "AGENT THOUGHT:" in line:
            thought = line.split("AGENT THOUGHT:")[1].strip()
            if thought: clean_lines.append(f"🔍 *{thought}*")
        
        # 2. Extract Final Summaries
        elif "AGENT FINAL THOUGHT:" in line:
            summary = line.split("AGENT FINAL THOUGHT:")[1].strip()
            if summary: clean_lines.append(f"✅ **{summary}**")
            
        # 3. Highlight Tool Usage (Human Readable)
        elif "Model requesting tool:" in line:
            tool_name = line.split("Model requesting tool:")[1].strip()
            # Beautify tool names
            tool_map = {
                "get_market_news": "Global News Pulse",
                "check_financial_health": "Fundamental Audit",
                "get_market_snapshot": "Live Price Feed",
                "calculate_orders": "Allocation Engine",
                "save_draft_proposal": "Drafting Plan"
            }
            display_name = tool_map.get(tool_name, tool_name.replace("_", " ").title())
            clean_lines.append(f"🛠️ *Invoking {display_name}...*")

        elif "Tool" in line and "executed successfully" in line:
            continue # Skip noise

        # 4. Critical Errors
        elif "ERROR" in line or "CRITICAL" in line:
             if "AGENT THOUGHT" not in line and "FINAL THOUGHT" not in line:
                clean_lines.append(f"⚠️ `{line.strip()}`")

    if not clean_lines:
        return "⚠️ *Process started... filtering technical metadata.*"
        
    return "\n\n".join(clean_lines)

# Load State
data = load_universe()
assets = data.get("assets", [])
settings = data.get("settings", {})
assets_df = pd.DataFrame(assets)

# Robust Column Check
for col in ["ticker", "sector", "cap_type", "type", "target_amount", "target_weight"]:
    if col not in assets_df.columns:
        assets_df[col] = 100000 if col == "target_amount" else (0.0 if col == "target_weight" else "Unknown")

with st.sidebar:
    st.info(f"👤 {st.session_state.get('user_id', 'User')}")
    if st.button("🔄 Refresh Market Data", use_container_width=True):
        st.cache_data.clear()
        st.success("Cache Cleared!")
        st.rerun()
    st.divider()

st.caption(f"Logged in as: {st.session_state.get('user_id', 'User')} | ✅ Connected to Kite")

# Fetch Live Data
@st.cache_data(ttl=300)
def fetch_live_data(tickers):
    try:
        os.environ["KITE_ACCESS_TOKEN"] = st.session_state["kite_token"]
        from src.functions.market_data.main import is_market_open, get_market_snapshot
        return get_market_snapshot(tickers)
    except Exception as e:
        return None

def normalize_t(t): return t.split(":")[-1].upper() if ":" in t else t.upper()

# Initialize Navigation
if "active_tab" not in st.session_state:
    st.session_state["active_tab"] = "📈 Portfolio"

st.markdown("""
    <style>
    .stHorizontalBlock div[style*="flex-direction: row"] {
        gap: 1rem;
    }
    .nav-btn {
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

nav_col1, nav_col2, nav_col3, nav_col4 = st.columns(4)
with nav_col1:
    if st.button("📈 Portfolio", use_container_width=True, type="primary" if st.session_state["active_tab"] == "📈 Portfolio" else "secondary"):
        st.session_state["active_tab"] = "📈 Portfolio"
        st.rerun()
with nav_col2:
    if st.button("🎯 Trading Desk", use_container_width=True, type="primary" if st.session_state["active_tab"] == "🎯 Trading Desk" else "secondary"):
        st.session_state["active_tab"] = "🎯 Trading Desk"
        st.rerun()
with nav_col3:
    if st.button("🧠 AI Insights", use_container_width=True, type="primary" if st.session_state["active_tab"] == "🧠 AI Insights" else "secondary"):
        st.session_state["active_tab"] = "🧠 AI Insights"
        st.rerun()
with nav_col4:
    if st.button("⚙️ Config", use_container_width=True, type="primary" if st.session_state["active_tab"] == "⚙️ Config" else "secondary"):
        st.session_state["active_tab"] = "⚙️ Config"
        st.rerun()

st.divider()

# --- 1. First Pass: Get Holdings to identify all tickers ---
@st.cache_data(ttl=300)
def get_all_portfolio_tickers(universe_tickers):
    res = fetch_live_data(universe_tickers)
    holdings = res.get("holdings", [])
    h_tickers = [h["tradingsymbol"] for h in holdings]
    return list(set(universe_tickers + h_tickers))

portfolio_tickers = get_all_portfolio_tickers(assets_df["ticker"].tolist())

# --- 2. Second Pass: Fetch full snapshot with metadata for all ---
live_res = fetch_live_data(portfolio_tickers)
live_metadata = live_res.get("metadata", {}) if live_res else {}
live_prices = live_res.get("prices", {}) if live_res else {}
holdings_df = pd.DataFrame(live_res.get("holdings", [])) if live_res else pd.DataFrame()

# Metadata & Processing
# 1. Gather all tickers that need metadata
all_tickers = set(portfolio_tickers)

# 2. Map metadata to a lookup for quick access
meta_lookup = {}
if live_metadata:
    for ticker in all_tickers:
        if ticker in live_metadata:
            meta_lookup[normalize_t(ticker)] = live_metadata[ticker]

# 3. Apply to Assets (Universe)
for idx, row in assets_df.iterrows():
    norm = normalize_t(row["ticker"])
    if norm in meta_lookup:
        meta = meta_lookup[norm]
        assets_df.at[idx, "sector"] = meta.get("sector", row["sector"])
        new_cap = meta.get("cap_type")
        if new_cap and new_cap != "Unknown":
            assets_df.at[idx, "cap_type"] = new_cap
        assets_df.at[idx, "beta"] = meta.get("risk_beta", 1.0)

# 4. Apply to Holdings (Full Portfolio)
if not holdings_df.empty:
    holdings_df["norm_ticker"] = holdings_df["tradingsymbol"].apply(normalize_t)
    holdings_df["current_value"] = holdings_df["quantity"] * holdings_df["last_price"]
    holdings_df["invested_cost"] = holdings_df["quantity"] * holdings_df["average_price"]
    holdings_df["pnl_pct"] = (holdings_df["pnl"] / (holdings_df["invested_cost"] + 1e-6)) * 100
    
    universe_norm_tickers = {normalize_t(t) for t in assets_df["ticker"].unique()}
    holdings_df["classification"] = holdings_df["norm_ticker"].apply(lambda x: "✅ Core" if x in universe_norm_tickers else "⚠️ Sell")
    
    # Enrich holdings with metadata even if not in universe
    for idx, row in holdings_df.iterrows():
        norm = row["norm_ticker"]
        if norm in meta_lookup:
            meta = meta_lookup[norm]
            holdings_df.at[idx, "sector"] = meta.get("sector", "Other")
            holdings_df.at[idx, "cap_type"] = meta.get("cap_type", "Unknown")
        else:
            # Fallback for those not in meta_lookup (unlikely but safe)
            holdings_df.at[idx, "sector"] = holdings_df.at[idx, "sector"] if "sector" in holdings_df.columns else "Legacy/Other"
            holdings_df.at[idx, "cap_type"] = holdings_df.at[idx, "cap_type"] if "cap_type" in holdings_df.columns else "Unknown"

    holdings_df["sector"] = holdings_df["sector"].fillna("Legacy/Other")
    holdings_df["cap_type"] = holdings_df["cap_type"].fillna("Unknown")

    # 5. Merge with Assets to get 'type' and target weights (Robust normalization)
    assets_df["norm_ticker"] = assets_df["ticker"].apply(normalize_t)
    holdings_df = holdings_df.merge(assets_df[["norm_ticker", "type", "target_amount", "target_weight"]], on="norm_ticker", how="left", suffixes=('', '_asset'))
    holdings_df["type"] = holdings_df["type"].fillna("Core") # Default type

# --- Render Active Tab ---
if st.session_state["active_tab"] == "📈 Portfolio":
    if not holdings_df.empty:
        total_inv = holdings_df["invested_cost"].sum()
        total_cur = holdings_df["current_value"].sum()
        pnl_pct = ((total_cur - total_inv) / (total_inv + 1e-6)) * 100
        
        # --- 1. Top-Level Metrics Bar ---
        m1, m2, m3, m4 = st.columns(4)
        with m1: st.metric("Total Invested", f"₹{total_inv:,.0f}")
        with m2: st.metric("Current Value", f"₹{total_cur:,.0f}", delta=f"₹{total_cur - total_inv:,.0f}")
        with m3: st.metric("Unrealized P&L", f"{pnl_pct:.2f}%", delta=f"{pnl_pct:.2f}%", delta_color="normal")
        
        with m4:
            high_risk_pct = (holdings_df[holdings_df["type"]=="High Risk"]["current_value"].sum() / (total_cur+1e-6)) * 100
            if high_risk_pct > 20:
                st.metric("🛡️ Risk Profile", "High Risk", delta=f"{high_risk_pct:.1f}% exp.", delta_color="inverse")
            else:
                st.metric("🛡️ Risk Profile", "Conservative", delta=f"{high_risk_pct:.1f}% exp.", delta_color="normal")
        
        st.divider()

        # --- 2. Main Content Split ---
        col_main, col_side = st.columns([3, 1], gap="large")
        
        with col_main:
            st.markdown("### 📋 Portfolio Holdings")
            # Calculate height to show all rows
            table_height = (len(holdings_df) + 1) * 35 + 40
            st.dataframe(
                holdings_df[["tradingsymbol", "classification", "quantity", "invested_cost", "current_value", "pnl_pct"]].rename(columns={
                    "tradingsymbol": "Symbol", "classification": "Status", "quantity": "Qty", "invested_cost": "Cost Basis", "current_value": "Market Val", "pnl_pct": "% Chg"
                }), hide_index=True, use_container_width=True, height=table_height
            )

        with col_side:
            st.markdown("### 📊 Distribution")
            
            # Use horizontal bars for better readability
            st.write("**Sector Weightage**")
            sector_data = holdings_df.groupby("sector")["current_value"].sum().sort_values(ascending=True)
            st.bar_chart(sector_data, horizontal=True, color="#D4AF37", height=400)
            
            st.markdown("<br><br>", unsafe_allow_html=True) # Large Spacer
            
            st.write("**Market Cap Mix**")
            cap_data = holdings_df.groupby("cap_type")["current_value"].sum().sort_values(ascending=True)
            st.bar_chart(cap_data, horizontal=True, color="#FF5722", height=300)
            
            # st.divider()
            # high_risk_pct = (holdings_df[holdings_df["type"]=="High Risk"]["current_value"].sum() / (total_cur+1e-6)) * 100
            # st.markdown("#### 🛡️ Risk Profile")
            # if high_risk_pct > 20: 
            #     st.warning(f"⚠️ **High Risk Exposure**: {high_risk_pct:.1f}%")
            # else: 
            #     st.success(f"✅ **Conservative**: {high_risk_pct:.1f}% exposure")
    else:
        st.info("No holdings found.")

elif st.session_state["active_tab"] == "🎯 Trading Desk":
    # 🏛️ DESK HEADER
    c_head1, c_head2 = st.columns([4, 1])
    with c_head1: st.markdown("## ⚡ Intelligent Trading Desk")
    with c_head2: st.markdown("<div style='text-align:right; color:#D4AF37; font-size:0.9rem; margin-top:2rem;'>SYSTEM V5.3 | ACTIVE</div>", unsafe_allow_html=True)
    
    # --- 1. Core State & Data Prep ---
    pending_ref = db.collection("pending_orders").document("latest")
    pending_doc = pending_ref.get()
    pending_data = pending_doc.to_dict() if pending_doc.exists else {}
    status = pending_data.get("status", "NONE")
    rebalance_id = pending_data.get("rebalance_id", "OLD")
    
    if status in ["DRAFT", "QUEUED", "APPROVED", "COMPLETED"]:
        # 1. Check for UI Snapshot (Maintained state)
        ui_snapshot = pending_data.get("ui_snapshot")
        
        if ui_snapshot:
            desk_df = pd.DataFrame(ui_snapshot)
            # Ensure LTP remains live for accuracy, but all other columns stay as snapped
            for idx, row in desk_df.iterrows():
                t = row["ticker"]
                if t in live_prices:
                    desk_df.at[idx, "LTP (₹)"] = live_prices[t]
                    desk_df.at[idx, "Est. Cost (₹)"] = row["Buy Qty"] * live_prices[t]
        else:
            # Reconstruct from Assets + Analysis (Fallback/Initial)
            draft_orders = pending_data.get("orders", [])
            def normalize_t(t): return t.split(":")[-1].upper() if ":" in t else t.upper()
            draft_map = {normalize_t(o["ticker"]): o for o in draft_orders if "ticker" in o}

            desk_rows = []
            for asset in assets:
                ticker = asset["ticker"]
                live_price = live_prices.get(ticker, 0.0)
                curr_qty, avg_price, hold_val = 0, 0.0, 0.0
                if not holdings_df.empty:
                    matches = holdings_df[holdings_df["tradingsymbol"] == ticker]
                    if not matches.empty:
                        curr_qty = matches.iloc[0]["quantity"]
                        avg_price = matches.iloc[0]["average_price"]
                        hold_val = matches.iloc[0].get("current_value", curr_qty * live_price)
                
                target_amt = asset.get("target_amount", 0)
                cost_basis = curr_qty * avg_price
                gap = target_amt - cost_basis
                
                ai_signal, ai_reason, sugg_qty = "⚪ WAIT", "No Analysis", 0
                norm_ticker = ticker.split(":")[-1].upper() if ":" in ticker else ticker.upper()
                if norm_ticker in draft_map:
                    d = draft_map[norm_ticker]
                    ai_signal = d.get("signal", "⚪ WAIT")
                    ai_reason = d.get("reason", "")
                    sugg_qty = d.get("quantity", 0)
                    if live_price == 0: live_price = d.get("price", 0.0)
                
                signal_icon = "⚪"
                if any(k in ai_signal for k in ["STRONG_BUY", "🌟"]): signal_icon = "🌟 BUY"
                elif any(k in ai_signal for k in ["BUY", "✅"]): signal_icon = "✅ BUY"
                elif any(k in ai_signal for k in ["ACCUMULATE", "➕", "ADD"]): signal_icon = "➕ ADD"
                elif any(k in ai_signal for k in ["HOLD", "⏸️"]): signal_icon = "⏸️ HOLD"
                elif any(k in ai_signal for k in ["SELL", "⚠️"]): signal_icon = "⚠️ SELL"

                desk_rows.append({
                    "ticker": ticker, "LTP (₹)": live_price, "Hold Val (₹)": hold_val,
                    "Current Qty": curr_qty, "Target (₹)": target_amt, "Gap (₹)": gap,
                    "AI Signal": signal_icon, "AI Rationale": ai_reason,
                    "Suggested Qty": sugg_qty, "Buy Qty": sugg_qty, "Est. Cost (₹)": sugg_qty * live_price
                })
            
            desk_df = pd.DataFrame(desk_rows)
            # --- AUTO-SAVE SNAPSHOT FOR PERSISTENCE ---
            # Now that we've built the table from orders/assets, save it so it survives rejections/clears
            try:
                pending_ref.update({"ui_snapshot": desk_df.to_dict(orient="records")})
                logger.info("💾 Auto-saved UI Snapshot to Firestore for persistence.")
            except Exception as e:
                logger.warning(f"Failed to auto-save snapshot: {e}")
        
        # --- 📈 FULL-WIDTH CHART (Toggleable) ---
        show_chart = st.checkbox("📊 Show Comparative Vision Chart", value=True)
        if show_chart:
            total_port_val = desk_df["Hold Val (₹)"].sum()
            chart_data = desk_df[["ticker"]].copy()
            chart_data["Vision (Target %)"] = (desk_df["Target (₹)"] / (desk_df["Target (₹)"].sum() + 1e-6)) * 100
            chart_data["Current (Actual %)"] = (desk_df["Hold Val (₹)"] / (total_port_val + 1e-6)) * 100
            st.bar_chart(chart_data.set_index("ticker"), color=["#D4AF37", "#FF5722"], height=250)
            st.divider()

        # --- 🏛️ THREE-COLUMN WORKSPACE ROW ---
        col_main, col_ctrl, col_logs = st.columns([3, 1, 1], gap="medium")

        # --- 2. Workspace Tabs Layout ---
        with col_ctrl:
            st.markdown("### ⚙️ Controls")
            default_budget = settings.get("budget", 12500.0)
            invest_amt = st.number_input("💰 Allocation Budget (₹)", min_value=1000.0, value=float(default_budget), step=500.0)

            # --- Action Bar ---
            if st.button("🚀 Run Analysis", type="primary", use_container_width=True):
                if "desk_edits" in st.session_state: del st.session_state["desk_edits"]
                # DO NOT clear orders here! Keep current queue visible until fresh analysis completes.
                pending_ref.update({
                    "status": "DRAFT"
                })
                with st.spinner("🤖 Analyzing..."):
                    import subprocess
                    cmd = [sys.executable, os.path.join(project_root, "src", "agent", "main.py"), "--auto", "--budget", str(invest_amt), "--skip-notify"]
                    env = os.environ.copy()
                    env["KITE_ACCESS_TOKEN"] = st.session_state["kite_token"]
                    env["PROJECT_ID"] = project_id
                    env["DASHBOARD_URL"] = dashboard_url
                    try:
                        logger.info(f"🤖 Starting Analysis Subprocess: Budget={invest_amt}")
                        result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)
                        logger.info("✅ Analysis Subprocess Completed Successfully.")
                        st.session_state["agent_logs"] = result.stdout
                        if result.stderr: 
                            logger.warning(f"⚠️ Analysis Subprocess StdErr: {result.stderr}")
                            st.session_state["agent_logs"] += f"\n{result.stderr}"
                        if "agent_summary" in st.session_state: del st.session_state["agent_summary"]
                        
                        # Increment refresh counter to force editor reset
                        st.session_state["desk_refresh_count"] = st.session_state.get("desk_refresh_count", 0) + 1
                        
                        time.sleep(1.0) # Brief pause for Firestore propagate
                        st.rerun()
                    except subprocess.CalledProcessError as e:
                        logger.error(f"❌ Analysis Subprocess Failed: {str(e)}")
                        error_msg = f"Failed: {e}"
                        if e.stderr: error_msg += f"\n\nDetails:\n{e.stderr}"
                        st.error(error_msg)
                    except Exception as e:
                        logger.error(f"❌ Analysis Subprocess Failed: {str(e)}")
                        st.error(f"Failed: {e}")

            st.divider()

        with col_logs:
            st.markdown("### 🧠 Logic Stream")
            if "agent_logs" in st.session_state:
                if "agent_summary" not in st.session_state:
                    try:
                        advisor = get_advisor()
                        st.session_state["agent_summary"] = advisor.summarize_run_logic(st.session_state["agent_logs"])
                    except Exception as e:
                        st.session_state["agent_summary"] = f"Summary failed: {str(e)}"
                
                st.markdown(f"<div style='font-size: 0.85rem;'>{st.session_state['agent_summary']}</div>", unsafe_allow_html=True)
                if st.button("❌ Clear", use_container_width=True):
                    del st.session_state["agent_logs"]
                    if "agent_summary" in st.session_state: del st.session_state["agent_summary"]
                    st.rerun()
            else:
                st.info("Run analysis to see AI insights.")

        with col_main:
            st.markdown("### 📜 Workspace")
            
            # --- Density Controls ---
            expand_logic = st.toggle("🔍 Expand AI Logic Full View", value=False)
            
            # Apply edits if any
            if "desk_edits" in st.session_state:
                for ticker, edits in st.session_state["desk_edits"].items():
                    match_idx = desk_df.index[desk_df["ticker"] == ticker]
                    if not match_idx.empty:
                        for col, val in edits.items(): desk_df.at[match_idx[0], col] = val
                desk_df["Est. Cost (₹)"] = desk_df["Buy Qty"] * desk_df["LTP (₹)"]

            # Prepare Display Columns
            desk_df["AI Rationale Display"] = desk_df["AI Rationale"].apply(lambda x: (x[:80] + "...") if len(x) > 80 and not expand_logic else x)
            desk_df["Gap (₹) Status"] = desk_df["Gap (₹)"].apply(lambda x: f"✅ ₹{abs(x):,.0f} (Excl)" if x <= 0 else f"⚠️ ₹{x:,.0f}")

            COLUMN_ORDER = ["ticker", "LTP (₹)", "Hold Val (₹)", "Current Qty", "Target (₹)", "Gap (₹) Status", "AI Signal", "AI Rationale Display", "Suggested Qty", "Buy Qty", "Est. Cost (₹)"]
            
            # Calculate Height Dynamically
            desk_height = (len(desk_df) + 1) * 35 + 40

            # Add refresh counter to key to force reset on analysis completion
            editor_key = f"trading_workspace_editor_{st.session_state.get('desk_refresh_count', 0)}"

            edited_df = st.data_editor(
                desk_df,
                column_order=COLUMN_ORDER,
                column_config={
                    "ticker": st.column_config.TextColumn("Ticker", width="small"),
                    "LTP (₹)": st.column_config.NumberColumn("LTP", format="₹%.2f", width="small"),
                    "Buy Qty": st.column_config.NumberColumn("🛒 Buy", min_value=0, step=1, width="small"),
                    "Est. Cost (₹)": st.column_config.NumberColumn("Cost", format="₹%d", disabled=True, width="small"),
                    "Gap (₹) Status": st.column_config.TextColumn("Gap", width="medium"),
                    "AI Rationale Display": st.column_config.TextColumn("AI Logic", width="large" if expand_logic else "medium"),
                    "Current Qty": st.column_config.NumberColumn("Own", width="small"),
                    "Hold Val (₹)": st.column_config.NumberColumn("Value", format="₹%d", width="small"),
                    "AI Signal": st.column_config.TextColumn("Signal", width="small")
                },
                disabled=["ticker", "LTP (₹)", "Hold Val (₹)", "Target (₹)", "AI Rationale Display", "Suggested Qty", "Current Qty", "AI Signal", "Est. Cost (₹)", "Gap (₹) Status", "AI Rationale"],
                hide_index=True, use_container_width=True, height=desk_height, key=editor_key
            )
            
            if st.session_state.get(editor_key):
                edits = st.session_state[editor_key].get("edited_rows", {})
                if edits:
                    if "desk_edits" not in st.session_state: st.session_state["desk_edits"] = {}
                    for idx_str, row_edits in edits.items():
                        ticker = desk_df.iloc[int(idx_str)]["ticker"]
                        if ticker not in st.session_state["desk_edits"]: st.session_state["desk_edits"][ticker] = {}
                        st.session_state["desk_edits"][ticker].update(row_edits)
                    st.rerun()

        # --- 3. Execution Bar (Inside the main IF block) ---
        with col_ctrl:
            total_buy_cost = (edited_df["Buy Qty"] * edited_df["LTP (₹)"]).sum()
            st.metric("Estimated Cost", f"₹{total_buy_cost:,.0f}", delta=f"₹{invest_amt - total_buy_cost:,.0f}")
            if status == "DRAFT":
                col_sub, col_clr = st.columns([1, 1])
                with col_sub:
                    if st.button("📤 Submit for Approval", type="primary", use_container_width=True, disabled=(total_buy_cost == 0)):
                        # 1. Save state
                        final_orders = []
                        for _, row in edited_df.iterrows():
                            if row["Buy Qty"] > 0:
                                final_orders.append({"ticker": row["ticker"], "quantity": int(row["Buy Qty"]), "action": "BUY", "reason": row["AI Rationale"]})
                        
                        sanitized = []
                        for _, row in edited_df.iterrows():
                            row_dict = row.to_dict()
                            for k, v in row_dict.items():
                                if isinstance(v, float) and (math.isnan(v) or math.isinf(v)): row_dict[k] = 0.0
                            sanitized.append(row_dict)
                        
                        pending_ref.update({
                            "orders": final_orders, 
                            "ui_snapshot": sanitized,
                            "budget": invest_amt,
                            "status": "QUEUED" # Queue for approval
                        })
                        
                        # 2. Trigger Notification
                        with st.spinner("Notifying..."):
                            cmd = [sys.executable, os.path.join(project_root, "src", "agent", "main.py"), "--notify"]
                            env = os.environ.copy()
                            env["DASHBOARD_URL"] = dashboard_url
                            subprocess.run(cmd, env=env, check=False)
                        
                        st.session_state["remote_feedback"] = ("success", "✅ Plan Submitted for Approval!")
                        st.rerun()
                with col_clr:
                    if st.button("🛑 Clear Workspace", use_container_width=True):
                        pending_ref.update({"orders": [], "ui_snapshot": firestore.DELETE_FIELD})
                        st.rerun()

            elif status == "QUEUED":
                st.info("🛰️ Plan is Pending Approval (sent to email).")
                col_app, col_rej, col_res = st.columns([1, 1, 1])
                with col_app:
                    if st.button("🚀 Approve Now", type="primary", use_container_width=True):
                        # Explicitly preserve snapshot to be safe
                        pending_ref.update({
                            "status": "APPROVED", 
                            "approved_at": firestore.SERVER_TIMESTAMP
                        })
                        st.session_state["remote_feedback"] = ("success", "✅ Trading Plan Approved Locally")
                        st.rerun()
                with col_rej:
                    if st.button("✍️ Reject & Edit", use_container_width=True):
                        pending_ref.update({"status": "DRAFT"})
                        st.rerun()
                with col_res:
                    if st.button("📧 Resend Email", use_container_width=True):
                        cmd = [sys.executable, os.path.join(project_root, "src", "agent", "main.py"), "--notify"]
                        subprocess.run(cmd, env=os.environ.copy(), check=False)
                        st.toast("Approval Email Resent")

            elif status == "APPROVED":
                st.success("🚀 Batch Approved. Waiting for Bell...")
                if st.button("🛑 Revoke Approval", use_container_width=True):
                    pending_ref.update({"status": "QUEUED"})
                    st.rerun()

            elif status == "COMPLETED":
                st.success("✅ Trades Fully Executed!")
                if st.button("🔄 Start New Cycle", use_container_width=True):
                    pending_ref.set({"status": "DRAFT", "orders": []})
                    st.rerun()

elif st.session_state["active_tab"] == "🧠 AI Insights":
    st.subheader("🧠 Research Assistant")
    col_res1, col_res2 = st.columns([2, 1])
    
    with col_res1:
        st.markdown("ask me anything about your investments. I have context of your full portfolio.")
        user_query = st.chat_input("Ex: 'Is it time to exit ITC?' or 'Analyze my risk exposure'")
        
        if "chat_history" not in st.session_state: st.session_state.chat_history = []
        
        for msg in st.session_state.chat_history:
            st.chat_message(msg["role"]).write(msg["content"])
            
        if user_query:
            st.session_state.chat_history.append({"role": "user", "content": user_query})
            st.chat_message("user").write(user_query)
            
            with st.spinner("Thinking..."):
                try:
                    advisor = get_advisor()
                    # Prepare Context (Holdings + Strategy Configuration)
                    context_data = holdings_df.to_dict(orient="records") if not holdings_df.empty else []
                    strategy_context = {"universe": assets, "config": advisor.config}
                    response = advisor.ask_question(user_query, context_data, strategy_context)
                    st.chat_message("assistant").write(response)
                    st.session_state.chat_history.append({"role": "assistant", "content": response})
                except Exception as e:
                    st.error(f"Advisor Error: {e}")

    with col_res2:
        st.markdown("### 📊 Portfolio Reports")
        if st.button("✨ Generate New Health Report"):
             with st.spinner("Analyzing Portfolio..."):
                 try:
                     advisor = get_advisor()
                     context_data = holdings_df.to_dict(orient="records") if not holdings_df.empty else []
                     report = advisor.generate_report(context_data)
                     st.success("Report Generated!")
                     st.rerun()
                 except Exception as e: st.error(f"Failed to generate: {e}")
                 
        try:
            latest_report_ref = db.collection("advisor_reports").document("latest")
            doc = latest_report_ref.get()
            if doc.exists:
                report_data = doc.to_dict()
                st.caption(f"Last Generated: {report_data.get('generated_at').strftime('%Y-%m-%d %H:%M')}")
                st.markdown(report_data.get("report_text"))
            else:
                st.info("No reports yet. Click 'Generate' above.")
        except: pass

elif st.session_state["active_tab"] == "⚙️ Config":
    st.subheader("⚙️ Dynamic Strategy & AI Configuration")
    st.info("Manage your 'Source of Truth' in the Cloud. Changes are saved to Firestore and picked up by the Agent immediately.")
    
    from src.utils.config_loader import config as cloud_config
    
    try:
        # Load Data from Unified Loader
        agent_data = cloud_config.get_agent_settings(force_refresh=True)
        universe_data = cloud_config.get_universe(force_refresh=True)
        
        # 1. Agent settings editing
        st.markdown("### 🤖 Agent Intelligence Settings")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            current_settings = agent_data.get("agent_settings", {})
            new_model = st.selectbox("Model Name", 
                                   options=["gemini-2.0-flash", "gemini-1.5-pro"], 
                                   index=0 if current_settings.get("model_name") == "gemini-2.0-flash" else 1)
            new_location = st.text_input("GCP Location", value=current_settings.get("location", "us-east4"))
            
        with col2:
            new_risk = st.slider("Risk Threshold (0-10)", 0, 10, int(current_settings.get("risk_threshold", 8)))
            current_goals = agent_data.get("investment_goals", {})
            new_budget = st.number_input("💰 Global Budget (₹)", min_value=1000, value=int(current_goals.get("budget", 12500)), step=500)

        with col3:
            current_scoring = agent_data.get("scoring_rules", {})
            st.caption("AI Scoring Protocol")
            s_noise = st.number_input("Noise Score (Ignore)", value=int(current_scoring.get("noise", 0)))
            s_context = st.number_input("Context Score (Note)", value=int(current_scoring.get("context", 5)))
            s_critical = st.number_input("Critical Score (Action)", value=int(current_scoring.get("critical", 10)))

        st.divider()
        
        # 2. Universe (Strategy) Editing
        st.markdown("### 🎯 Investment Universe & Weights")
        current_assets = universe_data.get("assets", [])
        strat_df = pd.DataFrame(current_assets)
        
        # Ensure standard columns
        for col in ["ticker", "sector", "type", "cap_type", "target_weight", "target_amount"]:
            if col not in strat_df.columns: strat_df[col] = ""

        strat_df = strat_df[["ticker", "sector", "type", "cap_type", "target_weight", "target_amount"]]
        
        edited_strat = st.data_editor(
            strat_df,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "ticker": st.column_config.TextColumn("TICKER", required=True),
                "sector": st.column_config.TextColumn("SECTOR"),
                "type": st.column_config.SelectboxColumn("Type", options=["Core", "Growth", "High Risk", "ETF", "REIT"], required=True),
                "cap_type": st.column_config.SelectboxColumn("Cap", options=["Large", "Mid", "Small", "Liquid"]),
                "target_weight": st.column_config.NumberColumn("Weight (0-1)", min_value=0.0, max_value=1.0, step=0.01),
                "target_amount": st.column_config.NumberColumn("Target (₹)", min_value=0, step=1000)
            },
            key="strat_editor"
        )
        
        # 3. Save All Logic
        if st.button("💾 Save All Changes to Cloud", type="primary"):
            try:
                # Prepare Agent Settings
                new_agent_config = {
                    "agent_settings": {
                        "model_name": new_model,
                        "location": new_location,
                        "risk_threshold": new_risk
                    },
                    "investment_goals": {
                        "budget": new_budget,
                        "target_portfolio": ", ".join(edited_strat["ticker"].tolist())
                    },
                    "scoring_rules": {
                        "noise": s_noise,
                        "context": s_context,
                        "critical": s_critical
                    }
                }
                
                # Prepare Universe Data
                edited_strat = edited_strat.fillna("") 
                new_assets = edited_strat.to_dict(orient="records")
                for a in new_assets:
                    a["target_amount"] = int(a.get("target_amount") or 0)
                    a["target_weight"] = float(a.get("target_weight") or 0.0)
                
                # Save via Utility and Direct Firestore for Universe
                db.collection("config").document("agent_settings").set(new_agent_config)
                db.collection("config").document("universe").set({"assets": new_assets})
                
                # Clear UI cache for calculations
                pending_ref = db.collection("pending_orders").document("latest")
                pending_ref.update({"ui_snapshot": firestore.DELETE_FIELD, "status": "DRAFT"})

                st.success("✅ Cloud Configuration Updated! Changes will take effect in the next Agent run.")
                st.balloons()
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Save failed: {e}")

    except Exception as e:
        st.error(f"Configuration Hub Error: {e}")

st.divider()
st.caption("Zerodha Invest Agent v4.1 | Phase 2: AI Advisor & Draft Workflow")
