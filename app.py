import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from fpdf import FPDF
import io

# --- 1. UI & STYLING ---
st.set_page_config(page_title="RPL Analytics Elite", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #FFFFFF; color: #212529; }
    .stMetric { background-color: #F8F9FA; border: 1px solid #DEE2E6; padding: 15px; border-radius: 10px; }
    [data-testid="stSidebar"] { background-color: #F1F3F5; border-right: 1px solid #DEE2E6; }
    .stTabs [data-baseweb="tab-list"] { background-color: #E9ECEF; border-radius: 8px; }
    .player-card { border: 2px solid #E9ECEF; padding: 20px; border-radius: 15px; background: white; }
    .status-critical { color: #dc3545; font-weight: bold; }
    .suggestion-box { background-color: #F0FFF4; border-left: 5px solid #38A169; padding: 15px; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

def calculate_analytics(df):
    weights = {'Technical': 0.35, 'Tactical': 0.25, 'Physical': 0.25, 'Mental': 0.15}
    # Ensure numeric types and fill missing values to prevent crash on profile switch
    cols = ['pass_accuracy', 'dribble_success', 'interceptions', 'positioning_rating', 
            'sprint_speed', 'stamina', 'composure', 'big_game_impact', 'market_value', 
            'age', 'contract_end_year', 'mins_played', 'goals', 'assists']
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    df['Tech_Score'] = df['pass_accuracy'] * 0.6 + df['dribble_success'] * 0.4
    df['Tact_Score'] = (df['interceptions'] * 5) + (df['positioning_rating'] * 0.5)
    df['Phys_Score'] = (df['sprint_speed'] * 2) + (df['stamina'] * 0.2)
    df['Ment_Score'] = (df['composure'] * 0.7) + (df['big_game_impact'] * 0.3)
    df['TPI'] = (df['Tech_Score']*weights['Technical'] + df['Tact_Score']*weights['Tactical'] + 
                 df['Phys_Score']*weights['Physical'] + df['Ment_Score']*weights['Mental'])
    
    df['Transfer_Prob'] = (((df['TPI'] * 0.6) + (35 - df['age']) * 2) / 100).clip(0, 0.95)
    df['Years_Left'] = df['contract_end_year'] - 2026
    
    team_avg = {'Tech': df['Tech_Score'].mean(), 'Tact': df['Tact_Score'].mean(), 
                'Phys': df['Phys_Score'].mean(), 'Ment': df['Ment_Score'].mean()}
    return df, team_avg

# --- 2. MAIN APP ---
st.sidebar.title("💎 RPL ELITE")
file = st.sidebar.file_uploader("Upload Elite CSV", type="csv")

if file:
    df, team_avg = calculate_analytics(pd.read_csv(file))
    tabs = st.tabs(["👤 Profile", "📊 Comparison Analysis", "📋 Squad Health", "🌍 Transfer War Room"])

    # --- TAB 1: PROFILE (STABILITY FIX) ---
    with tabs[0]:
        # Using a safer selection method to ensure all players load correctly
        p_list = df['player_name'].unique().tolist()
        p_name = st.selectbox("Select Player Profile", p_list, key="prof_select_unique")
        
        # Filter data strictly for the selected player
        p_d = df[df['player_name'] == p_name].iloc[0]
        
        st.markdown('<div class="player-card">', unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1, 1, 2])
        with c1:
            if pd.notna(p_d.get('club_logo_url')) and p_d['club_logo_url'] != "":
                st.image(p_d['club_logo_url'], width=100)
        with c2:
            if pd.notna(p_d.get('photo_url')) and p_d['photo_url'] != "":
                st.image(p_d['photo_url'], width=150)
            else: st.image("https://via.placeholder.com/150?text=Photo", width=150)
        with c3:
            st.header(p_name)
            st.subheader(f"{p_d.get('club', 'RPL Club')} | {p_d.get('nationality', 'N/A')}")
            st.write(f"**Total Career Minutes:** {int(p_d.get('mins_played', 0)):,} mins")
            if p_d['Years_Left'] <= 0:
                st.markdown('<p class="status-critical">⚠️ CONTRACT EXPIRED</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Goals (Total)", int(p_d.get('goals', 0)))
        m2.metric("TPI Index", f"{p_d['TPI']:.1f}")
        m3.metric("Market Value", f"${int(p_d.get('market_value', 0)):,}")

    # --- TAB 2: COMPARISON (TEAM AVG LOCKED) ---
    with tabs[1]:
        st.subheader("Performance Comparison & Benchmarking")
        col1, col2 = st.columns(2)
        with col1: p1_n = st.selectbox("Primary Player", df['player_name'].unique(), key="comp_p1")
        with col2: comp_on = st.checkbox("Enable Comparison Mode", key="comp_check")
        
        p1_data = df[df['player_name'] == p1_n].iloc[0]
        cats = ['Technical', 'Tactical', 'Physical', 'Mental']
        fig = go.Figure()
        fig.add_trace(go.Bar(x=cats, y=[p1_data['Tech_Score'], p1_data['Tact_Score'], p1_data['Phys_Score'], p1_data['Ment_Score']], name=p1_n, marker_color='#212529'))
        
        if comp_on:
            p2_n = st.selectbox("Compare With", df['player_name'].unique(), index=1, key="comp_p2")
            p2_data = df[df['player_name'] == p2_n].iloc[0]
            fig.add_trace(go.Bar(x=cats, y=[p2_data['Tech_Score'], p2_data['Tact_Score'], p2_data['Phys_Score'], p2_data['Ment_Score']], name=p2_n, marker_color='#D00000'))
        
        # High Visibility Team Average Line Overlay
        fig.add_trace(go.Scatter(x=cats, y=[team_avg['Tech'], team_avg['Tact'], team_avg['Phys'], team_avg['Ment']], 
                                 mode='lines+markers', name='Team Average', line=dict(color='#007BFF', width=4, dash='dash'), marker=dict(size=12, symbol='diamond')))
        st.plotly_chart(fig, use_container_width=True)

    # --- TAB 3: SQUAD HEALTH (TALENT MAP RESTORED) ---
    with tabs[2]:
        st.header("📋 Squad Strategic Readiness")
        low = df[df['Phys_Score'] < 65]
        if not low.empty:
            for _, p in low.iterrows(): st.error(f"🚨 **Injury Risk:** {p['player_name']} ({p['Phys_Score']:.1f}%)")
        else: st.success("All players fit and meeting readiness standards.")
        
        # RESTORED: Talent Map Visualization
        fig_health = px.scatter(df, x="Phys_Score", y="TPI", text="player_name", size="market_value", color="TPI",
                                labels={"Phys_Score": "Physical Readiness (%)", "TPI": "Performance Index (TPI)"},
                                title="Talent Map: Readiness vs. Performance")
        fig_health.update_traces(textposition='top center')
        st.plotly_chart(fig_health, use_container_width=True)

    # --- TAB 4: TRANSFER WAR ROOM (SUGGESTER LOCKED) ---
    with tabs[3]:
        st.subheader("Decision Support: Opportunity & Replacement")
        fig_war = px.scatter(df, x="contract_end_year", y="TPI", size="market_value", color="Transfer_Prob", text="player_name", title="Performance vs. Contract Expiry")
        st.plotly_chart(fig_war, use_container_width=True)
        
        st.divider()
        st.subheader("🔍 Automated Replacement Suggester")
        at_risk = df[df['Years_Left'] <= 1].sort_values(by='TPI', ascending=False)
        if not at_risk.empty:
            target_p = st.selectbox("At-Risk Player to Replace", at_risk['player_name'].unique(), key="sug_select")
            t_data = df[df['player_name'] == target_p].iloc[0]
            suggestions = df[(df['player_name'] != target_p) & (df['TPI'] >= t_data['TPI'] - 10) & (df['Years_Left'] > 1)].sort_values(by='TPI', ascending=False)
            if not suggestions.empty:
                st.markdown(f'<div class="suggestion-box"><b>Top Recommended Replacements for {target_p}:</b><br>' + 
                            "<br>".join([f"✅ {r['player_name']} ({r['club']}) - TPI: {r['TPI']:.1f}, Value: ${int(r['market_value']):,}" for _, r in suggestions.head(3).iterrows()]) + 
                            '</div>', unsafe_allow_html=True)
        
        st.dataframe(df[['player_name', 'club', 'TPI', 'market_value', 'contract_end_year']].sort_values
