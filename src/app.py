import streamlit as st
import pandas as pd
from src.scanner import AlphaScout
from src.graph import KnowledgeGraph
from datetime import datetime, date

# Page Config
st.set_page_config(page_title="Ripple Scout", page_icon="📡", layout="wide")

# Title and Description
st.title("📡 Ripple Scout v1.0")
st.markdown("""
**Physical AI 产业链监测系统**  
捕捉上游核心资产 (Core) 的能量溢出，定位下游 (Neighbors) 的蓄势机会 (VCP/Spark)。
""")

# Sidebar: Configuration
st.sidebar.header("Configuration")
use_backtest = st.sidebar.checkbox("Enable Backtesting", value=False)
target_date_input = st.sidebar.date_input("Target Date", value=datetime.now())

target_date_str = None
if use_backtest:
    target_date_str = target_date_input.strftime("%Y-%m-%d")
    st.sidebar.warning(f"Simulating market as of mode: {target_date_str}")
else:
    st.sidebar.info("Using Live/Latest Data")

# Initialize Logic
@st.cache_resource
def get_engine():
    return AlphaScout(), KnowledgeGraph()

scout, kg = get_engine()

# Main Action Button
if st.button("🚀 Start System Scan", type="primary"):
    status_text = st.empty()
    progress_bar = st.progress(0)
    
    # 1. Scan Core
    status_text.text("Scanning Core Tickers...")
    core_tickers = kg.get_core_tickers()
    core_results = scout.scan_list(core_tickers, target_date=target_date_str)
    progress_bar.progress(30)
    
    if core_results.empty:
        st.error("Failed to fetch Core Data.")
    else:
        # Display Core Results
        active_cores = core_results[core_results['actionable'] == True]
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("1. Upstream Signals (Core)")
            if active_cores.empty:
                st.info("No active signals in Core list today.")
            else:
                st.success(f"Found {len(active_cores)} Active Cores!")
                st.dataframe(active_cores[['ticker', 'current_price', 'vcp_score', 'spark_score']])

        # 2. Scan Ripples
        status_text.text("Analyzing Ripple Effects...")
        
        ripple_candidates = set()
        ripple_sources = {} # Map candidate -> source(s)
        
        # Logic: If Core is Active -> Scan Neighbors
        # (Optional: Scan ALL neighbors if user wants, but strictly follows active core logic)
        scan_sources = active_cores if not active_cores.empty else core_results # Fallback? No, strictly active.
        
        # For Demo/Debug: Let's scan neighbors of ALL active cores. 
        # If no active cores, maybe show a warning but don't scan ripples?
        # User feedback implied "Ripple" logic.
        
        sources_to_scan = active_cores
        
        if sources_to_scan.empty:
            st.warning("No Upstream 'Energy' detected. Skipping Downstream Scan.")
            progress_bar.progress(100)
        else:
            for _, row in sources_to_scan.iterrows():
                t = row['ticker']
                neighbors = kg.get_neighbors(t)
                ripple_candidates.update(neighbors)
                for n in neighbors:
                    ripple_sources.setdefault(n, []).append(t)
            
            status_text.text(f"Scanning {len(ripple_candidates)} Downstream Candidates...")
            ripple_results = scout.scan_list(list(ripple_candidates), target_date=target_date_str)
            progress_bar.progress(90)
            
            with col2:
                st.subheader("2. Downstream Opportunities (Ripple)")
                if ripple_results.empty:
                    st.info("No data for candidates.")
                else:
                    active_ripples = ripple_results[ripple_results['actionable'] == True]
                    
                    if active_ripples.empty:
                        st.info("No actionable signals found in downstream pool.")
                    else:
                        st.success(f"Found {len(active_ripples)} Opportunities!")
                        
                        # Formatting for display
                        display_data = []
                        for _, row in active_ripples.iterrows():
                            # Extract simplified metrics
                            is_vcp = row['vcp_score'].get('is_vcp')
                            tightness = row['vcp_score'].get('tightness')
                            is_spark = row['spark_score'].get('is_spark')
                            rsi = row['spark_score'].get('rsi')
                            
                            sources = ripple_sources.get(row['ticker'], [])
                            
                            display_data.append({
                                "Ticker": row['ticker'],
                                "Price": row['current_price'],
                                "Driven By": ", ".join(sources),
                                "Pattern": "VCP" if is_vcp else "Spark",
                                "Tightness": f"{tightness:.2%}" if is_vcp else "-",
                                "RSI": rsi
                            })
                        
                        st.dataframe(pd.DataFrame(display_data))

    status_text.text("Scan Complete.")
    progress_bar.progress(100)

# Knowledge Graph Viewer
with st.expander("🕸️ View Knowledge Graph"):
    st.json(kg.graph)
