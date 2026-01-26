import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from fpdf import FPDF
import io

# --- 1. SETTINGS & UI ---
st.set_page_config(page_title="RPL Analytics Elite", layout="wide", page_icon="⚽")

st.markdown("""
    <style>
    .main { background-color: #FFFFFF; color: #212529; }
    .stMetric { background-color: #F8F9FA; border: 1px solid #DEE2E6; padding: 15px; border-radius: 10px; }
    [data-testid="stSidebar"] { background-color: #F1F3F5; border-right: 1px solid #DEE2E6; }
    .stTabs [data-baseweb="tab-list"] { background-color: #E9ECEF; border-radius: 8px; }
    .player-card { border: 2px solid #E9ECEF; padding: 20px; border-radius: 15px; background: white; margin-bottom: 20px; }
    .status-critical { color: #dc3545; font-weight: bold; }
    .suggestion-box { background-color: #F0FFF4; border-left: 5px solid #38A169; padding: 15px; border-radius: 5px; }
    .preview-box { background-color: #1B263B; padding: 25px; border-radius: 15px; color: white; text-align: center; }
    .momentum-up { color: #28a745; font-weight: bold; }
    .momentum-down { color: #dc3545; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

def calculate_analytics(df):
    weights = {'Technical': 0.35, 'Tactical': 0.25, 'Physical': 0.25, 'Mental': 0.15}
    current_year = 2026
    
    # Comprehensive column check for data integrity
    numeric_cols = ['pass_accuracy', 'dribble_success', 'interceptions', 'positioning_rating', 
                    'sprint_speed', 'stamina', 'composure', 'big_game_impact', 'market_value', 
                    'age', 'contract_end_year', 'mins_played', 'goals', 'assists',
                    'tpi_m1', 'tpi_m2', 'tpi_m3', 'tpi_m4', 'tpi_m5']
    
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        else:
            df[col] = 0 # Safety fallback for trend data
    
    # Core Analytics Logic
    df['Tech_Score'] = df['pass_accuracy'] * 0.6 + df['dribble_success'] * 0.4
    df['Tact_Score'] = (df['interceptions'] * 5) + (df['positioning_rating'] * 0.5)
    df['Phys_Score'] = (df['sprint_speed'] * 2) + (df['stamina'] * 0.2)
    df['Ment_Score'] = (df['composure'] * 0.7) + (df['big_game_impact'] * 0.3)
    df['TPI'] = (df['Tech_Score']*weights['Technical'] + df['Tact_Score']*weights['Tactical'] + 
                 df['Phys_Score']*weights['Physical'] + df['Ment_Score']*weights['Mental'])
    
    df['Transfer_Prob'] = (((df['TPI'] * 0.6) + (35 - df['age']) * 2) / 100).clip(0, 0.95)
    df['Years_Left'] = df['contract_end_year'] - current_year
    
    team_avg = {'Tech': df['Tech_Score'].mean(), 'Tact': df['Tact_Score'].mean(), 
                'Phys': df['Phys_Score'].mean(), 'Ment': df['Ment_Score'].mean(), 'TPI': df['TPI'].mean()}
    return df, team_avg

# --- 2. DATA SOURCE ---
st.sidebar.title("💎 RPL ELITE")
DEFAULT_URL = "https://raw.githubusercontent.com/Marclon11/Data/main/rpl_master_data.csv"
source = st.sidebar.radio("Data Source", ["Cloud Database", "Local Upload"])

df_raw = None
if source == "Cloud Database":
    try:
        df_raw = pd.read_csv(DEFAULT_URL)
        st.sidebar.success("✅ Cloud Sync Active")
    except:
        st.sidebar.warning("Cloud Sync Offline. Use Local.")
else:
    file = st.sidebar.file_uploader("Upload CSV", type="csv")
    if file: df_raw = pd.read_csv(file)

if df_raw is not None:
    df, team_avg = calculate_analytics(df_raw)
    
    # Session state for Profile Tab stability
    if 'p_select' not in st.session_state:
        st.session_state.p_select = df['player_name'].iloc[0]

    tabs = st.tabs(["👤 Profile", "📊 Comparison", "📋 Squad Health", "🌍 War Room", "🔥 Match Day", "📈 Progress Tracker"])

    # --- TAB 1: PROFILE ---
    with tabs[0]:
        p_name = st.selectbox("Select Player Profile", df['player_name'].unique(), key="prof_box")
        p_d = df[df['player_name'] == p_name].iloc[0]
        st.markdown('<div class="player-card">', unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1, 1, 2])
        with c1: st.image(p_d.get('club_logo_url', ""), width=100)
        with c2: st.image(p_d.get('photo_url', ""), width=150)
        with c3:
            st.header(p_name)
            st.write(f"**Club:** {p_d.get('club')} | **Minutes:** {int(p_d.get('mins_played', 0)):,}")
            if p_d['Years_Left'] <= 0: st.markdown('<p class="status-critical">⚠️ CONTRACT EXPIRED</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        m1, m2, m3 = st.columns(3)
        m1.metric("Goals", int(p_d.get('goals', 0)))
        m2.metric("TPI", f"{p_d['TPI']:.1f}")
        m3.metric("Value", f"${int(p_d.get('market_value', 0)):,}")

    # --- TAB 2: COMPARISON (BENCHMARKING FIXED) ---
    with tabs[1]:
        col1, col2 = st.columns(2)
        p1 = col1.selectbox("Primary Player", df['player_name'].unique(), key="c1")
        comp_on = col2.checkbox("Enable Comparison", key="cc")
        p1_d = df[df['player_name'] == p1].iloc[0]
        fig_comp = go.Figure()
        fig_comp.add_trace(go.Bar(x=['Tech', 'Tact', 'Phys', 'Ment'], y=[p1_d['Tech_Score'], p1_d['Tact_Score'], p1_d['Phys_Score'], p1_d['Ment_Score']], name=p1, marker_color='#212529'))
        if comp_on:
            p2 = st.selectbox("Compare With", df['player_name'].unique(), index=1, key="c2")
            p2_d = df[df['player_name'] == p2].iloc[0]
            fig_comp.add_trace(go.Bar(x=['Tech', 'Tact', 'Phys', 'Ment'], y=[p2_d['Tech_Score'], p2_d['Tact_Score'], p2_d['Phys_Score'], p2_d['Ment_Score']], name=p2, marker_color='#D00000'))
        fig_comp.add_trace(go.Scatter(x=['Tech', 'Tact', 'Phys', 'Ment'], y=[team_avg['Tech'], team_avg['Tact'], team_avg['Phys'], team_avg['Ment']], mode='lines+markers', name='Team Avg', line=dict(color='#007BFF', width=4, dash='dash'), marker=dict(size=12, symbol='diamond')))
        st.plotly_chart(fig_comp, use_container_width=True)

    # --- TAB 3: SQUAD HEALTH ---
    with tabs[2]:
        low = df[df['Phys_Score'] < 65]
        for _, p in low.iterrows(): st.error(f"🚨 **Risk:** {p['player_name']} ({p['Phys_Score']:.1f}%)")
        fig_health = px.scatter(df, x="Phys_Score", y="TPI", text="player_name", size="market_value", color="TPI", title="Readiness Talent Map")
        st.plotly_chart(fig_health, use_container_width=True)

    # --- TAB 4: WAR ROOM ---
    with tabs[4]: # Logic for Match Day
        pass # Placeholder for stability during build

    # --- TAB 5: PROGRESS TRACKER (NEW) ---
    with tabs[5]:
        st.header("📈 Season Momentum Analysis")
        f_name = st.selectbox("Track Player Form", df['player_name'].unique(), key="form_box")
        f_d = df[df['player_name'] == f_name].iloc[0]
        
        hist = [f_d['tpi_m5'], f_d['tpi_m4'], f_d['tpi_m3'], f_d['tpi_m2'], f_d['tpi_m1']]
        matches = ["Match -5", "Match -4", "Match -3", "Match -2", "Match -1"]
        
        diff = f_d['tpi_m1'] - f_d['tpi_m5']
        m_class = "momentum-up" if diff > 0 else "momentum-down"
        m_text = "IMPROVING" if diff > 2 else ("DECLINING" if diff < -2 else "STABLE")

        c1, c2 = st.columns([2, 1])
        with c1:
            fig_trend = px.line(x=matches, y=hist, markers=True, title=f"Form Trajectory: {f_name}")
            fig_trend.update_traces(line_color='#1B263B', line_width=4)
            st.plotly_chart(fig_trend, use_container_width=True)
        with c2:
            st.markdown(f"### Momentum Indicator")
            st.markdown(f"<div class='stMetric'>Status: <span class='{m_class}'>{m_text}</span><br>Net TPI Variance: {diff:+.1f}</div>", unsafe_allow_html=True)
            st.info("💡 **Strategy:** Consistent upward trends indicate a player ready for a starting role in high-pressure matches.")

else:
    st.info("Upload the Master CSV to begin analysis.")
