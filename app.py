import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# --- 1. SETTINGS & UI ---
st.set_page_config(page_title="RPL Analytics Elite", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #FFFFFF; color: #212529; }
    .stMetric { background-color: #F8F9FA; border: 1px solid #DEE2E6; padding: 15px; border-radius: 10px; }
    [data-testid="stSidebar"] { background-color: #F1F3F5; border-right: 1px solid #DEE2E6; }
    .stTabs [data-baseweb="tab-list"] { background-color: #E9ECEF; border-radius: 8px; }
    .player-card { border: 2px solid #E9ECEF; padding: 20px; border-radius: 15px; background: white; }
    .status-critical { color: #dc3545; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

def calculate_analytics(df):
    weights = {'Technical': 0.35, 'Tactical': 0.25, 'Physical': 0.25, 'Mental': 0.15}
    current_year = 2026
    
    # Numeric Conversion Safety
    numeric_cols = ['market_value', 'age', 'pass_accuracy', 'dribble_success', 'interceptions', 
                    'positioning_rating', 'sprint_speed', 'stamina', 'composure', 'big_game_impact', 'contract_end_year']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # Pillar Logic
    df['Tech_Score'] = df['pass_accuracy'] * 0.6 + df['dribble_success'] * 0.4
    df['Tact_Score'] = (df['interceptions'] * 5) + (df['positioning_rating'] * 0.5)
    df['Phys_Score'] = (df['sprint_speed'] * 2) + (df['stamina'] * 0.2)
    df['Ment_Score'] = (df['composure'] * 0.7) + (df['big_game_impact'] * 0.3)
    df['TPI'] = (df['Tech_Score']*weights['Technical'] + df['Tact_Score']*weights['Tactical'] + 
                 df['Phys_Score']*weights['Physical'] + df['Ment_Score']*weights['Mental'])
    
    # Transfer Probability (High TPI + Low Age)
    df['Transfer_Prob'] = ((df['TPI'] * 0.6) + (35 - df['age']) * 2) / 100
    df['Transfer_Prob'] = df['Transfer_Prob'].clip(0, 0.95)
    
    # Contract Risk (Current year is 2026)
    df['Years_Left'] = df['contract_end_year'] - current_year
    
    team_avg = {'Technical': df['Tech_Score'].mean(), 'Tactical': df['Tact_Score'].mean(),
                'Physical': df['Phys_Score'].mean(), 'Mental': df['Ment_Score'].mean()}
    return df, team_avg

# --- 2. MAIN APP ---
st.sidebar.title("💎 RPL ELITE")
file = st.sidebar.file_uploader("Upload CSV", type="csv")

if file:
    df, team_avg = calculate_analytics(pd.read_csv(file))
    tabs = st.tabs(["👤 Profile", "📊 Performance Analysis", "📋 Squad Health", "🌍 Transfer War Room"])

    # --- TAB 1: PROFILE ---
    with tabs[0]:
        p_name = st.selectbox("Select Player Profile", df['player_name'].unique(), key="prof_box")
        p_data = df[df['player_name'] == p_name].iloc[0]
        
        st.markdown('<div class="player-card">', unsafe_allow_html=True)
        c_l, c_p, c_t = st.columns([1, 1, 3])
        with c_l:
            if pd.notna(p_data.get('club_logo_url')) and p_data['club_logo_url'] != "":
                st.image(p_data['club_logo_url'], width=100)
        with c_p:
            if pd.notna(p_data.get('photo_url')) and p_data['photo_url'] != "":
                st.image(p_data['photo_url'], width=150)
            else: st.image("https://via.placeholder.com/150?text=Photo", width=150)
        with c_t:
            st.header(p_data['player_name'])
            st.subheader(f"{p_data.get('club')} | {p_data.get('nationality')}")
            st.write(f"**Contract Ends:** {int(p_data['contract_end_year'])} ({int(p_data['Years_Left'])} years left)")
            if p_data['Years_Left'] <= 0:
                st.markdown('<span class="status-critical">⚠️ CONTRACT EXPIRED / EXPIRING SOON</span>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Transfer Probability", f"{int(p_data['Transfer_Prob']*100)}%")
        m2.metric("Performance (TPI)", f"{p_data['TPI']:.1f}")
        m3.metric("Market Value", f"${int(p_data['market_value']):,}")

    # --- TAB 2: ANALYSIS ---
    with tabs[1]:
        # (Comparison logic remains stable as before)
        p1_n = st.selectbox("Compare Player Performance", df['player_name'].unique(), key="an_p1")
        p1_d = df[df['player_name'] == p1_n].iloc[0]
        fig = go.Figure(go.Bar(x=['Tech', 'Tact', 'Phys', 'Ment'], y=[p1_d['Tech_Score'], p1_d['Tact_Score'], p1_d['Phys_Score'], p1_d['Ment_Score']], marker_color='#212529'))
        fig.add_trace(go.Scatter(x=['Tech', 'Tact', 'Phys', 'Ment'], y=[team_avg['Technical'], team_avg['Tactical'], team_avg['Physical'], team_avg['Mental']], name='Team Average'))
        st.plotly_chart(fig, use_container_width=True)

    # --- TAB 3: SQUAD HEALTH (INJURY ALERTS PRESERVED) ---
    with tabs[2]:
        st.header("⚠️ Medical Readiness Index")
        low_phys = df[df['Phys_Score'] < 65]
        if not low_phys.empty:
            for _, p in low_phys.iterrows():
                st.error(f"**INJURY RISK:** {p['player_name']} - Readiness: {p['Phys_Score']:.1f}%. High load detected.")
        else: st.success("Squad meeting all readiness standards.")

    # --- TAB 4: TRANSFER WAR ROOM ---
    with tabs[3]:
        st.subheader("Executive Market Overview")
        
        # Display table with Contract Expiry and Transfer Probability
        display_df = df[['player_name', 'age', 'TPI', 'market_value', 'contract_end_year', 'Transfer_Prob']].copy()
        display_df['Transfer_Prob'] = display_df['Transfer_Prob'].apply(lambda x: f"{int(x*100)}%")
        display_df['market_value'] = display_df['market_value'].apply(lambda x: f"${int(x):,}")
        
        # Highlight critical contract risks
        st.dataframe(display_df.sort_values(by='contract_end_year'), use_container_width=True)
        
        # Strategy Visualization
        st.subheader("Investment Potential vs. Contract Risk")
        fig_strat = px.scatter(df, x="contract_end_year", y="TPI", size="market_value", color="Transfer_Prob",
                              text="player_name", title="High Performance vs Contract Expiry")
        st.plotly_chart(fig_strat, use_container_width=True)
        
        st.info("💡 **Strategic Advice:** Target players in the **Top-Left** of the chart (High TPI, Early Expiry). These players are elite performers who can be signed for a lower fee due to their contract situation.")

else:
    st.info("Upload the finalized Elite CSV to begin.")
