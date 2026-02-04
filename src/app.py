import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
from src.scanner import AlphaScout
from src.graph import KnowledgeGraph
from datetime import datetime

# Page Config
st.set_page_config(page_title="Ripple Scout", page_icon="📡", layout="wide")

# Sidebar Navigation
page = st.sidebar.radio("Navigation", ["Live Scanner", "Backtest Analysis"])

# --- SHARED RESOURCES ---
@st.cache_resource
def get_engine():
    return AlphaScout(), KnowledgeGraph()

scout, kg = get_engine()

# --- PAGE 1: LIVE SCANNER ---
if page == "Live Scanner":
    st.title("📡 Ripple Scout - Live Monitor")
    st.markdown("""
    **Physical AI 产业链监测系统**  
    捕捉上游核心资产 (Core) 的能量溢出，定位下游 (Neighbors) 的蓄势机会。
    """)

    # Sidebar: Configuration
    st.sidebar.header("Configuration")
    use_backtest = st.sidebar.checkbox("Enable Specific Date Mode", value=False)
    target_date_input = st.sidebar.date_input("Target Date", value=datetime.now())

    target_date_str = None
    if use_backtest:
        target_date_str = target_date_input.strftime("%Y-%m-%d")
        st.sidebar.warning(f"Simulating market as of: {target_date_str}")
    else:
        st.sidebar.info("Using Live/Latest Data")

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
            # Only scan if core has activity, OR if user wants to see general status (but V1 logic = causal)
            sources_to_scan = active_cores
            
            if sources_to_scan.empty:
                st.warning("No Upstream 'Energy' detected. Skipping Downstream Scan.")
                progress_bar.progress(100)
            else:
                status_text.text("Analyzing Ripple Effects...")
                ripple_candidates = set()
                ripple_sources = {} 
                
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
                    st.subheader("2. Downstream Opportunities")
                    if ripple_results.empty:
                        st.info("No data for candidates.")
                    else:
                        active_ripples = ripple_results[ripple_results['actionable'] == True]
                        
                        if active_ripples.empty:
                            st.info("No actionable signals found downstream.")
                        else:
                            st.success(f"Found {len(active_ripples)} Opportunities!")
                            
                            display_data = []
                            for _, row in active_ripples.iterrows():
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
    
    with st.expander("🕸️ View Knowledge Graph"):
        st.json(kg.graph)


# --- PAGE 2: BACKTEST ANALYSIS ---
elif page == "Backtest Analysis":
    st.title("📊 Ripple Effect Backtest Analysis")
    st.markdown("Analyze historical performance of Core -> Neighbor signals.")
    
    # Load Data
    data_path = Path("data/ripple_backtest_results.csv")
    if not data_path.exists():
        st.error("Results file not found. Please run `python scripts/validate_ripples.py` first.")
    else:
        df = pd.read_csv(data_path)
        
        # 1. Overview Stats
        st.subheader("Global Statistics")
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Events Analyzed", len(df))
        c2.metric("Avg 20-Day Return", f"{df['return_20d'].mean()*100:.2f}%")
        c3.metric("Win Rate (>0%)", f"{(df['return_20d'] > 0).mean()*100:.1f}%")
        
        # 2. Pair Performance (Scatter Plot)
        st.subheader("Core-Neighbor Pair Performance")
        
        # Group by Core+Neighbor
        pair_stats = df.groupby(['core_ticker', 'neighbor']).agg(
            events=('core_date', 'count'),
            avg_return_20d=('return_20d', 'mean'),
            win_rate=('return_20d', lambda x: (x > 0).mean())
        ).reset_index()
        
        # Filter low sample size
        min_events = st.slider("Min Events Count", 5, 50, 10)
        filtered_pairs = pair_stats[pair_stats['events'] >= min_events]
        
        fig = px.scatter(
            filtered_pairs,
            x="win_rate",
            y="avg_return_20d",
            size="events",
            color="core_ticker",
            hover_data=["neighbor"],
            title=f"Risk/Reward Map (Min {min_events} Events)",
            labels={"win_rate": "Win Rate", "avg_return_20d": "Avg 20-Day Return"}
        )
        # Add reference lines
        fig.add_hline(y=0, line_dash="dash", line_color="red")
        fig.add_vline(x=0.5, line_dash="dash", line_color="gray")
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 3. Drill Down
        st.subheader("Drill Down: Specific Pair")
        
        col_sel1, col_sel2 = st.columns(2)
        with col_sel1:
            selected_core = st.selectbox("Select Core", sorted(df['core_ticker'].unique()))
        
        # Filter neighbors for this core
        avail_neighbors = sorted(df[df['core_ticker'] == selected_core]['neighbor'].unique())
        with col_sel2:
            selected_neighbor = st.selectbox("Select Neighbor", avail_neighbors)
            
        # Show subset data
        subset = df[(df['core_ticker'] == selected_core) & (df['neighbor'] == selected_neighbor)]
        
        st.markdown(f"**{selected_core} → {selected_neighbor}** ({len(subset)} events)")
        
        # Stats for this pair
        s1, s2, s3 = st.columns(3)
        s1.metric("Pair Avg Return", f"{subset['return_20d'].mean()*100:.2f}%")
        s2.metric("Pair Win Rate", f"{(subset['return_20d']>0).mean()*100:.1f}%")
        s3.metric("Max Return", f"{subset['return_20d'].max()*100:.2f}%")

        # Histogram of returns
        fig_hist = px.histogram(subset, x="return_20d", nbins=20, title="Return Distribution (20 Days)",
                               labels={"return_20d": "Return"})
        st.plotly_chart(fig_hist, use_container_width=True)
        
        # Table of recent signals
        st.write("Recent Signals:")
        st.dataframe(subset.sort_values("core_date", ascending=False).head(10))
