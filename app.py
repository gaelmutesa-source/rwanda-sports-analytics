import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from fpdf import FPDF
import io

# --- 1. SETTINGS & UI ---
st.set_page_config(page_title="RPL Analytics Elite", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #FFFFFF; color: #212529; }
    .stMetric { background-color: #F8F9FA; border: 1px solid #DEE2E6; padding: 15px; border-radius: 10px; }
    [data-testid="stSidebar"] { background-color: #F1F3F5; border-right: 1px solid #DEE2E6; }
    .stTabs [data-baseweb="tab-list"] { background-color: #E9ECEF; border-radius: 8px; }
    .player-card { border: 2px solid #E9ECEF; padding: 20px; border-radius: 15px; background: white; }
    .probability-high { color: #28a745; font-weight: bold; }
    .probability-med { color: #fd7e14; font-weight: bold; }
    .probability-low { color: #dc3545; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

def calculate_analytics(df):
    weights = {'Technical': 0.35, 'Tactical': 0.25, 'Physical': 0.25, 'Mental': 0.15}
    
    # Numeric Safety
    numeric_cols = ['market_value', 'age', 'pass_accuracy', 'dribble_success', 'interceptions', 
                    'positioning_rating', 'sprint_speed', 'stamina', 'composure', 'big_game_impact']
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
    
    # NEW: Transfer Probability Formula
    # Logic: Higher TPI + Lower Age + Lower Value relative to TPI = Higher Probability
    df['Transfer_Prob'] = ((df['TPI'] * 0.6) + (35 - df['age']) * 2) / 100
    df['Transfer_Prob'] = df['Transfer_Prob'].clip(0, 0.95) # Cap at 95%
    
    team_avg = {'Technical': df['Tech_Score'].mean(), 'Tactical': df['Tact_Score'].mean(),
                'Physical': df['Phys_Score'].mean(), 'Mental': df['Ment_Score'].mean()}
    return df, team_avg

# --- 2. MAIN APP ---
st.sidebar.title("💎 RPL ELITE")
file = st.sidebar.file_uploader("Upload CSV", type="csv")

if file:
    df, team_avg = calculate_analytics(pd.read_csv(file))
    tabs = st.tabs(["👤 Profile", "📊 Performance Analysis", "📋 Squad Health", "🌍 Global Ranking"])

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
            st.write(f"**Career Minutes:** {int(p_data.get('mins_played', 0))} | **Transfer Prob:** {int(p_data['Transfer_Prob']*100)}%")
        st.markdown('</div>', unsafe_allow_html=True)
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Goals", int(p_data.get('goals', 0)))
        m2.metric("TPI Score", f"{p_data['TPI']:.1f}")
        m3.metric("Market Value", f"${int(p_data['market_value']):,}")

    # --- TAB 2: ANALYSIS (COMPARISON & BENCHMARKING) ---
    with tabs[1]:
        col1, col2 = st.columns(2)
        with col1: p1_n = st.selectbox("Primary Player", df['player_name'].unique(), key="an_p1")
        with col2: compare = st.checkbox("Enable Comparison Mode", key="an_comp")
        
        p1_d = df[df['player_name'] == p1_n].iloc[0]
        cats = ['Technical', 'Tactical', 'Physical', 'Mental']
        fig = go.Figure()
        fig.add_trace(go.Bar(x=cats, y=[p1_d['Tech_Score'], p1_d['Tact_Score'], p1_d['Phys_Score'], p1_d['Ment_Score']], name=p1_n, marker_color='#212529'))
        fig.add_trace(go.Scatter(x=cats, y=[team_avg['Technical'], team_avg['Tactical'], team_avg['Physical'], team_avg['Mental']], mode='lines+markers', name='Team Average', line=dict(color='#007BFF', dash='dash')))
        
        if compare:
            p2_n = st.selectbox("Compare With", df['player_name'].unique(), index=1, key="an_p2")
            p2_d = df[df['player_name'] == p2_n].iloc[0]
            fig.add_trace(go.Bar(x=cats, y=[p2_d['Tech_Score'], p2_d['Tact_Score'], p2_d['Phys_Score'], p2_d['Ment_Score']], name=p2_n, marker_color='#D00000'))
        
        fig.update_layout(title="Pillar Benchmarking", yaxis_title="Score (0-100)")
        st.plotly_chart(fig, use_container_width=True)

    # --- TAB 3: SQUAD HEALTH (INJURY ALERTS) ---
    with tabs[2]:
        st.header("⚠️ Medical Readiness Index")
        low_phys = df[df['Phys_Score'] < 65]
        if not low_phys.empty:
            for _, p in low_phys.iterrows():
                st.error(f"**INJURY RISK:** {p['player_name']} - Readiness: {p['Phys_Score']:.1f}%. Career Load: {int(p['mins_played'])} mins.")
        else: st.success("Squad meeting all readiness standards.")
        
        fig_sq = px.scatter(df, x="Phys_Score", y="TPI", text="player_name", color="TPI", title="Squad Talent Map")
        st.plotly_chart(fig_sq, use_container_width=True)

    # --- TAB 4: GLOBAL RANKING (TRANSFER PROBABILITY FIXED) ---
    with tabs[3]:
        st.subheader("Global Squad Ranking & Transfer Probability")
        
        # Data Preparation
        rank_df = df[['player_name', 'club', 'age', 'market_value', 'TPI', 'Transfer_Prob']].copy()
        rank_df['Transfer_Prob'] = rank_df['Transfer_Prob'].apply(lambda x: f"{int(x*100)}%")
        rank_df['market_value'] = rank_df['market_value'].apply(lambda x: f"${int(x):,}")
        
        st.dataframe(rank_df.sort_values(by='TPI', ascending=False), use_container_width=True)
        
        st.info("💡 **Indicator Logic:** High Probability is assigned to young players (under 25) with high Performance (TPI) whose market value has not yet reached its peak potential.")

else:
    st.info("Upload the finalized Elite CSV to begin.")
